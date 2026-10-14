from dataclasses import replace

from foresight_os.domain.models import ExecutionIntent, ResearchNeed, ResearchNeedKind, WorkBrief, WorkStage


def create_work_brief(
    decision_question: str,
    investigation_id: str = "case-001",
    *,
    scope: list[str] | None = None,
    horizon: str = "unspecified",
    desired_deliverables: list[str] | None = None,
    assumptions: list[str] | None = None,
    open_dependencies: list[str] | None = None,
    stages: list[WorkStage] | None = None,
    consequence_level: str = "standard",
    user_preferences: dict[str, object] | None = None,
) -> WorkBrief:
    resolved_scope = list(scope or [])
    resolved_deliverables = list(desired_deliverables or ["analysis", "executive report"])
    resolved_assumptions = list(assumptions or [])
    resolved_dependencies = list(open_dependencies or [])
    return WorkBrief(
        investigation_id=investigation_id,
        decision_question=decision_question,
        scope=resolved_scope,
        desired_deliverables=resolved_deliverables,
        assumptions=resolved_assumptions,
        open_dependencies=resolved_dependencies,
        current_direction="Assess the decision question using the declared scope and evidence.",
        next_useful_step="Collect the next missing evidence and validate material contradictions.",
        stages=list(stages or []),
        horizon=horizon,
        consequence_level=consequence_level,
        user_preferences=dict(user_preferences or {}),
    )


def refine_work_brief(
    brief: WorkBrief,
    *,
    scope: list[str] | None = None,
    assumptions: list[str] | None = None,
    open_dependencies: list[str] | None = None,
    desired_deliverables: list[str] | None = None,
    horizon: str | None = None,
    consequence_level: str | None = None,
    user_preferences: dict[str, object] | None = None,
    required_patterns: tuple[str, ...] = (),
    preferred_patterns: tuple[str, ...] = (),
    required_participants: tuple[str, ...] = (),
    preferred_participants: tuple[str, ...] = (),
    required_capabilities: tuple[str, ...] = (),
    preferred_capabilities: tuple[str, ...] = (),
) -> WorkBrief:
    intent = None
    if any((required_patterns, preferred_patterns, required_participants, preferred_participants, required_capabilities, preferred_capabilities)):
        intent = ExecutionIntent(
            required_patterns=tuple(required_patterns),
            preferred_patterns=tuple(preferred_patterns),
            required_participants=tuple(required_participants),
            preferred_participants=tuple(preferred_participants),
            required_capabilities=tuple(required_capabilities),
            preferred_capabilities=tuple(preferred_capabilities),
            source="refined_user_intent",
        )
    return replace(
        brief,
        scope=list(brief.scope if scope is None else scope),
        assumptions=list(brief.assumptions if assumptions is None else assumptions),
        open_dependencies=list(brief.open_dependencies if open_dependencies is None else open_dependencies),
        desired_deliverables=list(brief.desired_deliverables if desired_deliverables is None else desired_deliverables),
        horizon=brief.horizon if horizon is None else horizon,
        consequence_level=brief.consequence_level if consequence_level is None else consequence_level,
        user_preferences={**brief.user_preferences, **dict(user_preferences or {})},
        execution_intent=intent if intent is not None else brief.execution_intent,
    )
