import asyncio

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.runtime.metrics import RunMetrics
from foresight_os.runtime.workflow import run_recipe_async


class FakeClient:
    additional_properties = {}

    def get_response(self, messages, **kwargs):
        if kwargs.get("stream"):
            async def updates():
                yield ChatResponseUpdate(contents=[Content("text", text="ok")], role="assistant")

            return ResponseStream(
                updates(),
                finalizer=lambda _: ChatResponse(messages=[Message("assistant", ["ok"])]),
            )

        async def response():
            return ChatResponse(messages=[Message("assistant", ["ok"])])

        return response()

    def as_agent(self, instructions: str):
        return Agent(self, instructions=instructions)


def test_run_recipe_returns_typed_metrics_and_real_executor_calls():
    result = asyncio.run(run_recipe_async(make_recipe(RecipeName.ANALYZE_REVIEW), "analyse", FakeClient(), "run-test"))

    assert isinstance(result.metrics, RunMetrics)
    assert result.metrics.model_calls == 2
    assert result.metrics.run_id == "run-test"
    assert len(result.outputs) == 2
