import asyncio
import time
from types import SimpleNamespace
import pytest

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
from foresight_os.controller.recipes import ExecutionPattern, RecipeName, ExecutionRecipe, RecipeStage, make_recipe
from foresight_os.runtime.metrics import BudgetExceededError, FailureClass, RunMetrics
from foresight_os.runtime.capabilities import CapabilityDefinition, ExecutionMode, ForesightFunctionMiddleware, ScopeOwnership, CapabilityScope, instrument_tool
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


def _group_chat_recipe(**limits):
    base = make_recipe(RecipeName.CHALLENGE_RECOMMENDATION)
    stage = RecipeStage("chat", ExecutionPattern.GROUP_CHAT, tuple(base.roles), "prompt", "typed-result", limits)
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


@pytest.mark.parametrize(("limit", "expected_outputs", "expected_rounds"), ((1, 1, 1), (2, 2, 2), (4, 2, 2)))
def test_fallback_group_chat_honors_stage_round_limit(limit, expected_outputs, expected_rounds):
    result = asyncio.run(run_recipe_async(_group_chat_recipe(max_rounds=limit), "analyse", None, f"group-{limit}"))

    assert len(result.outputs) == expected_outputs
    assert result.metrics.chat_rounds == expected_rounds


def test_group_chat_rejects_non_positive_round_limit():
    with pytest.raises(Exception) as caught:
        asyncio.run(run_recipe_async(_group_chat_recipe(max_rounds=0), "analyse", None, "group-invalid"))

    assert "positive integer" in str(caught.value)


def test_group_chat_run_limit_is_cumulative_across_stages():
    base = make_recipe(RecipeName.CHALLENGE_RECOMMENDATION)
    stages = (
        RecipeStage("first", ExecutionPattern.GROUP_CHAT, tuple(base.roles), "prompt", "typed-result", {"max_rounds": 1}),
        RecipeStage("second", ExecutionPattern.GROUP_CHAT, tuple(base.roles), "prompt", "typed-result", {"max_rounds": 4}),
    )
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=stages,
    )

    with pytest.raises(BudgetExceededError) as caught:
        asyncio.run(run_recipe_async(recipe, "analyse", None, "group-run-limit", {"max_rounds": 1}))

    assert caught.value.metrics.chat_rounds == 1
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


def test_agent_factory_applies_stage_model_and_reasoning_controls():
    class CapturingClient:
        def __init__(self):
            self.kwargs = None

        def as_agent(self, **kwargs):
            self.kwargs = kwargs
            return object()

    client = CapturingClient()
    AgentFactory(client).create(
        ParticipantConfig(
            "scout",
            "scout",
            "find signals",
            model="approved-model",
            reasoning_controls={"temperature": 0.1},
            provider="local",
        ),
    )

    assert client.kwargs["default_options"] == {"model": "approved-model", "temperature": 0.1}


def test_agent_factory_rejects_unconfigured_stage_provider():
    class CapturingClient:
        def as_agent(self, **kwargs):
            raise AssertionError("provider must be rejected before agent construction")

    with pytest.raises(RuntimeError, match="provider 'external' is not configured"):
        AgentFactory(CapturingClient()).create(
            ParticipantConfig("scout", "scout", "find signals", provider="external"),
        )


def test_stage_capability_override_is_required_at_dispatch():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage(
        "controlled",
        ExecutionPattern.DIRECT,
        ({"id": "scout", "purpose": "find signals"},),
        "prompt",
        "typed-result",
        {},
        capabilities=("missing-capability",),
    )
    recipe = ExecutionRecipe(
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

    with pytest.raises(RuntimeError, match="capabilities unavailable"):
        asyncio.run(run_recipe_async(recipe, "find signals", FakeClient()))


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


def test_mcp_instrumentation_uses_thin_public_adapter():
    from agent_framework import MCPStreamableHTTPTool

    tool = MCPStreamableHTTPTool("probe", "http://127.0.0.1", load_prompts=False)

    async def fake_call_tool(name, **kwargs):
        return {"name": name, **kwargs}

    tool.call_tool = fake_call_tool
    wrapped = instrument_tool(tool, CapabilityDefinition("mcp", "external_read"), {})
    assert wrapped is not tool
    assert wrapped.__foresight_instrumented__
    assert asyncio.run(wrapped.call_tool("read", query="capacity"))["name"] == "read"


def test_reused_mcp_tool_rebinds_budget_and_metrics_per_run():
    from agent_framework import MCPStreamableHTTPTool

    tool = MCPStreamableHTTPTool("probe", "http://127.0.0.1", load_prompts=False)

    async def fake_call_tool(name, **kwargs):
        return {"name": name, **kwargs}

    tool.call_tool = fake_call_tool
    first_metrics = RunMetrics("first", "DIRECT", "direct")
    second_metrics = RunMetrics("second", "DIRECT", "direct")
    first = instrument_tool(tool, CapabilityDefinition("mcp", "external_read"), {"budget": BudgetState(5, 1, 5, max_tool_calls=1), "metrics": first_metrics})
    second = instrument_tool(tool, CapabilityDefinition("mcp", "external_read"), {"budget": BudgetState(5, 1, 5, max_tool_calls=1), "metrics": second_metrics})
    asyncio.run(first.call_tool("read"))
    asyncio.run(second.call_tool("read"))
    assert first_metrics.tool_calls == 1
    assert second_metrics.tool_calls == 1


def test_blocking_capability_runs_off_event_loop_and_settles_cancellation():
    async def scenario():
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        metrics = RunMetrics("blocking", "DIRECT", "direct")

        def blocking(cancel_check=None):
            for _ in range(100):
                time.sleep(0.001)
                if cancel_check and cancel_check():
                    return "cancelled"
            return "done"

        wrapped = instrument_tool(
            blocking,
            CapabilityDefinition("spreadsheet_read", "local_deterministic", execution_mode=ExecutionMode.BLOCKING),
            {"scope": scope, "metrics": metrics},
        )
        heartbeat = asyncio.Event()

        async def pulse():
            await asyncio.sleep(0.005)
            heartbeat.set()

        task = asyncio.create_task(wrapped())
        await pulse()
        assert heartbeat.is_set()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await scope.close()
        assert metrics.cancellation_settlements == 1
        assert scope.executor is None

    asyncio.run(scenario())


def test_public_function_middleware_accounts_for_native_function_invocation():
    async def scenario():
        metrics = RunMetrics("middleware", "DIRECT", "direct")
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        middleware = ForesightFunctionMiddleware(
            {"read_evidence": CapabilityDefinition("mcp_read", "external_read")},
            {"scope": scope, "metrics": metrics, "budget": BudgetState(5, 1, 5, max_tool_calls=1)},
        )
        context = SimpleNamespace(function=SimpleNamespace(name="read_evidence"))
        called = []

        async def call_next():
            called.append(True)

        await middleware.process(context, call_next)
        assert called == [True]
        assert metrics.tool_calls == 1
        await scope.close()

    asyncio.run(scenario())


def test_public_function_middleware_preserves_provider_errors_and_cleanup():
    async def scenario():
        metrics = RunMetrics("middleware-error", "DIRECT", "direct")
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        middleware = ForesightFunctionMiddleware(
            {"read_evidence": CapabilityDefinition("mcp_read", "external_read")},
            {"scope": scope, "metrics": metrics, "budget": BudgetState(5, 1, 5, max_tool_calls=1)},
        )

        async def provider():
            raise RuntimeError("provider failed")

        function = SimpleNamespace(name="read_evidence")
        context = SimpleNamespace(function=function, arguments={"query": "capacity"})

        async def call_next():
            await provider()

        with pytest.raises(RuntimeError, match="provider failed"):
            await middleware.process(context, call_next)
        assert metrics.tool_calls == 1
        assert metrics.tool_failures == 1
        await scope.close()
        assert scope._closed

    asyncio.run(scenario())


def test_public_function_middleware_rejects_budget_before_provider_call():
    async def scenario():
        metrics = RunMetrics("middleware-budget", "DIRECT", "direct")
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        middleware = ForesightFunctionMiddleware(
            {"read_evidence": CapabilityDefinition("mcp_read", "external_read")},
            {"scope": scope, "metrics": metrics, "budget": BudgetState(5, 1, 5, max_tool_calls=0)},
        )
        provider_calls = 0
        context = SimpleNamespace(function=SimpleNamespace(name="read_evidence"), arguments={})

        async def call_next():
            nonlocal provider_calls
            provider_calls += 1

        with pytest.raises(BudgetExceededError):
            await middleware.process(context, call_next)
        assert provider_calls == 0
        assert metrics.tool_calls == 0
        assert metrics.budget_failures == 1
        await scope.close()

    asyncio.run(scenario())


def test_public_function_middleware_settles_cancellation_after_provider_exit():
    async def scenario():
        metrics = RunMetrics("middleware-cancel", "DIRECT", "direct")
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        middleware = ForesightFunctionMiddleware(
            {"read_evidence": CapabilityDefinition("mcp_read", "external_read")},
            {"scope": scope, "metrics": metrics, "budget": BudgetState(5, 1, 5, max_tool_calls=1)},
        )
        provider_exited = asyncio.Event()
        context = SimpleNamespace(function=SimpleNamespace(name="read_evidence"), arguments={})

        async def call_next():
            try:
                await asyncio.sleep(60)
            finally:
                provider_exited.set()

        task = asyncio.create_task(middleware.process(context, call_next))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert provider_exited.is_set()
        assert metrics.tool_calls == 1
        await scope.close()

    asyncio.run(scenario())
