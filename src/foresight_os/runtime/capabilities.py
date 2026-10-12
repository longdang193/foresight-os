import inspect
import asyncio
import functools
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class CapabilityDecision(StrEnum):
    USE_NATIVE = "USE_NATIVE"
    ADAPT_AT_BOUNDARY = "ADAPT_AT_BOUNDARY"
    DEFER = "DEFER"
    UNSUPPORTED = "UNSUPPORTED"


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
    _closed: bool = field(default=False, init=False, repr=False)

    def register(self, resource: Any, ownership: CapabilityOwnership = CapabilityOwnership.OWNED) -> Any:
        if ownership == CapabilityOwnership.OWNED and all(item is not resource for item in self.resources):
            self.resources.append(resource)
        return resource

    def register_agent(self, agent: Any) -> Any:
        return self.register(agent, CapabilityOwnership.OWNED)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        errors: list[BaseException] = []
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
        if errors:
            error = RuntimeError(f"failed to close {len(errors)} capability resource(s)")
            error.errors = errors
            raise error from errors[0]


class CapabilityResolver:
    def __init__(self, definitions: Mapping[str, CapabilityDefinition] | None = None) -> None:
        self.definitions = dict(definitions or DEFAULT_CAPABILITIES)

    def resolve(self, required_capabilities: tuple[str, ...] | list[str], run_context: Mapping[str, Any] | None = None) -> dict[str, CapabilityResolution]:
        context = dict(run_context or {})
        scope = context.get("scope") or CapabilityScope()
        return {capability_id: self._resolve_one(capability_id, context, scope) for capability_id in required_capabilities}

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
        definition = self.definitions.get(capability_id)
        if definition is None:
            return CapabilityResolution(CapabilityDefinition(capability_id, "unknown"), CapabilityDecision.UNSUPPORTED, False, "capability is not defined")
        if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
        denied = self._authorization_denial(definition, context)
        if denied is not None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, denied)
        candidate, decision, reason = self._candidate(capability_id, context)
        if candidate is None:
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
        definition = self.definitions.get(capability_id)
        if definition is None:
            return CapabilityResolution(CapabilityDefinition(capability_id, "unknown"), CapabilityDecision.UNSUPPORTED, False, "capability is not defined")
        if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
        denied = self._authorization_denial(definition, context)
        if denied is not None:
            return CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, denied)
        candidate, decision, reason = self._candidate(capability_id, context)
        if candidate is None:
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


def instrument_tool(tool: Any, definition: CapabilityDefinition, context: Mapping[str, Any]) -> Any:
    if not callable(tool) or getattr(tool, "__foresight_instrumented__", False):
        return tool
    semaphores = context.setdefault("_capability_semaphores", {})  # type: ignore[attr-defined]
    semaphore = semaphores.setdefault(definition.id, asyncio.Semaphore(max(1, definition.max_parallelism)))

    @functools.wraps(tool)
    async def invoke(*args: Any, **kwargs: Any) -> Any:
        from foresight_os.runtime.metrics import BudgetExceededError, FailureClass

        budget = context.get("budget")
        metrics = context.get("metrics")
        started = time.perf_counter()
        try:
            if budget is not None and not budget.reserve(tool_calls=1):
                raise BudgetExceededError(f"maximum tool calls exceeded before dispatch: {definition.id}")
            async with semaphore:
                if metrics is not None:
                    metrics.tool_calls += 1
                result = tool(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return result
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
                metrics.tool_latency_ms += round((time.perf_counter() - started) * 1000)

    setattr(invoke, "__foresight_instrumented__", True)
    setattr(invoke, "capability_id", definition.id)
    return invoke


DEFAULT_CAPABILITIES = {
    "graph_context": CapabilityDefinition("graph_context", "local_deterministic", "read", "RUN", 1),
    "calculation": CapabilityDefinition("calculation", "local_deterministic", "read", "RUN", 1),
    "domain_validation": CapabilityDefinition("domain_validation", "local_deterministic", "read", "RUN", 1),
    "web_search": CapabilityDefinition("web_search", "external_read", "read", "RUN", 3),
    "external_mutation": CapabilityDefinition("external_mutation", "external_mutation", "write", "RUN", 1, "HUMAN"),
}


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
