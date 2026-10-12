from dataclasses import dataclass

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import WorkBrief


@dataclass(frozen=True)
class CandidateProbe:
    name: str
    accepted: bool
    supported: bool
    available: bool
    rationale: str

    @property
    def production_admitted(self) -> bool:
        return self.supported and self.available


@dataclass(frozen=True)
class PatternSelection:
    selected_patterns: tuple[ExecutionPattern, ...]
    selection_source: str
    rationale: str
    run_id: str | None = None


def select_recipe(brief: WorkBrief, task_shape: TaskShape | None = None, override=None) -> ExecutionRecipe:
    override = override if override is not None else brief.execution_pattern_override
    if override is not None:
        patterns = (override,) if isinstance(override, str) else tuple(override)
        selected = tuple(ExecutionPattern(pattern) for pattern in patterns)
        if not selected or len(selected) > 4:
            raise ValueError("execution-pattern override must contain one to four patterns")
        recipe = make_recipe(RecipeName.ANALYZE_REVIEW if ExecutionPattern.SEQUENTIAL in selected else RecipeName.DIRECT)
        stages = tuple(
            RecipeStage(f"stage-{index}", pattern, tuple(recipe.roles), "typed-result", "typed-result", {})
            for index, pattern in enumerate(selected, 1)
        )
        return ExecutionRecipe(
            recipe.name, selected[0].value, recipe.roles, recipe.max_agent_steps,
            recipe.max_correction_rounds, recipe.max_total_agent_calls,
            recipe.completion, recipe.escalation, recipe.partial_result,
            metadata={"selection_source": "explicit_override", "selected_patterns": ",".join(pattern.value for pattern in selected)},
            purpose=recipe.purpose,
            stages=stages,
        )
    if task_shape is not None:
        patterns: list[ExecutionPattern] = []
        if task_shape.independent_subtasks:
            patterns.append(ExecutionPattern.CONCURRENT)
        if task_shape.dynamic_specialist_routing:
            patterns.append(ExecutionPattern.HANDOFF)
        if task_shape.interactive_deliberation:
            patterns.append(ExecutionPattern.GROUP_CHAT)
        if task_shape.ordered_dependencies or task_shape.review_required:
            patterns.append(ExecutionPattern.SEQUENTIAL)
        if patterns:
            return select_recipe(brief, override=[pattern.value for pattern in patterns])
    if brief.desired_deliverables:
        return make_recipe(RecipeName.ANALYZE_REVIEW)
    return make_recipe(RecipeName.DIRECT)


def probe_optional_patterns() -> list[CandidateProbe]:
    return [
        CandidateProbe(
            "Concurrent",
            False,
            False,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
        CandidateProbe(
            "Handoff",
            False,
            False,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
    ]
