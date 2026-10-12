from dataclasses import dataclass, field
from enum import StrEnum

from foresight_os.controller.profiles import Profile
from foresight_os.runtime.maf_probe import vertical_slice_guardrail


class RecipeName(StrEnum):
    DIRECT = "DIRECT"
    ANALYZE = "ANALYZE"
    ANALYZE_REVIEW = "ANALYZE_REVIEW"


@dataclass(frozen=True)
class ExecutionRecipe:
    name: RecipeName
    pattern: str
    roles: list[dict[str, str]]
    max_agent_steps: int
    max_correction_rounds: int
    max_total_agent_calls: int
    completion: str
    escalation: str
    partial_result: str
    metadata: dict[str, str] = field(default_factory=dict)


def make_recipe(name: RecipeName) -> ExecutionRecipe:
    guardrail = vertical_slice_guardrail()
    roles = [{"purpose": "execute", "profile": Profile.NORMAL.value}]
    pattern = "direct"
    if name == RecipeName.ANALYZE:
        pattern = "sequential"
    if name == RecipeName.ANALYZE_REVIEW:
        pattern = "sequential"
        roles = [
            {"purpose": "execute", "profile": Profile.NORMAL.value},
            {"purpose": "review", "profile": Profile.NORMAL.value},
        ]
    return ExecutionRecipe(
        name,
        pattern,
        roles,
        guardrail.max_agent_steps,
        guardrail.max_correction_rounds,
        guardrail.max_total_agent_calls,
        "accepted recommendation after required evidence and review",
        "route to human decision/review boundary",
        "no accepted recommendation; preserve partial state",
    )
