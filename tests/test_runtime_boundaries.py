import asyncio
import inspect
import time
from pathlib import Path
from types import SimpleNamespace
import pytest

from agent_framework import Agent, BaseChatClient, ChatResponse, ChatResponseUpdate, Content, FunctionTool, Message, ResponseStream
from agent_framework._middleware import ChatMiddlewareLayer
from agent_framework._tools import FunctionInvocationLayer
from foresight_os.controller.recipes import ExecutionPattern, RecipeName, ExecutionRecipe, RecipeStage, make_recipe
from foresight_os.runtime.metrics import BudgetExceededError, FailureClass, RunMetrics
from foresight_os.runtime.capabilities import CapabilityDefinition, CapabilityUnavailableError, ExecutionMode, ForesightFunctionMiddleware, ScopeOwnership, CapabilityScope, instrument_tool
from foresight_os.controller.budgets import BudgetState
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.runtime.executors import AnalystExecutor, ReviewerExecutor, _toolless_retry_agent, run_agent_with_tool_fallback
from foresight_os.runtime.workflow import run_recipe_async
from foresight_os.runtime.local_toolbelt import data_analysis, spreadsheet_read


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


class LoopingFunctionClient(FunctionInvocationLayer, ChatMiddlewareLayer, BaseChatClient):
    def __init__(self):
        self.calls = 0
        FunctionInvocationLayer.__init__(self)

    async def _inner_get_response(self, *, messages, stream, options, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return ChatResponse(
                messages=[
                    Message(
                        "assistant",
                        [Content.from_function_call("call-1", "retrieve", arguments={"query": "capacity"})],
                    )
                ],
                finish_reason="tool_calls",
            )
        return ChatResponse(messages=[Message("assistant", ["done"])], finish_reason="stop")


async def retrieve_capacity(query: str) -> str:
    return f"result for {query}"


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
    assert result.metrics.runtime_status == "SETTLED"
    assert result.metrics.persistence_status == "NOT_STARTED"
    assert result.metrics.analysis_status == "NOT_STARTED"


def test_tool_result_fallback_reserves_retry_call_budget():
    class ToolResponse:
        messages = [type("Message", (), {"role": "tool", "contents": [type("Content", (), {"result": {"value": 1}})()]})()]
        value = None
        text = ""

    class Agent:
        def __init__(self):
            self.calls = 0

        async def run(self, prompt, **kwargs):
            self.calls += 1
            return ToolResponse()

    agent = Agent()
    remaining = {"calls": 1}

    def reserve_call():
        if remaining["calls"] < 1:
            return False
        remaining["calls"] -= 1
        return True

    with pytest.raises(BudgetExceededError, match="agent calls"):
        asyncio.run(run_agent_with_tool_fallback(agent, "prompt", reserve_call=reserve_call))
    assert agent.calls == 1


def test_framework_function_continuation_reserves_each_provider_dispatch():
    client = LoopingFunctionClient()
    agent = Agent(client, tools=[retrieve_capacity])
    budget = BudgetState(5, 1, 1)
    metrics = RunMetrics("function-loop", "DIRECT", "direct")

    with pytest.raises(BudgetExceededError, match="agent calls"):
        asyncio.run(
            run_agent_with_tool_fallback(
                agent,
                "inspect capacity",
                reserve_call=budget.call,
                on_call=lambda: setattr(metrics, "model_calls", metrics.model_calls + 1),
            )
        )

    assert client.calls == 1
    assert budget.total_agent_calls == 1
    assert metrics.model_calls == 1


def test_budget_failure_is_rejected_before_dispatch_and_keeps_metrics():
    with pytest.raises(BudgetExceededError) as caught:
        asyncio.run(run_recipe_async(_limited_recipe(max_agent_steps=0), "analyse", FakeClient(), "budget-test"))

    assert caught.value.metrics.failure_class == FailureClass.BUDGET.value
    assert caught.value.metrics.settled
    assert caught.value.metrics.model_calls == 0
    assert caught.value.metrics.runtime_status == "FAILED"


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


@pytest.mark.parametrize("executor_type", (AnalystExecutor, ReviewerExecutor))
def test_executor_passes_structured_output_schema_at_runtime(executor_type):
    schema = {"type": "json_schema", "json_schema": {"name": "stage", "schema": {"type": "object"}}}
    seen = {}

    class CapturingAgent:
        async def run(self, prompt, **kwargs):
            seen.update(kwargs)
            return SimpleNamespace(value={"status": "ready"}, text="")

    class CapturingClient:
        def as_agent(self, **kwargs):
            return CapturingAgent()

    executor = executor_type(
        CapturingClient(),
        participant=ParticipantConfig("participant", "participant", "test"),
        run_context={"require_structured_output": True, "structured_output_schema": schema},
    )

    result = asyncio.run(executor.execute("prompt"))

    assert result == {"status": "ready"}
    assert seen["options"]["response_format"] == schema


def test_tool_result_fallback_retries_without_tools_when_provider_returns_empty_final():
    calls = []

    class Agent:
        async def run(self, prompt, **kwargs):
            calls.append((prompt, kwargs))
            if len(calls) == 1:
                return SimpleNamespace(
                    value=None,
                    text="",
                    messages=[
                        SimpleNamespace(role="tool", contents=[SimpleNamespace(result={"cell": "B2"})]),
                    ],
                )
            return SimpleNamespace(value={"status": "ready"}, text="", messages=[])

    result = asyncio.run(run_agent_with_tool_fallback(Agent(), "inspect workbook", {"response_format": {"type": "json"}}))

    assert result == {"status": "ready"}
    assert calls[0][1]["options"] == {"response_format": {"type": "json"}}
    assert calls[1][1]["tools"] == []
    assert "B2" in calls[1][0]


def test_tool_result_fallback_retries_when_framework_hides_tool_payload():
    calls = []

    class Agent:
        async def run(self, prompt, **kwargs):
            calls.append((prompt, kwargs))
            if len(calls) == 1:
                return SimpleNamespace(value=None, text="", messages=[])
            return SimpleNamespace(value={"status": "ready"}, text="", messages=[])

    result = asyncio.run(
        run_agent_with_tool_fallback(
            Agent(),
            "inspect workbook",
            {"response_format": {"type": "json"}},
            reserve_call=lambda: True,
        )
    )

    assert result == {"status": "ready"}
    assert len(calls) == 2
    assert calls[1][1]["tools"] == []


def test_tool_result_fallback_bounds_reinjected_tool_payload():
    calls = []

    class Agent:
        async def run(self, prompt, **kwargs):
            calls.append((prompt, kwargs))
            if len(calls) == 1:
                return SimpleNamespace(
                    value=None,
                    text="",
                    messages=[
                        SimpleNamespace(
                            role="tool",
                            contents=[SimpleNamespace(result={"payload": "x" * 100_000})],
                        ),
                    ],
                )
            return SimpleNamespace(value={"status": "ready"}, text="", messages=[])

    result = asyncio.run(
        run_agent_with_tool_fallback(
            Agent(),
            "inspect workbook",
            {"response_format": {"type": "json"}},
        )
    )

    assert result == {"status": "ready"}
    assert len(calls[1][0]) < 20_000


def test_toolless_retry_agent_drops_default_tools():
    def retrieve(query: str) -> str:
        return query

    agent = Agent(
        FakeClient(),
        tools=[retrieve],
        default_options={"response_format": {"type": "json"}},
    )
    agent.default_options["tools"] = ["tool"]
    agent.default_options["tool_choice"] = "auto"

    retry_agent = _toolless_retry_agent(agent)

    assert retry_agent is not agent
    assert retry_agent.default_options["tools"] == []
    assert retry_agent.default_options["tool_choice"] == "auto"
    assert retry_agent.default_options["response_format"] == {"type": "json"}


def test_tool_result_fallback_treats_provider_json_parse_errors_as_text():
    class Response:
        text = "{\"status\":\"ready\"}{\"extra\":true}"

        @property
        def value(self):
            raise ValueError("invalid JSON")

        messages = []

    class Agent:
        async def run(self, prompt, **kwargs):
            return Response()

    result = asyncio.run(run_agent_with_tool_fallback(Agent(), "prompt", {"response_format": {"type": "json"}}))

    assert result == Response.text


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

    with pytest.raises(CapabilityUnavailableError, match="capabilities unavailable"):
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


@pytest.mark.parametrize(
    ("tool", "tool_name", "public_parameters"),
    [
        (spreadsheet_read, "spreadsheet_read", {"source", "selection", "limits"}),
        (data_analysis, "data_analysis", {"table", "operation", "limits"}),
    ],
)
def test_instrumented_local_tool_hides_host_only_parameters_from_model_schema(tool, tool_name, public_parameters):
    wrapped = instrument_tool(
        tool,
        CapabilityDefinition(tool_name, "local_deterministic"),
        {},
    )

    parameters = inspect.signature(wrapped).parameters
    assert "cancel_check" not in parameters
    assert "_cache" not in parameters
    assert set(parameters) == public_parameters

    function_tool = FunctionTool(name=tool_name, func=wrapped)
    schema = function_tool.parameters()
    assert set(schema["properties"]) == public_parameters


def test_instrumented_callable_adapters_use_capability_names():
    class Adapter:
        def __call__(self, value: str) -> str:
            return value

    document = instrument_tool(Adapter(), CapabilityDefinition("document_read", "local_deterministic"), {})
    artifact = instrument_tool(Adapter(), CapabilityDefinition("artifact_generation", "local_deterministic"), {})

    assert document.__name__ == "document_read"
    assert artifact.__name__ == "artifact_generation"
    assert document.__name__ != artifact.__name__


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


def test_instrumented_workbook_tools_share_one_scope_context():
    async def scenario():
        workbook_path = Path(__file__).parent / "fixtures" / "analyst_multisheet.xlsx"
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        wrapped = instrument_tool(
            spreadsheet_read,
            CapabilityDefinition("spreadsheet_read", "local_deterministic", execution_mode=ExecutionMode.BLOCKING),
            {"scope": scope},
        )
        first = await wrapped(str(workbook_path))
        second = await wrapped(str(workbook_path))

        assert first.workbook_sha256 == second.workbook_sha256
        assert scope.workbook_context is not None
        assert scope.workbook_context.stats.capture_count == 1
        assert scope.workbook_context.stats.capture_hash_count == 1
        assert scope.workbook_context.stats.xlsx_parse_count == 1
        assert scope.workbook_context.stats.cache_hits == 1

        await scope.close()
        assert scope.workbook_context is None
        assert scope.workbook_cache is None

    asyncio.run(scenario())

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
