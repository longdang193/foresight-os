from dataclasses import dataclass
from enum import StrEnum


class CapabilityDecision(StrEnum):
    USE_NATIVE = "USE_NATIVE"
    ADAPT_AT_BOUNDARY = "ADAPT_AT_BOUNDARY"
    DEFER = "DEFER"
    UNSUPPORTED = "UNSUPPORTED"


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
