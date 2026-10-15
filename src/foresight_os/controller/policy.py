from dataclasses import dataclass

from foresight_os.controller.recipes import (
    INDEPENDENT_VALIDATION_POLICY,
    ExecutionPattern,
    ExecutionRecipe,
    RecipeName,
    RecipeStage,
    ReviewCheckKind,
    make_recipe,
)
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief


@dataclass(frozen=True)
class ReviewPolicy:
    policy_id: str
    version: str
    required_skill_ids: tuple[str, ...]
    required_check_ids: tuple[str, ...] = ()
    reviewer_capability_ids: tuple[str, ...] = ()
    acceptable_outcomes: tuple[str, ...] = ("ACCEPTED",)
    blocking_objection_kinds: tuple[str, ...] = ()
    unresolved_classification_issue: str | None = None

    @property
    def reviewer_skill_ids(self) -> tuple[str, ...]:
        return self.required_skill_ids


class ReviewPolicyResolver:
    """Single owner for deterministic review-policy selection."""

    def resolve(
        self,
        brief: WorkBrief | None = None,
        *,
        target_kind: str | None = None,
        research_needs: tuple[object, ...] | list[object] = (),
        consequence_level: str | None = None,
        typed: bool = False,
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
        if typed:
            return self._resolve_typed(
                brief,
                target_value=target_value,
                research_needs=research_needs,
                consequence_level=level,
                unresolved_classification_issue=unresolved,
            )
        if level == "high":
            return ReviewPolicy("review-policy-high-consequence-v1", "1", ("key-assumptions-check", "red-team-claim", "abstain-or-escalate"), blocking_objection_kinds=("FAILURE_MODE", "UNSUPPORTED_ASSUMPTION"), unresolved_classification_issue=unresolved)
        if quantitative:
            return ReviewPolicy("review-policy-quantitative-v1", "1", ("quantitative-sanity-check", "red-team-claim"), blocking_objection_kinds=("CALCULATION_ERROR",), unresolved_classification_issue=unresolved)
        if not target_kind:
            unresolved = unresolved or "missing target classification"
        elif target_value not in {"CLAIM", "IMPLICATION", "RECOMMENDATION", ResearchNeedKind.QUANTITATIVE_ANALYSIS.value}:
            unresolved = unresolved or f"unknown target classification: {target_kind}"
        return ReviewPolicy("review-policy-standard-v1", "1", ("source-appraisal", "red-team-claim"), blocking_objection_kinds=("SOURCE_CONTRADICTION",), unresolved_classification_issue=unresolved)

    def _resolve_typed(
        self,
        brief: WorkBrief | None,
        *,
        target_value: str,
        research_needs: tuple[object, ...] | list[object],
        consequence_level: str,
        unresolved_classification_issue: str | None,
    ) -> ReviewPolicy:
        needs = [*research_needs]
        if brief is not None:
            needs.extend(
                stage_need
                for stage in getattr(brief, "stages", ())
                for stage_need in getattr(stage, "research_needs", ())
            )
        need_kinds = {
            str(getattr(item, "kind", item))
            for item in needs
            if item is not None
        }
        source_kinds = {
            ResearchNeedKind.EXTERNAL_FACT.value,
            ResearchNeedKind.SOURCE_DETAIL.value,
            ResearchNeedKind.DOCUMENT_REVIEW.value,
            ResearchNeedKind.STRUCTURED_DATA.value,
            ResearchNeedKind.EXISTING_EVIDENCE.value,
            ResearchNeedKind.VALIDATION.value,
        }
        quantitative = bool(
            target_value == ResearchNeedKind.QUANTITATIVE_ANALYSIS.value
            or ResearchNeedKind.QUANTITATIVE_ANALYSIS.value in need_kinds
            or ResearchNeedKind.STRUCTURED_DATA.value in need_kinds
        )
        material_source = bool(
            need_kinds.intersection(source_kinds)
            or getattr(brief, "open_dependencies", ())
            or getattr(brief, "scope", ())
        )
        checks: list[str] = []
        if material_source or target_value in {"CLAIM", "IMPLICATION", "RECOMMENDATION"}:
            checks.append(ReviewCheckKind.SOURCE_FIDELITY.value)
        if brief is not None or target_value in {"IMPLICATION", "RECOMMENDATION"} or consequence_level == "high":
            checks.append(ReviewCheckKind.SCOPE_RECONCILIATION.value)
        if quantitative:
            checks.append(ReviewCheckKind.CALCULATION_RECONCILIATION.value)
        if consequence_level == "high" or target_value in {"IMPLICATION", "RECOMMENDATION"}:
            checks.append(ReviewCheckKind.DECISION_CHALLENGE.value)
        if not checks:
            checks.append(ReviewCheckKind.SCOPE_RECONCILIATION.value)

        skill_by_check = {
            ReviewCheckKind.SOURCE_FIDELITY.value: "source-appraisal",
            ReviewCheckKind.SCOPE_RECONCILIATION.value: "key-assumptions-check",
            ReviewCheckKind.CALCULATION_RECONCILIATION.value: "quantitative-sanity-check",
            ReviewCheckKind.DECISION_CHALLENGE.value: "red-team-claim",
        }
        capability_by_need = {
            ResearchNeedKind.EXTERNAL_FACT.value: ("web_search",),
            ResearchNeedKind.SOURCE_DETAIL.value: ("page_retrieval",),
            ResearchNeedKind.DOCUMENT_REVIEW.value: ("document_read",),
            ResearchNeedKind.STRUCTURED_DATA.value: ("spreadsheet_read",),
            ResearchNeedKind.QUANTITATIVE_ANALYSIS.value: ("data_analysis", "calculation"),
            ResearchNeedKind.EXISTING_EVIDENCE.value: ("graph_context",),
            ResearchNeedKind.VALIDATION.value: ("domain_validation",),
        }
        capabilities = list(checks)
        if ReviewCheckKind.SOURCE_FIDELITY.value in checks or ReviewCheckKind.CALCULATION_RECONCILIATION.value in checks:
            for kind in sorted(need_kinds):
                capabilities.extend(capability_by_need.get(kind, ()))
        skills = [skill_by_check[check] for check in checks]
        if consequence_level == "high" and "abstain-or-escalate" not in skills:
            skills.append("abstain-or-escalate")
        blocking = ("CALCULATION_ERROR",) if quantitative else ("SOURCE_CONTRADICTION", "UNSUPPORTED_ASSUMPTION")
        return ReviewPolicy(
            INDEPENDENT_VALIDATION_POLICY,
            "1",
            tuple(dict.fromkeys(skills)),
            tuple(dict.fromkeys(checks)),
            tuple(dict.fromkeys(capabilities)),
            blocking_objection_kinds=blocking,
            unresolved_classification_issue=unresolved_classification_issue,
        )


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


def _stage_pattern_override(stage: object):
    legacy_override = getattr(stage, "execution_pattern_override", None)
    if legacy_override is not None:
        return legacy_override
    intent = getattr(stage, "execution_intent", None)
    required_patterns = getattr(intent, "required_patterns", ())
    return required_patterns or None


def _explicit_reviewer_requested(brief: WorkBrief | None, task_shape: TaskShape | None) -> bool:
    if task_shape is not None and task_shape.review_required:
        return True
    if brief is None:
        return False
    intent = getattr(brief, "execution_intent", None)
    if "reviewer" in {str(item) for item in getattr(intent, "required_participants", ())}:
        return True
    for stage in getattr(brief, "stages", ()):
        if "reviewer" in {str(item) for item in getattr(stage, "participants", ())}:
            return True
        stage_intent = getattr(stage, "execution_intent", None)
        if "reviewer" in {str(item) for item in getattr(stage_intent, "required_participants", ())}:
            return True
    return False


def _recipe_for_patterns(
    patterns: tuple[ExecutionPattern, ...],
    source: str,
    rationale: str,
    work_stages=(),
    review_required: bool = False,
    reviewer_execution_required: bool = False,
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
    intent = getattr(brief, "execution_intent", None)
    required_capabilities = tuple(str(item) for item in getattr(intent, "required_capabilities", ()) if str(item) not in {item.value for item in ReviewCheckKind})
    required_participants = tuple(str(item) for item in getattr(intent, "required_participants", ()) if str(item))

    def stage_requirements(stage: object) -> tuple[tuple[str, ...], tuple[str, ...]]:
        stage_intent = getattr(stage, "execution_intent", None)
        stage_capabilities = tuple(str(item) for item in getattr(stage_intent, "required_capabilities", ()) if str(item) not in {item.value for item in ReviewCheckKind})
        stage_participants = tuple(str(item) for item in getattr(stage_intent, "required_participants", ()) if str(item))
        return (
            tuple(dict.fromkeys((*required_capabilities, *stage_capabilities))),
            tuple(dict.fromkeys((*required_participants, *stage_participants))),
        )

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
        required_stage_capabilities, _ = stage_requirements(stage)
        return tuple(dict.fromkeys((*capabilities, *required_stage_capabilities))), tuple(unresolved)

    review_needs = tuple(
        need
        for stage in work_stages
        for need in getattr(stage, "research_needs", ())
    )
    review_policy = ReviewPolicyResolver().resolve(
        brief,
        target_kind="RECOMMENDATION" if review_required else None,
        research_needs=review_needs,
        consequence_level=getattr(brief, "consequence_level", None) if brief is not None else None,
        typed=review_required,
    )

    stage_count = len(work_stages) or len(patterns)
    max_total_agent_calls = max(base.max_total_agent_calls, stage_count)
    if work_stages and source == "explicit_override" and len(patterns) not in (1, len(work_stages)):
        raise ValueError("pattern list must contain one pattern or exactly one pattern per WorkStage")
    stage_patterns = []
    for index in range(1, stage_count + 1):
        stage_override = _stage_pattern_override(work_stages[index - 1]) if index <= len(work_stages) else None
        stage_patterns.append(
            _patterns_from_override(stage_override)[0]
            if stage_override is not None
            else (patterns[index - 1] if index <= len(patterns) else patterns[-1])
        )

    def review_capabilities(stage: object) -> tuple[str, ...]:
        return review_policy.reviewer_capability_ids

    def review_runtime_capabilities(stage: object) -> tuple[str, ...]:
        declared = set(review_policy.reviewer_capability_ids)
        return tuple(item for item in ("web_search", "page_retrieval", "document_read", "spreadsheet_read", "data_analysis", "calculation", "graph_context", "internal_knowledge", "domain_validation", "artifact_generation") if item in declared)

    def participant_uses_tools(stage: object, role: dict[str, object]) -> bool:
        if role.get("capability_ids"):
            return True
        if role.get("purpose") == "review" and review_required:
            return bool(review_runtime_capabilities(stage))
        return bool(stage_capabilities(stage)[0])

    def stage_call_budget(stage: object, pattern: ExecutionPattern, is_last: bool) -> int:
        return sum(
            (3 if participant_uses_tools(stage, role) else 1)
            * (1 + base.max_correction_rounds)
            for role in stage_roles(stage, pattern, is_last)
        )

    def stage_roles(stage: object, pattern: ExecutionPattern, is_last: bool) -> list[dict[str, object]]:
        _, required_stage_participants = stage_requirements(stage)
        requested_ids = tuple(dict.fromkeys((
            *(str(item) for item in getattr(stage, "participants", ()) if str(item)),
            *required_stage_participants,
        )))
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
        if pattern == ExecutionPattern.SEQUENTIAL and not requested_ids and not reviewer_execution_required:
            roles = [role for role in roles if role.get("purpose") != "review"]

        needs_collaborator = pattern in {ExecutionPattern.HANDOFF, ExecutionPattern.GROUP_CHAT} or (
            reviewer_execution_required and is_last and pattern != ExecutionPattern.DIRECT
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
        if reviewer_execution_required and is_last and pattern != ExecutionPattern.DIRECT and not any(role.get("purpose") == "review" for role in roles):
            roles.append({"id": "reviewer", "role": "reviewer", "purpose": "review", "profile": "normal"})
        if pattern == ExecutionPattern.HANDOFF and len(roles) > 1:
            roles[0].setdefault("handoff_targets", (roles[1]["id"],))
        return roles

    if work_stages:
        planned_agent_calls = sum(
            stage_call_budget(
                work_stages[index - 1],
                stage_patterns[index - 1],
                index == stage_count,
            )
            for index in range(1, stage_count + 1)
        )
        max_total_agent_calls = max(max_total_agent_calls, planned_agent_calls)

    stages = tuple(
        RecipeStage(
            getattr(work_stages[index - 1], "stage_id", f"stage-{index}") if index <= len(work_stages) else f"stage-{index}",
            stage_patterns[index - 1],
            tuple(
                {
                    **role,
                    "capability_ids": review_runtime_capabilities(work_stages[index - 1] if index <= len(work_stages) else object()) if role.get("purpose") == "review" and review_required else (stage_capabilities(work_stages[index - 1])[0] if index <= len(work_stages) else required_capabilities),
                    "reviewer_capability_ids": review_capabilities(work_stages[index - 1] if index <= len(work_stages) else object()) if role.get("purpose") == "review" and review_required else tuple(role.get("reviewer_capability_ids", ())),
                    "unresolved_capabilities": stage_capabilities(work_stages[index - 1])[1] if index <= len(work_stages) and role.get("purpose") != "review" else (),
                    "skill_ids": review_policy.reviewer_skill_ids if role.get("purpose") == "review" and review_required else tuple(role.get("skill_ids", ())),
                    "review_check_ids": review_policy.required_check_ids if role.get("purpose") == "review" and review_required else tuple(role.get("review_check_ids", ())),
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
                "max_total_agent_calls": max(
                    int(
                        (
                            getattr(work_stages[index - 1], "limits", {})
                            if index <= len(work_stages)
                            else {}
                        ).get("max_total_agent_calls", base.max_total_agent_calls)
                    ),
                    stage_call_budget(
                        work_stages[index - 1] if index <= len(work_stages) else object(),
                        stage_patterns[index - 1],
                        index == stage_count,
                    )
                ),
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
            capabilities=stage_capabilities(work_stages[index - 1])[0] if index <= len(work_stages) else required_capabilities,
            access_scope=("read:local",),
            participant_responsibilities=tuple(
                {"participant_id": str(role.get("id", "")), "responsibility": str(role.get("purpose", "execute"))}
                for role in stage_roles(work_stages[index - 1] if index <= len(work_stages) else object(), stage_patterns[index - 1], index == stage_count)
            ),
            review_checks=review_policy.required_check_ids if review_required and index == stage_count else (),
            completion_rule="stage output matches expected result and required checks pass",
            escalation_rule="escalate unresolved capability, contradiction, or budget exhaustion",
            partial_result_rule="preserve completed evidence and mark incomplete stage explicitly",
            adaptation_policy=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
        )
        for index in range(1, stage_count + 1)
    )
    recipe_roles = base.roles
    if ExecutionPattern.SEQUENTIAL in patterns and not reviewer_execution_required:
        recipe_roles = [role for role in recipe_roles if role.get("purpose") != "review"]
    return ExecutionRecipe(
        base.name,
        patterns[0].value,
        recipe_roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        metadata={
            "selection_source": source,
            "selection_rationale": rationale,
            "selected_patterns": ",".join(pattern.value for pattern in patterns),
            "required_participants": ",".join(required_participants),
            "required_capabilities": ",".join(required_capabilities),
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
        review_policy=review_policy.policy_id if review_required else "stage output validation",
        reuse_policy="reuse only committed, provenance-complete matching receipts",
        adaptation_policy=("bounded_retry", "reduced_concurrency", "dependency_safe_topology_reduction"),
    )


def select_recipe(brief: WorkBrief, task_shape: TaskShape | None = None, override=None) -> ExecutionRecipe:
    intent = getattr(brief, "execution_intent", None)
    required_capabilities = tuple(str(item) for item in getattr(intent, "required_capabilities", ()) if str(item) not in {item.value for item in ReviewCheckKind})
    required_participants = tuple(str(item) for item in getattr(intent, "required_participants", ()) if str(item))
    if override is None and intent is not None and intent.required_patterns:
        override = list(intent.required_patterns)
    override = override if override is not None else brief.execution_pattern_override
    if override is not None:
        selected = _patterns_from_override(override)
        if isinstance(override, (list, tuple)) and len(selected) > 1 and brief.stages and len(selected) != len(brief.stages):
            raise ValueError("global pattern list must map positionally to every WorkStage")
        if task_shape is not None and task_shape.review_required and ExecutionPattern.SEQUENTIAL not in selected:
            if selected == (ExecutionPattern.DIRECT,):
                raise ValueError("review_required cannot be satisfied by a direct topology")
        return _recipe_for_patterns(
            selected,
            "explicit_override",
            "valid explicit execution-pattern override",
            brief.stages,
            _explicit_reviewer_requested(brief, task_shape),
            _explicit_reviewer_requested(brief, task_shape),
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
                _explicit_reviewer_requested(brief, task_shape),
                _explicit_reviewer_requested(brief, task_shape),
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
            True,
            brief,
        )
    if brief.desired_deliverables:
        if intent is None or not (required_capabilities or required_participants):
            return _recipe_for_patterns(
                (ExecutionPattern.SEQUENTIAL,),
                "work_brief",
                "desired deliverables require bounded analysis and independent validation",
                brief=brief,
                review_required=True,
            )
        return _recipe_for_patterns(
            (ExecutionPattern.SEQUENTIAL,),
            "work_brief",
            "desired deliverables require bounded analysis and review",
            brief.stages,
            True,
            _explicit_reviewer_requested(brief, task_shape),
            brief,
        )
    if intent is not None and (required_capabilities or required_participants):
        return _recipe_for_patterns(
            (ExecutionPattern.SEQUENTIAL,),
            "work_brief",
            "mandatory execution intent requires bounded analysis and review",
            brief.stages,
            True,
            _explicit_reviewer_requested(brief, task_shape),
            brief,
        )
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
