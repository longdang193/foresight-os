from foresight_os.domain.models import WorkBrief


def create_work_brief(decision_question: str, investigation_id: str = "case-001") -> WorkBrief:
    return WorkBrief(
        investigation_id=investigation_id,
        decision_question=decision_question,
        scope=["Northern Europe", "Southern Europe", "2030"],
        desired_deliverables=["key signals", "strategic implications", "executive report"],
        assumptions=["the 2030 planning horizon remains in scope"],
        open_dependencies=["capacity expansion cost is not included in the synthetic case"],
        current_direction="Assess forecast demand against capacity before recommending investment.",
        next_useful_step="Review the capacity contradiction and validate expansion cost.",
    )
