import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=ROOT / "tests" / "fixtures" / "analyst_multisheet.xlsx")
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    if not args.installed:
        sys.path.insert(0, str(ROOT / "src"))
    from foresight_os.analysis.evidence_workflow import accept_pending_evidence, run_xlsx_finding_workflow
    from foresight_os.persistence.analysis_store import AnalysisStore
    from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, ToolbeltError, data_analysis, spreadsheet_read

    before = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    result = spreadsheet_read(args.fixture, SheetSelection(sheet_names=("Demand", "Hidden"), include_hidden=True, include_hidden_rows=True))
    selected = spreadsheet_read(args.fixture, SheetSelection(tables=(("Demand", "DemandTable"),), include_hidden_rows=True))
    demand = next(table for table in selected.tables if table.sheet == "Demand")
    duplicate = data_analysis(demand, AnalysisOperation("duplicates", key_columns=("Region", "Metric", "Value")))
    scenario = data_analysis(demand, AnalysisOperation("scenario", value_column="Value", scenarios=(("base", 1.0), ("high", 1.2))))
    sensitivity = data_analysis(demand, AnalysisOperation("sensitivity", value_column="Value", sensitivity=(("multiplier", (0.8, 1.0, 1.2)),)))
    missing = data_analysis(demand, AnalysisOperation("missing"))
    try:
        spreadsheet_read(args.fixture, limits=__import__("foresight_os.runtime.local_toolbelt", fromlist=["ToolbeltLimits"]).ToolbeltLimits(max_cells=1))
    except ToolbeltError as error:
        cancellation = type(error).__name__
    else:
        cancellation = "not_triggered"
    finding_store = args.output_root / "xlsx-finding"
    finding = run_xlsx_finding_workflow(
        AnalysisStore(finding_store),
        args.fixture,
        AnalysisOperation("sum", value_column="Value"),
        selection=SheetSelection(tables=(("Demand", "DemandTable"),), include_hidden_rows=True),
        human_decision="PENDING",
    )
    resumed = accept_pending_evidence(AnalysisStore(finding_store), human_decision="ACCEPT") if finding.status == "pending" else None
    after = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    receipt = {
        "mode": "xlsx",
        "status": "verified" if before == after and duplicate.rows and scenario.rows and sensitivity.rows and missing.rows and resumed and resumed.status == "accepted" else "failed",
        "source_sha256_unchanged": before == after,
        "workbook_sha256": result.workbook_sha256,
        "sheet_names": [sheet.name for sheet in result.sheets],
        "hidden_rows": {sheet.name: list(sheet.hidden_rows) for sheet in result.sheets},
        "table_count": len(result.tables),
        "measurement_count": len(result.measurements),
        "formula_statuses": sorted({str(item.formula_status) for item in result.measurements if item.formula}),
        "duplicate_rows": len(duplicate.rows),
        "scenario_order": [row["scenario"] for row in scenario.rows],
        "sensitivity_values": [row["value"] for row in sensitivity.rows],
        "missing_columns": [row["column"] for row in missing.rows],
        "provenance_complete": all(item.provenance.workbook_sha256 == result.workbook_sha256 for item in result.measurements),
        "cross_sheet_provenance": bool(demand.related_provenance),
        "finding_pending_then_accepted": bool(finding.status == "pending" and resumed and resumed.status == "accepted"),
        "finding_calculation_inputs": len(resumed.analysis.calculations[0].input_ids) if resumed and resumed.analysis and resumed.analysis.calculations else 0,
        "cancellation_checkpoint": cancellation,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "xlsx-probe.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
