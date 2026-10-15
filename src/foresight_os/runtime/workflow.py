import asyncio
import hashlib
import inspect
import json
import time
from dataclasses import asdict, dataclass, replace
from uuid import uuid4
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, StageInput
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor, run_agent_with_tool_fallback
from foresight_os.controller.budgets import BudgetState
from foresight_os.domain.validation import ValidationError
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import RevisionStatus
from foresight_os.runtime.metrics import (
    BudgetExceededError,
    CleanupError,
    ConcurrentAggregate,
    FailureClass,
    RunMetrics,
    RunResult,
    RunCanceledError,
)
from foresight_os.runtime.capabilities import CapabilityScope, ScopeOwnership, prepare_capability_context
from foresight_os.persistence.analysis_store import AnalysisStore, StageReceipt
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.artifacts.brief import deliverable_status
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.controller.skills import SkillRegistry
from foresight_os.analysis.result_committer import ANALYSIS_STAGE_RESULT_CONTRACT, CanonicalStageResult, analysis_stage_result_schema, decode_stage_output, normalize_stage_result


CanonicalResultCommitter = Callable[
    [Any, object, Mapping[str, Any]],
    CanonicalStageResult | None | Awaitable[CanonicalStageResult | None],
]


class StaleReuseError(RuntimeError):
    """Raised when approved execution refuses to refresh a stale stage receipt."""


class _ReservedChatClient:
    def __init__(
        self,
        client: Any,
        reserve_call: Callable[[], bool] | None,
        on_call: Callable[[], None] | None,
    ) -> None:
        self._client = client
        self._reserve_call = reserve_call
        self._on_call = on_call

    def get_response(self, *args: Any, **kwargs: Any) -> Any:
        if self._reserve_call is not None and not self._reserve_call():
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        if self._on_call is not None:
            self._on_call()
        return self._client.get_response(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


def _positive_limit(value: object, *, default: int | None = None, label: str) -> int:
    if value is None:
        if default is None:
            raise ValidationError(f"{label} must be a positive integer")
        return default
    if isinstance(value, bool):
        raise ValidationError(f"{label} must be a positive integer")
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a positive integer") from exc
    if limit < 1:
        raise ValidationError(f"{label} must be a positive integer")
    return limit


def _round_available(budget: BudgetState) -> bool:
    return budget.max_rounds is None or budget.rounds < budget.max_rounds


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


def _workflow_output_value(output: object) -> object:
    return decode_stage_output(output)


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
    if context.get("execution_admitted"):
        expected_recipe_fingerprint = context.get("approved_recipe_fingerprint")
        actual_recipe_fingerprint = context.get("recipe_fingerprint")
        if expected_recipe_fingerprint and expected_recipe_fingerprint != actual_recipe_fingerprint:
            raise ValidationError("approved recipe snapshot is immutable and cannot be changed at runtime")
    context.setdefault("skill_registry", SkillRegistry())
    context["handoff"] = pattern == ExecutionPattern.HANDOFF
    max_rounds = _positive_limit(context.get("max_rounds"), default=4, label="max_rounds")
    reserve_call = context.get("reserve_agent_call")
    on_call = None if metrics is None else lambda: setattr(metrics, "model_calls", metrics.model_calls + 1)
    for index, role in enumerate(roles or [{"purpose": "participant"}], 1):
        participant = ParticipantConfig.from_mapping(role, f"participant-{index}")
        agent = factory.create(participant, context)
        agents.append(agent)
    tools_enabled = any(getattr(agent, "default_options", {}).get("tools") for agent in agents)
    wrapped_agent_ids: set[str] = set()
    if not (tools_enabled and context.get("require_structured_output")):
        wrapped_clients: dict[int, _ReservedChatClient] = {}
        for agent in agents:
            client_instance = getattr(agent, "client", None)
            if client_instance is None or not hasattr(client_instance, "get_response"):
                continue
            client_key = id(client_instance)
            wrapped_client = wrapped_clients.get(client_key)
            if wrapped_client is None:
                wrapped_client = _ReservedChatClient(client_instance, reserve_call, on_call)
                wrapped_clients[client_key] = wrapped_client
            agent.client = wrapped_client
            wrapped_agent_ids.add(getattr(agent, "id", ""))
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
            max_rounds=max_rounds,
            output_from="all",
        ).build()
    if pattern not in {
        ExecutionPattern.SEQUENTIAL,
        ExecutionPattern.CONCURRENT,
        ExecutionPattern.HANDOFF,
        ExecutionPattern.GROUP_CHAT,
    }:
        client_instance = getattr(agents[0], "client", None)
        if getattr(agents[0], "id", "") not in wrapped_agent_ids and client_instance is not None and hasattr(client_instance, "get_response"):
            agents[0].client = _ReservedChatClient(client_instance, reserve_call, on_call)
        elif getattr(agents[0], "id", "") not in wrapped_agent_ids and reserve_call is not None and not reserve_call():
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        if getattr(agents[0], "id", "") not in wrapped_agent_ids and (client_instance is None or not hasattr(client_instance, "get_response")):
            if on_call is not None:
                on_call()
        return [await agents[0].run(prompt)]
    if tools_enabled and context.get("require_structured_output"):
        options = {"response_format": context.get("structured_output_schema")}
        if pattern == ExecutionPattern.CONCURRENT:
            results = await asyncio.gather(
                *[
                    run_agent_with_tool_fallback(
                        agent,
                        prompt,
                        options,
                        reserve_call=reserve_call,
                        on_call=on_call,
                    )
                    for agent in agents
                ]
            )
            return list(results)
        if pattern == ExecutionPattern.GROUP_CHAT:
            results: list[object] = []
            current_prompt = prompt
            for round_index in range(max_rounds):
                agent = agents[round_index % len(agents)]
                result = await run_agent_with_tool_fallback(
                    agent,
                    current_prompt,
                    options,
                    reserve_call=reserve_call,
                    on_call=on_call,
                )
                results.append(result)
                current_prompt = f"Challenge this proposal and return the required structured result:\n{result}"
                if metrics is not None:
                    metrics.chat_rounds += 1
            return results
        results = []
        current_prompt = prompt
        for index, agent in enumerate(agents):
            result = await run_agent_with_tool_fallback(
                agent,
                current_prompt,
                options,
                reserve_call=reserve_call,
                on_call=on_call,
            )
            results.append(result)
            if index + 1 < len(agents):
                current_prompt = f"Review this proposal and return the required structured result:\n{result}"
        return results
    if tools_enabled:
        result = await workflow.run(prompt)
        if pattern == ExecutionPattern.GROUP_CHAT:
            observed_rounds = {
                getattr(getattr(event, "data", None), "round_index")
                for event in result
                if getattr(event, "type", None) == "group_chat"
                and type(getattr(event, "data", None)).__name__ == "GroupChatRequestSentEvent"
            }
            if observed_rounds:
                budget = context.get("budget")
                if budget is not None and not budget.reserve(rounds=len(observed_rounds)):
                    raise BudgetExceededError("maximum group chat rounds exceeded")
                if metrics is not None:
                    metrics.chat_rounds += len(observed_rounds)
    elif metrics is None and reserve_call is None:
        result = await workflow.run(prompt)
    else:
        agent_ids = {getattr(agent, "id", None) for agent in agents}
        observed_rounds: set[int] = set()
        stream = await workflow.run(prompt, stream=True)
        try:
            async for event in stream:
                if (
                    event.type == "executor_invoked"
                    and event.executor_id in agent_ids
                    and getattr(getattr(event, "data", None), "should_respond", True)
                ):
                    if event.executor_id not in wrapped_agent_ids and reserve_call is not None and not reserve_call():
                        raise BudgetExceededError("maximum agent calls exceeded before dispatch")
                    if event.executor_id not in wrapped_agent_ids and metrics is not None:
                        metrics.model_calls += 1
                elif event.type == "handoff_sent":
                    if metrics is not None:
                        metrics.handoffs += 1
                elif pattern == ExecutionPattern.GROUP_CHAT and event.type == "group_chat":
                    data = event.data
                    if type(data).__name__ == "GroupChatRequestSentEvent":
                        observed_rounds.add(getattr(data, "round_index", len(observed_rounds)))
            result = await stream.get_final_response()
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                closed = close()
                if inspect.isawaitable(closed):
                    await closed
        if pattern == ExecutionPattern.GROUP_CHAT and observed_rounds:
            budget = context.get("budget")
            if budget is not None and not budget.reserve(rounds=len(observed_rounds)):
                raise BudgetExceededError("maximum group chat rounds exceeded")
            if metrics is not None:
                metrics.chat_rounds += len(observed_rounds)
    outputs = [_workflow_output_value(output) for output in result.get_outputs()]
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


def _synthesize_stage_outputs(
    stage: Any,
    outputs: list[object],
    failures: tuple[BaseException, ...] = (),
    *,
    allow_legacy_fallback: bool = False,
    existing_records: Mapping[str, object] | None = None,
) -> object:
    if len(outputs) == 1 and not failures:
        return outputs[0]
    if str(getattr(stage, "synthesis_policy", "")) != "aggregate-typed-results":
        raise ValidationError(f"stage {getattr(stage, 'stage_id', 'stage')} requires an explicit synthesis policy")
    if not outputs or not all(isinstance(item, Mapping) for item in outputs):
        if allow_legacy_fallback:
            return outputs[-1] if outputs else None
        raise ValidationError("typed stage synthesis requires mapping outputs")
    normalized_outputs: list[Mapping[str, Any]] = []
    for output in outputs:
        if "contract" in output and "stage_id" in output:
            normalized_outputs.append(
                normalize_stage_result(
                    output,
                    expected_stage_id=str(getattr(stage, "stage_id", "stage")),
                    existing_records=existing_records,
                ).to_contract_payload()
            )
        else:
            normalized_outputs.append(output)
    outputs = normalized_outputs
    first = dict(outputs[0])
    collections = ("evidence", "calculations", "claims", "implications", "recommendations", "artifacts", "relationships")

    def merge_records(key: str) -> list[object]:
        merged: list[object] = []
        by_id: dict[str, object] = {}
        for output in outputs:
            entries = output.get(key, [])
            if entries is None:
                continue
            if not isinstance(entries, (list, tuple)):
                raise ValidationError(f"typed stage synthesis requires a list for {key}")
            for entry in entries:
                record_id = entry.get("id") if isinstance(entry, Mapping) else None
                if not record_id:
                    merged.append(entry)
                    continue
                existing = by_id.get(str(record_id))
                if existing is None:
                    by_id[str(record_id)] = entry
                    merged.append(entry)
                    continue
                if _canonical_result_hash(existing) != _canonical_result_hash(entry):
                    raise ValidationError(f"conflicting canonical record for {key}:{record_id}")
        return merged

    for key in collections:
        first[key] = merge_records(key)
    first["assumptions"] = [entry for output in outputs for entry in list(output.get("assumptions", []))]
    first["uncertainty"] = [entry for output in outputs for entry in list(output.get("uncertainty", []))]
    first["monitoring_indicators"] = [entry for output in outputs for entry in list(output.get("monitoring_indicators", []))]
    if failures:
        first["uncertainty"].extend(f"participant failure: {type(error).__name__}" for error in failures)
    return first


def _effective_skill_ids(stage_skill_ids: tuple[str, ...], participant_skill_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*stage_skill_ids, *participant_skill_ids)))


def _stage_participants(stage: Any) -> tuple[ParticipantConfig, ...]:
    stage_capabilities = tuple(str(item) for item in getattr(stage, "capabilities", ()))
    stage_scope = tuple(str(item) for item in getattr(stage, "access_scope", ()))
    stage_provider = str(getattr(stage, "provider", "local"))
    stage_model = str(getattr(stage, "model", "unspecified"))
    stage_reasoning_controls = dict(getattr(stage, "reasoning_controls", {}) or {})
    participants = []
    for index, item in enumerate(getattr(stage, "participants", ()), 1):
        participant = ParticipantConfig.from_mapping(item, f"participant-{index}")
        participants.append(replace(
            participant,
            capability_ids=tuple(dict.fromkeys((*stage_capabilities, *participant.capability_ids))),
            data_scope=tuple(dict.fromkeys((*stage_scope, *participant.data_scope))),
            provider=stage_provider,
            model=stage_model if stage_model != "unspecified" else participant.model,
            reasoning_controls={**participant.reasoning_controls, **stage_reasoning_controls},
        ))
    return tuple(participants)


def _stage_fingerprints(
    stage: Any,
    stage_input: object,
    skill_ids: tuple[str, ...],
    selected_skills_by_participant: Mapping[str, tuple[object, ...]] | None = None,
) -> tuple[str, str]:
    participant_configs = tuple(_stage_participants(stage))
    participants = tuple(participant.id for participant in participant_configs)
    if selected_skills_by_participant is None:
        skill_plan = tuple(
            {
                "participant_id": participant.id,
                "skills": tuple(
                    {"skill_id": skill_id}
                    for skill_id in _effective_skill_ids(tuple(skill_ids), participant.skill_ids)
                ),
            }
            for participant in participant_configs
        )
    else:
        skill_plan = tuple(
            {
                "participant_id": participant.id,
                "skills": tuple(
                    {
                        "skill_id": getattr(skill, "skill_id", ""),
                        "version": getattr(skill, "version", ""),
                        "content_sha256": getattr(skill, "content_sha256", ""),
                    }
                    for skill in selected_skills_by_participant.get(participant.id, ())
                ),
            }
            for participant in participant_configs
        )
    input_payload = _stage_input_payload(stage_input)
    dependency_outputs = input_payload.get("dependency_outputs", {})
    semantic_payload = {
        "stage_id": getattr(stage, "stage_id", "stage"),
        "pattern": str(getattr(stage, "pattern", "direct")),
        "objective": getattr(stage, "objective", ""),
        "expected_result": getattr(stage, "expected_result", ""),
        "research_needs": getattr(stage, "research_needs", ()),
        "specialist_ids": participants,
        "skill_plan": skill_plan,
        "decision_question": input_payload.get("decision_question", ""),
        "horizon": input_payload.get("horizon", ""),
        "relevant_constraints": input_payload.get("relevant_constraints", ()),
        "dependency_result_hashes": {
            stage_id: _canonical_result_hash(output)
            for stage_id, output in dict(dependency_outputs).items()
        },
        "participants": tuple(asdict(participant) for participant in participant_configs),
        "synthesis_policy": getattr(stage, "synthesis_policy", ""),
    }
    policy_payload = {
        "limits": getattr(stage, "limits", {}),
        "capabilities": getattr(stage, "capabilities", ()),
        "access_scope": getattr(stage, "access_scope", ()),
        "provider": getattr(stage, "provider", "local"),
        "model": getattr(stage, "model", "unspecified"),
        "reasoning_controls": getattr(stage, "reasoning_controls", {}),
        "synthesis_policy": getattr(stage, "synthesis_policy", ""),
    }
    return (
        hashlib.sha256(json.dumps(semantic_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest(),
        hashlib.sha256(json.dumps(policy_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest(),
    )


def _stage_cache_key(
    stage: Any,
    current: object,
    skill_ids: tuple[str, ...],
    selected_skills_by_participant: Mapping[str, tuple[object, ...]] | None = None,
) -> str:
    return _stage_fingerprints(stage, current, skill_ids, selected_skills_by_participant)[0]


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
    metrics.runtime_status = "RUNNING"
    outputs: list[object] = []
    metrics.cleanup_complete = True
    context = dict(run_context or {})
    context["recipe_fingerprint"] = canonical_json_hash(recipe.to_dict())
    run_max_rounds = None
    if "max_rounds" in context and context["max_rounds"] is not None:
        run_max_rounds = _positive_limit(context["max_rounds"], label="max_rounds")
    budget = BudgetState(recipe.max_agent_steps, recipe.max_correction_rounds, recipe.max_total_agent_calls, max_rounds=run_max_rounds)
    factory = AgentFactory(client) if client is not None else None
    context.setdefault("skill_registry", SkillRegistry())
    receipt_store = context.get("analysis_store") or context.get("stage_receipt_store")
    if isinstance(receipt_store, AnalysisStore):
        context.setdefault("stage_receipts", receipt_store.load_stage_receipts())
    context.setdefault("canonical_records", {})
    context.setdefault("canonical_outputs", {})
    context.setdefault("stage_receipts", {})
    if isinstance(receipt_store, AnalysisStore) and not context["canonical_records"]:
        try:
            context["canonical_records"].update(receipt_store.load_analysis().canonical_records())
        except FileNotFoundError:
            pass
    changed_record_ids = tuple(str(item) for item in context.get("changed_record_ids", context.get("changed_ids", ())))
    relation_index = context.get("relation_index")
    if changed_record_ids and relation_index is not None:
        impact_closure = getattr(relation_index, "impact_closure", None) or getattr(relation_index, "impacted_descendants")
        impacted_ids = set(impact_closure(changed_record_ids))
        auto_invalidated_stage_ids = tuple(
            sorted(
                stage_id
                for stage_id, receipt in context["stage_receipts"].items()
                if impacted_ids.intersection(getattr(receipt, "result_references", ()))
            )
        )
        context["auto_invalidated_stage_ids"] = auto_invalidated_stage_ids
        context["invalidated_stage_ids"] = auto_invalidated_stage_ids
    fresh_requested = set(str(item) for item in context.get("run_fresh_stages", ()))
    if fresh_requested:
        affected = set(fresh_requested)
        changed = True
        while changed:
            changed = False
            for stage in recipe.stages or ():
                stage_id = str(getattr(stage, "stage_id", ""))
                if stage_id not in affected and any(str(dep) in affected for dep in getattr(stage, "dependencies", ())):
                    affected.add(stage_id)
                    changed = True
        context["invalidated_stage_ids"] = tuple(sorted(set(context.get("invalidated_stage_ids", ())) | affected))
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
    required_capabilities: set[str] = set()
    selected_skills_by_stage: dict[str, dict[str, tuple[object, ...]]] = {}
    for stage in recipe.stages or ():
        stage_skill_ids = tuple(getattr(stage, "skill_ids", ()))
        stage_plan: dict[str, tuple[object, ...]] = {}
        for participant in _stage_participants(stage):
            effective_ids = _effective_skill_ids(stage_skill_ids, participant.skill_ids)
            selected_skills = context["skill_registry"].resolve(effective_ids)
            stage_plan[participant.id] = selected_skills
            required_capabilities.update(context["skill_registry"].required_capabilities(selected_skills))
            required_capabilities.update(participant.capability_ids)
        selected_skills_by_stage[getattr(stage, "stage_id", "stage")] = stage_plan
    if not recipe.stages:
        for participant in recipe.roles:
            required_capabilities.update(ParticipantConfig.from_mapping(participant).capability_ids)
    context["selected_skills_by_stage"] = selected_skills_by_stage
    context = prepare_capability_context(tuple(sorted(required_capabilities)), context, scope=scope)

    def classify(error: BaseException) -> FailureClass:
        if isinstance(error, BudgetExceededError):
            return FailureClass.BUDGET
        if isinstance(error, CleanupError):
            return FailureClass.CLEANUP
        if isinstance(error, asyncio.TimeoutError):
            return FailureClass.TIMEOUT
        if isinstance(error, asyncio.CancelledError):
            return FailureClass.CANCELLATION
        if isinstance(error, RunCanceledError):
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
        metrics.runtime_status = "PARTIAL" if (context.get("canonical_records") or outputs) else "FAILED"
        _refresh_execution_status(context, metrics)
        try:
            setattr(error, "run_metrics", metrics)
            setattr(error, "metrics", metrics)
        except BaseException:
            pass

    async def dispatch_stage(stage: Any, stage_input: object) -> tuple[list[object], object]:
        pattern = ExecutionPattern(stage.pattern)
        stage_skill_ids = tuple(getattr(stage, "skill_ids", ()))
        participants = list(_stage_participants(stage))
        selected_skills_by_participant = dict(
            context.get("selected_skills_by_stage", {}).get(getattr(stage, "stage_id", ""), {})
        )
        selected_skills = tuple(
            skill
            for participant in participants
            for skill in selected_skills_by_participant.get(participant.id, ())
        )
        stage_skill_hashes = tuple(skill.content_sha256 for skill in selected_skills)
        context.setdefault("skill_hashes_by_stage", {})[getattr(stage, "stage_id", "")] = stage_skill_hashes
        stage_context = dict(context)
        stage_context["stage_id"] = str(getattr(stage, "stage_id", "stage"))
        stage_context["selected_skills"] = selected_skills
        stage_context["selected_skills_by_participant"] = selected_skills_by_participant
        stage_context["reserve_agent_call"] = lambda: budget.call()
        stage_context["record_agent_call"] = lambda: setattr(metrics, "model_calls", metrics.model_calls + 1)
        dependency_records: dict[str, object] = {}
        for dependency in tuple(getattr(stage, "dependencies", ())):
            dependency_receipt = context.get("stage_receipts", {}).get(str(dependency))
            for reference in tuple(getattr(dependency_receipt, "result_references", ())):
                if reference in context.get("canonical_records", {}):
                    dependency_records[reference] = context["canonical_records"][reference]
        stage_context["dependency_records"] = dependency_records
        cache_key = _stage_cache_key(stage, stage_input, stage_skill_ids, selected_skills_by_participant)
        semantic_fingerprint, execution_policy_fingerprint = _stage_fingerprints(
            stage,
            stage_input,
            stage_skill_ids,
            selected_skills_by_participant,
        )
        stage_context["stage_fingerprints"] = (semantic_fingerprint, execution_policy_fingerprint)
        stage_context["result_contract"] = str(getattr(stage, "result_contract", ANALYSIS_STAGE_RESULT_CONTRACT))
        stage_context["require_structured_output"] = bool(context.get("require_structured_output", False))
        stage_context["structured_output_schema"] = analysis_stage_result_schema()
        cache_entry = context.get("stage_cache", {}).get(cache_key)
        receipt = context.get("stage_receipts", {}).get(getattr(stage, "stage_id", ""))
        canonical_output = context.get("canonical_outputs", {}).get(getattr(stage, "stage_id", ""))
        if receipt is not None:
            cache_entry = None
        stage_id = getattr(stage, "stage_id", "")
        fresh_requested_stage = stage_id in fresh_requested
        invalidated_stage = stage_id in set(context.get("invalidated_stage_ids", ()))
        auto_invalidated_stage = stage_id in set(context.get("auto_invalidated_stage_ids", ()))
        if auto_invalidated_stage and not fresh_requested_stage and receipt is not None and context.get("fallback_on_stale_reuse") == "stop":
            raise StaleReuseError(f"stale stage receipt for {stage_id}: changed evidence invalidated the receipt")
        if invalidated_stage:
            receipt = None
            cache_entry = None
        fallback_on_stale_reuse = context.get("fallback_on_stale_reuse")
        if receipt is not None and fallback_on_stale_reuse == "stop" and canonical_output is None:
            raise StaleReuseError(f"stale stage receipt for {getattr(stage, 'stage_id', 'stage')}: canonical output is unavailable")
        if receipt is not None and canonical_output is not None and hasattr(receipt, "reusable_for"):
            receipt_matches = receipt.reusable_for(
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
            )
            if not receipt_matches and fallback_on_stale_reuse == "stop":
                raise StaleReuseError(f"stale stage receipt for {getattr(stage, 'stage_id', 'stage')}: fingerprints or provenance do not match")
            if receipt_matches:
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
        for field_name in ("max_agent_steps", "max_total_agent_calls", "max_branches", "max_handoffs", "max_tool_calls"):
            value = limits.get(field_name)
            if value is not None:
                existing_budget = getattr(budget, field_name)
                setattr(budget, field_name, min(existing_budget, int(value)) if existing_budget is not None else int(value))
        if pattern == ExecutionPattern.GROUP_CHAT:
            declared_rounds = _positive_limit(limits.get("max_rounds"), default=4, label="stage max_rounds")
            if not _round_available(budget):
                raise BudgetExceededError("maximum group chat rounds exhausted before dispatch")
            remaining_rounds = None if budget.max_rounds is None else budget.max_rounds - budget.rounds
            effective_rounds = declared_rounds if remaining_rounds is None else min(declared_rounds, remaining_rounds)
            remaining_calls = (
                None
                if budget.max_total_agent_calls is None
                else budget.max_total_agent_calls - budget.total_agent_calls
            )
            if remaining_calls is not None:
                if remaining_calls < 1:
                    raise BudgetExceededError("maximum agent calls exceeded before group chat dispatch")
                effective_rounds = min(effective_rounds, remaining_calls)
            stage_context["max_rounds"] = effective_rounds
        if limits.get("max_agent_steps") is not None and budget.agent_steps + 1 > int(limits["max_agent_steps"]):
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        if not budget.step():
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        metrics.participant_invocations += len(participants) or 1
        if pattern == ExecutionPattern.CONCURRENT:
            branch_count = len(participants) or 2
            if limits.get("max_branches") is not None and branch_count > int(limits["max_branches"]):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
            if not budget.reserve(branches=branch_count):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
        async def invoke(stage_prompt: str | None = None) -> tuple[list[object], object]:
            prompt_value = stage_prompt or str(stage_input)
            if client is not None and pattern != ExecutionPattern.DIRECT:
                native_outputs = await _run_native_stage(pattern, prompt_value, client, participants, metrics, stage_context)
                if pattern == ExecutionPattern.CONCURRENT:
                    metrics.branches = len(participants)
                    metrics.parallelism = metrics.branches
                return native_outputs, _synthesize_stage_outputs(
                    stage,
                    native_outputs,
                    allow_legacy_fallback=context.get("analysis_store") is None,
                    existing_records=context.get("canonical_records"),
                )
            if pattern == ExecutionPattern.DIRECT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(prompt_value)]
            elif pattern == ExecutionPattern.CONCURRENT:
                branch_count = len(participants) or 2
                metrics.branches = branch_count
                metrics.parallelism = branch_count
                branch_results = await asyncio.gather(
                    *[AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participant, f"participant-{index}"), stage_context).execute(prompt_value) for index, participant in enumerate(participants or ({"purpose": "participant"},) * branch_count, 1)],
                    return_exceptions=True,
                )
                results = tuple(item for item in branch_results if not isinstance(item, BaseException))
                failures = tuple(item for item in branch_results if isinstance(item, BaseException))
                return list(results), _synthesize_stage_outputs(
                    stage,
                    list(results),
                    failures,
                    allow_legacy_fallback=context.get("analysis_store") is None,
                    existing_records=context.get("canonical_records"),
                )
            elif pattern == ExecutionPattern.GROUP_CHAT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(prompt_value)]
                if not budget.reserve(rounds=1):
                    raise BudgetExceededError("maximum group chat rounds exceeded")
                metrics.chat_rounds += 1
                if len(participants) > 1 and effective_rounds > 1 and _round_available(budget):
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), stage_context).execute(f"Challenge this proposal:\n{stage_outputs[-1]}"))
                    if not budget.reserve(rounds=1):
                        raise BudgetExceededError("maximum group chat rounds exceeded")
                    metrics.chat_rounds += 1
            else:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(prompt_value)]
                if len(participants) > 1 or pattern == ExecutionPattern.HANDOFF:
                    reviewer_prompt = f"Review this proposal:\n{stage_outputs[-1]}"
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), stage_context).execute(reviewer_prompt))
            return stage_outputs, _synthesize_stage_outputs(
                stage,
                stage_outputs,
                allow_legacy_fallback=context.get("analysis_store") is None,
                existing_records=context.get("canonical_records"),
            )
        committer = context.get("canonical_result_committer")
        correction_prompt: str | None = None
        canonical = None
        while True:
            try:
                if max_timeout is not None:
                    stage_outputs, current = await asyncio.wait_for(invoke(correction_prompt), float(max_timeout))
                else:
                    stage_outputs, current = await invoke(correction_prompt)
                if committer is None:
                    break
                canonical = committer(
                    stage,
                    current,
                    {**stage_context, "stage_input": stage_input, "stage_outputs": tuple(stage_outputs)},
                )
                if inspect.isawaitable(canonical):
                    canonical = await canonical
                break
            except ValidationError as error:
                if not budget.correct():
                    raise
                metrics.correction_rounds += 1
                correction_prompt = (
                    f"{stage_input}\n\n"
                    "The previous structured result was rejected by canonical validation. "
                    f"Correct only the validation issue and return the complete result again: {error}"
                )
        if committer is None:
            return stage_outputs, current
        if canonical is None:
            return stage_outputs, current
        if not isinstance(canonical, CanonicalStageResult):
            raise ValidationError("canonical result committer must return CanonicalStageResult or None")
        if canonical.canonical_records:
            context["canonical_records"].update(canonical.canonical_records)
        elif len(canonical.result_references) == 1:
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
            source_revision=str(context.get("source_revision", "")),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            reuse_decision="run_fresh" if getattr(stage, "stage_id", "") in fresh_requested else "reuse",
        )
        context["stage_receipts"][committed_receipt.stage_id] = committed_receipt
        if isinstance(receipt_store, AnalysisStore):
            receipt_store.save_stage_receipt(committed_receipt)
        return stage_outputs, canonical.output

    def _refresh_execution_status(run_context: dict[str, Any], run_metrics: RunMetrics) -> None:
        committer_configured = run_context.get("canonical_result_committer") is not None
        store = run_context.get("analysis_store") or run_context.get("stage_receipt_store")
        state = None
        if isinstance(store, AnalysisStore):
            try:
                state = store.load_analysis()
            except FileNotFoundError:
                state = None
        if not committer_configured:
            run_metrics.persistence_status = "NOT_STARTED"
            run_metrics.analysis_status = "NOT_STARTED"
            run_metrics.deliverable_status = {}
            return
        if state is None:
            run_metrics.persistence_status = "FAILED" if run_metrics.failure_class else "NOT_STARTED"
            run_metrics.analysis_status = "NOT_STARTED"
            run_metrics.deliverable_status = {}
            return
        run_metrics.persistence_status = "PARTIAL" if run_metrics.failure_class else "PERSISTED"
        if not state.canonical_records():
            run_metrics.analysis_status = "NOT_STARTED"
        elif state.revision_status == RevisionStatus.ACCEPTED:
            views = derive_finding_views(state)
            run_metrics.analysis_status = "ACCEPTED" if not views or all(view.accepted for view in views) else "PENDING_REVIEW"
        else:
            run_metrics.analysis_status = "PENDING_REVIEW"
        try:
            brief = store.load_brief()
        except (FileNotFoundError, ValueError):
            run_metrics.deliverable_status = {}
            return
        run_metrics.deliverable_status = {
            str(requested): deliverable_status(str(requested), state)
            for requested in brief.desired_deliverables
        }

    primary_error: BaseException | None = None
    try:
        stages = recipe.stages or ()
        if not stages:
            stages = (type("Stage", (), {"pattern": ExecutionPattern(recipe.pattern), "participants": tuple(recipe.roles)})(),)
        outputs_by_stage: dict[str, object] = {}
        for stage in stages:
            run_control = context.get("run_control")
            if run_control is not None:
                try:
                    await run_control.before_stage()
                except Exception as error:
                    raise RunCanceledError(str(error)) from error
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
                research_needs=tuple(getattr(stage, "research_needs", ()) or ()),
            )
            stage_outputs, current = await dispatch_stage(stage, stage_input)
            outputs_by_stage[getattr(stage, "stage_id", f"stage-{len(outputs_by_stage) + 1}")] = current
            outputs.extend(stage_outputs)
        metrics.settled = True
        metrics.runtime_status = "SETTLED"
        _refresh_execution_status(context, metrics)
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
