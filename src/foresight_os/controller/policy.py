from dataclasses import dataclass

from foresight_os.controller.recipes import ExecutionRecipe, RecipeName, make_recipe
from foresight_os.domain.models import WorkBrief


@dataclass(frozen=True)
class CandidateProbe:
    name: str
    accepted: bool
    production_admitted: bool
    rationale: str


def select_recipe(brief: WorkBrief) -> ExecutionRecipe:
    if brief.desired_deliverables:
        return make_recipe(RecipeName.ANALYZE_REVIEW)
    return make_recipe(RecipeName.DIRECT)


def probe_optional_patterns() -> list[CandidateProbe]:
    return [
        CandidateProbe(
            "Concurrent",
            False,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
        CandidateProbe(
            "Handoff",
            False,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
    ]
