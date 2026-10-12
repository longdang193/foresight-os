import asyncio
import inspect
import time
from uuid import uuid4
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor
from foresight_os.runtime.metrics import RunMetrics, RunResult


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
) -> list[object]:
    from agent_framework.orchestrations import ConcurrentBuilder, GroupChatBuilder, HandoffBuilder, SequentialBuilder

    agents = []
    run_error: BaseException | None = None
    try:
        if not hasattr(client, "as_agent"):
            raise RuntimeError("a native MAF client with as_agent() is required for this pattern")
        for index, role in enumerate(roles or [{"purpose": "participant"}], 1):
            instructions = f"Act as the {role.get('purpose', 'participant')} participant and return a structured result."
            try:
                agent = client.as_agent(
                    id=f"participant-{index}",
                    name=f"participant-{index}",
                    instructions=instructions,
                    require_per_service_call_history_persistence=pattern == ExecutionPattern.HANDOFF,
                )
            except TypeError:
                agent = client.as_agent(instructions=instructions)
            agents.append(agent)
        if pattern == ExecutionPattern.SEQUENTIAL:
            workflow = SequentialBuilder(participants=agents, output_from="all").build()
        elif pattern == ExecutionPattern.CONCURRENT:
            workflow = ConcurrentBuilder(participants=agents, output_from="all").build()
        elif pattern == ExecutionPattern.HANDOFF:
            builder = HandoffBuilder(participants=agents, output_from="all").with_start_agent(agents[0])
            for source in agents:
                targets = [target for target in agents if target is not source]
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
    except BaseException as error:
        run_error = error
        raise
    finally:
        close_errors = await _close_agents(agents)
        if metrics is not None and close_errors:
            metrics.cleanup_complete = False
        if close_errors and run_error is None:
            raise RuntimeError(f"failed to close {len(close_errors)} native agent(s)") from close_errors[0]


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
) -> RunResult:
    started = time.perf_counter()
    metrics = RunMetrics(run_id or f"run-{uuid4().hex}", recipe.name.value, recipe.pattern)
    outputs: list[object] = []
    metrics.cleanup_complete = True
    try:
        stages = recipe.stages or ()
        if not stages:
            stages = (type("Stage", (), {"pattern": ExecutionPattern(recipe.pattern), "participants": tuple(recipe.roles)})(),)
        current: object = prompt
        for stage in stages:
            pattern = ExecutionPattern(stage.pattern)
            participants = list(stage.participants)
            if client is not None and pattern != ExecutionPattern.DIRECT:
                native_outputs = await _run_native_stage(pattern, str(current), client, participants, metrics)
                outputs.extend(native_outputs)
                current = native_outputs[-1]
                if pattern == ExecutionPattern.CONCURRENT:
                    metrics.branches = len(participants)
                    metrics.parallelism = metrics.branches
                continue
            if pattern == ExecutionPattern.DIRECT:
                stage_outputs = [await AnalystExecutor(client).execute(str(current))]
            elif pattern == ExecutionPattern.CONCURRENT:
                metrics.branches = len(participants) or 2
                metrics.parallelism = metrics.branches
                stage_outputs = list(await asyncio.gather(*[AnalystExecutor(client).execute(str(current)) for _ in range(metrics.branches)]))
            elif pattern == ExecutionPattern.GROUP_CHAT:
                stage_outputs = [await AnalystExecutor(client).execute(str(current))]
                metrics.chat_rounds += 1
                if len(participants) > 1:
                    stage_outputs.append(await ReviewerExecutor(client).execute(f"Challenge this proposal:\n{stage_outputs[-1]}"))
                    metrics.chat_rounds += 1
            else:
                stage_outputs = [await AnalystExecutor(client).execute(str(current))]
                metrics.model_calls += 1 if client is not None else 0
                if len(participants) > 1 or pattern == ExecutionPattern.HANDOFF:
                    reviewer_prompt = f"Review this proposal:\n{stage_outputs[-1]}"
                    stage_outputs.append(await ReviewerExecutor(client).execute(reviewer_prompt))
                    metrics.model_calls += 1 if client is not None else 0
            metrics.model_calls += sum(1 for _ in stage_outputs) if client is not None and pattern in {ExecutionPattern.DIRECT, ExecutionPattern.CONCURRENT, ExecutionPattern.GROUP_CHAT} else 0
            outputs.extend(stage_outputs)
            current = stage_outputs[-1]
        return RunResult(metrics.run_id, tuple(outputs), metrics)
    except BaseException:
        metrics.provider_failures += 1
        raise
    finally:
        metrics.wall_time_ms = round((time.perf_counter() - started) * 1000)


def run_recipe(recipe: ExecutionRecipe, prompt: str, client: Any | None = None, run_id: str | None = None) -> RunResult:
    return asyncio.run(run_recipe_async(recipe, prompt, client, run_id))
