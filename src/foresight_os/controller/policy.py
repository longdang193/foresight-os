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

    @property
    def available_for_execution(self) -> bool:
        return self.supported and self.available


@dataclass(frozen=True)
class PatternSelection:
    selected_patterns: tuple[ExecutionPattern, ...]
    selection_source: str
    rationale: str
    run_id: str | None = None


def _patterns_from_override(override) -> tuple[ExecutionPattern, ...]:
    values = (override,) if isinstance(override, str) else tuple(override)
    if not values or len(values) > 4:
        raise ValueError("execution-pattern override must contain one to four patterns")
    selected = tuple(ExecutionPattern(value) for value in values)
    if len(selected) > 1 and ExecutionPattern.DIRECT in selected:
        raise ValueError("direct cannot be composed with other execution patterns")
    if len(set(selected)) != len(selected):
        raise ValueError("execution-pattern override cannot repeat a pattern")
    return selected


def _recipe_for_patterns(patterns: tuple[ExecutionPattern, ...], source: str, rationale: str) -> ExecutionRecipe:
    if not patterns:
        raise ValueError("at least one execution pattern is required")
    base = make_recipe(RecipeName.ANALYZE_REVIEW if ExecutionPattern.SEQUENTIAL in patterns else RecipeName.DIRECT)
    recipe_names = {
        ExecutionPattern.DIRECT: RecipeName.DIRECT,
        ExecutionPattern.SEQUENTIAL: RecipeName.ANALYZE_REVIEW,
        ExecutionPattern.CONCURRENT: RecipeName.CONCURRENT,
        ExecutionPattern.HANDOFF: RecipeName.HANDOFF,
        ExecutionPattern.GROUP_CHAT: RecipeName.CHALLENGE_RECOMMENDATION,
    }
    stages = tuple(
        RecipeStage(
            f"stage-{index}",
            pattern,
            tuple(make_recipe(recipe_names[pattern]).roles),
            "typed-result",
            "typed-result",
            {"max_agent_steps": base.max_agent_steps, "max_total_agent_calls": base.max_total_agent_calls},
        )
        for index, pattern in enumerate(patterns, 1)
    )
    return ExecutionRecipe(
        base.name,
        patterns[0].value,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        metadata={
            "selection_source": source,
            "selection_rationale": rationale,
            "selected_patterns": ",".join(pattern.value for pattern in patterns),
        },
        purpose=base.purpose,
        stages=stages,
    )


def select_recipe(brief: WorkBrief, task_shape: TaskShape | None = None, override=None) -> ExecutionRecipe:
    override = override if override is not None else brief.execution_pattern_override
    if override is not None:
        selected = _patterns_from_override(override)
        if task_shape is not None and task_shape.review_required and ExecutionPattern.SEQUENTIAL not in selected:
            raise ValueError("review_required cannot be removed by an execution-pattern override")
        return _recipe_for_patterns(selected, "explicit_override", "valid explicit execution-pattern override")
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
            return _recipe_for_patterns(tuple(patterns), "task_shape", "structural task-shape mapping")
        return _recipe_for_patterns((ExecutionPattern.DIRECT,), "task_shape", "direct task shape")
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
