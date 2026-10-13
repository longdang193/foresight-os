import asyncio
import hashlib
import inspect
import json
import time
from dataclasses import dataclass, replace
from uuid import uuid4
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, StageInput
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor
from foresight_os.controller.budgets import BudgetState
from foresight_os.domain.validation import ValidationError
from foresight_os.runtime.metrics import (
    BudgetExceededError,
    CleanupError,
    ConcurrentAggregate,
    FailureClass,
    RunMetrics,
    RunResult,
)
from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope, ScopeOwnership
from foresight_os.runtime.crawl4ai import bind_crawl4ai
from foresight_os.runtime.external_signals import load_hosted_mcp_bindings
from foresight_os.runtime.web_search import bind_web_search
from foresight_os.persistence.analysis_store import AnalysisStore, StageReceipt
from foresight_os.runtime.page_retrieval import PageRetrievalCapability, bind_page_retrieval
from foresight_os.runtime.local_toolbelt import bind_local_toolbelt
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.controller.skills import SkillRegistry


@dataclass(frozen=True)
class CanonicalStageResult:
    result_references: tuple[str, ...]
    result_hashes: tuple[str, ...]
    output: object

    def __post_init__(self) -> None:
        if not self.result_references or len(self.result_references) != len(self.result_hashes):
            raise ValueError("canonical stage results require matching non-empty references and hashes")
        if len(self.result_references) == 1 and self.result_hashes[0] != _canonical_result_hash(self.output):
            raise ValueError("canonical stage result hash does not match its output")


CanonicalResultCommitter = Callable[
    [Any, object, Mapping[str, Any]],
    CanonicalStageResult | None | Awaitable[CanonicalStageResult | None],
]


async def _close_agents(agents: list[object]) -> list[BaseException]:
    errors: list[BaseException] = []
    for agent in agents:
        close = getattr(agent, "close", None)
        if close is None:
            continue
        try:
            result = close()
            if inspect.isawaitable(result):
                await result
        except BaseException as error:
            errors.append(error)
    return errors


async def _run_native_stage(
    pattern: ExecutionPattern,
    prompt: str,
    client: Any,
    roles: list[dict[str, str]],
    metrics: RunMetrics | None = None,
    run_context: dict[str, Any] | None = None,
) -> list[object]:
    from agent_framework.orchestrations import ConcurrentBuilder, GroupChatBuilder, HandoffBuilder, SequentialBuilder

    agents = []
    factory = AgentFactory(client)
    if not hasattr(client, "as_agent"):
        raise RuntimeError("a native MAF client with as_agent() is required for this pattern")
    context = dict(run_context or {})
    context.setdefault("skill_registry", SkillRegistry())
    context["handoff"] = pattern == ExecutionPattern.HANDOFF
    for index, role in enumerate(roles or [{"purpose": "participant"}], 1):
        participant = ParticipantConfig.from_mapping(role, f"participant-{index}")
        agent = factory.create(participant, context)
        agents.append(agent)
    if pattern == ExecutionPattern.SEQUENTIAL:
        workflow = SequentialBuilder(participants=agents, output_from="all").build()
    elif pattern == ExecutionPattern.CONCURRENT:
        workflow = ConcurrentBuilder(participants=agents, output_from="all").build()
    elif pattern == ExecutionPattern.HANDOFF:
        builder = HandoffBuilder(participants=agents, output_from="all").with_start_agent(agents[0])
        for source, role in zip(agents, roles, strict=False):
            allowed_targets = set(
                role.get("handoff_targets", ())
                if isinstance(role, dict)
                else getattr(role, "handoff_targets", ())
            )
            targets = [target for target in agents if target.id in allowed_targets]
            if targets:
                builder.add_handoff(source, targets)
        workflow = builder.build()
    elif pattern == ExecutionPattern.GROUP_CHAT:
        async def select_speaker(state: Any) -> str:
            return agents[state.current_round % len(agents)].id

        workflow = GroupChatBuilder(
            participants=agents,
            selection_func=select_speaker,
            max_rounds=4,
            output_from="all",
        ).build()
    else:
        return [await agents[0].run(prompt)]
    if metrics is None:
        result = await workflow.run(prompt)
    else:
        agent_ids = {getattr(agent, "id", None) for agent in agents}
        observed_rounds: set[int] = set()
        stream = await workflow.run(prompt, stream=True)
        async for event in stream:
            if event.type == "executor_invoked" and event.executor_id in agent_ids:
                metrics.model_calls += 1
            elif event.type == "handoff_sent":
                metrics.handoffs += 1
            elif pattern == ExecutionPattern.GROUP_CHAT and event.type == "group_chat":
                data = event.data
                if type(data).__name__ == "GroupChatRequestSentEvent":
                    observed_rounds.add(getattr(data, "round_index", len(observed_rounds)))
        result = await stream.get_final_response()
        metrics.chat_rounds += len(observed_rounds)
    outputs = result.get_outputs()
    return list(outputs) if outputs else [result]


def _make_stage(stage_name: str):
    async def stage(message: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> None:
        staged = dict(message)
        completed = list(staged.get("completed_stages", []))
        completed.append(stage_name)
        staged["completed_stages"] = completed
        await ctx.send_message(staged)
        await ctx.yield_output(staged)

    return stage


def _stage_input_payload(stage_input: object) -> dict[str, object]:
    if isinstance(stage_input, StageInput):
        return stage_input.to_payload()
    return {"decision_question": stage_input}


def _stage_fingerprints(
    stage: Any,
    stage_input: object,
    skill_ids: tuple[str, ...],
) -> tuple[str, str]:
    participants = tuple(ParticipantConfig.from_mapping(item).id for item in getattr(stage, "participants", ()))
    input_payload = _stage_input_payload(stage_input)
    dependency_outputs = input_payload.get("dependency_outputs", {})
    semantic_payload = {
        "stage_id": getattr(stage, "stage_id", "stage"),
        "pattern": str(getattr(stage, "pattern", "direct")),
        "objective": getattr(stage, "objective", ""),
        "expected_result": getattr(stage, "expected_result", ""),
        "research_needs": getattr(stage, "research_needs", ()),
        "specialist_ids": participants,
        "skill_ids": tuple(skill_ids),
        "decision_question": input_payload.get("decision_question", ""),
        "horizon": input_payload.get("horizon", ""),
        "relevant_constraints": input_payload.get("relevant_constraints", ()),
        "dependency_result_hashes": {
            stage_id: _canonical_result_hash(output)
            for stage_id, output in dict(dependency_outputs).items()
        },
    }
    policy_payload = {"limits": getattr(stage, "limits", {})}
    return (
        hashlib.sha256(json.dumps(semantic_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest(),
        hashlib.sha256(json.dumps(policy_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest(),
    )


def _stage_cache_key(stage: Any, current: object, skill_ids: tuple[str, ...]) -> str:
    return _stage_fingerprints(stage, current, skill_ids)[0]


def _committed_cache_output(entry: Any, canonical_records: dict[str, object] | None = None) -> tuple[bool, object]:
    if isinstance(entry, dict):
        references = entry.get("result_references", entry.get("canonical_result_ids", ()))
        hashes = entry.get("result_hashes", ())
        valid = entry.get("status") == "committed" and entry.get("provenance_complete") is True and bool(references) and bool(hashes) and "output" in entry
        if not valid or not _canonical_provenance_matches(references, hashes, canonical_records):
            return False, None
        values = [canonical_records[reference] for reference in references]
        return True, values[0] if len(values) == 1 else values
    valid = (
        getattr(entry, "status", None) == "committed"
        and getattr(entry, "provenance_complete", False) is True
        and bool(getattr(entry, "result_references", ()))
        and bool(getattr(entry, "result_hashes", ()))
    )
    references = tuple(getattr(entry, "result_references", ()))
    hashes = tuple(getattr(entry, "result_hashes", ()))
    if not valid or not _canonical_provenance_matches(references, hashes, canonical_records):
        return False, None
    values = [canonical_records[reference] for reference in references]
    return True, values[0] if len(values) == 1 else values


def _canonical_result_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def _canonical_provenance_matches(
    references: tuple[str, ...] | list[str],
    hashes: tuple[str, ...] | list[str],
    canonical_records: dict[str, object] | None,
) -> bool:
    if canonical_records is None or len(references) != len(hashes) or not references:
        return False
    return all(
        reference in canonical_records and _canonical_result_hash(canonical_records[reference]) == expected_hash
        for reference, expected_hash in zip(references, hashes, strict=True)
    )


def run_sequential_steps(stage_names: list[str]) -> dict[str, Any]:
    executors = [
        FunctionExecutor(
            _make_stage(name),
            id=name,
            input=dict,
            output=dict,
            workflow_output=dict,
        )
        for name in stage_names
    ]
    workflow = WorkflowBuilder(start_executor=executors[0], output_from=[executors[-1]]).add_chain(executors).build()

    async def run() -> dict[str, Any]:
        result = await workflow.run({"completed_stages": []})
        outputs = result.get_outputs()
        return outputs[-1]

    return asyncio.run(run())


async def run_recipe_async(
    recipe: ExecutionRecipe,
    prompt: str,
    client: Any | None = None,
    run_id: str | None = None,
    run_context: dict[str, Any] | None = None,
) -> RunResult:
    started = time.perf_counter()
    metrics = RunMetrics(run_id or f"run-{uuid4().hex}", recipe.name.value, recipe.pattern)
    outputs: list[object] = []
    metrics.cleanup_complete = True
    budget = BudgetState(recipe.max_agent_steps, recipe.max_correction_rounds, recipe.max_total_agent_calls)
    factory = AgentFactory(client) if client is not None else None
    context = dict(run_context or {})
    context.setdefault("skill_registry", SkillRegistry())
    receipt_store = context.get("analysis_store") or context.get("stage_receipt_store")
    if isinstance(receipt_store, AnalysisStore):
        context.setdefault("stage_receipts", receipt_store.load_stage_receipts())
    context.setdefault("canonical_records", {})
    context.setdefault("canonical_outputs", {})
    context.setdefault("stage_receipts", {})
    changed_record_ids = tuple(str(item) for item in context.get("changed_record_ids", context.get("changed_ids", ())))
    relation_index = context.get("relation_index")
    if changed_record_ids and relation_index is not None:
        impact_closure = getattr(relation_index, "impact_closure", None) or getattr(relation_index, "impacted_descendants")
        impacted_ids = set(impact_closure(changed_record_ids))
        context["invalidated_stage_ids"] = tuple(
            sorted(
                stage_id
                for stage_id, receipt in context["stage_receipts"].items()
                if impacted_ids.intersection(getattr(receipt, "result_references", ()))
            )
        )
    for stage_id, receipt in context["stage_receipts"].items():
        if stage_id in context["canonical_outputs"] or not context["canonical_records"]:
            continue
        values = [context["canonical_records"].get(reference) for reference in receipt.result_references]
        if all(value is not None for value in values):
            context["canonical_outputs"][stage_id] = values[0] if len(values) == 1 else values
    supplied_scope = context.get("scope")
    scope = supplied_scope or CapabilityScope(ownership=ScopeOwnership.RUN)
    owns_scope = supplied_scope is None or getattr(scope, "ownership", ScopeOwnership.BORROWED) == ScopeOwnership.RUN
    context["scope"] = scope
    context["metrics"] = metrics
    context["budget"] = budget
    context.setdefault("capability_resolver", CapabilityResolver())
    required_capabilities: set[str] = set()
    for stage in recipe.stages or ():
        selected_skills = context["skill_registry"].resolve(tuple(getattr(stage, "skill_ids", ())))
        required_capabilities.update(context["skill_registry"].required_capabilities(selected_skills))
        for participant in getattr(stage, "participants", ()):
            required_capabilities.update(ParticipantConfig.from_mapping(participant).capability_ids)
    if not recipe.stages:
        for participant in recipe.roles:
            required_capabilities.update(ParticipantConfig.from_mapping(participant).capability_ids)
    context["required_capabilities"] = tuple(sorted(required_capabilities))
    local_bindings = context.setdefault("local_capabilities", {})
    for name, binding in bind_local_toolbelt().items():
        local_bindings.setdefault(name, binding)
    if context.get("mcp_bindings") is not None:
        context.setdefault("mcp_tools", {}).update(
            {key: value for key, value in context["mcp_bindings"].items() if not required_capabilities or key in required_capabilities}
        )
    else:
        if required_capabilities:
            for capability_id, binding in load_hosted_mcp_bindings(
                context.get("mcp_environment"),
                required_capabilities=required_capabilities,
            ).items():
                if capability_id in required_capabilities:
                    context.setdefault("mcp_tools", {}).setdefault(capability_id, binding)
    if context.get("web_search_provider") is not None:
        context.setdefault("adapters", {}).setdefault("web_search", bind_web_search(context["web_search_provider"]))
    if context.get("page_retrieval") is not None:
        context.setdefault("adapters", {}).setdefault("page_retrieval", bind_page_retrieval(context["page_retrieval"]))
    elif context.get("page_retrieval_fixture_hosts") is not None:
        context.setdefault("adapters", {}).setdefault(
            "page_retrieval",
            bind_page_retrieval(PageRetrievalCapability(fixture_hosts=set(context["page_retrieval_fixture_hosts"]))),
        )
    if context.get("crawl4ai") is not None:
        context.setdefault("adapters", {}).setdefault("web_crawl", bind_crawl4ai(context["crawl4ai"]))

    def classify(error: BaseException) -> FailureClass:
        if isinstance(error, BudgetExceededError):
            return FailureClass.BUDGET
        if isinstance(error, CleanupError):
            return FailureClass.CLEANUP
        if isinstance(error, asyncio.TimeoutError):
            return FailureClass.TIMEOUT
        if isinstance(error, asyncio.CancelledError):
            return FailureClass.CANCELLATION
        if isinstance(error, ValidationError):
            return FailureClass.DOMAIN_VALIDATION
        name = type(error).__name__.lower()
        if "tool" in name:
            return FailureClass.TOOL
        return FailureClass.PROVIDER

    def settle_failure(error: BaseException) -> None:
        metrics.record_failure(classify(error), error)
        metrics.settled = True
        try:
            setattr(error, "run_metrics", metrics)
            setattr(error, "metrics", metrics)
        except BaseException:
            pass

    async def dispatch_stage(stage: Any, stage_input: object) -> tuple[list[object], object]:
        pattern = ExecutionPattern(stage.pattern)
        stage_skill_ids = tuple(getattr(stage, "skill_ids", ()))
        selected_skills = context["skill_registry"].resolve(stage_skill_ids)
        stage_skill_hashes = tuple(skill.content_sha256 for skill in selected_skills)
        context.setdefault("skill_hashes_by_stage", {})[getattr(stage, "stage_id", "")] = stage_skill_hashes
        stage_context = dict(context)
        stage_context["selected_skills"] = selected_skills
        participants = [
            replace(
                ParticipantConfig.from_mapping(participant, f"participant-{index}"),
                skill_ids=tuple(dict.fromkeys((
                    *stage_skill_ids,
                    *ParticipantConfig.from_mapping(participant, f"participant-{index}").skill_ids,
                ))),
            )
            for index, participant in enumerate(stage.participants, 1)
        ]
        cache_key = _stage_cache_key(stage, stage_input, stage_skill_ids)
        semantic_fingerprint, execution_policy_fingerprint = _stage_fingerprints(stage, stage_input, stage_skill_ids)
        stage_context["stage_fingerprints"] = (semantic_fingerprint, execution_policy_fingerprint)
        cache_entry = context.get("stage_cache", {}).get(cache_key)
        receipt = context.get("stage_receipts", {}).get(getattr(stage, "stage_id", ""))
        canonical_output = context.get("canonical_outputs", {}).get(getattr(stage, "stage_id", ""))
        if receipt is not None:
            cache_entry = None
        if getattr(stage, "stage_id", "") in set(context.get("invalidated_stage_ids", ())):
            receipt = None
        if receipt is not None and canonical_output is not None and hasattr(receipt, "reusable_for"):
            if receipt.reusable_for(
                input_fingerprint=cache_key,
                execution_policy_fingerprint=execution_policy_fingerprint,
                skill_hashes=tuple(context.get("skill_hashes_by_stage", {}).get(getattr(stage, "stage_id", ""), ())),
                capability_fingerprints=tuple(context.get("capability_fingerprints", ())),
                model_config_fingerprint=str(context.get("model_config_fingerprint", "")),
                authorization_scope_fingerprint=str(context.get("authorization_scope_fingerprint", "")),
            ) and _canonical_provenance_matches(
                receipt.result_references,
                receipt.result_hashes,
                context.get("canonical_records"),
            ):
                cache_entry = {"status": "committed", "provenance_complete": True, "result_references": receipt.result_references, "result_hashes": receipt.result_hashes, "output": canonical_output}
        if cache_entry is not None:
            cache_valid, cached_output = _committed_cache_output(cache_entry, context.get("canonical_records"))
            if cache_valid:
                metrics.cache_hits += 1
                metrics.reused_stages += 1
                return [cached_output], cached_output
        metrics.reassessed_stages += 1
        limits = dict(getattr(stage, "limits", {}) or {})
        max_timeout = limits.get("max_timeout_seconds", limits.get("timeout_seconds"))
        for field_name in ("max_agent_steps", "max_total_agent_calls", "max_branches", "max_handoffs", "max_rounds", "max_tool_calls"):
            value = limits.get(field_name)
            if value is not None:
                existing_budget = getattr(budget, field_name)
                setattr(budget, field_name, min(existing_budget, int(value)) if existing_budget is not None else int(value))
        if limits.get("max_agent_steps") is not None and budget.agent_steps + 1 > int(limits["max_agent_steps"]):
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        if limits.get("max_total_agent_calls") is not None and budget.total_agent_calls + 1 > int(limits["max_total_agent_calls"]):
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        if not budget.step():
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        if not budget.call():
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        metrics.participant_invocations += len(participants) or 1
        if pattern == ExecutionPattern.CONCURRENT:
            branch_count = len(participants) or 2
            if limits.get("max_branches") is not None and branch_count > int(limits["max_branches"]):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
            if not budget.reserve(branches=branch_count):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
        async def invoke() -> tuple[list[object], object]:
            if client is not None and pattern != ExecutionPattern.DIRECT:
                native_outputs = await _run_native_stage(pattern, str(stage_input), client, participants, metrics, stage_context)
                if pattern == ExecutionPattern.CONCURRENT:
                    aggregate = ConcurrentAggregate(tuple(native_outputs))
                    metrics.branches = len(participants)
                    metrics.parallelism = metrics.branches
                    return native_outputs, aggregate
                return native_outputs, native_outputs[-1]
            if pattern == ExecutionPattern.DIRECT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(str(stage_input))]
            elif pattern == ExecutionPattern.CONCURRENT:
                branch_count = len(participants) or 2
                metrics.branches = branch_count
                metrics.parallelism = branch_count
                branch_results = await asyncio.gather(
                    *[AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participant, f"participant-{index}"), stage_context).execute(str(stage_input)) for index, participant in enumerate(participants or ({"purpose": "participant"},) * branch_count, 1)],
                    return_exceptions=True,
                )
                results = tuple(item for item in branch_results if not isinstance(item, BaseException))
                failures = tuple(item for item in branch_results if isinstance(item, BaseException))
                aggregate = ConcurrentAggregate(results, failures)
                return list(results), aggregate
            elif pattern == ExecutionPattern.GROUP_CHAT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(str(stage_input))]
                metrics.chat_rounds += 1
                if len(participants) > 1:
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), stage_context).execute(f"Challenge this proposal:\n{stage_outputs[-1]}"))
                    metrics.chat_rounds += 1
            else:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(str(stage_input))]
                if len(participants) > 1 or pattern == ExecutionPattern.HANDOFF:
                    reviewer_prompt = f"Review this proposal:\n{stage_outputs[-1]}"
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), stage_context).execute(reviewer_prompt))
            if client is not None:
                metrics.model_calls += len(stage_outputs)
            return stage_outputs, stage_outputs[-1]
        if max_timeout is not None:
            stage_outputs, current = await asyncio.wait_for(invoke(), float(max_timeout))
        else:
            stage_outputs, current = await invoke()
        committer = context.get("canonical_result_committer")
        if committer is None:
            return stage_outputs, current
        canonical = committer(
            stage,
            current,
            {**stage_context, "stage_input": stage_input, "stage_outputs": tuple(stage_outputs)},
        )
        if inspect.isawaitable(canonical):
            canonical = await canonical
        if canonical is None:
            return stage_outputs, current
        if not isinstance(canonical, CanonicalStageResult):
            raise ValidationError("canonical result committer must return CanonicalStageResult or None")
        if len(canonical.result_references) == 1:
            context["canonical_records"][canonical.result_references[0]] = canonical.output
        context["canonical_outputs"][getattr(stage, "stage_id", "")] = canonical.output
        committed_receipt = StageReceipt(
            stage_id=str(getattr(stage, "stage_id", "stage")),
            input_fingerprint=semantic_fingerprint,
            execution_policy_fingerprint=execution_policy_fingerprint,
            skill_hashes=stage_skill_hashes,
            capability_fingerprints=tuple(context.get("capability_fingerprints", ())),
            model_config_fingerprint=str(context.get("model_config_fingerprint", "")),
            authorization_scope_fingerprint=str(context.get("authorization_scope_fingerprint", "")),
            result_references=canonical.result_references,
            result_hashes=canonical.result_hashes,
            status="committed",
            committed=True,
            provenance_complete=True,
        )
        context["stage_receipts"][committed_receipt.stage_id] = committed_receipt
        if isinstance(receipt_store, AnalysisStore):
            receipt_store.save_stage_receipt(committed_receipt)
        return stage_outputs, canonical.output

    primary_error: BaseException | None = None
    try:
        stages = recipe.stages or ()
        if not stages:
            stages = (type("Stage", (), {"pattern": ExecutionPattern(recipe.pattern), "participants": tuple(recipe.roles)})(),)
        outputs_by_stage: dict[str, object] = {}
        for stage in stages:
            dependencies = tuple(getattr(stage, "dependencies", ()))
            missing = tuple(dependency for dependency in dependencies if dependency not in outputs_by_stage)
            if missing:
                raise ValidationError(f"stage {getattr(stage, 'stage_id', 'stage')} has unavailable dependency outputs: {', '.join(missing)}")
            stage_input = StageInput(
                decision_question=str(getattr(stage, "decision_question", "") or context.get("decision_question") or recipe.metadata.get("decision_question") or prompt),
                horizon=str(getattr(stage, "horizon", "") or context.get("horizon") or recipe.metadata.get("horizon", "unspecified")),
                objective=str(getattr(stage, "objective", "") or "execute declared stage"),
                expected_result=str(getattr(stage, "expected_result", "") or ""),
                relevant_constraints=tuple(
                    str(item)
                    for item in (
                        getattr(stage, "relevant_constraints", ())
                        or context.get("relevant_constraints", ())
                        or tuple(filter(None, str(recipe.metadata.get("relevant_constraints", "")).split("|")))
                    )
                ),
                dependency_outputs=tuple((dependency, outputs_by_stage[dependency]) for dependency in dependencies),
            )
            stage_outputs, current = await dispatch_stage(stage, stage_input)
            outputs_by_stage[getattr(stage, "stage_id", f"stage-{len(outputs_by_stage) + 1}")] = current
            outputs.extend(stage_outputs)
        metrics.settled = True
        return RunResult(metrics.run_id, tuple(outputs), metrics)
    except BaseException as error:
        primary_error = error
        settle_failure(error)
        raise
    finally:
        metrics.wall_time_ms = round((time.perf_counter() - started) * 1000)
        if owns_scope:
            metrics.cleanup_complete = False
            try:
                await scope.close()
            except BaseException as error:
                metrics.record_failure(FailureClass.CLEANUP, error)
                if primary_error is None:
                    cleanup_error = CleanupError("failed to close capability scope")
                    settle_failure(cleanup_error)
                    raise cleanup_error from error
            else:
                metrics.cleanup_complete = True


def run_recipe(
    recipe: ExecutionRecipe,
    prompt: str,
    client: Any | None = None,
    run_id: str | None = None,
    run_context: dict[str, Any] | None = None,
) -> RunResult:
    return asyncio.run(run_recipe_async(recipe, prompt, client, run_id, run_context))
