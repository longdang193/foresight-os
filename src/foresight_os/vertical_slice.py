from dataclasses import dataclass, replace
from pathlib import Path

from foresight_os.analysis.analyst import draft_analysis
from foresight_os.analysis.reviewer import ReviewResult, review_reasoning
from foresight_os.domain.challenge import ReviewOutcome, ReviewRecord, build_material_fingerprint
from foresight_os.analysis.workbook import extract_evidence, read_workbook
from foresight_os.artifacts.report import write_report
from foresight_os.domain.models import AnalysisState, Artifact, Invalidation, Relationship, Revision
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.maf_probe import vertical_slice_guardrail
from foresight_os.runtime.workflow import run_sequential_steps


@dataclass(frozen=True)
class VerticalSliceOutcome:
    accepted: bool
    review: ReviewResult
    analysis: AnalysisState | None
    report_path: Path | None
    status: str


def run_vertical_slice(
    workbook_path: Path,
    work_dir: Path,
    human_accept: bool,
    agent_steps: int = 5,
    correction_rounds: int = 0,
    total_agent_calls: int = 3,
) -> VerticalSliceOutcome:
    guardrail = vertical_slice_guardrail()
    if (
        agent_steps > guardrail.max_agent_steps
        or correction_rounds > guardrail.max_correction_rounds
        or total_agent_calls > guardrail.max_total_agent_calls
    ):
        return VerticalSliceOutcome(
            False,
            ReviewResult(False, [guardrail.exhaustion_outcome]),
            None,
            None,
            "exhausted",
        )
    rows = read_workbook(workbook_path)
    sequence = run_sequential_steps(["analyst", "reviewer"])
    if sequence["completed_stages"] != ["analyst", "reviewer"]:
        return VerticalSliceOutcome(False, ReviewResult(False, ["MAF sequential workflow did not complete"]), None, None, "failed")
    evidence = extract_evidence(workbook_path, rows)
    draft = draft_analysis(evidence)
    records = [*draft.claims, *draft.implications, *draft.recommendations]
    review = review_reasoning(draft.evidence, records)
    if not review.accepted or not human_accept:
        return VerticalSliceOutcome(False, review, None, None, "human_review")

    if guardrail.max_correction_rounds < 1 or guardrail.max_total_agent_calls < 3:
        return VerticalSliceOutcome(False, ReviewResult(False, ["guardrail does not permit the benchmark flow"]), None, None, "exhausted")

    report_path = Path(work_dir) / "artifacts" / "executive-report.md"
    artifact = Artifact("artifact-executive-report", "executive-report", str(report_path), relationship_ids=["relationship-recommendation-artifact"])
    artifact_link = Relationship("relationship-recommendation-artifact", draft.recommendations[0].id, artifact.id, "produces")
    recommendation = draft.recommendations[0]
    recommendation = type(recommendation)(
        recommendation.id,
        recommendation.statement,
        recommendation.basis,
        recommendation.assessment,
        recommendation.lifecycle,
        recommendation.evidence_ids,
        [*recommendation.relationship_ids, artifact_link.id],
    )
    analysis = AnalysisState(
        "case-001",
        1,
        draft.evidence,
        draft.claims,
        draft.implications,
        [recommendation],
        [artifact],
        [*draft.relationships, artifact_link],
        [Revision("revision-1", 1, "accepted benchmark analysis", [item.id for item in [*draft.evidence, *draft.claims, *draft.implications, recommendation, artifact, *draft.calculations, *[*draft.relationships, artifact_link]]])],
        Invalidation(),
        calculations=draft.calculations,
    )
    review_target_ids = tuple(item.id for item in [*analysis.claims, *analysis.implications, *analysis.recommendations])
    analysis = replace(
        analysis,
        review_records=[
            ReviewRecord(
                review_id="review-vertical-slice",
                target_ids=review_target_ids,
                reviewed_state_revision=analysis.revision,
                input_fingerprint=build_material_fingerprint(analysis, review_target_ids),
                outcome=ReviewOutcome.ACCEPTED,
            )
        ],
    )
    store = AnalysisStore(Path(work_dir))
    pending = store.save_pending(analysis)
    committed = store.commit_revision(pending, expected_revision=pending.revision, accepted=True)
    write_report(report_path, committed)
    return VerticalSliceOutcome(True, ReviewResult(True, []), committed, report_path, "accepted")
