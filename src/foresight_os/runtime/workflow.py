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
from foresight_os.runtime.executors import (
    AnalystExecutor,
    DeterministicLocalExecutor,
    ReviewerExecutor,
    _ReservedChatClient,
    _ReservedProviderCallMiddleware,
    _supports_function_invocation,
    run_agent_with_tool_fallback,
)
from foresight_os.controller.budgets import BudgetState
from foresight_os.domain.validation import ValidationError
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import RevisionStatus
from foresight_os.domain.relationships import RecordKind
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

_NON_RETRYABLE_VALIDATION_CODES = frozenset(
    {"MATERIAL_CONFLICT", "SOURCE_STALE", "PROVIDER_INTERRUPTION", "BUDGET_EXHAUSTED", "UNSUPPORTED_RECOVERY"}
)
_COMPUTATIONAL_REFERENCE_FIELDS = ("evidence_ids", "input_ids")


def _failure_class(error: BaseException) -> FailureClass:
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
    if "tool" in type(error).__name__.lower():
        return FailureClass.TOOL
    return FailureClass.PROVIDER


def _synthesis_error(code: str, message: str) -> ValidationError:
    return ValidationError(message, code=code)


class StaleReuseError(RuntimeError):
    """Raised when approved execution refuses to refresh a stale stage receipt."""


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


def _expand_dependency_records(
    dependency_records: Mapping[str, object],
    canonical_records: Mapping[str, object],
) -> dict[str, object]:
    expanded = dict(dependency_records)
    pending = list(expanded.values())
    while pending:
        record = pending.pop()
        references: list[str] = []
        for field_name in _COMPUTATIONAL_REFERENCE_FIELDS:
            value = record.get(field_name) if isinstance(record, Mapping) else getattr(record, field_name, None)
            if isinstance(value, str):
                references.append(value)
            elif isinstance(value, (list, tuple)):
                references.extend(item for item in value if isinstance(item, str))
        for reference in references:
            if reference in expanded or reference not in canonical_records:
                continue
            referenced_record = canonical_records[reference]
            expanded[reference] = referenced_record
            pending.append(referenced_record)
    return expanded


def _dependency_stage_ids(stage: Any, stages_by_id: Mapping[str, Any]) -> tuple[str, ...]:
    ordered: list[str] = []
    pending = list(getattr(stage, "dependencies", ()) or ())
    seen: set[str] = set()
    while pending:
        stage_id = str(pending.pop(0))
        if stage_id in seen:
            continue
        seen.add(stage_id)
        ordered.append(stage_id)
        ancestor = stages_by_id.get(stage_id)
        if ancestor is not None:
            pending.extend(str(item) for item in getattr(ancestor, "dependencies", ()) or ())
    return tuple(ordered)


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
    context["provider_call_middleware"] = _ReservedProviderCallMiddleware(reserve_call, on_call)
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
            if _supports_function_invocation(client_instance):
                wrapped_agent_ids.add(getattr(agent, "id", ""))
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
    if tools_enabled and context.get("require_structured_output") and pattern != ExecutionPattern.HANDOFF:
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
                budget = context.get("budget")
                if budget is not None and not budget.reserve(rounds=1):
                    raise BudgetExceededError("maximum group chat rounds exceeded")
                agent = agents[round_index % len(agents)]
                result = await run_agent_with_tool_fallback(
                    agent,
                    current_prompt,
                    options,
                    reserve_call=reserve_call,
                    on_call=on_call,
                )
                results.append(result)
                current_prompt = (
                    f"Retain the original stage input and source context:\n{prompt}\n\n"
                    "Challenge this proposal and return the required structured result. Preserve every unchanged "
                    "record verbatim; use a new record ID for any revised interpretation, and never reuse an "
                    "existing ID for materially different content:\n"
                    f"{result}"
                )
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
                current_prompt = (
                    f"Retain the original stage input and source context:\n{prompt}\n\n"
                    "Review this proposal and return the required structured result. Preserve every unchanged "
                    "record verbatim; use a new record ID for any revised interpretation, and never reuse an "
                    "existing ID for materially different content:\n"
                    f"{result}"
                )
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
    dependency_records: Mapping[str, object] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    participant_ids: tuple[str, ...] | None = None,
    return_normalized_result: bool = False,
) -> object:
    operation_limit: int | None = None
    operation_count = 0

    def checkpoint() -> None:
        nonlocal operation_count
        if cancel_check is not None and cancel_check():
            raise RunCanceledError("run canceled during stage synthesis")
        if operation_limit is not None:
            operation_count += 1
            if operation_count > operation_limit:
                raise _synthesis_error("BUDGET_EXHAUSTED", "typed stage synthesis exceeded the normalization operation budget")

    limits = dict(getattr(stage, "limits", {}) or {})
    max_participants = _positive_limit(
        limits.get("max_synthesis_participants"),
        default=max(1, len(outputs)),
        label="max_synthesis_participants",
    )
    max_payload_bytes = _positive_limit(
        limits.get("max_synthesis_payload_bytes"),
        default=10_000_000,
        label="max_synthesis_payload_bytes",
    )
    checkpoint()
    if len(outputs) > max_participants:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_participants} participants")
    try:
        payload_bytes = len(json.dumps(outputs, default=str, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError) as error:
        raise _synthesis_error("MALFORMED_OUTPUT", "typed stage synthesis payload is not serializable") from error
    if payload_bytes > max_payload_bytes:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_payload_bytes} payload bytes")
    if (
        len(outputs) == 1
        and not failures
        and not (
            isinstance(outputs[0], Mapping)
            and "contract" in outputs[0]
            and "stage_id" in outputs[0]
        )
    ):
        return outputs[0]
    if str(getattr(stage, "synthesis_policy", "")) != "aggregate-typed-results":
        raise _synthesis_error(
            "MALFORMED_OUTPUT",
            f"stage {getattr(stage, 'stage_id', 'stage')} requires an explicit synthesis policy",
        )
    if not outputs or not all(isinstance(item, Mapping) for item in outputs):
        if allow_legacy_fallback:
            return outputs[-1] if outputs else None
        raise _synthesis_error("MALFORMED_OUTPUT", "typed stage synthesis requires mapping outputs")
    typed_outputs = all("contract" in output and "stage_id" in output for output in outputs)
    max_records = _positive_limit(limits.get("max_synthesis_records"), default=10_000, label="max_synthesis_records")
    max_relationships = _positive_limit(limits.get("max_synthesis_relationships"), default=10_000, label="max_synthesis_relationships")
    max_aliases = _positive_limit(
        limits.get("max_synthesis_aliases"),
        default=50_000,
        label="max_synthesis_aliases",
    )
    max_dependency_depth = _positive_limit(
        limits.get("max_synthesis_dependency_depth"),
        default=64,
        label="max_synthesis_dependency_depth",
    )
    if limits.get("max_synthesis_normalization_operations") is not None:
        operation_limit = _positive_limit(
            limits.get("max_synthesis_normalization_operations"),
            label="max_synthesis_normalization_operations",
        )
    collections = ("evidence", "calculations", "claims", "implications", "recommendations", "artifacts", "relationships")
    participant_ids = tuple(participant_ids or ())
    collection_kinds = {
        "evidence": RecordKind.EVIDENCE,
        "claims": RecordKind.CLAIM,
        "implications": RecordKind.IMPLICATION,
        "recommendations": RecordKind.RECOMMENDATION,
        "artifacts": RecordKind.ARTIFACT,
    }
    preflight_records = 0
    preflight_calculations = 0
    preflight_relationships = 0
    preflight_aliases = 0
    raw_record_ids: set[str] = set()
    raw_dependencies: dict[str, set[str]] = {}
    for output in outputs:
        checkpoint()
        for key in collections:
            entries = output.get(key, [])
            if entries is None:
                continue
            if not isinstance(entries, (list, tuple)):
                raise _synthesis_error("MALFORMED_OUTPUT", f"typed stage synthesis requires a list for {key}")
            if key == "relationships":
                preflight_relationships += len(entries)
            else:
                preflight_records += len(entries)
            if key == "calculations":
                preflight_calculations += len(entries)
            for entry in entries:
                checkpoint()
                if not isinstance(entry, Mapping):
                    continue
                record_id = entry.get("id")
                if isinstance(record_id, str) and record_id:
                    preflight_aliases += 1
                    raw_record_ids.add(record_id)
                    dependencies = raw_dependencies.setdefault(record_id, set())
                    for field_name in _COMPUTATIONAL_REFERENCE_FIELDS:
                        value = entry.get(field_name)
                        if isinstance(value, str):
                            dependencies.add(value)
                        elif isinstance(value, (list, tuple)):
                            dependencies.update(item for item in value if isinstance(item, str))
    for key in collections:
        entries = outputs[0].get(key, []) if len(outputs) == 1 else None
        if isinstance(entries, (list, tuple)) and len(entries) > max_records:
            raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_records} records")
    if preflight_records > max_records * len(collections):
        raise _synthesis_error("BUDGET_EXHAUSTED", "typed stage synthesis exceeded the record budget")
    if preflight_relationships > max_relationships:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_relationships} relationships")
    if preflight_aliases > max_aliases:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_aliases} aliases")
    if preflight_calculations > max_records:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_records} calculations")
    dependency_state: dict[str, str] = {}
    dependency_depths: dict[str, int] = {}

    def visit_dependency(record_id: str, depth: int, path: tuple[str, ...]) -> int:
        checkpoint()
        if depth > max_dependency_depth:
            raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_dependency_depth} dependency levels")
        state = dependency_state.get(record_id, "UNSEEN")
        if state == "VISITING":
            cycle_start = path.index(record_id) if record_id in path else 0
            cycle = " -> ".join((*path[cycle_start:], record_id))
            raise _synthesis_error("DEPENDENCY_CYCLE", f"typed stage synthesis contains a dependency cycle: {cycle}")
        if state == "DONE":
            longest_depth = depth + dependency_depths[record_id]
            if longest_depth > max_dependency_depth:
                raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_dependency_depth} dependency levels")
            return dependency_depths[record_id]
        dependency_state[record_id] = "VISITING"
        longest_depth = 0
        for dependency in sorted(raw_dependencies.get(record_id, ())):
            checkpoint()
            if dependency in raw_record_ids:
                child_depth = visit_dependency(dependency, depth + 1, (*path, record_id))
                longest_depth = max(longest_depth, child_depth + 1)
        dependency_depths[record_id] = longest_depth
        dependency_state[record_id] = "DONE"
        return longest_depth

    for root in sorted(raw_record_ids):
        visit_dependency(root, 0, ())

    if len(outputs) == 1 and typed_outputs and not failures:
        checkpoint()
        try:
            normalized = normalize_stage_result(
                outputs[0],
                expected_stage_id=str(getattr(stage, "stage_id", "stage")),
                existing_records=dependency_records if dependency_records is not None else existing_records,
                prefer_current_aliases=True,
                trusted_existing_records=(dependency_records if dependency_records is not None else existing_records) or {},
            )
        except ValidationError as error:
            raise ValidationError(
                str(error),
                code=getattr(error, "code", None) or "MALFORMED_OUTPUT",
                participant_index=0,
                participant_id=participant_ids[0] if participant_ids else None,
            ) from error
        if return_normalized_result:
            return normalized
        return normalized.to_contract_payload()

    normalized_outputs: list[Mapping[str, Any]] = []
    alias_records: dict[str, object] = {}
    alias_kinds: dict[str, RecordKind] = {}
    hash_cache: dict[int, str] = {}

    def record_hash(record: object) -> str:
        key = id(record)
        if key not in hash_cache:
            hash_cache[key] = _canonical_result_hash(record)
        return hash_cache[key]

    if typed_outputs:
        seed_outputs: list[Mapping[str, Any]] = list(outputs)
        peer_candidates: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
        for output in seed_outputs:
            checkpoint()
            for key in collections:
                for entry in output.get(key, []):
                    checkpoint()
                    if isinstance(entry, Mapping) and entry.get("id"):
                        peer_candidates.setdefault((key, str(entry["id"])), []).append(entry)

        peer_records: list[dict[str, object]] = []
        peer_record_kinds: list[dict[str, RecordKind]] = []
        for index, _output in enumerate(seed_outputs):
            checkpoint()
            records: dict[str, object] = {}
            kinds: dict[str, RecordKind] = {}
            for peer_index, peer_output in enumerate(seed_outputs):
                if peer_index == index:
                    continue
                for key in collections:
                    for entry in peer_output.get(key, []):
                        checkpoint()
                        if not isinstance(entry, Mapping) or not entry.get("id"):
                            continue
                        record_id = str(entry["id"])
                        candidates = peer_candidates.get((key, record_id), [])
                        if not candidates or not all(record_hash(candidate) == record_hash(candidates[0]) for candidate in candidates):
                            continue
                        records.setdefault(record_id, entry)
                        kind = collection_kinds.get(key)
                        if kind is not None:
                            previous = kinds.get(record_id)
                            if previous is None or previous == kind:
                                kinds[record_id] = kind
                            else:
                                kinds.pop(record_id, None)
            peer_records.append(records)
            peer_record_kinds.append(kinds)

        next_outputs: list[Mapping[str, Any]] = []
        next_alias_targets: dict[str, set[str]] = {}
        next_alias_records: dict[str, object] = {}
        next_alias_kinds: dict[str, set[RecordKind]] = {}
        participant_alias_maps: list[dict[str, str]] = []
        for index, output in enumerate(seed_outputs):
            checkpoint()
            dependency_records = dict(existing_records or {})
            dependency_records.update(peer_records[index])
            dependency_record_kinds = dict(peer_record_kinds[index])
            try:
                normalized, output_aliases, output_kinds = normalize_stage_result(
                    output,
                    expected_stage_id=str(getattr(stage, "stage_id", "stage")),
                    existing_records=dependency_records,
                    existing_record_kinds=dependency_record_kinds,
                    prefer_current_aliases=True,
                    trusted_existing_records=(dependency_records if dependency_records is not None else existing_records) or {},
                    return_aliases=True,
                )
            except ValidationError as error:
                if getattr(error, "participant_index", None) is not None:
                    raise
                raise ValidationError(
                    str(error),
                    code=getattr(error, "code", None) or "MALFORMED_OUTPUT",
                    participant_index=index,
                    participant_id=participant_ids[index] if index < len(participant_ids) else None,
                ) from error
            next_outputs.append(normalized.to_contract_payload())
            participant_alias_maps.append(dict(output_aliases))
            canonical_records = normalized.canonical_records()
            for alias, canonical_id in output_aliases.items():
                record = canonical_records.get(canonical_id)
                if record is None:
                    continue
                next_alias_targets.setdefault(alias, set()).add(canonical_id)
                next_alias_records.setdefault(alias, record)
                kind = output_kinds.get(alias) or output_kinds.get(canonical_id)
                if kind is not None:
                    next_alias_kinds.setdefault(alias, set()).add(kind)
                    next_alias_kinds.setdefault(canonical_id, set()).add(kind)

        alias_records = {
            alias: record
            for alias, record in next_alias_records.items()
            if len(next_alias_targets.get(alias, ())) == 1
        }
        alias_kinds = {
            alias: next(iter(kinds))
            for alias, kinds in next_alias_kinds.items()
            if len(kinds) == 1
        }
        global_aliases = {
            alias: next(iter(targets))
            for alias, targets in next_alias_targets.items()
            if len(targets) == 1
        }

        def rewrite_participant_aliases(payload: Mapping[str, Any], local_aliases: Mapping[str, str]) -> dict[str, Any]:
            rewritten = dict(payload)
            aliases = {**global_aliases, **dict(local_aliases)}
            trusted_aliases = {
                str(record_id): str(getattr(record, "id", record_id))
                for record_id, record in dict(existing_records or {}).items()
            }

            def resolve_alias(value: object) -> object:
                if not isinstance(value, str):
                    return value
                return trusted_aliases.get(value, aliases.get(value, value))
            for key in collections:
                entries = rewritten.get(key, [])
                if not isinstance(entries, (list, tuple)):
                    continue
                rewritten_entries: list[object] = []
                for entry in entries:
                    checkpoint()
                    if not isinstance(entry, Mapping):
                        rewritten_entries.append(entry)
                        continue
                    item = dict(entry)
                    for field_name in ("evidence_ids", "relationship_ids", "input_ids"):
                        values = item.get(field_name)
                        if isinstance(values, (list, tuple)):
                            item[field_name] = [resolve_alias(value) for value in values]
                    for field_name in ("from_id", "to_id"):
                        value = item.get(field_name)
                        if isinstance(value, str):
                            item[field_name] = resolve_alias(value)
                    rewritten_entries.append(item)
                rewritten[key] = rewritten_entries
            return rewritten

        normalized_outputs = [
            rewrite_participant_aliases(output, local_aliases)
            for output, local_aliases in zip(next_outputs, participant_alias_maps, strict=False)
        ]
    else:
        normalized_outputs = list(outputs)

    merge_alias_records = dict(existing_records or {})
    for alias, record in alias_records.items():
        merge_alias_records.setdefault(alias, record)
    merge_alias_kinds = dict(alias_kinds)
    outputs = normalized_outputs
    first = dict(outputs[0])

    def merge_records(key: str) -> list[object]:
        merged: list[object] = []
        by_id: dict[str, object] = {}
        for participant_index, output in enumerate(outputs):
            checkpoint()
            entries = output.get(key, [])
            if entries is None:
                continue
            if not isinstance(entries, (list, tuple)):
                raise _synthesis_error("MALFORMED_OUTPUT", f"typed stage synthesis requires a list for {key}")
            for entry in entries:
                checkpoint()
                if len(merged) >= max_records:
                    raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_records} records")
                record_id = entry.get("id") if isinstance(entry, Mapping) else None
                if not record_id:
                    merged.append(entry)
                    continue
                existing = by_id.get(str(record_id))
                if existing is None:
                    by_id[str(record_id)] = entry
                    merged.append(entry)
                    continue
                if record_hash(existing) != record_hash(entry):
                    raise ValidationError(
                        f"conflicting canonical record for {key}:{record_id}",
                        code="MATERIAL_CONFLICT",
                        participant_index=participant_index,
                        participant_id=participant_ids[participant_index] if participant_index < len(participant_ids) else None,
                    )
        return merged

    for key in collections:
        checkpoint()
        first[key] = merge_records(key)
    if len(first["relationships"]) > max_relationships:
        raise _synthesis_error("BUDGET_EXHAUSTED", f"typed stage synthesis exceeded {max_relationships} relationships")
    first["assumptions"] = [entry for output in outputs for entry in list(output.get("assumptions", []))]
    first["uncertainty"] = [entry for output in outputs for entry in list(output.get("uncertainty", []))]
    first["monitoring_indicators"] = [entry for output in outputs for entry in list(output.get("monitoring_indicators", []))]
    if failures:
        first["uncertainty"].extend(f"participant failure: {type(error).__name__}" for error in failures)
    if typed_outputs:
        checkpoint()
        try:
            return normalize_stage_result(
                first,
                expected_stage_id=str(getattr(stage, "stage_id", "stage")),
                existing_records=merge_alias_records,
                existing_record_kinds=merge_alias_kinds,
                prefer_current_aliases=True,
                trusted_existing_records=existing_records or {},
            ).to_contract_payload()
        except ValidationError as error:
            if getattr(error, "participant_index", None) is not None or len(outputs) != 1:
                raise
            raise ValidationError(
                str(error),
                code=getattr(error, "code", None) or "MALFORMED_OUTPUT",
                participant_index=0,
                participant_id=participant_ids[0] if participant_ids else None,
            ) from error
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
    participant_configs = () if str(getattr(stage, "executor_kind", "agent")) == "deterministic_local" else tuple(_stage_participants(stage))
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
        "analysis_contract_fingerprints": input_payload.get("analysis_contract_fingerprints", {}),
        "analysis_analyzer_fingerprints": input_payload.get("analysis_analyzer_fingerprints", {}),
        "workbook_source_sha256": input_payload.get("workbook_source_sha256", ""),
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


def _record_workbook_metrics(scope: CapabilityScope, metrics: RunMetrics) -> None:
    workbook_context = getattr(scope, "workbook_context", None)
    stats = getattr(workbook_context, "stats", None)
    if stats is None:
        return
    for field in (
        "capture_count",
        "capture_hash_count",
        "currentness_hash_count",
        "xlsx_parse_count",
        "openpyxl_load_count",
        "cache_hits",
        "analysis_cache_hits",
        "snapshot_bytes",
        "retained_read_result_bytes",
        "retained_analysis_result_bytes",
        "retained_authority_record_bytes",
    ):
        metric_field = "workbook_cache_hits" if field == "cache_hits" else field
        setattr(metrics, metric_field, int(getattr(stats, field, 0) or 0))


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
    has_external_stage = any(str(getattr(stage, "executor_kind", "agent")) != "deterministic_local" for stage in recipe.stages or ())
    factory = AgentFactory(client) if client is not None and has_external_stage else None
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

    def cancel_requested() -> bool:
        checker = context.get("cancel_check")
        if checker is not None and checker():
            return True
        control = context.get("run_control")
        return getattr(control, "state", "") in {"cancel_requested", "canceled"}

    def ensure_not_cancelled() -> None:
        if cancel_requested():
            raise RunCanceledError("run canceled during stage execution")

    required_capabilities: set[str] = set()
    selected_skills_by_stage: dict[str, dict[str, tuple[object, ...]]] = {}
    for stage in recipe.stages or ():
        if str(getattr(stage, "executor_kind", "agent")) == "deterministic_local":
            selected_skills_by_stage[getattr(stage, "stage_id", "stage")] = {}
            continue
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
    try:
        context = prepare_capability_context(tuple(sorted(required_capabilities)), context, scope=scope)
    except BaseException as error:
        metrics.record_failure(_failure_class(error), error)
        metrics.settled = True
        metrics.runtime_status = "FAILED"
        metrics.wall_time_ms = round((time.perf_counter() - started) * 1000)
        _record_workbook_metrics(scope, metrics)
        if owns_scope:
            metrics.cleanup_complete = False
            try:
                await scope.close()
            except BaseException as cleanup_error:
                metrics.record_failure(FailureClass.CLEANUP, cleanup_error)
            else:
                metrics.cleanup_complete = True
        try:
            setattr(error, "run_metrics", metrics)
            setattr(error, "metrics", metrics)
        except BaseException:
            pass
        raise
    stages_by_id = {
        str(getattr(stage, "stage_id", "")): stage
        for stage in recipe.stages or ()
    }

    def settle_failure(error: BaseException) -> None:
        metrics.record_failure(_failure_class(error), error)
        metrics.settled = True
        metrics.runtime_status = "PARTIAL" if (context.get("canonical_records") or outputs) else "FAILED"
        _refresh_execution_status(context, metrics)
        try:
            setattr(error, "run_metrics", metrics)
            setattr(error, "metrics", metrics)
        except BaseException:
            pass

    async def dispatch_stage(stage: Any, stage_input: object) -> tuple[list[object], object]:
        ensure_not_cancelled()
        pattern = ExecutionPattern(stage.pattern)
        stage_skill_ids = tuple(getattr(stage, "skill_ids", ()))
        executor_kind = str(getattr(stage, "executor_kind", "agent"))
        participants = [] if executor_kind == "deterministic_local" else list(_stage_participants(stage))
        selected_skills_by_participant = dict(
            context.get("selected_skills_by_stage", {}).get(getattr(stage, "stage_id", ""), {})
        )
        selected_skills = tuple(
            skill
            for participant in participants
            for skill in selected_skills_by_participant.get(participant.id, ())
        )
        stage_skill_hashes = tuple(skill.content_sha256 for skill in selected_skills)
        limits = dict(getattr(stage, "limits", {}) or {})
        stage_call_limit = limits.get("max_total_agent_calls")
        if stage_call_limit is not None:
            stage_call_limit = _positive_limit(stage_call_limit, label="stage max_total_agent_calls")
        stage_calls = 0

        def reserve_stage_call() -> bool:
            nonlocal stage_calls
            if stage_call_limit is not None and stage_calls >= stage_call_limit:
                return False
            if not budget.call():
                return False
            stage_calls += 1
            return True

        context.setdefault("skill_hashes_by_stage", {})[getattr(stage, "stage_id", "")] = stage_skill_hashes
        stage_context = dict(context)
        stage_context["stage_id"] = str(getattr(stage, "stage_id", "stage"))
        stage_context["selected_skills"] = selected_skills
        stage_context["selected_skills_by_participant"] = selected_skills_by_participant
        stage_context["reserve_agent_call"] = reserve_stage_call
        stage_context["record_agent_call"] = lambda: setattr(metrics, "model_calls", metrics.model_calls + 1)
        stage_context["provider_call_middleware"] = _ReservedProviderCallMiddleware(
            stage_context["reserve_agent_call"], stage_context["record_agent_call"]
        )
        dependency_records: dict[str, object] = {}
        for dependency in _dependency_stage_ids(stage, stages_by_id):
            dependency_receipt = context.get("stage_receipts", {}).get(str(dependency))
            for reference in tuple(getattr(dependency_receipt, "result_references", ())):
                if reference in context.get("canonical_records", {}):
                    dependency_records[reference] = context["canonical_records"][reference]
        stage_context["dependency_records"] = _expand_dependency_records(
            dependency_records,
            context.get("canonical_records", {}),
        )
        semantic_fingerprint, execution_policy_fingerprint = _stage_fingerprints(
            stage,
            stage_input,
            stage_skill_ids,
            selected_skills_by_participant,
        )
        cache_key = semantic_fingerprint
        stage_context["stage_fingerprints"] = (semantic_fingerprint, execution_policy_fingerprint)
        stage_context["stage_fingerprint_bundle"] = {
            "semantic": semantic_fingerprint,
            "execution_policy": execution_policy_fingerprint,
            "analysis_contracts": tuple(stage_input.analysis_contract_fingerprints),
            "analysis_analyzers": tuple(stage_input.analysis_analyzer_fingerprints),
        }
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
                analyzer_fingerprints=tuple(stage_input.analysis_analyzer_fingerprints),
                source_revision=stage_input.workbook_source_sha256 or None,
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
        max_timeout = limits.get("max_timeout_seconds", limits.get("timeout_seconds"))
        for field_name in ("max_agent_steps", "max_branches", "max_handoffs", "max_tool_calls"):
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
            if stage_call_limit is not None:
                remaining_calls = stage_call_limit if remaining_calls is None else min(remaining_calls, stage_call_limit)
            if remaining_calls is not None:
                if remaining_calls < 1:
                    raise BudgetExceededError("maximum agent calls exceeded before group chat dispatch")
                effective_rounds = min(effective_rounds, remaining_calls)
            stage_context["max_rounds"] = effective_rounds
        if limits.get("max_agent_steps") is not None and budget.agent_steps + 1 > int(limits["max_agent_steps"]):
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        if not budget.step():
            raise BudgetExceededError("maximum agent steps exceeded before dispatch")
        if executor_kind != "deterministic_local":
            metrics.participant_invocations += len(participants) or 1
        if pattern == ExecutionPattern.CONCURRENT:
            branch_count = len(participants) or 2
            if limits.get("max_branches") is not None and branch_count > int(limits["max_branches"]):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
            if not budget.reserve(branches=branch_count):
                raise BudgetExceededError("maximum concurrent branches exceeded before dispatch")
        async def invoke(stage_prompt: str | None = None) -> tuple[list[object], object]:
            ensure_not_cancelled()
            if str(getattr(stage, "executor_kind", "agent")) == "deterministic_local":
                output = await DeterministicLocalExecutor(stage, stage_input, stage_context).execute()
                return [output], output
            prompt_value = stage_prompt or str(stage_input)
            if stage_context.get("correction_participant_ids") and client is not None and pattern != ExecutionPattern.DIRECT:
                raise _synthesis_error("UNSUPPORTED_RECOVERY", "native orchestration cannot expose participant-local correction state")
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
                    dependency_records=stage_context.get("dependency_records"),
                    cancel_check=cancel_requested,
                    return_normalized_result=committer is not None,
                )
            if pattern == ExecutionPattern.DIRECT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), stage_context).execute(prompt_value)]
            elif pattern == ExecutionPattern.CONCURRENT:
                participant_roles = tuple(participants or ({"purpose": "participant"},) * 2)
                branch_count = len(participant_roles)
                metrics.branches = branch_count
                metrics.parallelism = branch_count
                participant_configs = tuple(
                    ParticipantConfig.from_mapping(item, f"participant-{index + 1}")
                    for index, item in enumerate(participant_roles)
                )
                participant_ids = tuple(item.id for item in participant_configs)
                correction_ids = tuple(str(item) for item in stage_context.pop("correction_participant_ids", ()))
                participant_outputs = dict(stage_context.get("participant_outputs", {}))
                if correction_ids and not participant_outputs:
                    raise _synthesis_error("UNSUPPORTED_RECOVERY", "participant-local correction state is unavailable")
                if participant_outputs and set(participant_outputs) - set(participant_ids):
                    raise _synthesis_error("UNSUPPORTED_RECOVERY", "participant-local correction state contains an unknown participant")
                selected_ids = correction_ids or participant_ids
                if any(item not in participant_ids for item in selected_ids):
                    raise _synthesis_error("UNSUPPORTED_RECOVERY", "participant-local correction state contains an unknown participant")
                selected_results = await asyncio.gather(
                    *[
                        AnalystExecutor(client, factory, participant_configs[participant_ids.index(participant_id)], stage_context).execute(prompt_value)
                        for participant_id in selected_ids
                    ],
                    return_exceptions=True,
                )
                for participant_id, item in zip(selected_ids, selected_results, strict=False):
                    participant_outputs[participant_id] = item
                if len(participant_outputs) != branch_count:
                    raise _synthesis_error("UNSUPPORTED_RECOVERY", "participant-local correction state is incomplete")
                failed_ids: list[str] = []
                for participant_id in participant_ids:
                    item = participant_outputs[participant_id]
                    if isinstance(item, BaseException):
                        failed_ids.append(participant_id)
                stage_context["participant_outputs"] = participant_outputs
                if any(isinstance(item, (asyncio.CancelledError, RunCanceledError)) for item in participant_outputs.values()):
                    cancellation = next(item for item in participant_outputs.values() if isinstance(item, (asyncio.CancelledError, RunCanceledError)))
                    raise cancellation
                successful_ids = tuple(item for item in participant_ids if not isinstance(participant_outputs[item], BaseException))
                results = tuple(participant_outputs[item] for item in successful_ids)
                failures = tuple(participant_outputs[item] for item in participant_ids if isinstance(participant_outputs[item], BaseException))
                stage_context["failed_participant_ids"] = tuple(failed_ids)
                return list(results), _synthesize_stage_outputs(
                    stage,
                    list(results),
                    failures,
                    allow_legacy_fallback=context.get("analysis_store") is None,
                    existing_records=context.get("canonical_records"),
                    dependency_records=stage_context.get("dependency_records"),
                    participant_ids=successful_ids,
                    cancel_check=cancel_requested,
                    return_normalized_result=committer is not None,
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
                dependency_records=stage_context.get("dependency_records"),
                cancel_check=cancel_requested,
                return_normalized_result=committer is not None,
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
                failed_participant_ids = tuple(stage_context.pop("failed_participant_ids", ()))
                if failed_participant_ids and correction_prompt is None:
                    if not budget.correct():
                        raise _synthesis_error("BUDGET_EXHAUSTED", "participant correction budget exhausted")
                    if pattern not in {ExecutionPattern.CONCURRENT, ExecutionPattern.DIRECT}:
                        raise _synthesis_error("UNSUPPORTED_RECOVERY", "participant-local correction is unsupported for this execution pattern")
                    metrics.correction_rounds += 1
                    stage_context["correction_participant_ids"] = failed_participant_ids
                    correction_prompt = (
                        f"{json.dumps(_stage_input_payload(stage_input), default=str, ensure_ascii=False, sort_keys=True)}\n\n"
                        "The previous participant result failed during execution. Correct only your participant result, "
                        "return the complete structured result, and do not repeat successful participants or source reads."
                    )
                    continue
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
                recovery_code = getattr(error, "code", None)
                stage_context["last_recovery_code"] = recovery_code
                if recovery_code in _NON_RETRYABLE_VALIDATION_CODES:
                    raise
                if recovery_code is None:
                    if not budget.correct():
                        raise
                    metrics.correction_rounds += 1
                    correction_prompt = (
                        f"{json.dumps(_stage_input_payload(stage_input), default=str, ensure_ascii=False, sort_keys=True)}\n\n"
                        "The previous structured result was rejected by canonical validation. "
                        "Correct only the validation issue and return the complete result again. "
                        "For relationships, correct only the exact invalid edge when its participants "
                        "are known; never silently drop a required edge or return a guessed edge. "
                        "For dependency outputs, reference an existing canonical dependency ID only "
                        "after you validate its hash and invalidation state, dependency closure, and "
                        "participant authorization. "
                        f"Validation issue: {error}"
                    )
                    continue
                if not budget.correct():
                    raise
                participant_id = getattr(error, "participant_id", None)
                participant_index = getattr(error, "participant_index", None)
                if participant_id is None and participant_index is not None and 0 <= int(participant_index) < len(participants):
                    participant_id = participants[int(participant_index)].id
                if participant_id is None and len(participants) > 1:
                    raise _synthesis_error(
                        "UNSUPPORTED_RECOVERY",
                        "validation failure does not identify a safe participant-local correction target",
                    ) from error
                if pattern == ExecutionPattern.SEQUENTIAL:
                    metrics.correction_rounds += 1
                    correction_prompt = (
                        f"{json.dumps(_stage_input_payload(stage_input), default=str, ensure_ascii=False, sort_keys=True)}\n\n"
                        "The sequential stage produced a validation failure. Rerun the complete sequential stage, "
                        "preserve the original source context, and return the complete corrected structured result. "
                        "Before returning, audit every evidence_ids, relationship_ids, input_ids, from_id, and "
                        "to_id value against an ID declared in this payload or an authorized dependency; remove "
                        "any reference without a matching record, and never invent, reuse, or guess an ID from "
                        "another stage or prior run. "
                        f"Validation issue identified at participant {participant_id or 'unknown'}: {error}"
                    )
                    continue
                if pattern not in {ExecutionPattern.CONCURRENT, ExecutionPattern.DIRECT}:
                    raise _synthesis_error(
                        "UNSUPPORTED_RECOVERY",
                        f"participant-local correction is unsupported for {pattern.value}",
                    ) from error
                metrics.correction_rounds += 1
                if participant_id is not None:
                    stage_context["correction_participant_ids"] = (str(participant_id),)
                correction_prompt = (
                    f"{json.dumps(_stage_input_payload(stage_input), default=str, ensure_ascii=False, sort_keys=True)}\n\n"
                    "The previous structured result was rejected by canonical validation. "
                    "Correct only the validation issue and return the complete result again. "
                     "For relationships, every from_id and to_id must refer to a record declared "
                     "in this current result or copied exactly from dependency_outputs. Correct "
                     "only the exact invalid edge when both participants and the intended edge are "
                     "known; otherwise stop with an explicit unsupported recovery result. Never "
                     "silently drop a required edge or replace it with a guessed or dangling edge. "
                     "Before returning, audit every evidence_ids, relationship_ids, input_ids, "
                     "from_id, and to_id value against an ID declared in this payload; remove any "
                     "reference without a matching local record, and do not reuse IDs from another "
                     "stage or prior run. "
                     "For dependency outputs, reference an existing canonical dependency ID only "
                     "after you validate its hash and invalidation state, dependency closure, and "
                     "participant authorization; do not copy dependency records into this result "
                     "unless the canonical contract explicitly requires materialization. "
                    "For same-ID/different-content conflicts, preserve the exact canonical record "
                    "content and do not rewrite an existing record under the same ID; when two "
                    "participants conflict, preserve the first participant's record verbatim. "
                     "Every text-list item such as limitations, assumptions, uncertainty, "
                     "disconfirmation_conditions, and monitoring_indicators must be non-empty; "
                     "omit empty strings instead of returning them. "
                    f"Validation issue: {error}"
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
            analyzer_fingerprints=tuple(stage_input.analysis_analyzer_fingerprints),
            result_references=canonical.result_references,
            result_hashes=canonical.result_hashes,
            status="committed",
            committed=True,
            provenance_complete=True,
            source_revision=str(
                context.get("source_revision", "") or stage_input.workbook_source_sha256
            ),
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
            all_contract_fingerprints = {
                str(domain): str(fingerprint)
                for domain, fingerprint in dict(context.get("analysis_contract_fingerprints", {})).items()
            }
            declared_domains = tuple(str(item) for item in getattr(stage, "analysis_domains", ()))
            stage_id = str(getattr(stage, "stage_id", "stage"))
            relevant_contract_fingerprints = {
                domain: all_contract_fingerprints.get(
                    f"{stage_id}:{domain}",
                    all_contract_fingerprints.get(f"GLOBAL_SCOPE:{domain}", all_contract_fingerprints.get(domain)),
                )
                for domain in declared_domains
                if all_contract_fingerprints.get(
                    f"{stage_id}:{domain}",
                    all_contract_fingerprints.get(f"GLOBAL_SCOPE:{domain}", all_contract_fingerprints.get(domain)),
                )
                is not None
            }
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
                analysis_contract_fingerprints=tuple(
                    sorted(relevant_contract_fingerprints.items())
                ),
                analysis_analyzer_fingerprints=tuple(
                    sorted(
                        {
                            domain: context.get("analysis_analyzer_fingerprints", {}).get(
                                f"{stage_id}:{domain}",
                                context.get("analysis_analyzer_fingerprints", {}).get(domain, ""),
                            )
                            for domain in declared_domains
                            if context.get("analysis_analyzer_fingerprints", {}).get(
                                f"{stage_id}:{domain}",
                                context.get("analysis_analyzer_fingerprints", {}).get(domain),
                            ) is not None
                        }.items()
                    )
                ),
                workbook_source_sha256=(str(context.get("workbook_source_sha256", "")) if declared_domains else ""),
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
        _record_workbook_metrics(scope, metrics)
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
