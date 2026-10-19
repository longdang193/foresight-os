from dataclasses import dataclass
import asyncio
import inspect
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Mapping

from agent_framework import Agent, ChatMiddleware
from agent_framework._tools import FunctionInvocationLayer

from foresight_os.analysis.result_committer import decode_stage_output
from foresight_os.domain.analysis_inputs import GLOBAL_SCOPE
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.runtime.metrics import BudgetExceededError

_MAX_REINJECTED_TOOL_RESULT_CHARS = 12_000


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
            result = None
            for field in ("result", "output", "stdout"):
                candidate = getattr(content, field, None)
                if candidate not in (None, ""):
                    result = candidate
                    break
            if result is None:
                continue
            if hasattr(result, "to_dict"):
                result = result.to_dict()
            if isinstance(result, str):
                results.append(result)
            else:
                results.append(json.dumps(result, default=str, ensure_ascii=False))
    return results


def _bounded_tool_results(results: list[str]) -> str:
    payload = json.dumps(results, ensure_ascii=False)
    if len(payload) <= _MAX_REINJECTED_TOOL_RESULT_CHARS:
        return payload
    return payload[:_MAX_REINJECTED_TOOL_RESULT_CHARS] + '...[tool results truncated; use the existing tool conversation]'


def _toolless_retry_agent(agent: Any) -> Any:
    client = getattr(agent, "client", None)
    if client is None:
        return agent
    default_options = getattr(agent, "default_options", None)
    if isinstance(default_options, Mapping):
        default_options = dict(default_options)
        default_options.pop("tools", None)
        default_options.pop("tool_choice", None)
    return Agent(
        client,
        instructions=getattr(agent, "instructions", None),
        id=getattr(agent, "id", None),
        name=getattr(agent, "name", None),
        description=getattr(agent, "description", None),
        default_options=default_options,
        context_providers=getattr(agent, "context_providers", None),
        middleware=getattr(agent, "middleware", None),
        require_per_service_call_history_persistence=getattr(
            agent,
            "require_per_service_call_history_persistence",
            False,
        ),
    )


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
    value = decode_stage_output(response)
    if value is not None:
        return value
    results = _tool_results(response)
    if not results and "response_format" not in run_options:
        return ""
    retry_prompt = (
        f"{prompt}\n\n"
        "The local analysis tools completed, but the provider did not return a final structured message. "
        "Return the required result now as one JSON object only. "
        "Use the following tool results when present; otherwise use the completed tool conversation already in context:\n"
        f"{_bounded_tool_results(results)}"
    )
    reserve_fallback_call()
    retry_agent = _toolless_retry_agent(agent)
    retry = await retry_agent.run(retry_prompt, tools=[], options=run_options) if run_options else await retry_agent.run(retry_prompt, tools=[])
    return decode_stage_output(retry) or ""


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
class DeterministicLocalExecutor:
    """Run a declared workbook analysis without constructing an agent."""

    stage: Any
    stage_input: Any
    run_context: Mapping[str, Any]

    async def execute(self) -> Any:
        callback = self.run_context.get("deterministic_local_dispatch")
        if callback is not None:
            result = callback(self.stage, self.stage_input, self.run_context)
            return await result if inspect.isawaitable(result) else result

        domains = tuple(str(item) for item in getattr(self.stage, "analysis_domains", ()))
        analyzers = self.run_context.get("workbook_analyzers") or _default_workbook_analyzers()
        source = self.run_context.get("workbook_source")
        contracts = self.run_context.get("analysis_contracts", {})
        if len(domains) != 1 or source is None or not isinstance(analyzers, Mapping):
            raise ValueError("deterministic-local stage requires one workbook domain, source, and analyzer")
        domain = domains[0]
        analyzer = analyzers.get(domain)
        contract = None
        if isinstance(contracts, Mapping):
            stage_id = str(getattr(self.stage, "stage_id", "stage"))
            contract = contracts.get(f"{stage_id}:{domain}") or contracts.get(f"{GLOBAL_SCOPE}:{domain}") or contracts.get(domain)
        if contract is None:
            resolver = self.run_context.get("analysis_contract_resolver")
            if resolver is not None:
                contract = resolver(domain, str(getattr(self.stage, "stage_id", "stage"))).to_dict()
        if analyzer is None or contract is None:
            raise ValueError(f"deterministic-local stage is not bound to workbook domain: {domain}")
        from foresight_os.analysis.workbook_engine import WorkbookAnalysisEngine

        scope = self.run_context.get("scope")
        workbook_context = self.run_context.get("workbook_context")
        if workbook_context is None and scope is not None:
            workbook_context = getattr(scope, "workbook_context", None)
        if workbook_context is None and scope is not None:
            from foresight_os.runtime.local_toolbelt import WorkbookContext

            workbook_context = WorkbookContext()
            scope.workbook_context = workbook_context
        snapshot = self.run_context.get("workbook_snapshot")
        if snapshot is not None:
            if workbook_context is None:
                from foresight_os.runtime.local_toolbelt import WorkbookContext

                workbook_context = WorkbookContext()
            workbook_context.adopt_snapshot(snapshot)
        engine = self.run_context.get("workbook_engine") or WorkbookAnalysisEngine(context=workbook_context)
        cancel_event = threading.Event()
        original_cancel_check = self.run_context.get("cancel_check")

        def cancelled() -> bool:
            return cancel_event.is_set() or bool(original_cancel_check and original_cancel_check())

        def run_blocking() -> Any:
            return engine.run(source, contract, analyzer, cancel_check=cancelled, materialize_scope=False)

        if scope is not None and getattr(scope, "executor", None) is None:
            scope.executor = ThreadPoolExecutor(max_workers=1)
        executor = getattr(scope, "executor", None) if scope is not None else None
        if executor is None:
            executor = ThreadPoolExecutor(max_workers=1)
            owns_executor = True
        else:
            owns_executor = False
        future = asyncio.get_running_loop().run_in_executor(executor, run_blocking)
        try:
            result = await asyncio.shield(future)
        except asyncio.CancelledError:
            cancel_event.set()
            while not future.done():
                try:
                    await asyncio.shield(future)
                except asyncio.CancelledError:
                    continue
            if owns_executor:
                executor.shutdown(wait=True, cancel_futures=False)
            raise
        finally:
            if owns_executor:
                executor.shutdown(wait=True, cancel_futures=False)
        if result.status != "completed" or result.domain_result is None:
            if result.status == "cancelled":
                from foresight_os.runtime.metrics import RunCanceledError

                raise RunCanceledError(result.failure or "deterministic workbook analysis cancelled")
            if result.status == "blocked_input":
                raise ValueError(f"BLOCKED_INPUT: {result.failure or 'deterministic workbook input is invalid'}")
            raise RuntimeError(result.failure or f"deterministic workbook analysis {result.status}")
        return result.domain_result.result


def _default_workbook_analyzers() -> Mapping[str, Callable[..., Any]]:
    from foresight_os.analysis.workbook_registry import workbook_analyzer_map

    return workbook_analyzer_map()


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
