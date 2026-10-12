import asyncio

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.runtime.metrics import RunMetrics
from foresight_os.runtime.workflow import run_recipe_async


class FakeResponse:
    value = {"status": "ok"}
    text = "ok"


class FakeAgent:
    async def run(self, prompt: str):
        return FakeResponse()


class FakeClient:
    def as_agent(self, instructions: str):
        return FakeAgent()


def test_run_recipe_returns_typed_metrics_and_real_executor_calls():
    result = asyncio.run(run_recipe_async(make_recipe(RecipeName.ANALYZE_REVIEW), "analyse", FakeClient(), "run-test"))

    assert isinstance(result.metrics, RunMetrics)
    assert result.metrics.model_calls == 2
    assert result.metrics.run_id == "run-test"
    assert len(result.outputs) == 2
