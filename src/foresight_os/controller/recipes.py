from dataclasses import dataclass, field
from enum import StrEnum
import json
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
class StageInput:
    decision_question: str
    horizon: str
    objective: str
    expected_result: str
    relevant_constraints: tuple[str, ...] = ()
    dependency_outputs: tuple[tuple[str, object], ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "decision_question": self.decision_question,
            "horizon": self.horizon,
            "objective": self.objective,
            "expected_result": self.expected_result,
            "relevant_constraints": self.relevant_constraints,
            "dependency_outputs": {stage_id: output for stage_id, output in self.dependency_outputs},
        }

    def __str__(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True, default=str, separators=(",", ":"))


@dataclass(frozen=True)
class RecipeStage:
    stage_id: str
    pattern: ExecutionPattern
    participants: tuple[object, ...]
    input_type: str
    output_type: str
    limits: dict[str, int | str]
    skill_ids: tuple[str, ...] = ()
    objective: str = ""
    dependencies: tuple[str, ...] = ()
    expected_result: str = ""
    research_needs: tuple[object, ...] = ()
    decision_question: str = ""
    horizon: str = "unspecified"
    relevant_constraints: tuple[str, ...] = ()


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
            {"purpose": "analyst", "profile": Profile.NORMAL.value, "handoff_targets": ("participant-2",)},
            {"purpose": "reviewer", "profile": Profile.NORMAL.value, "handoff_targets": ()},
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
        tuple(
            {
                **role,
                "id": role.get("id", f"participant-{index}"),
            }
            for index, role in enumerate(roles, 1)
        ),
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
