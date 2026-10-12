import inspect
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Mapping


class CapabilityDecision(StrEnum):
    USE_NATIVE = "USE_NATIVE"
    ADAPT_AT_BOUNDARY = "ADAPT_AT_BOUNDARY"
    DEFER = "DEFER"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CapabilityDefinition:
    id: str
    capability_class: str
    access: str = "read"
    share_scope: str = "RUN"
    max_parallelism: int = 1
    approval_policy: str = "NONE"


@dataclass(frozen=True)
class CapabilityResolution:
    definition: CapabilityDefinition
    decision: CapabilityDecision
    available: bool
    reason: str
    tool: Any = None


@dataclass
class CapabilityScope:
    resources: list[Any] = field(default_factory=list)
    cache: dict[tuple[str, str, str], Any] = field(default_factory=dict)

    def register(self, resource: Any) -> Any:
        self.resources.append(resource)
        return resource

    async def close(self) -> None:
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
            raise RuntimeError(f"failed to close {len(errors)} capability resource(s)") from errors[0]


class CapabilityResolver:
    def __init__(self, definitions: Mapping[str, CapabilityDefinition] | None = None) -> None:
        self.definitions = dict(definitions or DEFAULT_CAPABILITIES)

    def resolve(self, required_capabilities: tuple[str, ...] | list[str], run_context: Mapping[str, Any] | None = None) -> dict[str, CapabilityResolution]:
        context = dict(run_context or {})
        scope = context.get("scope") or CapabilityScope()
        local = context.get("local_capabilities", {})
        native = context.get("native_tools", {})
        mcp = context.get("mcp_tools", {})
        adapters = context.get("adapters", {})
        resolved: dict[str, CapabilityResolution] = {}
        for capability_id in required_capabilities:
            definition = self.definitions.get(capability_id)
            if definition is None:
                resolved[capability_id] = CapabilityResolution(
                    CapabilityDefinition(capability_id, "unknown"),
                    CapabilityDecision.UNSUPPORTED,
                    False,
                    "capability is not defined",
                )
                continue
            if definition.approval_policy == "HUMAN" and not context.get("human_approved", False):
                resolved[capability_id] = CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "human approval required")
                continue
            cache_key = (capability_id, "", "")
            if cache_key in scope.cache:
                resolved[capability_id] = CapabilityResolution(definition, CapabilityDecision.USE_NATIVE, True, "reused run-scoped capability", scope.cache[cache_key])
                continue
            binding = local.get(capability_id)
            decision = CapabilityDecision.USE_NATIVE
            reason = "local deterministic capability"
            if binding is None:
                binding = native.get(capability_id)
                reason = "native/provider capability"
            if binding is None:
                binding = mcp.get(capability_id)
                decision = CapabilityDecision.ADAPT_AT_BOUNDARY
                reason = "configured MCP capability"
            if binding is None:
                binding = adapters.get(capability_id)
                decision = CapabilityDecision.ADAPT_AT_BOUNDARY
                reason = "configured thin adapter"
            if binding is None:
                resolved[capability_id] = CapabilityResolution(definition, CapabilityDecision.UNSUPPORTED, False, "capability is unavailable")
                continue
            if callable(binding):
                binding = binding(context)
            if inspect.isawaitable(binding):
                raise RuntimeError("capability initialization must be completed before resolver binding")
            if binding is not None and definition.share_scope == "RUN":
                scope.register(binding) if binding not in scope.resources else None
                scope.cache[cache_key] = binding
            resolved[capability_id] = CapabilityResolution(definition, decision, True, reason, binding)
        return resolved


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
