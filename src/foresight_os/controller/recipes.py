from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from foresight_os.controller.profiles import Profile
from foresight_os.runtime.maf_probe import vertical_slice_guardrail


class RecipeName(StrEnum):
    DIRECT = "DIRECT"
    ANALYZE = "ANALYZE"
    ANALYZE_REVIEW = "ANALYZE_REVIEW"
    CONCURRENT = "CONCURRENT"
    HANDOFF = "HANDOFF"
    CHALLENGE_RECOMMENDATION = "CHALLENGE_RECOMMENDATION"


class ExecutionPattern(StrEnum):
    DIRECT = "direct"
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    HANDOFF = "handoff"
    GROUP_CHAT = "group_chat"


@dataclass(frozen=True)
class RecipeStage:
    stage_id: str
    pattern: ExecutionPattern
    participants: tuple[dict[str, str], ...]
    input_type: str
    output_type: str
    limits: dict[str, int | str]


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
    purpose: str = "execute"
    stages: tuple[RecipeStage, ...] = ()


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
    if name == RecipeName.CONCURRENT:
        pattern = "concurrent"
        roles = [
            {"purpose": "scan-a", "profile": Profile.NORMAL.value},
            {"purpose": "scan-b", "profile": Profile.NORMAL.value},
        ]
    if name == RecipeName.HANDOFF:
        pattern = "handoff"
        roles = [
            {"purpose": "analyst", "profile": Profile.NORMAL.value},
            {"purpose": "reviewer", "profile": Profile.NORMAL.value},
        ]
    if name == RecipeName.CHALLENGE_RECOMMENDATION:
        pattern = "group_chat"
        roles = [
            {"purpose": "analyst", "profile": Profile.NORMAL.value},
            {"purpose": "skeptic", "profile": Profile.NORMAL.value},
        ]
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern(pattern),
        tuple(roles),
        "prompt",
        "typed-result",
        {"max_agent_steps": guardrail.max_agent_steps, "max_total_agent_calls": guardrail.max_total_agent_calls},
    )
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
        purpose=name.value,
        stages=(stage,),
    )
