from pathlib import Path

from foresight_os.domain.models import AnalysisState, Assessment, RevisionStatus


def render_report(state: AnalysisState, *, provisional: bool = False) -> str:
    if state.invalidation.stale_artifact_ids:
        raise ValueError("stale artifacts require reassessment before report generation")
    if not provisional and state.revision_status != RevisionStatus.ACCEPTED:
        raise ValueError("normal reports require an accepted revision")
    if not provisional and any(record.assessment == Assessment.UNASSESSED for record in [*state.claims, *state.implications, *state.recommendations]):
        raise ValueError("normal reports require assessed analytical records")
    lines = [
        "# Executive Report",
        *( ["", "DRAFT / UNVALIDATED"] if provisional else [] ),
        "",
        f"Investigation: `{state.investigation_id}`",
        f"Revision: `{state.revision}`",
        "",
        "## Findings",
    ]
    for record in [*state.claims, *state.implications, *state.recommendations]:
        evidence = ", ".join(f"`{evidence_id}`" for evidence_id in record.evidence_ids)
        lines.append(f"- {record.statement} (evidence: {evidence})")
    return "\n".join(lines) + "\n"


def write_report(path: Path, state: AnalysisState, *, provisional: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(state, provisional=provisional), encoding="utf-8")
