from dataclasses import replace

import pytest

from foresight_os.artifacts.report import render_report
from foresight_os.domain.challenge import (
    ReviewOutcome,
    ReviewRecord,
    accepted_consequential_recommendation,
    build_material_fingerprint,
    derive_finding_views,
    finding_summary_status,
)
from tests.test_review_records import make_state


def test_finding_view_is_derived_and_pending_without_a_valid_review():
    state = make_state()
    finding = derive_finding_views(state, ("claim-1",))[0]

    assert finding.review_status == "PENDING_REVIEW"
    assert not finding.accepted
    with pytest.raises(ValueError, match="accepted review"):
        render_report(replace(state, recommendations=[state.claims[0]]))

    assert finding_summary_status(finding) == "human-review-pending"


def test_accepted_recommendation_requires_current_review_without_unresolved_objections():
    state = make_state()
    recommendation = replace(state.claims[0], id="recommendation-1", statement="Recommend action")
    target_ids = (recommendation.id,)
    review = ReviewRecord(
        "review-1",
        target_ids,
        state.revision,
        build_material_fingerprint(replace(state, recommendations=[recommendation], claims=[]), target_ids),
        outcome=ReviewOutcome.ACCEPTED,
    )
    reviewed = replace(state, claims=[], recommendations=[recommendation], review_records=[review])

    assert accepted_consequential_recommendation(reviewed, recommendation.id)
    assert derive_finding_views(reviewed, target_ids)[0].accepted


def test_finding_summary_distinguishes_supported_and_uncertain_results():
    state = make_state()
    claim = state.claims[0]
    fingerprint = build_material_fingerprint(state, (claim.id,))
    review = ReviewRecord(
        "review-1",
        (claim.id,),
        state.revision,
        fingerprint,
        outcome=ReviewOutcome.ACCEPTED,
        check_id="source_fidelity",
        reviewer_id="validator-a",
        execution_id="execution-1",
        attempt_id="attempt-1",
        method="source-fidelity",
    )
    reviewed = replace(state, review_records=[review])

    assert finding_summary_status(derive_finding_views(reviewed, (claim.id,))[0]) == "uncertain"
    supported = replace(reviewed, claims=[replace(claim, uncertainty=())], review_records=[])
    supported_review = replace(
        review,
        input_fingerprint=build_material_fingerprint(supported, (claim.id,)),
    )
    supported = replace(supported, review_records=[supported_review])
    assert finding_summary_status(derive_finding_views(supported, (claim.id,))[0]) == "supported"
