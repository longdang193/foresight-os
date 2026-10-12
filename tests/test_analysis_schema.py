from pathlib import Path

import pytest

from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Artifact,
    Assessment,
    Basis,
    Evidence,
    Invalidation,
    Lifecycle,
    Relationship,
    Revision,
    SourceLocator,
    WorkBrief,
)
from foresight_os.domain.validation import ValidationError, validate_analysis, validate_work_brief


def locator() -> SourceLocator:
    return SourceLocator("case-v1", "Demand", "A2:F3", "index", "none", "demand - capacity")


def state() -> AnalysisState:
    evidence = Evidence("evidence-1", locator(), "case-v1", "2030-01-01", "140 demand; 115 capacity")
    claim = AnalyticalRecord("claim-1", "Demand exceeds capacity.", Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=[evidence.id])
    recommendation = AnalyticalRecord("recommendation-1", "Validate expansion cost.", Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=[evidence.id])
    relationship = Relationship("relationship-1", evidence.id, claim.id, "supports")
    claim = AnalyticalRecord(claim.id, claim.statement, claim.basis, claim.assessment, evidence_ids=[evidence.id], relationship_ids=[relationship.id])
    revision = Revision("revision-1", 1, "initial analysis", [evidence.id, claim.id, recommendation.id, relationship.id])
    return AnalysisState(
        "case-001",
        1,
        evidence=[evidence],
        claims=[claim],
        recommendations=[recommendation],
        relationships=[relationship],
        revisions=[revision],
        invalidation=Invalidation(),
    )


def test_valid_analysis_and_work_brief_validate():
    assert validate_analysis(state())["investigation_id"] == "case-001"
    brief = WorkBrief("case-001", "Should investment increase?", ["Northern Europe"], ["report"], ["2030"], [], "Assess capacity.", "Review contradiction.")
    assert validate_work_brief(brief)["investigation_id"] == "case-001"


def test_invalid_locator_and_relationship_fail():
    invalid = state().to_dict()
    invalid["evidence"][0]["source_locator"].pop("sheet")
    with pytest.raises(ValidationError):
        validate_analysis(invalid)

    invalid = state().to_dict()
    invalid["relationships"][0]["to_id"] = "missing"
    with pytest.raises(ValidationError):
        validate_analysis(invalid)


def test_duplicate_ids_and_malformed_revisions_fail():
    invalid = state().to_dict()
    invalid["claims"].append(invalid["claims"][0])
    with pytest.raises(ValidationError):
        validate_analysis(invalid)

    invalid = state().to_dict()
    invalid["revisions"][0]["number"] = 2
    with pytest.raises(ValidationError):
        validate_analysis(invalid)
