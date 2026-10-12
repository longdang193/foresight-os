from pathlib import Path

from foresight_os.domain.models import AnalysisState


def render_report(state: AnalysisState) -> str:
    if state.invalidation.stale_artifact_ids:
        raise ValueError("stale artifacts require reassessment before report generation")
    lines = [
        "# Executive Report",
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


def write_report(path: Path, state: AnalysisState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(state), encoding="utf-8")
