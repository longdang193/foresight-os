from dataclasses import dataclass

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief


@dataclass(frozen=True)
class ReviewPolicy:
    policy_id: str
    version: str
    required_skill_ids: tuple[str, ...]
    acceptable_outcomes: tuple[str, ...] = ("ACCEPTED",)
    blocking_objection_kinds: tuple[str, ...] = ()
    unresolved_classification_issue: str | None = None


class ReviewPolicyResolver:
    """Single owner for deterministic review-policy selection."""

    def resolve(
        self,
        brief: WorkBrief | None = None,
        *,
        target_kind: str | None = None,
        research_needs: tuple[object, ...] | list[object] = (),
        consequence_level: str | None = None,
    ) -> ReviewPolicy:
        level = consequence_level if consequence_level is not None else getattr(brief, "consequence_level", "standard")
        level = str(level or "standard").lower()
        target_value = str(target_kind or "").upper()
        quantitative = target_value == ResearchNeedKind.QUANTITATIVE_ANALYSIS.value or any(str(getattr(item, "kind", item)) == ResearchNeedKind.QUANTITATIVE_ANALYSIS.value for item in research_needs)
        if brief is not None:
            quantitative = quantitative or any(
                str(getattr(stage_need, "kind", stage_need)) == ResearchNeedKind.QUANTITATIVE_ANALYSIS.value
                for stage in getattr(brief, "stages", ())
                for stage_need in getattr(stage, "research_needs", ())
            )
        unresolved = None
        if level not in {"standard", "high"}:
            unresolved = f"unknown consequence classification: {level}"
            level = "standard"
        if level == "high":
            return ReviewPolicy("review-policy-high-consequence-v1", "1", ("key-assumptions-check", "red-team-claim", "abstain-or-escalate"), blocking_objection_kinds=("FAILURE_MODE", "UNSUPPORTED_ASSUMPTION"), unresolved_classification_issue=unresolved)
        if quantitative:
            return ReviewPolicy("review-policy-quantitative-v1", "1", ("quantitative-sanity-check", "red-team-claim"), blocking_objection_kinds=("CALCULATION_ERROR",), unresolved_classification_issue=unresolved)
        if not target_kind:
            unresolved = unresolved or "missing target classification"
        elif target_value not in {"CLAIM", "IMPLICATION", "RECOMMENDATION", ResearchNeedKind.QUANTITATIVE_ANALYSIS.value}:
            unresolved = unresolved or f"unknown target classification: {target_kind}"
        return ReviewPolicy("review-policy-standard-v1", "1", ("source-appraisal", "red-team-claim"), blocking_objection_kinds=("SOURCE_CONTRADICTION",), unresolved_classification_issue=unresolved)


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
    if not values or len(values) > 32:
        raise ValueError("execution-pattern override must contain one to thirty-two patterns")
    selected = tuple(ExecutionPattern(value) for value in values)
    if len(selected) > 1 and ExecutionPattern.DIRECT in selected:
        raise ValueError("direct cannot be composed with other execution patterns")
    return selected


def _recipe_for_patterns(
    patterns: tuple[ExecutionPattern, ...],
    source: str,
    rationale: str,
    work_stages=(),
    review_required: bool = False,
    brief: WorkBrief | None = None,
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
        ResearchNeedKind.EXTERNAL_FACT.value: ("web_search",),
        ResearchNeedKind.SOURCE_DETAIL.value: ("page_retrieval",),
        ResearchNeedKind.DOCUMENT_REVIEW.value: ("document_read",),
        ResearchNeedKind.STRUCTURED_DATA.value: ("spreadsheet_read",),
        ResearchNeedKind.QUANTITATIVE_ANALYSIS.value: ("data_analysis", "calculation"),
        ResearchNeedKind.EXISTING_EVIDENCE.value: ("graph_context",),
        ResearchNeedKind.INTERNAL_KNOWLEDGE.value: ("internal_knowledge",),
        ResearchNeedKind.VALIDATION.value: ("domain_validation",),
        ResearchNeedKind.ARTIFACT_OUTPUT.value: ("artifact_generation",),
    }

    def stage_capabilities(stage: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
        capabilities: list[str] = []
        unresolved: list[str] = []
        for need in getattr(stage, "research_needs", ()):
            if isinstance(need, str):
                unresolved.append(f"{ResearchNeedKind.UNRESOLVED_CAPABILITY.value}:{need}")
                continue
            kind = str(getattr(need, "kind", ""))
            query = str(getattr(need, "query", ""))
            matches = capability_map.get(kind, ())
            if matches:
                capabilities.extend(matches)
            else:
                unresolved.append(f"{kind or ResearchNeedKind.UNRESOLVED_CAPABILITY.value}:{query}")
        return tuple(dict.fromkeys(capabilities)), tuple(unresolved)

    stage_count = len(work_stages) or len(patterns)
    if work_stages and source == "explicit_override" and len(patterns) not in (1, len(work_stages)):
        raise ValueError("pattern list must contain one pattern or exactly one pattern per WorkStage")
    stage_patterns = [
        _patterns_from_override(getattr(work_stages[index - 1], "execution_pattern_override"))[0]
        if index <= len(work_stages) and getattr(work_stages[index - 1], "execution_pattern_override", None) is not None
        else (patterns[index - 1] if index <= len(patterns) else patterns[-1])
        for index in range(1, stage_count + 1)
    ]

    def review_capabilities(stage: object) -> tuple[str, ...]:
        capabilities, _ = stage_capabilities(stage)
        return capabilities

    def stage_roles(stage: object, pattern: ExecutionPattern, is_last: bool) -> list[dict[str, object]]:
        requested_ids = tuple(str(item) for item in getattr(stage, "participants", ()) if str(item))
        if requested_ids:
            roles = [
                {
                    "id": participant_id,
                    "role": "reviewer" if participant_id == "reviewer" else participant_id,
                    "purpose": "review" if participant_id == "reviewer" else participant_id,
                    "profile": "normal",
                }
                for participant_id in requested_ids
            ]
        else:
            roles = [dict(role) for role in make_recipe(recipe_names[pattern]).roles]
            for index, role in enumerate(roles, 1):
                role.setdefault("id", f"participant-{index}")

        needs_collaborator = pattern in {ExecutionPattern.HANDOFF, ExecutionPattern.GROUP_CHAT} or (
            review_required and is_last and pattern != ExecutionPattern.DIRECT
        )
        if needs_collaborator and len(roles) < 2:
            roles.append(
                {
                    "id": "participant-2" if pattern == ExecutionPattern.HANDOFF else "reviewer",
                    "role": "reviewer",
                    "purpose": "review" if pattern != ExecutionPattern.GROUP_CHAT else "skeptic",
                    "profile": "normal",
                }
            )
        if review_required and is_last and pattern != ExecutionPattern.DIRECT and not any(role.get("purpose") == "review" for role in roles):
            roles.append({"id": "reviewer", "role": "reviewer", "purpose": "review", "profile": "normal"})
        if pattern == ExecutionPattern.HANDOFF and len(roles) > 1:
            roles[0].setdefault("handoff_targets", (roles[1]["id"],))
        return roles

    stages = tuple(
        RecipeStage(
            getattr(work_stages[index - 1], "stage_id", f"stage-{index}") if index <= len(work_stages) else f"stage-{index}",
            stage_patterns[index - 1],
            tuple(
                {
                    **role,
                    "capability_ids": stage_capabilities(work_stages[index - 1])[0] if index <= len(work_stages) and role.get("purpose") != "review" else (review_capabilities(work_stages[index - 1]) if index <= len(work_stages) and role.get("purpose") == "review" else ()),
                    "unresolved_capabilities": stage_capabilities(work_stages[index - 1])[1] if index <= len(work_stages) and role.get("purpose") != "review" else (),
                }
                for role in stage_roles(work_stages[index - 1] if index <= len(work_stages) else object(), stage_patterns[index - 1], index == stage_count)
            ),
            "typed-result",
            "typed-result",
            {
                **(
                    getattr(work_stages[index - 1], "limits", {})
                    if index <= len(work_stages)
                    else {}
                ),
                "max_agent_steps": base.max_agent_steps,
                "max_total_agent_calls": base.max_total_agent_calls,
            },
            tuple(getattr(work_stages[index - 1], "skill_ids", ())) if index <= len(work_stages) else (),
            getattr(work_stages[index - 1], "objective", "") if index <= len(work_stages) else "",
            tuple(getattr(work_stages[index - 1], "dependencies", ())) if index <= len(work_stages) else (),
            getattr(work_stages[index - 1], "expected_result", "") if index <= len(work_stages) else "",
            tuple(getattr(work_stages[index - 1], "research_needs", ())) if index <= len(work_stages) else (),
            getattr(brief, "decision_question", "") if brief is not None else "",
            getattr(brief, "horizon", "unspecified") if brief is not None else "unspecified",
            tuple(
                dict.fromkeys(
                    [
                        *getattr(brief, "scope", ()),
                        *getattr(brief, "assumptions", ()),
                        *getattr(brief, "open_dependencies", ()),
                    ]
                )
            ) if brief is not None else (),
            rationale=(
                f"{source}: {rationale}; selected {stage_patterns[index - 1].value} for "
                f"stage {getattr(work_stages[index - 1], 'stage_id', f'stage-{index}') if index <= len(work_stages) else f'stage-{index}'}"
            ),
            capabilities=stage_capabilities(work_stages[index - 1])[0] if index <= len(work_stages) else (),
            access_scope=("read:local",),
            participant_responsibilities=tuple(
                {"participant_id": str(role.get("id", "")), "responsibility": str(role.get("purpose", "execute"))}
                for role in stage_roles(work_stages[index - 1] if index <= len(work_stages) else object(), stage_patterns[index - 1], index == stage_count)
            ),
            review_checks=("independent review" if review_required and index == stage_count else "stage output validation",),
            completion_rule="stage output matches expected result and required checks pass",
            escalation_rule="escalate unresolved capability, contradiction, or budget exhaustion",
            partial_result_rule="preserve completed evidence and mark incomplete stage explicitly",
            adaptation_policy=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
        )
        for index in range(1, stage_count + 1)
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
            "decision_question": getattr(brief, "decision_question", "") if brief is not None else "",
            "horizon": getattr(brief, "horizon", "unspecified") if brief is not None else "unspecified",
            "relevant_constraints": "|".join(
                dict.fromkeys(
                    [
                        *getattr(brief, "scope", ()),
                        *getattr(brief, "assumptions", ()),
                        *getattr(brief, "open_dependencies", ()),
                    ]
                )
            ) if brief is not None else "",
        },
        purpose=base.purpose,
        stages=stages,
        rationale=rationale,
        review_policy="required review policy applies at the final stage" if review_required else "stage output validation",
        reuse_policy="reuse only committed, provenance-complete matching receipts",
        adaptation_policy=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
    )


def select_recipe(brief: WorkBrief, task_shape: TaskShape | None = None, override=None) -> ExecutionRecipe:
    intent = getattr(brief, "execution_intent", None)
    if override is None and intent is not None and intent.required_patterns:
        override = list(intent.required_patterns)
    override = override if override is not None else brief.execution_pattern_override
    if override is not None:
        selected = _patterns_from_override(override)
        if isinstance(override, (list, tuple)) and brief.stages and len(selected) != len(brief.stages):
            raise ValueError("global pattern list must map positionally to every WorkStage")
        if task_shape is not None and task_shape.review_required and ExecutionPattern.SEQUENTIAL not in selected:
            if selected == (ExecutionPattern.DIRECT,):
                raise ValueError("review_required cannot be satisfied by a direct topology")
        return _recipe_for_patterns(
            selected,
            "explicit_override",
            "valid explicit execution-pattern override",
            brief.stages,
            bool(task_shape and task_shape.review_required),
            brief,
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
                brief,
            )
        return _recipe_for_patterns((ExecutionPattern.DIRECT,), "task_shape", "direct task shape", brief.stages, brief=brief)
    if brief.stages:
        return _recipe_for_patterns(
            (ExecutionPattern.SEQUENTIAL,),
            "work_brief",
            "ordered Work Brief stages",
            brief.stages,
            True,
            brief,
        )
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
