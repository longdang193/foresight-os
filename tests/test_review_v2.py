import json
from dataclasses import replace

import pytest

from foresight_os.analysis.evidence_workflow import attach_review_record
from foresight_os.analysis.reviewer import ReviewResult
from foresight_os.domain.challenge import (
    ReviewCheckResult,
    ReviewOutcome,
    ReviewSlotStatus,
    build_material_fingerprint,
    derive_review_coverage,
    review_validity,
)
from foresight_os.persistence.analysis_store import AnalysisStore

from test_review_records import make_state


def typed_review(*, reviewer_id: str, attempt_id: str, source_fingerprint: str = "source-sha") -> ReviewResult:
    return ReviewResult(
        True,
        [],
        outcome=ReviewOutcome.ACCEPTED,
        policy_id="independent-validation/v1",
        policy_version="1",
        check_id="source_fidelity",
        method="source-read",
        check_results=(
            ReviewCheckResult(
                "source_fidelity",
                ReviewSlotStatus.PASS,
                expected=source_fingerprint,
                actual=source_fingerprint,
                source_ids=("evidence-1",),
                interpretation="source fingerprint matches",
            ),
        ),
        source_fingerprints=(source_fingerprint,),
    )


def attach_typed(state, review_id: str, *, reviewer_id: str, attempt_id: str, source_fingerprint: str = "source-sha", slot_key: str = "slot-1"):
    return attach_review_record(
        state,
        typed_review(reviewer_id=reviewer_id, attempt_id=attempt_id, source_fingerprint=source_fingerprint),
        review_id,
        target_ids=("claim-1",),
        reviewer_id=reviewer_id,
        execution_id="execution-1",
        attempt_id=attempt_id,
        slot_key=slot_key,
    )


def test_typed_attachment_requires_explicit_targets_and_round_trips(tmp_path):
    state = make_state()
    review = typed_review(reviewer_id="validator-a", attempt_id="attempt-1")

    attached = attach_review_record(
        state,
        review,
        "review-v2",
        target_ids=("claim-1",),
        reviewer_id="validator-a",
        execution_id="execution-1",
        attempt_id="attempt-1",
    )
    store = AnalysisStore(tmp_path / "round-trip")
    store.save_analysis(attached)
    reloaded = store.load_analysis()

    record = reloaded.review_records[0]
    assert record.target_ids == ("claim-1",)
    assert record.check_id == "source_fidelity"
    assert record.reviewer_id == "validator-a"
    assert record.check_results[0].status == ReviewSlotStatus.PASS
    assert not record.is_legacy


def test_typed_attachment_rejects_empty_targets():
    with pytest.raises(ValueError, match="at least one target"):
        attach_review_record(
            make_state(),
            typed_review(reviewer_id="validator-a", attempt_id="attempt-1"),
            "review-v2",
            target_ids=(),
            reviewer_id="validator-a",
            execution_id="execution-1",
            attempt_id="attempt-1",
        )


def test_legacy_attachment_is_readable_but_does_not_cover_typed_slots():
    state = make_state()
    legacy = attach_review_record(state, ReviewResult(True, [], outcome=ReviewOutcome.ACCEPTED), "legacy-review")

    assert legacy.review_records[0].is_legacy
    coverage = derive_review_coverage(legacy, ("claim-1",), ("source_fidelity",))
    assert coverage[0].statuses == (("source_fidelity", ReviewSlotStatus.PENDING),)
    assert not coverage[0].complete


def test_source_fingerprint_change_makes_typed_review_stale():
    state = attach_typed(make_state(), "review-v2", reviewer_id="validator-a", attempt_id="attempt-1")
    review = state.review_records[0]
    assert review_validity(state, review).value == "CURRENT"

    changed = replace(review, source_fingerprints=("changed-source-sha",))
    assert review_validity(state, changed).value == "STALE"


def test_retry_supersedes_same_slot_and_replay_is_idempotent():
    first = attach_typed(make_state(), "review-1", reviewer_id="validator-a", attempt_id="attempt-1")
    second = attach_typed(first, "review-2", reviewer_id="validator-a", attempt_id="attempt-2")

    assert second.review_records[0].superseded_by_review_id == "review-2"
    assert second.review_records[1].supersedes_review_id is None
    assert attach_typed(second, "review-2", reviewer_id="validator-a", attempt_id="attempt-2") == second


def test_independent_same_slot_reviews_remain_conflicting():
    first = attach_typed(make_state(), "review-1", reviewer_id="validator-a", attempt_id="attempt-1")
    second = attach_typed(first, "review-2", reviewer_id="validator-b", attempt_id="attempt-1")

    assert second.review_records[0].conflict_review_ids == ("review-2",)
    assert second.review_records[1].conflict_review_ids == ("review-1",)
    coverage = derive_review_coverage(second, ("claim-1",), ("source_fidelity",))
    assert coverage[0].statuses == (("source_fidelity", ReviewSlotStatus.CONFLICT),)


def test_material_fingerprint_accepts_separate_dependency_fingerprints():
    state = make_state()
    fingerprint = build_material_fingerprint(
        state,
        ("claim-1",),
        source_fingerprints=("source-sha",),
        dependency_fingerprints=(("Sheet!A1:B2", "range-sha"),),
    )
    assert fingerprint


def test_schema_v1_review_records_migrate_as_legacy(tmp_path):
    value = make_state().to_dict()
    value["schema_version"] = 1
    value["review_records"] = [{
        "review_id": "legacy-review",
        "target_ids": ["claim-1"],
        "reviewed_state_revision": 1,
        "input_fingerprint": "legacy-fingerprint",
        "skill_ids": [],
        "skill_versions": [],
        "objections": [],
        "outcome": "ACCEPTED",
        "limitations": [],
        "unresolved_issues": [],
    }]
    store = AnalysisStore(tmp_path / "migration")
    store.analysis_path.parent.mkdir(parents=True, exist_ok=True)
    store.analysis_path.write_text(json.dumps(value), encoding="utf-8")

    migrated = store.load_analysis()
    assert migrated.schema_version == 2
    assert migrated.review_records[0].is_legacy
