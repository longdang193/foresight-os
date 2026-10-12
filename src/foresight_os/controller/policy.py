from dataclasses import dataclass

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import WorkBrief


@dataclass(frozen=True)
class CandidateProbe:
    name: str
    supported: bool
    available: bool
    selected: bool
    measured: bool
    contract_passed: bool
    quality_passed: bool
    rationale: str

    @property
    def status(self) -> str:
        if not self.supported:
            return "unsupported"
        if not self.available:
            return "unavailable"
        if self.quality_passed:
            return "quality_passed"
        if self.contract_passed:
            return "contract_passed"
        if self.measured:
            return "measured"
        if self.selected:
            return "selected"
        return "available"

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


def _recipe_for_patterns(
    patterns: tuple[ExecutionPattern, ...],
    source: str,
    rationale: str,
    work_stages=(),
    review_required: bool = False,
) -> ExecutionRecipe:
    if not patterns:
        raise ValueError("at least one execution pattern is required")
    if review_required and patterns == (ExecutionPattern.DIRECT,):
        raise ValueError("review_required cannot be satisfied by a direct topology")
    for index, stage in enumerate(work_stages, 1):
        known = {getattr(item, "stage_id", "") for item in work_stages[: index - 1]}
        invalid = [dependency for dependency in getattr(stage, "dependencies", ()) if dependency not in known]
        if invalid:
            raise ValueError(f"stage {stage.stage_id} depends on missing or later stage(s): {', '.join(invalid)}")
    base = make_recipe(RecipeName.ANALYZE_REVIEW if ExecutionPattern.SEQUENTIAL in patterns else RecipeName.DIRECT)
    recipe_names = {
        ExecutionPattern.DIRECT: RecipeName.DIRECT,
        ExecutionPattern.SEQUENTIAL: RecipeName.ANALYZE_REVIEW,
        ExecutionPattern.CONCURRENT: RecipeName.CONCURRENT,
        ExecutionPattern.HANDOFF: RecipeName.HANDOFF,
        ExecutionPattern.GROUP_CHAT: RecipeName.CHALLENGE_RECOMMENDATION,
    }
    capability_map = {
        "external_research": "web_search",
        "web": "web_search",
        "search": "web_search",
        "source_detail": "page_retrieval",
        "page": "page_retrieval",
        "existing_evidence": "graph_context",
        "graph": "graph_context",
        "quantitative_work": "calculation",
        "cost": "calculation",
        "quality_check": "domain_validation",
        "validate": "domain_validation",
    }

    def stage_capabilities(stage: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
        capabilities: list[str] = []
        unresolved: list[str] = []
        for need in getattr(stage, "research_needs", ()):
            text = str(need).lower()
            matches = [capability for key, capability in capability_map.items() if key in text]
            if matches:
                capabilities.extend(matches)
            else:
                unresolved.append(str(need))
        return tuple(dict.fromkeys(capabilities)), tuple(unresolved)

    stages = tuple(
        RecipeStage(
            getattr(work_stages[index - 1], "stage_id", f"stage-{index}") if index <= len(work_stages) else f"stage-{index}",
            pattern,
            tuple(
                [
                    {
                        **role,
                        "capability_ids": stage_capabilities(work_stages[index - 1])[0] if index <= len(work_stages) and role.get("purpose") != "review" else (),
                        "unresolved_capabilities": stage_capabilities(work_stages[index - 1])[1] if index <= len(work_stages) and role.get("purpose") != "review" else (),
                    }
                    for role in make_recipe(recipe_names[pattern]).roles
                ]
                + ([{"id": "reviewer", "role": "reviewer", "purpose": "review", "profile": "normal"}] if review_required and index == len(patterns) and pattern != ExecutionPattern.DIRECT else [])
            ),
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
            "unresolved_capabilities": ";".join(
                need
                for stage in work_stages
                for need in stage_capabilities(stage)[1]
            ),
        },
        purpose=base.purpose,
        stages=stages,
    )


def select_recipe(brief: WorkBrief, task_shape: TaskShape | None = None, override=None) -> ExecutionRecipe:
    override = override if override is not None else brief.execution_pattern_override
    if override is not None:
        selected = _patterns_from_override(override)
        if task_shape is not None and task_shape.review_required and ExecutionPattern.SEQUENTIAL not in selected:
            if selected == (ExecutionPattern.DIRECT,):
                raise ValueError("review_required cannot be satisfied by a direct topology")
        return _recipe_for_patterns(
            selected,
            "explicit_override",
            "valid explicit execution-pattern override",
            brief.stages,
            bool(task_shape and task_shape.review_required),
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
            return _recipe_for_patterns(
                tuple(patterns),
                "task_shape",
                "structural task-shape mapping",
                brief.stages,
                task_shape.review_required,
            )
        return _recipe_for_patterns((ExecutionPattern.DIRECT,), "task_shape", "direct task shape", brief.stages)
    if brief.desired_deliverables:
        return make_recipe(RecipeName.ANALYZE_REVIEW)
    return make_recipe(RecipeName.DIRECT)


def probe_pattern_status() -> list[CandidateProbe]:
    return [
        CandidateProbe(
            "Concurrent",
            True,
            True,
            False,
            True,
            True,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
        CandidateProbe(
            "Handoff",
            True,
            True,
            False,
            True,
            True,
            False,
            "No measurable accepted-finding or recovery improvement over sequential review within budget.",
        ),
    ]
