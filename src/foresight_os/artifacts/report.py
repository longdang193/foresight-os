from pathlib import Path

from foresight_os.domain.challenge import accepted_consequential_recommendation, derive_finding_views
from foresight_os.domain.models import AnalysisState, Assessment, RevisionStatus


def render_report(state: AnalysisState, *, provisional: bool = False) -> str:
    if state.invalidation.stale_artifact_ids:
        raise ValueError("stale artifacts require reassessment before report generation")
    if not provisional and state.revision_status != RevisionStatus.ACCEPTED:
        raise ValueError("normal reports require an accepted revision")
    if not provisional and any(record.assessment == Assessment.UNASSESSED for record in [*state.claims, *state.implications, *state.recommendations]):
        raise ValueError("normal reports require assessed analytical records")
    if not provisional and any(
        not accepted_consequential_recommendation(state, record.id)
        for record in state.recommendations
    ):
        raise ValueError("normal reports require a current accepted review for each recommendation")
    lines = [
        "# Executive Report",
        *( ["", "DRAFT / UNVALIDATED"] if provisional else [] ),
        "",
        f"Investigation: `{state.investigation_id}`",
        f"Revision: `{state.revision}`",
        "",
        "## Findings",
    ]
    if provisional:
        for finding in derive_finding_views(state):
            if finding.limitations:
                lines.append(f"- Review limitations for `{finding.target_id}`: {'; '.join(finding.limitations)}")
    for record in [*state.claims, *state.implications, *state.recommendations]:
        evidence = ", ".join(f"`{evidence_id}`" for evidence_id in record.evidence_ids)
        lines.append(f"- {record.statement} (evidence: {evidence})")
        if record.assumptions:
            lines.append(f"  - Assumptions: {'; '.join(record.assumptions)}")
        if record.uncertainty:
            lines.append(f"  - Uncertainty: {'; '.join(record.uncertainty)}")
        if provisional and record.disconfirmation_conditions:
            lines.append(f"  - Disconfirmation conditions: {'; '.join(record.disconfirmation_conditions)}")
        if provisional and record.confidence_rationale:
            lines.append(f"  - Rationale: {record.confidence_rationale}")
    return "\n".join(lines) + "\n"


def write_report(path: Path, state: AnalysisState, *, provisional: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(state, provisional=provisional), encoding="utf-8")
