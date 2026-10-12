import asyncio
import time
from uuid import uuid4
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor
from foresight_os.runtime.metrics import RunMetrics, RunResult


async def _run_native_stage(pattern: ExecutionPattern, prompt: str, client: Any, roles: list[dict[str, str]]) -> list[object] | None:
    from agent_framework import Agent
    from agent_framework.orchestrations import ConcurrentBuilder, GroupChatBuilder, HandoffBuilder, SequentialBuilder

    agents = [client.as_agent(instructions=f"Act as the {role.get('purpose', 'participant')} participant and return a structured result.") for role in roles]
    if not agents or not all(isinstance(agent, Agent) for agent in agents):
        return None
    if pattern == ExecutionPattern.SEQUENTIAL:
        workflow = SequentialBuilder(participants=agents, output_from="all").build()
    elif pattern == ExecutionPattern.CONCURRENT:
        workflow = ConcurrentBuilder(participants=agents, output_from="all").build()
    elif pattern == ExecutionPattern.HANDOFF:
        workflow = HandoffBuilder(participants=agents, output_from="all").with_start_agent(agents[0]).build()
    elif pattern == ExecutionPattern.GROUP_CHAT:
        workflow = GroupChatBuilder(participants=agents, max_rounds=4, output_from="all").build()
    else:
        return [await agents[0].run(prompt)]
    result = await workflow.run(prompt)
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
) -> RunResult:
    started = time.perf_counter()
    metrics = RunMetrics(run_id or f"run-{uuid4().hex}", recipe.name.value, recipe.pattern)
    outputs: list[object] = []
    try:
        stages = recipe.stages or ()
        if not stages:
            stages = (type("Stage", (), {"pattern": ExecutionPattern(recipe.pattern), "participants": tuple(recipe.roles)})(),)
        current: object = prompt
        for stage in stages:
            pattern = ExecutionPattern(stage.pattern)
            participants = list(stage.participants)
            if client is not None and pattern != ExecutionPattern.DIRECT:
                native_outputs = await _run_native_stage(pattern, str(current), client, participants)
                if native_outputs is not None:
                    outputs.extend(native_outputs)
                    current = native_outputs[-1]
                    metrics.model_calls += len(participants)
                    metrics.handoffs += int(pattern == ExecutionPattern.HANDOFF)
                    metrics.chat_rounds += int(pattern == ExecutionPattern.GROUP_CHAT)
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
                    metrics.handoffs += int(pattern == ExecutionPattern.HANDOFF)
            metrics.model_calls += sum(1 for _ in stage_outputs) if client is not None and pattern in {ExecutionPattern.DIRECT, ExecutionPattern.CONCURRENT, ExecutionPattern.GROUP_CHAT} else 0
            outputs.extend(stage_outputs)
            current = stage_outputs[-1]
        return RunResult(metrics.run_id, tuple(outputs), metrics)
    except Exception:
        metrics.provider_failures += 1
        raise
    finally:
        metrics.wall_time_ms = round((time.perf_counter() - started) * 1000)
        metrics.cleanup_complete = True


def run_recipe(recipe: ExecutionRecipe, prompt: str, client: Any | None = None, run_id: str | None = None) -> RunResult:
    return asyncio.run(run_recipe_async(recipe, prompt, client, run_id))
