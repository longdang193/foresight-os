import asyncio
from typing import Any

from agent_framework import FunctionExecutor, WorkflowBuilder, WorkflowContext


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
