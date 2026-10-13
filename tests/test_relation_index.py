from foresight_os.domain.models import AnalysisState, AnalyticalRecord, Assessment, Basis, Evidence, Relationship, SourceLocator
from foresight_os.domain.relationships import RelationIndex


def test_relation_index_material_and_impact_closures_follow_relation_semantics():
    evidence = Evidence("evidence-1", SourceLocator("v1", "Sheet", "A1", "units", "none", "source"), "v1", "2030", "observed")
    claim = AnalyticalRecord("claim-1", "claim", Basis.OBSERVED, Assessment.SUPPORTED, evidence_ids=[evidence.id])
    recommendation = AnalyticalRecord("recommendation-1", "recommendation", Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=[])
    state = AnalysisState(
        "relations",
        1,
        evidence=[evidence],
        claims=[claim],
        recommendations=[recommendation],
        relationships=[
            Relationship("supports-claim", evidence.id, claim.id, "supports"),
            Relationship("supports-recommendation", claim.id, recommendation.id, "supports"),
            Relationship("depends-on", recommendation.id, claim.id, "depends_on"),
        ],
    )

    index = RelationIndex.from_state(state)

    assert index.material_closure((recommendation.id,)) == ("claim-1", "evidence-1", "recommendation-1")
    assert index.impact_closure((evidence.id,)) == ("claim-1", "evidence-1", "recommendation-1")
    assert index.support_context((recommendation.id,)) == ("claim-1", "evidence-1")


def test_relation_index_counterevidence_context_is_recursive_and_excludes_targets():
    state = AnalysisState(
        "relations",
        1,
        relationships=[
            Relationship("counter-1", "evidence-1", "claim-1", "contradicts"),
            Relationship("counter-2", "claim-1", "recommendation-1", "contradicts"),
        ],
    )

    assert RelationIndex.from_state(state).counterevidence_context(("recommendation-1",)) == ("claim-1", "evidence-1")
