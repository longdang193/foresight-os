from pathlib import Path

import pytest

from foresight_os.analysis.reviewer import ReviewResult
from foresight_os.analysis.review_workflow import AcceptanceResult
from foresight_os.domain.challenge import ReviewCheckResult, ReviewOutcome, ReviewSlotStatus
from foresight_os.persistence.analysis_store import AnalysisStore

from test_ncc_recipe_and_probe import make_analysis, run_probe


def test_ncc_validation_persists_decision_challenge_before_acceptance(tmp_path: Path):
    analysis_dir = make_analysis(tmp_path / "analysis")
    store = AnalysisStore(analysis_dir)
    store.save_pending(store.load_analysis())
    receipt = run_probe(tmp_path, analysis_dir=analysis_dir)
    decision_review = ReviewResult(
        accepted=True,
        issues=[],
        outcome=ReviewOutcome.ACCEPTED,
        policy_id=receipt["policy_id"],
        policy_version=receipt["policy_version"],
        skill_ids=("key-assumptions-check", "red-team-claim"),
        check_id="decision_challenge",
        method="human-or-authorized-reviewer-challenge",
        check_results=(
            ReviewCheckResult(
                "decision_challenge",
                ReviewSlotStatus.PASS,
                interpretation="bounded recommendation challenge completed",
            ),
        ),
    )

    from foresight_os.analysis.ncc_validation import persist_ncc_validation_reviews

    result = persist_ncc_validation_reviews(
        store,
        receipt,
        decision_review,
        reviewer_id="reviewer-ncc-1",
        execution_id="execution-ncc-1",
        attempt_id="attempt-ncc-1",
        human_decision="PENDING",
    )

    assert isinstance(result, AcceptanceResult)
    assert result.status == "pending"
    reloaded = AnalysisStore(analysis_dir).load_pending()
    assert reloaded.revision_status.value == "PENDING_REVIEW"
    assert {item.check_id for item in reloaded.review_records} == {
        "source_fidelity",
        "scope_reconciliation",
        "calculation_reconciliation",
        "decision_challenge",
    }
    decision_records = [item for item in reloaded.review_records if item.check_id == "decision_challenge"]
    assert len(decision_records) == 1
    assert decision_records[0].reviewer_id == "reviewer-ncc-1"
    assert decision_records[0].check_results[0].status == ReviewSlotStatus.PASS


def test_ncc_validation_rejects_receipt_for_a_different_pending_revision(tmp_path: Path):
    analysis_dir = make_analysis(tmp_path / "analysis")
    store = AnalysisStore(analysis_dir)
    store.save_pending(store.load_analysis())
    receipt = run_probe(tmp_path, analysis_dir=analysis_dir)
    receipt["state_revision"] += 1
    decision_review = ReviewResult(
        accepted=True,
        issues=[],
        outcome=ReviewOutcome.ACCEPTED,
        check_id="decision_challenge",
        method="authorized-reviewer-challenge",
        check_results=(ReviewCheckResult("decision_challenge", ReviewSlotStatus.PASS),),
    )

    from foresight_os.analysis.ncc_validation import persist_ncc_validation_reviews

    with pytest.raises(ValueError, match="does not match the pending revision"):
        persist_ncc_validation_reviews(
            store,
            receipt,
            decision_review,
            reviewer_id="reviewer-ncc-1",
            execution_id="execution-ncc-1",
            attempt_id="attempt-ncc-1",
        )

    assert not AnalysisStore(analysis_dir).load_pending().review_records


def test_ncc_validation_does_not_accept_without_required_decision_challenge(tmp_path: Path):
    analysis_dir = make_analysis(tmp_path / "analysis")
    store = AnalysisStore(analysis_dir)
    store.save_pending(store.load_analysis())
    receipt = run_probe(tmp_path, analysis_dir=analysis_dir)
    receipt["review_checks"] = [item for item in receipt["review_checks"] if item != "decision_challenge"]
    decision_review = ReviewResult(
        accepted=True,
        issues=[],
        outcome=ReviewOutcome.ACCEPTED,
        check_id="decision_challenge",
        method="authorized-reviewer-challenge",
        check_results=(ReviewCheckResult("decision_challenge", ReviewSlotStatus.PASS),),
    )

    from foresight_os.analysis.ncc_validation import persist_ncc_validation_reviews

    with pytest.raises(ValueError, match="must require decision_challenge"):
        persist_ncc_validation_reviews(
            store,
            receipt,
            decision_review,
            reviewer_id="reviewer-ncc-1",
            execution_id="execution-ncc-1",
            attempt_id="attempt-ncc-1",
            human_decision="ACCEPT",
        )

    assert not AnalysisStore(analysis_dir).load_pending().review_records


def test_ncc_validation_keeps_acceptance_pending_when_decision_challenge_is_pending(tmp_path: Path):
    analysis_dir = make_analysis(tmp_path / "analysis")
    store = AnalysisStore(analysis_dir)
    store.save_pending(store.load_analysis())
    receipt = run_probe(tmp_path, analysis_dir=analysis_dir)
    decision_review = ReviewResult(
        accepted=False,
        issues=[],
        outcome=ReviewOutcome.PROVISIONAL,
        check_id="decision_challenge",
        method="authorized-reviewer-challenge",
        check_results=(ReviewCheckResult("decision_challenge", ReviewSlotStatus.PENDING),),
    )

    from foresight_os.analysis.ncc_validation import persist_ncc_validation_reviews

    result = persist_ncc_validation_reviews(
        store,
        receipt,
        decision_review,
        reviewer_id="reviewer-ncc-1",
        execution_id="execution-ncc-1",
        attempt_id="attempt-ncc-1",
        human_decision="ACCEPT",
    )

    assert result.status == "pending"
    assert result.state.revision_status.value == "PENDING_REVIEW"
    assert all(
        status == ReviewSlotStatus.PENDING
        for coverage in result.coverage
        for check_id, status in coverage.statuses
        if check_id == "decision_challenge"
    )
    assert AnalysisStore(analysis_dir).load_pending().revision_status.value == "PENDING_REVIEW"
