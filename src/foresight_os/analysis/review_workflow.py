from dataclasses import dataclass
from typing import Iterable

from foresight_os.analysis.evidence_workflow import attach_review_record
from foresight_os.analysis.reviewer import ReviewResult
from foresight_os.domain.challenge import ReviewCoverage, ReviewSlotStatus, derive_review_coverage
from foresight_os.domain.models import AnalysisState, RevisionStatus
from foresight_os.persistence.analysis_store import AnalysisStore


@dataclass(frozen=True)
class ReviewPhaseResult:
    state: AnalysisState
    review_ids: tuple[str, ...]
    coverage: tuple[ReviewCoverage, ...]
    status: str
    failure: str | None = None


@dataclass(frozen=True)
class AcceptanceResult:
    status: str
    state: AnalysisState
    coverage: tuple[ReviewCoverage, ...] = ()
    failure: str | None = None


def run_review_phase(
    store: AnalysisStore,
    state: AnalysisState,
    reviews: Iterable[tuple[str, ReviewResult, dict[str, object]]],
    *,
    required_check_ids: tuple[str, ...] = (),
    policy_id: str = "",
    policy_version: str = "",
) -> ReviewPhaseResult:
    reviewed = state
    review_ids = []
    try:
        for review_id, review, metadata in reviews:
            reviewed = attach_review_record(reviewed, review, review_id, **metadata)
            review_ids.append(review_id)
    except (TypeError, ValueError) as error:
        return ReviewPhaseResult(reviewed, tuple(review_ids), (), "failed", str(error))
    targets = tuple(item.id for collection in (reviewed.claims, reviewed.implications, reviewed.recommendations) for item in collection)
    coverage = derive_review_coverage(reviewed, targets, required_check_ids, policy_id=policy_id, policy_version=policy_version) if required_check_ids else ()
    status = "accepted" if all(item.complete for item in coverage) else "pending" if coverage else "completed"
    return ReviewPhaseResult(reviewed, tuple(review_ids), coverage, status)


def accept_pending_analysis(
    store: AnalysisStore,
    *,
    human_decision: str,
    state: AnalysisState | None = None,
    review: ReviewResult | None = None,
    required_check_ids: tuple[str, ...] = (),
    policy_id: str = "",
    policy_version: str = "",
    target_ids: tuple[str, ...] = (),
    expected_revision: int | None = None,
) -> AcceptanceResult:
    state = state or store.load_pending()
    if state.revision_status != RevisionStatus.PENDING_REVIEW:
        raise ValueError("analysis does not contain a pending review")
    if expected_revision is not None and state.revision != expected_revision:
        raise ValueError(f"stale analysis revision: expected {expected_revision}, pending {state.revision}")
    targets = target_ids or tuple(item.id for collection in (state.claims, state.implications, state.recommendations) for item in collection)
    coverage = derive_review_coverage(state, targets, required_check_ids, policy_id=policy_id, policy_version=policy_version) if required_check_ids else ()
    statuses = {status for coverage_item in coverage for _, status in coverage_item.statuses}
    if human_decision.upper() in {"PENDING", "PENDING_REVIEW"}:
        return AcceptanceResult("pending", state, coverage, "human acceptance is still pending")
    if human_decision.upper() != "ACCEPT":
        committed = store.commit_revision(state, expected_revision=state.revision, accepted=False)
        return AcceptanceResult("rejected", committed, coverage, "explicit acceptance was not granted")
    if ReviewSlotStatus.PENDING in statuses or ReviewSlotStatus.STALE in statuses:
        return AcceptanceResult("pending", state, coverage, "required review coverage is incomplete or stale")
    if ReviewSlotStatus.FAIL in statuses or ReviewSlotStatus.CONFLICT in statuses:
        committed = store.commit_revision(state, expected_revision=state.revision, accepted=False)
        return AcceptanceResult("rejected", committed, coverage, "required review coverage contains a blocking failure or conflict")
    if review is not None and not review.accepted:
        committed = store.commit_revision(state, expected_revision=state.revision, accepted=False)
        return AcceptanceResult("rejected", committed, coverage, "automated review did not accept the analysis")
    committed = store.commit_revision(state, expected_revision=state.revision, accepted=True)
    return AcceptanceResult("accepted", committed, coverage)


def review_and_accept_pending_analysis(
    store: AnalysisStore,
    state: AnalysisState,
    review: ReviewResult,
    review_id: str,
    *,
    human_decision: str,
    required_check_ids: tuple[str, ...] = (),
    policy_id: str = "",
    policy_version: str = "",
    target_ids: tuple[str, ...] = (),
    metadata: dict[str, object] | None = None,
) -> AcceptanceResult:
    metadata = dict(metadata or {})
    if required_check_ids:
        metadata.setdefault("target_ids", target_ids or tuple(item.id for collection in (state.claims, state.implications, state.recommendations) for item in collection))
    reviewed = attach_review_record(state, review, review_id, **metadata)
    result = accept_pending_analysis(
        store,
        state=reviewed,
        review=review,
        human_decision=human_decision,
        required_check_ids=required_check_ids,
        policy_id=policy_id,
        policy_version=policy_version,
        target_ids=target_ids,
        expected_revision=state.revision,
    )
    if result.status == "pending":
        reviewed = store.update_pending(reviewed)
        return AcceptanceResult("pending", reviewed, result.coverage, result.failure)
    return result
