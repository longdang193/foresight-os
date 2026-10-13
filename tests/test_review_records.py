from dataclasses import replace
import asyncio
from pathlib import Path

from foresight_os.domain.challenge import (
    ChallengeObjection,
    ObjectionDisposition,
    ReviewOutcome,
    ReviewRecord,
    ReviewValidity,
    build_material_fingerprint,
    review_validity,
    select_review_record,
)
from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Assessment,
    Basis,
    CalculationRecord,
    Evidence,
    Invalidation,
    Revision,
    SourceLocator,
    MeasurementKey,
    Relationship,
)
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.analysis.reviewer import review_reasoning_with_skills
from foresight_os.controller.skills import SkillRegistry


def make_state() -> AnalysisState:
    evidence = Evidence("evidence-1", SourceLocator("v1", "Sheet", "A1", "units", "none", "source"), "v1", "2030", "observed")
    claim = AnalyticalRecord(
        "claim-1",
        "A claim",
        Basis.OBSERVED,
        Assessment.SUPPORTED,
        evidence_ids=[evidence.id],
        assumptions=("the source remains current",),
        uncertainty=("scope is limited",),
    )
    return AnalysisState(
        "review-case",
        1,
        evidence=[evidence],
        claims=[claim],
        revisions=[Revision("revision-1", 1, "initial", [evidence.id, claim.id])],
        invalidation=Invalidation(),
    )


def test_material_fingerprint_ignores_global_revision_and_unrelated_inputs():
    state = make_state()
    fingerprint = build_material_fingerprint(state, ("claim-1",), ("key-assumptions-check",))
    assert review_validity(state, ReviewRecord("review-1", ("claim-1",), 1, fingerprint, ("key-assumptions-check",))) == ReviewValidity.CURRENT

    revised = replace(state, revision=2)
    assert build_material_fingerprint(revised, ("claim-1",), ("key-assumptions-check",)) == fingerprint

    unrelated = replace(
        state,
        evidence=[*state.evidence, Evidence("unrelated", SourceLocator("v1", "Sheet", "B1", "units", "none", "source"), "v1", "2030", "unrelated")],
    )
    assert build_material_fingerprint(unrelated, ("claim-1",), ("key-assumptions-check",)) == fingerprint


def test_material_input_changes_stale_review_and_selection_is_deterministic():
    state = make_state()
    fingerprint = build_material_fingerprint(state, ("claim-1",), ())
    review = ReviewRecord(
        "review-2",
        ("claim-1",),
        1,
        fingerprint,
        objections=(ChallengeObjection("scope", "claim-1", "scope is narrow", disposition=ObjectionDisposition.REJECTED),),
        outcome=ReviewOutcome.ACCEPTED,
    )
    current = replace(state, review_records=[review])
    assert select_review_record(current, ("claim-1",)) == review
    changed = replace(current, claims=[replace(current.claims[0], uncertainty=("new uncertainty",))])
    assert review_validity(changed, review) == ReviewValidity.STALE
    assert select_review_record(changed, ("claim-1",)) is None


def test_review_record_round_trips_through_analysis_store(tmp_path: Path):
    state = make_state()
    fingerprint = build_material_fingerprint(state, ("claim-1",), ("red-team-claim",))
    state = replace(
        state,
        review_records=[ReviewRecord("review-1", ("claim-1",), 1, fingerprint, ("red-team-claim",), ("1.0.0",))],
    )
    store = AnalysisStore(tmp_path / "review-case")
    store.save_analysis(state)

    loaded = store.load_analysis()
    assert loaded.review_records == state.review_records
    assert loaded.claims[0].assumptions == state.claims[0].assumptions


def test_material_inputs_include_calculation_chain_and_missing_inputs():
    state = make_state()
    state = replace(
        state,
        calculations=[
            CalculationRecord(
                "calculation-1",
                MeasurementKey("scope", "measure", "2030", "units"),
                "evidence-1 + missing-input",
                ["evidence-1", "missing-input"],
                1.0,
                "units",
                ["A1"],
            )
        ],
    )
    from foresight_os.domain.challenge import collect_material_inputs

    material = collect_material_inputs(state, ("claim-1",))
    assert "calculation-1" in material["calculations"]
    assert material["missing_inputs"] == ("missing-input",)


def test_material_inputs_recurse_through_supporting_claims_and_preserve_provenance():
    state = make_state()
    supporting = replace(
        state.claims[0],
        id="claim-supporting",
        statement="Supporting claim",
        assumptions=("support assumption",),
        uncertainty=("support uncertainty",),
    )
    recommendation = AnalyticalRecord(
        "recommendation-1",
        "Recommendation",
        Basis.DERIVED,
        Assessment.SUPPORTED,
    )
    state = replace(
        state,
        claims=[supporting],
        recommendations=[recommendation],
        relationships=[
            Relationship("support-claim", supporting.id, recommendation.id, "supports"),
            Relationship("support-evidence", state.evidence[0].id, supporting.id, "supports"),
        ],
    )

    from foresight_os.domain.challenge import collect_material_inputs

    material = collect_material_inputs(state, (recommendation.id,))
    assert set(material["records"]) == {recommendation.id, supporting.id}
    assert material["evidence"] == {state.evidence[0].id: state.evidence[0]}
    assert material["assumptions"] == ("support assumption",)
    assert material["uncertainty"] == ("support uncertainty",)
    assert material["provenance"] == {"direct": (recommendation.id,), "derived": (supporting.id,)}


def test_selected_review_skills_produce_validated_typed_objections():
    class FakeExecutor:
        async def execute(self, prompt):
            assert "ChallengeObjection" in prompt
            return {
                "objections": [
                    {
                        "kind": "UNSUPPORTED_ASSUMPTION",
                        "target_id": "claim-1",
                        "statement": "The scope assumption is untested.",
                        "disposition": "UNRESOLVED",
                    }
                ]
            }

    state = make_state()
    policy = type(
        "Policy",
        (),
        {
            "policy_id": "policy-1",
            "version": "1",
            "required_skill_ids": ("red-team-claim",),
            "acceptable_outcomes": ("ACCEPTED",),
            "blocking_objection_kinds": (),
        },
    )()
    review = asyncio.run(
        review_reasoning_with_skills(
            state.evidence,
            state.claims,
            policy=policy,
            executor=FakeExecutor(),
        )
    )

    assert review.accepted
    assert review.skill_ids == ("red-team-claim",)
    registry = SkillRegistry()
    assert review.skill_versions == (registry.manifest("red-team-claim").version,)
    assert review.skill_hashes
    assert review.objections[-1].kind == "UNSUPPORTED_ASSUMPTION"
