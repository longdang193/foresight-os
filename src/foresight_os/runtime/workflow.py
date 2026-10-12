import asyncio
import time
from uuid import uuid4
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext

from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor
from foresight_os.runtime.metrics import RunMetrics, RunResult


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
        analyst = AnalystExecutor(client)
        outputs.append(await analyst.execute(prompt))
        metrics.model_calls += 1 if client is not None else 0
        if len(recipe.roles) > 1:
            reviewer = ReviewerExecutor(client)
            outputs.append(await reviewer.execute(f"Review this proposal:\n{outputs[-1]}"))
            metrics.model_calls += 1 if client is not None else 0
        return RunResult(metrics.run_id, tuple(outputs), metrics)
    except Exception:
        metrics.provider_failures += 1
        raise
    finally:
        metrics.wall_time_ms = round((time.perf_counter() - started) * 1000)


def run_recipe(recipe: ExecutionRecipe, prompt: str, client: Any | None = None, run_id: str | None = None) -> RunResult:
    return asyncio.run(run_recipe_async(recipe, prompt, client, run_id))
