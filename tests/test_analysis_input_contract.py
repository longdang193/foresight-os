from pathlib import Path

import pytest

from foresight_os.analysis.supplier_resilience import analyze_supplier_resilience
from foresight_os.analysis.portfolio_resilience import analyze_portfolio_resilience
from foresight_os.analysis.powerbi_strategic_portfolio import analyze_powerbi_strategic_portfolio
from foresight_os.domain.analysis_inputs import AnalysisInputContract, normalize_work_brief
from foresight_os.domain.models import WorkBrief
from foresight_os.domain.validation import ValidationError, validate_work_brief


def _brief(**analysis_inputs):
    return WorkBrief(
        "contract-test",
        "Which inputs should be assessed?",
        [],
        ["analysis"],
        [],
        [],
        "assess",
        "execute",
        analysis_inputs=analysis_inputs,
    )


def test_analysis_input_contract_round_trips_and_fingerprints_deterministically():
    contract = AnalysisInputContract(
        domain="supplier_resilience",
        required_tables=("Supplier_Master",),
        periods=("2026",),
        reporting_currency="EUR",
        conversion_rates={"USD": 0.92, "EUR": 1.0},
        assumptions=("legacy compatibility",),
    )
    value = validate_work_brief(_brief(supplier_resilience=contract.to_dict()))
    normalized = normalize_work_brief(value)

    assert normalized.contract_for_domain("supplier_resilience") == contract
    assert normalized.contract_for_domain("supplier_resilience").fingerprint == contract.fingerprint
    assert validate_work_brief(value)["analysis_inputs"][0]["domain"] == "supplier_resilience"


def test_invalid_contract_policy_is_rejected_before_analysis():
    with pytest.raises((ValidationError, ValueError), match="duplicate policy"):
        validate_work_brief(_brief(supplier_resilience={"domain": "supplier_resilience", "duplicate_policy": "invented"}))


def test_explicit_incomplete_supplier_conversion_does_not_use_legacy_fx():
    source = Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx")
    analysis = analyze_supplier_resilience(
        source,
        AnalysisInputContract(
            domain="supplier_resilience",
            conversion_rates={"EUR": 1.0},
            reporting_currency="EUR",
        ),
    )

    assert any(issue.kind == "UNSUPPORTED_CONVERSION" for issue in analysis.data_quality_issues)


def test_legacy_supplier_contract_retains_documented_fx_assumption():
    analysis = analyze_supplier_resilience(Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx"))

    assert any("USD=0.92" in assumption for assumption in analysis.assumptions)


def test_explicit_empty_supplier_conversion_map_never_uses_legacy_rates():
    analysis = analyze_supplier_resilience(
        Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx"),
        AnalysisInputContract(domain="supplier_resilience", reporting_currency="EUR"),
    )

    assert any(issue.kind == "UNSUPPORTED_CONVERSION" for issue in analysis.data_quality_issues)


def test_supplier_entity_scope_and_reject_policy_are_enforced():
    source = Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx")
    scoped = analyze_supplier_resilience(source, AnalysisInputContract(domain="supplier_resilience", entity_scope=("DOES_NOT_EXIST",)))
    assert "EMPTY_ENTITY_SCOPE" in {issue.kind for issue in scoped.data_quality_issues}
    with pytest.raises(ValueError, match="duplicate policy reject"):
        analyze_supplier_resilience(source, AnalysisInputContract(domain="supplier_resilience", duplicate_policy="reject"))


def test_portfolio_column_mapping_and_reporting_units_reach_calculations(tmp_path):
    from openpyxl import load_workbook

    source = tmp_path / "portfolio.xlsx"
    source.write_bytes(Path("tests/fixtures/exercise/01_Portfolio_Resilience.xlsx").read_bytes())
    workbook = load_workbook(source)
    workbook["Sales_History"].cell(1, 1).value = "FiscalQuarter"
    workbook.save(source)

    analysis = analyze_portfolio_resilience(
        source,
        AnalysisInputContract(
            domain="portfolio_resilience",
            column_mappings={"Quarter": "FiscalQuarter"},
            reporting_currency="USD",
            units="USD",
            conversion_rates={"EUR": 2.0, "USD": 1.0},
        ),
    )

    assert sum(item.revenue for item in analysis.segment_baselines) > 0
    assert analysis.state.calculations[0].units == "USD"
    assert analysis.state.calculations[0].key.units == "USD"


def test_powerbi_changed_period_narrative_follows_computed_direction():
    analysis = analyze_powerbi_strategic_portfolio(
        Path("tests/fixtures/exercise/05_PowerBI_Strategic_Portfolio.xlsx"),
        AnalysisInputContract(
            domain="powerbi_strategic_portfolio",
            baseline_period="2026",
            comparison_period="2025",
            periods=("2025-01:2025-09", "2026-01:2026-09"),
        ),
    )

    assert analysis.yoy_revenue_growth < 0
    assert "growth is negative" in analysis.state.implications[0].statement
