from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief, WorkStage


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
    )
