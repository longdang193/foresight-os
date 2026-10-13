from dataclasses import replace

import pytest

from foresight_os.artifacts.report import render_report
from foresight_os.domain.challenge import (
    ReviewOutcome,
    ReviewRecord,
    accepted_consequential_recommendation,
    build_material_fingerprint,
    derive_finding_views,
)
from tests.test_review_records import make_state


def test_finding_view_is_derived_and_pending_without_a_valid_review():
    state = make_state()
    finding = derive_finding_views(state, ("claim-1",))[0]

    assert finding.review_status == "PENDING_REVIEW"
    assert not finding.accepted
    with pytest.raises(ValueError, match="accepted review"):
        render_report(replace(state, recommendations=[state.claims[0]]))


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
