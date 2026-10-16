from pathlib import Path

from foresight_os.analysis.portfolio_resilience import analyze_portfolio_resilience
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.runtime.local_toolbelt import WorkbookContext


def test_changed_portfolio_contract_changes_selected_baseline_scope():
    source = Path("tests/fixtures/exercise/01_Portfolio_Resilience.xlsx")
    default = analyze_portfolio_resilience(source)
    changed = analyze_portfolio_resilience(
        source,
        AnalysisInputContract(
            domain="portfolio_resilience",
            baseline_period="2025",
            comparison_period="2024",
            periods=("2025",),
            entity_scope=("DACH",),
            scenarios=("Base",),
            units="EUR",
            reporting_currency="EUR",
        ),
    )

    assert default.contract_fingerprint != changed.contract_fingerprint
    assert sum(item.revenue for item in default.segment_baselines) != sum(item.revenue for item in changed.segment_baselines)


def test_brief_portability_probe_uses_all_production_xlsx_analyzers(tmp_path):
    from evaluation.probes.run_brief_portability_probe import run

    receipt = run(tmp_path)

    assert receipt["status"] == "VERIFIED"
    assert {item["domain"] for item in receipt["cases"]} == {
        "portfolio_resilience",
        "supplier_resilience",
        "ev_capacity_investment",
        "technology_radar",
        "powerbi_strategic_portfolio",
    }
    assert all(item["source_sha256"] == item["fixture_copy_sha256"] for item in receipt["cases"])
    assert all(item["provider_status"] == "not_measured" and item["human_acceptance"] == "not_measured" for item in receipt["cases"])
    assert any("UNSUPPORTED_CONVERSION" in item["changed"]["issue_kinds"] for item in receipt["cases"])


def test_portfolio_analyzer_reuses_run_workbook_context(tmp_path):
    source = Path("tests/fixtures/exercise/01_Portfolio_Resilience.xlsx")
    context = WorkbookContext()

    first = analyze_portfolio_resilience(source, workbook_context=context)
    second = analyze_portfolio_resilience(source, workbook_context=context)

    assert first.source_sha256 == second.source_sha256
    assert context.stats.capture_count == 1
    assert context.stats.capture_hash_count == 1
    assert context.stats.xlsx_parse_count == 1
    assert context.stats.cache_hits == 1
