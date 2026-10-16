import inspect
import asyncio
import functools
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from agent_framework import FunctionMiddleware


class CapabilityDecision(StrEnum):
    USE_NATIVE = "USE_NATIVE"
    ADAPT_AT_BOUNDARY = "ADAPT_AT_BOUNDARY"
    DEFER = "DEFER"
    UNSUPPORTED = "UNSUPPORTED"


class CapabilityUnavailableError(RuntimeError):
    """Raised when an admitted participant cannot resolve a required capability."""


class CapabilityBindingKind(StrEnum):
    TOOL = "TOOL"
    FACTORY = "FACTORY"
    RESOURCE_FACTORY = "RESOURCE_FACTORY"


class CapabilityOwnership(StrEnum):
    OWNED = "OWNED"
    BORROWED = "BORROWED"


class ScopeOwnership(StrEnum):
    RUN = "RUN"
    BORROWED = "BORROWED"


class ExecutionMode(StrEnum):
    ASYNC = "ASYNC"
    INLINE = "INLINE"
    BLOCKING = "BLOCKING"


@dataclass(frozen=True)
class CapabilityBinding:
    value: Any
    kind: CapabilityBindingKind = CapabilityBindingKind.TOOL
    ownership: CapabilityOwnership = CapabilityOwnership.BORROWED
    share_scope: str = "RUN"
    fingerprint: str = ""


@dataclass(frozen=True)
class CapabilityDefinition:
    id: str
    capability_class: str
    access: str = "read"
    share_scope: str = "RUN"
    max_parallelism: int = 1
    approval_policy: str = "NONE"
    binding_kind: CapabilityBindingKind = CapabilityBindingKind.TOOL
    data_scope: str = "public"
    execution_mode: ExecutionMode = ExecutionMode.ASYNC


@dataclass(frozen=True)
class CapabilityResolution:
    definition: CapabilityDefinition
    decision: CapabilityDecision
    available: bool
    reason: str
    tool: Any = None


@dataclass
class CapabilityScope:
    ownership: ScopeOwnership = ScopeOwnership.BORROWED
    resources: list[Any] = field(default_factory=list)
    cache: dict[tuple[str, str, str], Any] = field(default_factory=dict)
    semaphores: dict[str, asyncio.Semaphore] = field(default_factory=dict)
    executor: ThreadPoolExecutor | None = None
    workbook_context: Any = None
    _closed: bool = field(default=False, init=False, repr=False)

    def ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("capability scope is closed")

    def register(self, resource: Any, ownership: CapabilityOwnership = CapabilityOwnership.OWNED) -> Any:
        self.ensure_open()
        if ownership == CapabilityOwnership.OWNED and all(item is not resource for item in self.resources):
            self.resources.append(resource)
        return resource

    def register_agent(self, agent: Any) -> Any:
        return self.register(agent, CapabilityOwnership.OWNED)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        async def settle() -> list[BaseException]:
            errors: list[BaseException] = []
            if self.executor is not None:
                executor = self.executor
                self.executor = None
                try:
                    await asyncio.to_thread(executor.shutdown, wait=True, cancel_futures=False)
                except BaseException as error:
                    errors.append(error)
            workbook_owner = self.workbook_context
            if workbook_owner is not None:
                clear = getattr(workbook_owner, "clear", None)
                if clear is not None:
                    try:
                        clear()
                    except BaseException as error:
                        errors.append(error)
                self.workbook_context = None
            for resource in reversed(self.resources):
                close = getattr(resource, "close", None)
                if close is None:
                    continue
                try:
                    result = close()
                    if inspect.isawaitable(result):
                        await result
                except BaseException as error:
                    errors.append(error)
            return errors

        cleanup_task = asyncio.create_task(settle())
        interrupted = False
        while not cleanup_task.done():
            try:
                await asyncio.shield(cleanup_task)
            except asyncio.CancelledError:
                interrupted = True
        errors = await cleanup_task
        if errors:
            error = RuntimeError(f"failed to close {len(errors)} capability resource(s)")
            error.errors = errors
            raise error from errors[0]
        if interrupted:
            raise asyncio.CancelledError


class CapabilityResolver:
    def __init__(self, definitions: Mapping[str, CapabilityDefinition] | None = None) -> None:
        self.definitions = dict(definitions or DEFAULT_CAPABILITIES)

    def resolve(self, required_capabilities: tuple[str, ...] | list[str], run_context: Mapping[str, Any] | None = None) -> dict[str, CapabilityResolution]:
        context = dict(run_context or {})
        scope = context.get("scope") or CapabilityScope()
        return {capability_id: self._resolve_one(capability_id, context, scope) for capability_id in required_capabilities}

    def admit(
        self,
        required_capabilities: tuple[str, ...] | list[str],
        run_context: Mapping[str, Any] | None = None,
    ) -> dict[str, CapabilityResolution]:
        """Validate capability definitions and bindings without activating resources."""
        context = dict(run_context or {})
        scope = context.get("scope") or CapabilityScope()
        scope.ensure_open()
        resolutions: dict[str, CapabilityResolution] = {}
        for capability_id in required_capabilities:
            definition = self.definitions.get(capability_id)
            if definition is None:
                resolutions[capability_id] = CapabilityResolution(
                    CapabilityDefinition(capability_id, "unknown"),
                    CapabilityDecision.UNSUPPORTED,
                    False,
                    "capability is not defined",
                )
                continue
            candidate, decision, reason = self._candidate(capability_id, context)
            if definition.capability_class == "unavailable" and candidate is None:
                resolutions[capability_id] = CapabilityResolution(
                    definition,
                    CapabilityDecision.UNSUPPORTED,
                    False,
                    "capability is registered but its adapter is not activated",
                )
                continue
            if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
                resolutions[capability_id] = CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
                continue
            denied = self._authorization_denial(definition, context)
            if denied is not None:
                resolutions[capability_id] = CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, denied)
                continue
            if candidate is None:
                resolutions[capability_id] = CapabilityResolution(definition, decision, False, reason)
                continue
            binding = candidate if isinstance(candidate, CapabilityBinding) else CapabilityBinding(candidate, definition.binding_kind)
            if binding.kind in (CapabilityBindingKind.FACTORY, CapabilityBindingKind.RESOURCE_FACTORY) and not callable(binding.value):
                raise TypeError(f"{binding.kind.value} binding for {capability_id} must be callable")
            resolutions[capability_id] = CapabilityResolution(definition, decision, True, "capability admitted; activation deferred")
        return resolutions

    async def resolve_async(
        self,
        required_capabilities: tuple[str, ...] | list[str],
        run_context: Mapping[str, Any] | None = None,
    ) -> dict[str, CapabilityResolution]:
        context = dict(run_context or {})
        scope = context.get("scope") or CapabilityScope()
        resolved: dict[str, CapabilityResolution] = {}
        for capability_id in required_capabilities:
            resolved[capability_id] = await self._resolve_one_async(capability_id, context, scope)
        return resolved

    def _candidate(self, capability_id: str, context: Mapping[str, Any]) -> tuple[Any, CapabilityDecision, str]:
        local = context.get("local_capabilities", {})
        native = context.get("native_tools", {})
        mcp = context.get("mcp_tools", {})
        adapters = context.get("adapters", {})
        for values, decision, reason in (
            (local, CapabilityDecision.USE_NATIVE, "local deterministic capability"),
            (native, CapabilityDecision.USE_NATIVE, "native/provider capability"),
            (mcp, CapabilityDecision.ADAPT_AT_BOUNDARY, "configured MCP capability"),
            (adapters, CapabilityDecision.ADAPT_AT_BOUNDARY, "configured thin adapter"),
        ):
            if capability_id in values:
                return values[capability_id], decision, reason
        return None, CapabilityDecision.UNSUPPORTED, "capability is unavailable"

    @staticmethod
    def _cache_key(capability_id: str, binding: CapabilityBinding, definition: CapabilityDefinition) -> tuple[str, str, str] | None:
        if not binding.fingerprint:
            return None
        return capability_id, binding.fingerprint, str(binding.share_scope or definition.share_scope)

    def _resolve_one(self, capability_id: str, context: Mapping[str, Any], scope: CapabilityScope) -> CapabilityResolution:
        scope.ensure_open()
        definition = self.definitions.get(capability_id)
        if definition is None:
            return CapabilityResolution(CapabilityDefinition(capability_id, "unknown"), CapabilityDecision.UNSUPPORTED, False, "capability is not defined")
        candidate, decision, reason = self._candidate(capability_id, context)
        if definition.capability_class == "unavailable" and candidate is None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "capability is registered but its adapter is not activated")
        if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
        denied = self._authorization_denial(definition, context)
        if denied is not None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, denied)
        if candidate is None:
            if definition.capability_class == "unavailable":
                reason = "capability is registered but its adapter is not activated"
            return CapabilityResolution(definition, decision, False, reason)
        binding = candidate if isinstance(candidate, CapabilityBinding) else CapabilityBinding(candidate, definition.binding_kind)
        cache_key = self._cache_key(capability_id, binding, definition)
        if cache_key is not None and binding.share_scope == "RUN" and cache_key in scope.cache:
            return CapabilityResolution(definition, CapabilityDecision.USE_NATIVE, True, "reused run-scoped capability", scope.cache[cache_key])
        value = binding.value
        if binding.kind in (CapabilityBindingKind.FACTORY, CapabilityBindingKind.RESOURCE_FACTORY):
            if not callable(value):
                raise TypeError(f"{binding.kind.value} binding for {capability_id} must be callable")
            value = value(dict(context))
        if inspect.isawaitable(value):
            raise RuntimeError(f"{binding.kind.value} binding for {capability_id} requires resolve_async()")
        if binding.kind == CapabilityBindingKind.RESOURCE_FACTORY and value is None:
            return CapabilityResolution(definition, decision, False, "resource factory returned no resource")
        if cache_key is not None and binding.share_scope == "RUN":
            scope.cache[cache_key] = value
        scope.register(value, binding.ownership)
        return CapabilityResolution(definition, decision, True, reason, value)

    async def _resolve_one_async(self, capability_id: str, context: Mapping[str, Any], scope: CapabilityScope) -> CapabilityResolution:
        scope.ensure_open()
        definition = self.definitions.get(capability_id)
        if definition is None:
            return CapabilityResolution(CapabilityDefinition(capability_id, "unknown"), CapabilityDecision.UNSUPPORTED, False, "capability is not defined")
        candidate, decision, reason = self._candidate(capability_id, context)
        if definition.capability_class == "unavailable" and candidate is None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "capability is registered but its adapter is not activated")
        if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
        denied = self._authorization_denial(definition, context)
        if denied is not None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, denied)
        if candidate is None:
            if definition.capability_class == "unavailable":
                reason = "capability is registered but its adapter is not activated"
            return CapabilityResolution(definition, decision, False, reason)
        binding = candidate if isinstance(candidate, CapabilityBinding) else CapabilityBinding(candidate, definition.binding_kind)
        cache_key = self._cache_key(capability_id, binding, definition)
        if cache_key is not None and binding.share_scope == "RUN" and cache_key in scope.cache:
            return CapabilityResolution(definition, CapabilityDecision.USE_NATIVE, True, "reused run-scoped capability", scope.cache[cache_key])
        value = binding.value
        if binding.kind in (CapabilityBindingKind.FACTORY, CapabilityBindingKind.RESOURCE_FACTORY):
            if not callable(value):
                raise TypeError(f"{binding.kind.value} binding for {capability_id} must be callable")
            value = value(dict(context))
            if inspect.isawaitable(value):
                value = await value
        if inspect.isawaitable(value):
            raise RuntimeError(f"{binding.kind.value} binding for {capability_id} returned an unresolved awaitable")
        if binding.kind == CapabilityBindingKind.RESOURCE_FACTORY and value is None:
            return CapabilityResolution(definition, decision, False, "resource factory returned no resource")
        if cache_key is not None and binding.share_scope == "RUN":
            scope.cache[cache_key] = value
        scope.register(value, binding.ownership)
        return CapabilityResolution(definition, decision, True, reason, value)

    @staticmethod
    def _authorization_denial(definition: CapabilityDefinition, context: Mapping[str, Any]) -> str | None:
        requested = {str(value) for value in context.get("participant_data_scope", ())}
        if definition.data_scope == "internal" and "internal" not in requested:
            return "participant data scope does not authorize internal capability"
        if definition.access == "write" and not context.get("human_approved", False):
            return "write capability requires human approval"
        return None


def prepare_capability_context(
    required_capabilities: tuple[str, ...] | list[str],
    run_context: Mapping[str, Any] | None = None,
    *,
    scope: CapabilityScope | None = None,
    human_approved: bool | None = None,
    load_local: bool = True,
    load_hosted: bool = True,
    bind_adapters: bool = True,
    activate: bool = True,
) -> dict[str, Any]:
    """Build and validate the capability context shared by admission and runtime."""
    context = dict(run_context or {})
    required = tuple(dict.fromkeys(str(item) for item in required_capabilities if str(item)))
    context["required_capabilities"] = required
    if scope is not None:
        context["scope"] = scope
    else:
        context.setdefault("scope", CapabilityScope())
    context["scope"].ensure_open()
    if human_approved is not None:
        context["human_approved"] = human_approved
    context.setdefault("capability_resolver", CapabilityResolver())

    if load_local:
        from foresight_os.runtime.local_toolbelt import bind_local_toolbelt

        local_bindings = context.setdefault("local_capabilities", {})
        for name, binding in bind_local_toolbelt().items():
            local_bindings.setdefault(name, binding)
        if context.get("local_workspace") is not None:
            from foresight_os.runtime.local_adapters import bind_local_adapters

            local_adapters = bind_local_adapters(
                context["local_workspace"],
                document_roots=context.get("document_roots"),
            )
            adapters = context.setdefault("adapters", {})
            for name, binding in local_adapters.items():
                adapters.setdefault(name, binding)

    if context.get("mcp_bindings") is not None:
        context.setdefault("mcp_tools", {}).update(
            {
                key: value
                for key, value in context["mcp_bindings"].items()
                if not required or key in required
            }
        )
    elif load_hosted and required:
        from foresight_os.runtime.external_signals import load_hosted_mcp_bindings

        for capability_id, binding in load_hosted_mcp_bindings(
            context.get("mcp_environment"),
            required_capabilities=required,
        ).items():
            context.setdefault("mcp_tools", {}).setdefault(capability_id, binding)

    if bind_adapters:
        if context.get("web_search_provider") is not None:
            from foresight_os.runtime.web_search import bind_web_search

            context.setdefault("adapters", {}).setdefault(
                "web_search", bind_web_search(context["web_search_provider"])
            )
        if context.get("page_retrieval") is not None:
            from foresight_os.runtime.page_retrieval import bind_page_retrieval

            context.setdefault("adapters", {}).setdefault(
                "page_retrieval", bind_page_retrieval(context["page_retrieval"])
            )
        elif context.get("page_retrieval_fixture_hosts") is not None:
            from foresight_os.runtime.page_retrieval import PageRetrievalCapability, bind_page_retrieval

            context.setdefault("adapters", {}).setdefault(
                "page_retrieval",
                bind_page_retrieval(PageRetrievalCapability(fixture_hosts=set(context["page_retrieval_fixture_hosts"]))),
            )
        if context.get("crawl4ai") is not None:
            from foresight_os.runtime.crawl4ai import bind_crawl4ai

            context.setdefault("adapters", {}).setdefault(
                "web_crawl", bind_crawl4ai(context["crawl4ai"])
            )

    admitted = context["capability_resolver"].admit(required, context)
    unavailable = [f"{key}: {item.reason}" for key, item in admitted.items() if not item.available]
    if unavailable:
        raise CapabilityUnavailableError(f"capabilities unavailable: {'; '.join(unavailable)}")
    if not activate:
        context["capability_resolutions"] = admitted
        return context
    resolved = context["capability_resolver"].resolve(required, context)
    context["capability_resolutions"] = resolved
    unavailable = [f"{key}: {item.reason}" for key, item in resolved.items() if not item.available]
    if unavailable:
        raise CapabilityUnavailableError(f"capabilities unavailable: {'; '.join(unavailable)}")
    return context


def admit_capability_context(
    required_capabilities: tuple[str, ...] | list[str],
    run_context: Mapping[str, Any] | None = None,
    *,
    scope: CapabilityScope | None = None,
    human_approved: bool | None = None,
    load_local: bool = True,
    load_hosted: bool = True,
    bind_adapters: bool = True,
) -> dict[str, Any]:
    """Validate capability metadata without activating factories or resources."""
    return prepare_capability_context(
        required_capabilities,
        run_context,
        scope=scope,
        human_approved=human_approved,
        load_local=load_local,
        load_hosted=load_hosted,
        bind_adapters=bind_adapters,
        activate=False,
    )


def _instrumented_dispatch(dispatch: Any, definition: CapabilityDefinition, context: Mapping[str, Any], adapter_parameters: frozenset[str] | None = None):
    scope = context.get("scope")
    semaphores = getattr(scope, "semaphores", None) if scope is not None else None
    if semaphores is None:
        semaphores = context.setdefault("_capability_semaphores", {})  # type: ignore[attr-defined]
    semaphore = semaphores.setdefault(definition.id, asyncio.Semaphore(max(1, definition.max_parallelism)))
    mode = definition.execution_mode
    parameters = adapter_parameters

    def blocking_call(args: tuple[Any, ...], kwargs: dict[str, Any], cancel_event: threading.Event | None) -> Any:
        effective_kwargs = dict(kwargs)
        if definition.id in {"spreadsheet_read", "data_analysis", "calculation"} and scope is not None:
            from foresight_os.runtime.local_toolbelt import WorkbookContext

            if getattr(scope, "workbook_context", None) is None:
                scope.workbook_context = WorkbookContext()
            workbook_context = scope.workbook_context
            if "_cache" in parameters:
                effective_kwargs.setdefault("_cache", workbook_context.cache)
            if "_workbook_context" in parameters:
                effective_kwargs.setdefault("_workbook_context", workbook_context)
            if "_authority_index" in parameters:
                effective_kwargs.setdefault("_authority_index", workbook_context.authority_index)
            if "_stats" in parameters:
                effective_kwargs.setdefault("_stats", workbook_context.stats)
        if cancel_event is not None:
            accepts_cancel = "cancel_check" in parameters if parameters is not None else False
            if accepts_cancel:
                effective_kwargs.setdefault("cancel_check", cancel_event.is_set)
        result = dispatch(*args, **effective_kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result

    async def invoke(*args: Any, **kwargs: Any) -> Any:
        from foresight_os.runtime.metrics import BudgetExceededError, FailureClass

        budget = context.get("budget")
        metrics = context.get("metrics")
        started = time.perf_counter()
        queue_started = time.perf_counter()
        cancel_event = threading.Event() if mode == ExecutionMode.BLOCKING else None
        try:
            if budget is not None and not budget.reserve(tool_calls=1):
                raise BudgetExceededError(f"maximum tool calls exceeded before dispatch: {definition.id}")
            async with semaphore:
                if metrics is not None:
                    metrics.queue_wait_ms += round((time.perf_counter() - queue_started) * 1000)
                if metrics is not None:
                    metrics.record_tool_call(str(context.get("tool_call_kind", "local")))
                if mode == ExecutionMode.BLOCKING:
                    if scope is not None and getattr(scope, "executor", None) is None:
                        scope.executor = ThreadPoolExecutor(max_workers=max(1, definition.max_parallelism))
                    executor = getattr(scope, "executor", None)
                    if executor is None:
                        raise RuntimeError("blocking capability scope has no executor")
                    loop = asyncio.get_running_loop()
                    future = loop.run_in_executor(executor, blocking_call, args, dict(kwargs), cancel_event)
                    try:
                        result = await asyncio.shield(future)
                    except asyncio.CancelledError as cancellation:
                        if cancel_event is not None:
                            cancel_event.set()
                        if metrics is not None:
                            metrics.cancellation_settlements += 1
                        worker_error: BaseException | None = None
                        while not future.done():
                            try:
                                await asyncio.shield(future)
                            except asyncio.CancelledError:
                                continue
                            except BaseException as error:
                                worker_error = error
                                break
                        if worker_error is None:
                            try:
                                future.result()
                            except BaseException as error:
                                worker_error = error
                        if worker_error is not None:
                            if metrics is not None:
                                metrics.record_failure(FailureClass.TOOL, worker_error)
                        raise cancellation
                    workbook_context = getattr(scope, "workbook_context", None) if scope is not None else None
                    if workbook_context is not None:
                        workbook_context._enforce_budget()
                else:
                    effective_kwargs = dict(kwargs)
                    if definition.id in {"spreadsheet_read", "data_analysis", "calculation"} and scope is not None:
                        from foresight_os.runtime.local_toolbelt import WorkbookContext

                        if getattr(scope, "workbook_context", None) is None:
                            scope.workbook_context = WorkbookContext()
                        workbook_context = scope.workbook_context
                        effective_parameters = parameters or frozenset()
                        if "_cache" in effective_parameters:
                            effective_kwargs.setdefault("_cache", workbook_context.cache)
                        if "_workbook_context" in effective_parameters:
                            effective_kwargs.setdefault("_workbook_context", workbook_context)
                        if "_authority_index" in effective_parameters:
                            effective_kwargs.setdefault("_authority_index", workbook_context.authority_index)
                        if "_stats" in effective_parameters:
                            effective_kwargs.setdefault("_stats", workbook_context.stats)
                    result = dispatch(*args, **effective_kwargs)
                    if inspect.isawaitable(result):
                        result = await result
                    workbook_context = getattr(scope, "workbook_context", None) if scope is not None else None
                    if workbook_context is not None:
                        workbook_context._enforce_budget()
                return result
        except BudgetExceededError as error:
            if metrics is not None:
                metrics.record_failure(FailureClass.BUDGET, error)
            raise
        except asyncio.CancelledError as error:
            if metrics is not None:
                metrics.record_failure(FailureClass.CANCELLATION, error)
            raise
        except BaseException as error:
            if metrics is not None:
                metrics.record_failure(FailureClass.TOOL, error)
            raise
        finally:
            if metrics is not None:
                elapsed_ms = round((time.perf_counter() - started) * 1000)
                metrics.tool_latency_ms += elapsed_ms
                metrics.execution_time_ms += elapsed_ms

    return invoke


class ForesightFunctionMiddleware(FunctionMiddleware):
    """Public Agent Framework middleware for native MCP function calls."""

    def __init__(self, definitions: Mapping[str, CapabilityDefinition], context: Mapping[str, Any]) -> None:
        self.definitions = dict(definitions)
        self.context = context

    async def process(self, invocation_context: Any, call_next: Any) -> None:
        from foresight_os.runtime.metrics import BudgetExceededError, FailureClass

        name = getattr(invocation_context.function, "name", "")
        definition = self.definitions.get(name)
        if definition is None:
            await call_next()
            return
        budget = self.context.get("budget")
        metrics = self.context.get("metrics")
        scope = self.context.get("scope")
        semaphores = getattr(scope, "semaphores", None) if scope is not None else None
        if semaphores is None:
            semaphores = self.context.setdefault("_capability_semaphores", {})
        semaphore = semaphores.setdefault(definition.id, asyncio.Semaphore(max(1, definition.max_parallelism)))
        started = time.perf_counter()
        try:
            if budget is not None and not budget.reserve(tool_calls=1):
                raise BudgetExceededError(f"maximum tool calls exceeded before dispatch: {definition.id}")
            async with semaphore:
                if metrics is not None:
                    metrics.record_tool_call(str(self.context.get("tool_call_kind", "mcp")))
                await call_next()
        except BudgetExceededError as error:
            if metrics is not None:
                metrics.record_failure(FailureClass.BUDGET, error)
            raise
        except BaseException as error:
            if metrics is not None:
                metrics.record_failure(FailureClass.TOOL, error)
            raise
        finally:
            if metrics is not None:
                elapsed_ms = round((time.perf_counter() - started) * 1000)
                metrics.tool_latency_ms += elapsed_ms
                metrics.execution_time_ms += elapsed_ms


class _InstrumentedMCPTool:
    def __init__(self, tool: Any, call_tool: Any):
        self._tool = tool
        self._call_tool = call_tool
        self.__foresight_instrumented__ = True
        self.capability_id = ""

    async def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        return await self._call_tool(tool_name, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tool, name)


def instrument_tool(tool: Any, definition: CapabilityDefinition, context: Mapping[str, Any]) -> Any:
    mcp_call = getattr(tool, "call_tool", None)
    if callable(mcp_call) and not callable(tool):
        try:
            adapter_parameters = frozenset(inspect.signature(mcp_call).parameters)
        except (TypeError, ValueError):
            adapter_parameters = frozenset()
        dispatch = _instrumented_dispatch(mcp_call, definition, context, adapter_parameters)
        wrapped = _InstrumentedMCPTool(tool, dispatch)
        wrapped.capability_id = definition.id
        return wrapped
    if not callable(tool):
        return tool

    original = getattr(tool, "__foresight_original_callable__", None) or tool
    try:
        signature = inspect.signature(original)
        adapter_parameters = frozenset(signature.parameters)
    except (TypeError, ValueError):
        signature = None
        adapter_parameters = frozenset()
    dispatch = _instrumented_dispatch(original, definition, context, adapter_parameters)

    @functools.wraps(tool)
    async def invoke(*args: Any, **kwargs: Any) -> Any:
        return await dispatch(*args, **kwargs)

    if not getattr(tool, "__name__", None):
        invoke.__name__ = definition.id
        invoke.__qualname__ = definition.id
    public_signature = inspect.signature(tool)
    invoke.__signature__ = public_signature.replace(
        parameters=[
            parameter
            for parameter in public_signature.parameters.values()
            if parameter.name not in {"cancel_check", "_cache", "_snapshot", "_workbook_context", "_authority_index", "_stats"}
        ]
    )
    setattr(invoke, "__foresight_instrumented__", True)
    setattr(invoke, "__foresight_original_callable__", original)
    setattr(invoke, "capability_id", definition.id)
    return invoke


DEFAULT_CAPABILITIES = {
    "web_search": CapabilityDefinition("web_search", "external_read", "read", "RUN", 3, data_scope="public"),
    "page_retrieval": CapabilityDefinition("page_retrieval", "external_read", "read", "RUN", 2, data_scope="public"),
    "web_crawl": CapabilityDefinition("web_crawl", "external_read", "read", "RUN", 1, data_scope="public"),
    "technology_signals": CapabilityDefinition("technology_signals", "external_read", "read", "RUN", 1, data_scope="public"),
    "market_signals": CapabilityDefinition("market_signals", "external_read", "read", "RUN", 1, data_scope="public"),
    "macro_signals": CapabilityDefinition("macro_signals", "external_read", "read", "RUN", 1, data_scope="public"),
    "spreadsheet_read": CapabilityDefinition("spreadsheet_read", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.BLOCKING),
    "data_analysis": CapabilityDefinition("data_analysis", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.BLOCKING),
    "calculation": CapabilityDefinition("calculation", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.INLINE),
    "graph_context": CapabilityDefinition("graph_context", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.BLOCKING),
    "domain_validation": CapabilityDefinition("domain_validation", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.INLINE),
    "powerbi_project_read": CapabilityDefinition("powerbi_project_read", "local_deterministic", "read", "RUN", 1, data_scope="local", execution_mode=ExecutionMode.BLOCKING),
    "document_read": CapabilityDefinition("document_read", "unavailable", "read", "RUN", 1, data_scope="local"),
    "internal_knowledge": CapabilityDefinition("internal_knowledge", "unavailable", "read", "RUN", 1, data_scope="internal"),
    "artifact_generation": CapabilityDefinition("artifact_generation", "unavailable", "write", "RUN", 1, "HUMAN", data_scope="local"),
    "external_mutation": CapabilityDefinition("external_mutation", "external_mutation", "write", "RUN", 1, "HUMAN"),
}


def register_artifact_generation_adapter(
    run_context: dict[str, Any],
    adapter: Any,
    *,
    fingerprint: str = "",
) -> dict[str, Any]:
    """Register a caller-owned artifact adapter without activating one by default."""
    run_context.setdefault("adapters", {})["artifact_generation"] = CapabilityBinding(
        adapter,
        kind=CapabilityBindingKind.TOOL,
        fingerprint=fingerprint,
    )
    return run_context


@dataclass(frozen=True)
class CapabilityResult:
    name: str
    decision: CapabilityDecision
    available: bool
    detail: str


@dataclass(frozen=True)
class PatternCapability:
    pattern: str
    supported: bool
    available: bool
    reason: str


@dataclass(frozen=True)
class VerticalSliceGuardrail:
    max_agent_steps: int = 5
    max_correction_rounds: int = 1
    max_total_agent_calls: int = 3
    exhaustion_outcome: str = "no accepted recommendation; human decision/review boundary"


REQUIRED_CAPABILITIES = (
    "single_agent",
    "sequential_review",
    "human_input",
    "structured_output",
    "checkpoint_restart",
)

DEFERRED_CAPABILITIES = ("magentic",)

PATTERN_CAPABILITIES = {
    "direct": PatternCapability("direct", True, True, "bounded direct execution"),
    "sequential": PatternCapability("sequential", True, True, "native sequential workflow"),
    "concurrent": PatternCapability("concurrent", True, True, "native concurrent workflow"),
    "handoff": PatternCapability("handoff", True, True, "native handoff workflow"),
    "group_chat": PatternCapability("group_chat", True, True, "native group chat workflow"),
}
