from dataclasses import dataclass
import inspect
import json
from typing import Any, Callable, Mapping

from agent_framework import ChatMiddleware
from agent_framework._tools import FunctionInvocationLayer

from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.runtime.metrics import BudgetExceededError


async def _close_agent(agent: object) -> None:
    close = getattr(agent, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


def _run_options(participant: ParticipantConfig, run_context: Mapping[str, Any] | None) -> dict[str, Any]:
    context = run_context or {}
    response_format = participant.structured_output if isinstance(participant.structured_output, dict) else None
    if response_format is None and context.get("require_structured_output"):
        response_format = context.get("structured_output_schema")
    return {"response_format": response_format} if response_format is not None else {}


def _response_value(response: Any) -> Any:
    try:
        value = getattr(response, "value", None)
    except (TypeError, ValueError, json.JSONDecodeError):
        value = None
    if value is not None:
        return value
    try:
        text = getattr(response, "text", "") or ""
    except (TypeError, ValueError, json.JSONDecodeError):
        text = ""
    return text if text.strip() else None


def _tool_results(response: Any) -> list[str]:
    results: list[str] = []
    for message in getattr(response, "messages", ()) or ():
        if getattr(message, "role", None) != "tool":
            continue
        for content in getattr(message, "contents", ()) or ():
            result = getattr(content, "result", None)
            if result is None:
                continue
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            if isinstance(result, str):
                results.append(result)
            else:
                results.append(json.dumps(result, default=str, ensure_ascii=False))
    return results


def _reserve_agent_call(reserve_call: Callable[[], bool] | None) -> None:
    if reserve_call is not None and not reserve_call():
        from foresight_os.runtime.metrics import BudgetExceededError

        raise BudgetExceededError("maximum agent calls exceeded before dispatch")


class _ReservedChatClient:
    _foresight_reserved = True

    def __init__(
        self,
        client: Any,
        reserve_call: Callable[[], bool] | None,
        on_call: Callable[[], None] | None,
    ) -> None:
        self._client = client
        self._reserve_call = reserve_call
        self._on_call = on_call

    def get_response(self, *args: Any, **kwargs: Any) -> Any:
        if self._reserve_call is not None and not self._reserve_call():
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        if self._on_call is not None:
            self._on_call()
        return self._client.get_response(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _ReservedProviderCallMiddleware(ChatMiddleware):
    _foresight_provider_budget = True

    def __init__(self, reserve_call: Callable[[], bool] | None, on_call: Callable[[], None] | None) -> None:
        self._reserve_call = reserve_call
        self._on_call = on_call

    async def process(self, context: Any, call_next: Callable[[], Any]) -> None:
        if self._reserve_call is not None and not self._reserve_call():
            raise BudgetExceededError("maximum agent calls exceeded before dispatch")
        if self._on_call is not None:
            self._on_call()
        await call_next()


def _supports_function_invocation(client: Any) -> bool:
    return isinstance(client, FunctionInvocationLayer)


def _install_provider_budget_middleware(
    agent: Any,
    reserve_call: Callable[[], bool] | None,
    on_call: Callable[[], None] | None,
) -> bool:
    client = getattr(agent, "client", None)
    if not _supports_function_invocation(client):
        return False
    middleware = list(getattr(agent, "middleware", ()) or ())
    if not any(getattr(item, "_foresight_provider_budget", False) for item in middleware):
        middleware.append(_ReservedProviderCallMiddleware(reserve_call, on_call))
        agent.middleware = middleware
        if hasattr(agent, "_cached_agent_middleware_pipeline"):
            agent._cached_agent_middleware_pipeline = None
    return True


async def run_agent_with_tool_fallback(
    agent: Any,
    prompt: str,
    options: Mapping[str, Any] | None = None,
    *,
    reserve_call: Callable[[], bool] | None = None,
    on_call: Callable[[], None] | None = None,
) -> Any:
    run_options = dict(options or {})
    client = getattr(agent, "client", None)
    provider_boundary = _install_provider_budget_middleware(agent, reserve_call, on_call)
    if not provider_boundary and client is not None and hasattr(client, "get_response") and not getattr(client, "_foresight_reserved", False):
        agent.client = _ReservedChatClient(client, reserve_call, on_call)
        provider_boundary = True
    elif getattr(client, "_foresight_reserved", False):
        provider_boundary = True

    def reserve_fallback_call() -> None:
        if provider_boundary:
            return
        _reserve_agent_call(reserve_call)
        if on_call is not None:
            on_call()

    reserve_fallback_call()
    response = await agent.run(prompt, options=run_options) if run_options else await agent.run(prompt)
    value = _response_value(response)
    if value is not None:
        return value
    results = _tool_results(response)
    if not results:
        return ""
    retry_prompt = (
        f"{prompt}\n\n"
        "The local analysis tools completed, but the provider did not return a final message. "
        "Use the following tool results as the only source material and return the required result now:\n"
        f"{json.dumps(results, ensure_ascii=False)}"
    )
    reserve_fallback_call()
    retry = await agent.run(retry_prompt, tools=[], options=run_options) if run_options else await agent.run(retry_prompt, tools=[])
    return _response_value(retry) or ""


@dataclass
class AnalystExecutor:
    client: Any | None = None
    factory: AgentFactory | None = None
    participant: ParticipantConfig | None = None
    run_context: Mapping[str, Any] | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "analyst", "status": "completed", "prompt": prompt}
        factory = self.factory or AgentFactory(self.client)
        participant = self.participant or ParticipantConfig("analyst", "analyst", "structured analytical proposal")
        agent = factory.create(participant, self.run_context or {})
        options = _run_options(participant, self.run_context)
        return await run_agent_with_tool_fallback(
            agent,
            prompt,
            options,
            reserve_call=(self.run_context or {}).get("reserve_agent_call"),
            on_call=(self.run_context or {}).get("record_agent_call"),
        )


@dataclass
class ReviewerExecutor:
    client: Any | None = None
    factory: AgentFactory | None = None
    participant: ParticipantConfig | None = None
    run_context: Mapping[str, Any] | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "reviewer", "status": "completed", "prompt": prompt}
        factory = self.factory or AgentFactory(self.client)
        participant = self.participant or ParticipantConfig("reviewer", "reviewer", "structured review of the proposal")
        agent = factory.create(participant, self.run_context or {})
        options = _run_options(participant, self.run_context)
        return await run_agent_with_tool_fallback(
            agent,
            prompt,
            options,
            reserve_call=(self.run_context or {}).get("reserve_agent_call"),
            on_call=(self.run_context or {}).get("record_agent_call"),
        )
