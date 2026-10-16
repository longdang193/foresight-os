from __future__ import annotations

from pathlib import Path

import pytest

from foresight_os.analysis.foresight_validator import validate_exercises, run_validator_workflow
from foresight_os.analysis.powerbi_strategic_portfolio import (
    analyze_powerbi_strategic_portfolio,
    run_powerbi_strategic_portfolio_workflow,
)
from foresight_os.analysis.portfolio_resilience import analyze_portfolio_resilience
from foresight_os.analysis.technology_radar import analyze_technology_radar, run_technology_radar_workflow
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import WorkBrief
from foresight_os.persistence.analysis_store import AnalysisStore


ROOT = Path(__file__).parents[1]
EXERCISE = ROOT / "tests" / "fixtures" / "exercise"


def test_technology_radar_deduplicates_source_families_and_assigns_actions():
    analysis = analyze_technology_radar(EXERCISE / "04_Technology_Radar.xlsx")

    assert {item.kind for item in analysis.data_quality_issues} >= {"DUPLICATE_SOURCE_FAMILY", "NAIVE_SCORE_RISK"}
    ai = next(item for item in analysis.assessments if item.technology == "AI Engineering Copilots")
    assert ai.independent_source_families < ai.signal_count
    assert next(item for item in analysis.assessments if item.technology == "SiC Power Electronics").action_category == "Invest"
    assert next(item for item in analysis.assessments if item.technology == "AI Engineering Copilots").action_category == "Experiment"
    assert next(item for item in analysis.assessments if item.technology == "Solid-State Batteries").action_category == "Monitor"


@pytest.mark.parametrize(
    ("analyzer", "filename", "quality_claim_id"),
    [
        (analyze_technology_radar, "04_Technology_Radar.xlsx", "technology-data-quality"),
        (analyze_powerbi_strategic_portfolio, "05_PowerBI_Strategic_Portfolio.xlsx", "powerbi-data-quality"),
    ],
)
def test_data_quality_claim_uses_string_evidence_ids(analyzer, filename: str, quality_claim_id: str):
    analysis = analyzer(EXERCISE / filename)

    claim = next(item for item in analysis.state.claims if item.id == quality_claim_id)
    evidence_ids = {item.id for item in analysis.state.evidence}
    assert claim.evidence_ids
    assert set(claim.evidence_ids).issubset(evidence_ids)


def test_portfolio_revenue_keeps_valid_row_with_missing_cost_as_provisional():
    analysis = analyze_portfolio_resilience(EXERCISE / "01_Portfolio_Resilience.xlsx")

    assert sum(item.revenue for item in analysis.segment_baselines) == pytest.approx(26058685.30, abs=0.01)
    assert any(item.kind == "MISSING_COST" for item in analysis.data_quality_issues)


def test_technology_workflow_persists_reviewed_report(tmp_path: Path):
    result = run_technology_radar_workflow(
        AnalysisStore(tmp_path / "case"),
        EXERCISE / "04_Technology_Radar.xlsx",
        human_decision="ACCEPT",
    )

    assert result.status == "accepted"
    assert result.report_path is not None and result.report_path.exists()
    assert all(item.accepted for item in derive_finding_views(result.analysis))
    report = result.report_path.read_text(encoding="utf-8")
    for section in ["Signal quality", "Competing hypotheses", "Alternative futures", "Action category", "Signposts"]:
        assert section in report


def test_powerbi_recipe_reconciles_comparable_period_and_flags_model_risks():
    analysis = analyze_powerbi_strategic_portfolio(EXERCISE / "05_PowerBI_Strategic_Portfolio.xlsx")

    assert {item.kind for item in analysis.data_quality_issues} >= {
        "DUPLICATE_FACT",
        "MISSING_TARGET",
        "STALE_REFRESH",
        "FILTER_CONTEXT_TRAP",
        "CONTRADICTORY_FORWARD_SIGNAL",
    }
    assert analysis.revenue_2025_jan_sep == pytest.approx(92897572.18, abs=0.01)
    assert analysis.revenue_2026_jan_sep == pytest.approx(100574681.8, abs=0.01)
    assert analysis.yoy_revenue_growth == pytest.approx(0.082641, abs=0.00001)
    assert "stage" in analysis.recommendation.lower()


def test_powerbi_workflow_persists_reviewed_report(tmp_path: Path):
    result = run_powerbi_strategic_portfolio_workflow(
        AnalysisStore(tmp_path / "case"),
        EXERCISE / "05_PowerBI_Strategic_Portfolio.xlsx",
        human_decision="ACCEPT",
    )

    assert result.status == "accepted"
    assert result.report_path is not None and result.report_path.exists()
    assert all(item.accepted for item in derive_finding_views(result.analysis))
    report = result.report_path.read_text(encoding="utf-8")
    for section in ["Reconciled KPIs", "Filter-context checks", "Contradiction analysis", "Monitoring signposts"]:
        assert section in report


def test_validator_key_reconciles_all_completed_exercises():
    result = validate_exercises(EXERCISE / "06_ForesightOS_Validator_Key.xlsx", EXERCISE)

    assert result.all_passed
    assert {item.exercise for item in result.checks} >= {"Portfolio", "Supplier", "EV", "Technology", "Power BI"}
    assert not result.failures


def test_validator_workflow_persists_reviewed_report(tmp_path: Path):
    result = run_validator_workflow(
        AnalysisStore(tmp_path / "case"),
        EXERCISE / "06_ForesightOS_Validator_Key.xlsx",
        EXERCISE,
        human_decision="ACCEPT",
    )

    assert result.status == "accepted"
    assert result.report_path is not None and result.report_path.exists()
    assert all(item.accepted for item in derive_finding_views(result.analysis))


def test_validator_workflow_preserves_legacy_brief_defaults(tmp_path: Path):
    store = AnalysisStore(tmp_path / "legacy")
    store.save_brief(
        WorkBrief(
            "legacy-validator",
            "Validate the exercise workbooks",
            [],
            ["validation report"],
            [],
            [],
            "assess",
            "execute",
        )
    )

    result = run_validator_workflow(
        store,
        EXERCISE / "06_ForesightOS_Validator_Key.xlsx",
        EXERCISE,
        human_decision="PENDING",
    )

    assert result.status == "pending"
