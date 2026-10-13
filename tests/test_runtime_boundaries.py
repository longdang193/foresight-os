import asyncio
import pytest

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
from foresight_os.controller.recipes import ExecutionPattern, RecipeName, ExecutionRecipe, RecipeStage, make_recipe
from foresight_os.runtime.metrics import BudgetExceededError, FailureClass, RunMetrics
from foresight_os.runtime.capabilities import CapabilityDefinition, instrument_tool
from foresight_os.controller.budgets import BudgetState
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
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

    def as_agent(self, **kwargs):
        return Agent(self, **kwargs)


def _limited_recipe(**limits):
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("limited", ExecutionPattern.DIRECT, tuple(base.roles), "prompt", "typed-result", limits)
    return ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )


def test_run_recipe_returns_typed_metrics_and_real_executor_calls():
    result = asyncio.run(run_recipe_async(make_recipe(RecipeName.ANALYZE_REVIEW), "analyse", FakeClient(), "run-test"))

    assert isinstance(result.metrics, RunMetrics)
    assert result.metrics.model_calls == 2
    assert result.metrics.run_id == "run-test"
    assert len(result.outputs) == 2
    assert result.metrics.settled


def test_budget_failure_is_rejected_before_dispatch_and_keeps_metrics():
    with pytest.raises(BudgetExceededError) as caught:
        asyncio.run(run_recipe_async(_limited_recipe(max_agent_steps=0), "analyse", FakeClient(), "budget-test"))

    assert caught.value.metrics.failure_class == FailureClass.BUDGET.value
    assert caught.value.metrics.settled
    assert caught.value.metrics.model_calls == 0


def test_agent_factory_preserves_participant_identity_and_profile_options():
    class CapturingClient:
        def __init__(self):
            self.kwargs = None

        def as_agent(self, **kwargs):
            self.kwargs = kwargs
            return object()

    client = CapturingClient()
    factory = AgentFactory(client)
    factory.create(
        ParticipantConfig("scout", "scout", "find signals", profile="high", structured_output={"type": "json"}),
        {"profile_options": {"high": {"model": "configured-model"}}},
    )

    assert client.kwargs["id"] == "scout"
    assert client.kwargs["default_options"]["model"] == "configured-model"
    assert client.kwargs["default_options"]["response_format"] == {"type": "json"}


def test_tool_budget_fails_before_dispatch_and_reports_budget():
    calls = []

    async def tool():
        calls.append(True)
        return "ok"

    metrics = RunMetrics("tool-budget", "DIRECT", "direct")
    wrapped = instrument_tool(
        tool,
        CapabilityDefinition("tool", "local_deterministic", max_parallelism=1),
        {"budget": BudgetState(5, 1, 5, max_tool_calls=1), "metrics": metrics},
    )

    asyncio.run(wrapped())
    with pytest.raises(BudgetExceededError):
        asyncio.run(wrapped())

    assert len(calls) == 1
    assert metrics.tool_calls == 1
    assert metrics.budget_failures == 1
    assert metrics.tool_failures == 0


def test_tool_semaphore_enforces_declared_parallelism():
    active = 0
    peak = 0

    async def tool():
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return "ok"

    wrapped = instrument_tool(tool, CapabilityDefinition("tool", "local_deterministic", max_parallelism=1), {})
    async def run_both():
        await asyncio.gather(wrapped(), wrapped())

    asyncio.run(run_both())

    assert peak == 1


def test_mcp_tool_calls_are_instrumented_through_maf_boundary():
    calls = []

    class MCPTool:
        async def call_tool(self, name, **kwargs):
            calls.append((name, kwargs))
            return "ok"

    metrics = RunMetrics("mcp-tool", "DIRECT", "direct")
    wrapped = instrument_tool(MCPTool(), CapabilityDefinition("mcp", "external_read"), {"metrics": metrics})
    assert asyncio.run(wrapped.call_tool("read", query="capacity")) == "ok"
    assert calls == [("read", {"query": "capacity"})]
    assert metrics.tool_calls == 1
    assert metrics.tool_failures == 0


def test_mcp_instrumentation_preserves_agent_framework_sdk_type():
    from agent_framework import MCPStreamableHTTPTool

    tool = MCPStreamableHTTPTool("probe", "http://127.0.0.1", load_prompts=False)

    async def fake_call_tool(name, **kwargs):
        return {"name": name, **kwargs}

    tool.call_tool = fake_call_tool
    wrapped = instrument_tool(tool, CapabilityDefinition("mcp", "external_read"), {})
    assert wrapped is tool
    assert isinstance(wrapped, MCPStreamableHTTPTool)
    assert asyncio.run(wrapped.call_tool("read", query="capacity"))["name"] == "read"
