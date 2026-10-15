from __future__ import annotations

from typing import Any, Mapping

from foresight_os.analysis.reviewer import ReviewResult
from foresight_os.analysis.review_workflow import AcceptanceResult, accept_pending_analysis, run_review_phase
from foresight_os.domain.challenge import ReviewCheckResult, ReviewOutcome, ReviewSlotStatus
from foresight_os.domain.models import RevisionStatus
from foresight_os.persistence.analysis_store import AnalysisStore


def _status(value: Any) -> ReviewSlotStatus:
    text = str(value)
    if text.startswith("ReviewSlotStatus."):
        text = text.split(".", 1)[1]
    return ReviewSlotStatus(text)


def _review_from_receipt(
    receipt: Mapping[str, Any],
    check_id: str,
    checks: list[Mapping[str, Any]],
) -> ReviewResult:
    results = tuple(
        ReviewCheckResult(
            check_id=check_id,
            status=_status(item.get("status", ReviewSlotStatus.PENDING.value)),
            expected=item.get("expected"),
            actual=item.get("actual"),
            delta=item.get("delta"),
            tolerance=item.get("tolerance"),
            source_ids=tuple(str(value) for value in item.get("source_ids", ())),
            input_ids=tuple(str(value) for value in item.get("input_ids", ())),
            interpretation="independent NCC validation receipt",
            limitations=tuple(str(value) for value in item.get("limitations", ())),
        )
        for item in checks
    )
    passed = bool(results) and all(item.status == ReviewSlotStatus.PASS for item in results)
    limitations = tuple(value for item in results for value in item.limitations)
    return ReviewResult(
        accepted=passed,
        issues=[] if passed else list(limitations),
        outcome=ReviewOutcome.ACCEPTED if passed else ReviewOutcome.REJECTED,
        policy_id=str(receipt.get("policy_id", "")),
        policy_version=str(receipt.get("policy_version", "")),
        check_id=check_id,
        method="independent-workbook-validation",
        check_results=results,
    )


def _decision_review(review: ReviewResult, receipt: Mapping[str, Any]) -> ReviewResult:
    if review.check_id != "decision_challenge":
        raise ValueError("NCC decision review must use the decision_challenge check")
    if not review.method:
        raise ValueError("NCC decision review requires a method")
    if not review.check_results:
        status = ReviewSlotStatus.PASS if review.accepted else ReviewSlotStatus.FAIL
        result = ReviewCheckResult(
            check_id="decision_challenge",
            status=status,
            interpretation="authorized reviewer decision challenge",
            limitations=tuple(review.issues),
        )
        review = ReviewResult(
            accepted=review.accepted,
            issues=list(review.issues),
            corrected=review.corrected,
            objections=review.objections,
            outcome=review.outcome,
            policy_id=review.policy_id,
            policy_version=review.policy_version,
            skill_ids=review.skill_ids,
            skill_versions=review.skill_versions,
            skill_hashes=review.skill_hashes,
            check_id=review.check_id,
            method=review.method,
            check_results=(result,),
            source_fingerprints=review.source_fingerprints,
            dependency_fingerprints=review.dependency_fingerprints,
        )
    if not review.policy_id:
        review = ReviewResult(
            accepted=review.accepted,
            issues=list(review.issues),
            corrected=review.corrected,
            objections=review.objections,
            outcome=review.outcome,
            policy_id=str(receipt.get("policy_id", "")),
            policy_version=review.policy_version or str(receipt.get("policy_version", "")),
            skill_ids=review.skill_ids,
            skill_versions=review.skill_versions,
            skill_hashes=review.skill_hashes,
            check_id=review.check_id,
            method=review.method,
            check_results=review.check_results,
            source_fingerprints=review.source_fingerprints,
            dependency_fingerprints=review.dependency_fingerprints,
        )
    return review


def persist_ncc_validation_reviews(
    store: AnalysisStore,
    receipt: Mapping[str, Any],
    decision_review: ReviewResult,
    *,
    reviewer_id: str,
    execution_id: str,
    attempt_id: str,
    human_decision: str = "PENDING",
) -> AcceptanceResult:
    state = store.load_pending()
    if state.revision_status != RevisionStatus.PENDING_REVIEW:
        raise ValueError("NCC validation requires a pending review state")
    if int(receipt.get("state_revision", -1)) != state.revision:
        raise ValueError("NCC validation receipt does not match the pending revision")
    target_ids = tuple(str(item) for item in receipt.get("target_record_ids", ()))
    known_ids = {
        item.id
        for collection in (state.claims, state.implications, state.recommendations, state.calculations)
        for item in collection
    }
    if not target_ids or not set(target_ids).issubset(known_ids):
        raise ValueError("NCC validation receipt has invalid target_record_ids")

    required_check_ids = tuple(str(item) for item in receipt.get("review_checks", ()))
    if "decision_challenge" not in required_check_ids:
        raise ValueError("NCC validation receipt must require decision_challenge")
    checks_by_id: dict[str, list[Mapping[str, Any]]] = {check_id: [] for check_id in required_check_ids}
    for item in receipt.get("checks", ()):
        check_id = str(item.get("check_id", ""))
        if check_id in checks_by_id:
            checks_by_id[check_id].append(item)
    decision_review = _decision_review(decision_review, receipt)
    source_fingerprints = tuple(
        value for value in (str(receipt.get("workbook_sha256", "")),) if value
    )
    dependency_fingerprints = (
        ("review-spec", str(receipt.get("execution_recipe_fingerprint", ""))),
    ) if receipt.get("execution_recipe_fingerprint") else ()
    reviews = []
    metadata = {
        "target_ids": target_ids,
        "source_fingerprints": source_fingerprints,
        "dependency_fingerprints": dependency_fingerprints,
    }
    for check_id in required_check_ids:
        review = decision_review if check_id == "decision_challenge" else _review_from_receipt(receipt, check_id, checks_by_id[check_id])
        reviews.append(
            (
                f"ncc-validation-{state.revision}-{check_id}",
                review,
                {
                    **metadata,
                    "check_id": check_id,
                    "reviewer_id": reviewer_id if check_id == "decision_challenge" else "independent-validation",
                    "execution_id": execution_id,
                    "attempt_id": attempt_id,
                    "method": review.method,
                },
            )
        )
    phase = run_review_phase(
        store,
        state,
        reviews,
        required_check_ids=required_check_ids,
        policy_id=str(receipt.get("policy_id", "")),
        policy_version=str(receipt.get("policy_version", "")),
    )
    if phase.status == "failed":
        raise ValueError(phase.failure or "NCC review persistence failed")
    reviewed = store.update_pending(phase.state)
    return accept_pending_analysis(
        store,
        state=reviewed,
        human_decision=human_decision,
        required_check_ids=required_check_ids,
        policy_id=str(receipt.get("policy_id", "")),
        policy_version=str(receipt.get("policy_version", "")),
        target_ids=target_ids,
        expected_revision=reviewed.revision,
    )
