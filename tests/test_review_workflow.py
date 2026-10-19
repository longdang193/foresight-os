from dataclasses import replace
from pathlib import Path

import pytest

from foresight_os.analysis.reviewer import ReviewResult
from foresight_os.analysis.review_workflow import (
    accept_pending_analysis,
    review_and_accept_pending_analysis,
)
from foresight_os.domain.challenge import (
    ReviewCheckResult,
    ReviewOutcome,
    ReviewSlotStatus,
    derive_finding_views,
)
from foresight_os.domain.models import RevisionStatus
from foresight_os.persistence.analysis_store import AnalysisStore
from tests.test_review_records import make_state


POLICY_ID = "independent-validation/v1"
POLICY_VERSION = "1"


def make_review(check_id: str, status: ReviewSlotStatus = ReviewSlotStatus.PASS, *, reviewer_id: str = "validator-a", attempt_id: str = "attempt-1") -> ReviewResult:
    accepted = status == ReviewSlotStatus.PASS
    return ReviewResult(
        accepted,
        [] if accepted else [f"{check_id} failed"],
        outcome=ReviewOutcome.ACCEPTED if accepted else ReviewOutcome.REJECTED,
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        check_id=check_id,
        method=f"{check_id}-independent",
        check_results=(ReviewCheckResult(check_id, status, expected=1, actual=1 if accepted else 2, delta=0 if accepted else 1, tolerance=0),),
        source_fingerprints=("source-sha",),
    )


def attach(store: AnalysisStore, pending, review: ReviewResult, review_id: str, *, reviewer_id: str = "validator-a", attempt_id: str = "attempt-1"):
    return review_and_accept_pending_analysis(
        store,
        pending,
        review,
        review_id,
        human_decision="PENDING",
        required_check_ids=(review.check_id,),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        metadata={
            "reviewer_id": reviewer_id,
            "execution_id": "execution-1",
            "attempt_id": attempt_id,
            "method": review.method,
        },
    )


def test_acceptance_stays_pending_when_required_category_is_missing(tmp_path: Path):
    store = AnalysisStore(tmp_path / "pending")
    pending = store.save_pending(make_state())
    result = attach(store, pending, make_review("source_fidelity"), "review-source")

    loaded = store.load_pending()
    final = accept_pending_analysis(
        store,
        state=loaded,
        human_decision="ACCEPT",
        required_check_ids=("source_fidelity", "calculation_reconciliation"),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        expected_revision=loaded.revision,
    )

    assert result.status == "pending"
    assert final.status == "pending"
    assert final.state.revision_status == RevisionStatus.PENDING_REVIEW
    assert final.coverage[0].statuses == (("source_fidelity", ReviewSlotStatus.PASS), ("calculation_reconciliation", ReviewSlotStatus.PENDING))
    assert store.stats.pending_write_count == 2


def test_complete_current_coverage_requires_explicit_human_acceptance(tmp_path: Path):
    store = AnalysisStore(tmp_path / "accepted")
    pending = store.save_pending(make_state())
    final = review_and_accept_pending_analysis(
        store,
        pending,
        make_review("source_fidelity"),
        "review-source",
        human_decision="ACCEPT",
        required_check_ids=("source_fidelity",),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        metadata={"reviewer_id": "validator-a", "execution_id": "execution-1", "attempt_id": "attempt-1", "method": "source-fidelity-independent"},
    )

    assert final.status == "accepted"
    assert final.state.revision_status == RevisionStatus.ACCEPTED
    assert final.coverage[0].complete
    assert store.stats.pending_write_count == 1
    assert store.stats.committed_write_count == 1


def test_blocking_check_rejects_and_persists_rejected_revision(tmp_path: Path):
    store = AnalysisStore(tmp_path / "failed")
    pending = store.save_pending(make_state())
    failed = attach(store, pending, make_review("calculation_reconciliation", ReviewSlotStatus.FAIL), "review-failed")

    assert failed.status == "pending"
    final = accept_pending_analysis(
        store,
        human_decision="ACCEPT",
        required_check_ids=("calculation_reconciliation",),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        expected_revision=pending.revision,
    )

    assert final.status == "rejected"
    assert final.state.revision_status == RevisionStatus.REJECTED
    assert final.coverage[0].statuses == (("calculation_reconciliation", ReviewSlotStatus.FAIL),)


def test_independent_same_slot_reviews_remain_conflicting(tmp_path: Path):
    store = AnalysisStore(tmp_path / "conflict")
    pending = store.save_pending(make_state())
    first = attach(store, pending, make_review("source_fidelity"), "review-a")
    assert first.status == "pending"
    second = attach(store, store.load_pending(), make_review("source_fidelity", ReviewSlotStatus.FAIL, reviewer_id="validator-b", attempt_id="attempt-2"), "review-b", reviewer_id="validator-b", attempt_id="attempt-2")
    assert second.status == "pending"

    final = accept_pending_analysis(
        store,
        human_decision="ACCEPT",
        required_check_ids=("source_fidelity",),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        expected_revision=pending.revision,
    )

    assert final.status == "rejected"
    assert final.coverage[0].statuses == (("source_fidelity", ReviewSlotStatus.CONFLICT),)


def test_stale_review_does_not_accept_changed_pending_state(tmp_path: Path):
    store = AnalysisStore(tmp_path / "stale")
    pending = store.save_pending(make_state())
    attached = attach(store, pending, make_review("source_fidelity"), "review-source")
    changed = replace(store.load_pending(), claims=[replace(store.load_pending().claims[0], statement="Changed claim")])
    store.update_pending(changed)

    final = accept_pending_analysis(
        store,
        human_decision="ACCEPT",
        required_check_ids=("source_fidelity",),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        expected_revision=changed.revision,
    )

    assert attached.status == "pending"
    assert final.status == "pending"
    assert final.coverage[0].statuses == (("source_fidelity", ReviewSlotStatus.STALE),)


def test_finding_view_cannot_hide_missing_required_review(tmp_path: Path):
    store = AnalysisStore(tmp_path / "finding")
    pending = store.save_pending(make_state())
    attached = attach(store, pending, make_review("source_fidelity"), "review-source")
    state = store.load_pending()
    finding = derive_finding_views(
        state,
        ("claim-1",),
        required_check_ids=("source_fidelity", "decision_challenge"),
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
    )[0]

    assert attached.status == "pending"
    assert not finding.accepted
    assert "decision_challenge" in " ".join(finding.unresolved_issues)


def test_wrong_revision_is_rejected_before_commit(tmp_path: Path):
    store = AnalysisStore(tmp_path / "revision")
    pending = store.save_pending(make_state())
    with pytest.raises(ValueError, match="stale analysis revision"):
        accept_pending_analysis(store, human_decision="ACCEPT", expected_revision=pending.revision + 1)
