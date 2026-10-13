import asyncio
import inspect
import time
from uuid import uuid4
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe
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
from foresight_os.runtime.page_retrieval import PageRetrievalCapability, bind_page_retrieval
from foresight_os.runtime.local_toolbelt import bind_local_toolbelt
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


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
    supplied_scope = context.get("scope")
    scope = supplied_scope or CapabilityScope(ownership=ScopeOwnership.RUN)
    owns_scope = supplied_scope is None or getattr(scope, "ownership", ScopeOwnership.BORROWED) == ScopeOwnership.RUN
    context["scope"] = scope
    context["metrics"] = metrics
    context["budget"] = budget
    context.setdefault("capability_resolver", CapabilityResolver())
    required_capabilities: set[str] = set()
    for stage in recipe.stages or ():
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

    async def dispatch_stage(stage: Any, current: object) -> tuple[list[object], object]:
        pattern = ExecutionPattern(stage.pattern)
        participants = list(stage.participants)
        limits = dict(getattr(stage, "limits", {}) or {})
        max_timeout = limits.get("max_timeout_seconds", limits.get("timeout_seconds"))
        for field_name in ("max_agent_steps", "max_total_agent_calls", "max_branches", "max_handoffs", "max_rounds", "max_tool_calls"):
            value = limits.get(field_name)
            if value is not None:
                current = getattr(budget, field_name)
                setattr(budget, field_name, min(current, int(value)) if current is not None else int(value))
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
                native_outputs = await _run_native_stage(pattern, str(current), client, participants, metrics, context)
                if pattern == ExecutionPattern.CONCURRENT:
                    aggregate = ConcurrentAggregate(tuple(native_outputs))
                    metrics.branches = len(participants)
                    metrics.parallelism = metrics.branches
                    return native_outputs, aggregate
                return native_outputs, native_outputs[-1]
            if pattern == ExecutionPattern.DIRECT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), context).execute(str(current))]
            elif pattern == ExecutionPattern.CONCURRENT:
                branch_count = len(participants) or 2
                metrics.branches = branch_count
                metrics.parallelism = branch_count
                branch_results = await asyncio.gather(
                    *[AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participant, f"participant-{index}"), context).execute(str(current)) for index, participant in enumerate(participants or ({"purpose": "participant"},) * branch_count, 1)],
                    return_exceptions=True,
                )
                results = tuple(item for item in branch_results if not isinstance(item, BaseException))
                failures = tuple(item for item in branch_results if isinstance(item, BaseException))
                aggregate = ConcurrentAggregate(results, failures)
                return list(results), aggregate
            elif pattern == ExecutionPattern.GROUP_CHAT:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), context).execute(str(current))]
                metrics.chat_rounds += 1
                if len(participants) > 1:
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), context).execute(f"Challenge this proposal:\n{stage_outputs[-1]}"))
                    metrics.chat_rounds += 1
            else:
                stage_outputs = [await AnalystExecutor(client, factory, ParticipantConfig.from_mapping(participants[0] if participants else {}, "analyst"), context).execute(str(current))]
                if len(participants) > 1 or pattern == ExecutionPattern.HANDOFF:
                    reviewer_prompt = f"Review this proposal:\n{stage_outputs[-1]}"
                    reviewer = participants[1] if len(participants) > 1 else {"purpose": "review"}
                    stage_outputs.append(await ReviewerExecutor(client, factory, ParticipantConfig.from_mapping(reviewer, "reviewer"), context).execute(reviewer_prompt))
            if client is not None:
                metrics.model_calls += len(stage_outputs)
            return stage_outputs, stage_outputs[-1]
        if max_timeout is not None:
            return await asyncio.wait_for(invoke(), float(max_timeout))
        return await invoke()

    primary_error: BaseException | None = None
    try:
        stages = recipe.stages or ()
        if not stages:
            stages = (type("Stage", (), {"pattern": ExecutionPattern(recipe.pattern), "participants": tuple(recipe.roles)})(),)
        current: object = prompt
        for stage in stages:
            stage_outputs, current = await dispatch_stage(stage, current)
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
