from pathlib import Path

import pytest

from foresight_os.analysis.reviewer import review_reasoning
from foresight_os.domain.models import AnalyticalRecord, Assessment, Basis, Evidence, SourceLocator
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_vertical_slice_requires_human_acceptance(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=False)

    assert not outcome.accepted
    assert outcome.analysis is None
    assert outcome.report_path is None
    assert outcome.status == "human_review"


def test_vertical_slice_routes_budget_exhaustion_to_human_boundary(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True, total_agent_calls=4)

    assert not outcome.accepted
    assert outcome.status == "exhausted"
    assert "no accepted recommendation" in outcome.review.issues[0]


def test_vertical_slice_persists_accepted_analysis_and_report(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)

    assert outcome.accepted
    assert outcome.review.accepted
    assert outcome.report_path is not None
    assert (tmp_path / "case-001" / "analysis.json").exists()


def test_invalid_workbook_boundary_and_contradictory_record_are_rejected(tmp_path: Path):
    invalid_workbook = tmp_path / "invalid.csv"
    invalid_workbook.write_text("wrong,columns\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        run_vertical_slice(invalid_workbook, tmp_path / "invalid-case", human_accept=True)

    evidence = [
        Evidence(
            "evidence-1",
            SourceLocator("v1", "Capacity", "A2:F3", "index", "none", "source value"),
            "v1",
            "2030-01-01",
            "capacity trails demand",
        )
    ]
    record = AnalyticalRecord(
        "recommendation-1",
        "Increase investment immediately despite the capacity constraint.",
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=["evidence-1"],
    )
    review = review_reasoning(evidence, [record])
    assert not review.accepted
    assert "capacity contradiction" in review.issues[0]
