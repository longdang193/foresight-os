import hashlib
import zipfile
from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

from foresight_os.runtime.local_toolbelt import (
    AnalysisOperation,
    FormulaStatus,
    SheetSelection,
    ToolbeltError,
    calculation,
    data_analysis,
    spreadsheet_read,
)


def _make_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    demand = workbook.active
    demand.title = "Demand"
    demand.append(["Demand inputs", "", "", "", "", ""])
    demand.append(["Region", "Metric", "Value", "Date", "Formula", "Error"])
    demand.append(["North", "demand", 10, datetime(2026, 1, 1), "=Assumptions!B2*C3", "#N/A"])
    demand.append(["North", "demand", 10, datetime(2026, 1, 1), "=C4*2", None])
    demand.row_dimensions[4].hidden = True
    demand.merge_cells("A1:B1")
    demand.tables.add(openpyxl.worksheet.table.Table(displayName="DemandTable", ref="A2:F4"))
    hidden = workbook.create_sheet("Hidden")
    hidden.sheet_state = "hidden"
    hidden.append(["Secret", 99])
    assumptions = workbook.create_sheet("Assumptions")
    assumptions.append(["Scenario", "Multiplier"])
    assumptions.append(["base", 1.0])
    assumptions.append(["high", 1.2])
    workbook.save(path)


@pytest.fixture
def workbook_path(tmp_path: Path) -> Path:
    path = tmp_path / "analyst_multisheet.xlsx"
    _make_workbook(path)
    return path


def test_xlsx_read_inspects_sheets_hidden_rows_headers_types_formulas_and_provenance(workbook_path):
    before = hashlib.sha256(workbook_path.read_bytes()).hexdigest()
    result = spreadsheet_read(workbook_path, SheetSelection(tables=(("Demand", "DemandTable"),)))
    after = hashlib.sha256(workbook_path.read_bytes()).hexdigest()

    assert before == after
    assert {sheet.name for sheet in result.sheets} == {"Demand", "Assumptions"}
    assert result.sheets[0].hidden_rows == (4,)
    table = result.tables[0]
    assert table.name == "DemandTable"
    assert table.headers[0][:2] == ("Region", "Metric")
    assert len(table.rows) == 1
    formula_cells = [item for item in result.measurements if item.formula]
    assert {item.formula_status for item in formula_cells} == {FormulaStatus.FORMULA_WITHOUT_CACHE}
    assert any(item.cross_sheet_references == ("Assumptions",) for item in formula_cells)
    assert any(item.data_type == "date" for item in result.measurements)
    assert any(item.data_type == "error" for item in result.measurements)
    assert all(item.provenance.workbook_sha256 == result.workbook_sha256 for item in result.measurements)


def test_xlsx_selection_can_include_hidden_sheet_and_rows_and_analysis_is_deterministic(workbook_path):
    result = spreadsheet_read(
        workbook_path,
        SheetSelection(sheet_names=("Demand", "Hidden"), include_hidden=True, include_hidden_rows=True),
    )
    demand = next(table for table in result.tables if table.sheet == "Demand")
    assert len(demand.rows) == 2
    assert any(table.sheet == "Hidden" for table in result.tables)

    first = data_analysis(demand, AnalysisOperation("duplicates", key_columns=("Region", "Metric", "Value")))
    second = data_analysis(demand, AnalysisOperation("duplicates", key_columns=("Region", "Metric", "Value")))
    assert first.deterministic_key == second.deterministic_key
    assert first.rows[0]["count"] == 2

    scenarios = data_analysis(demand, AnalysisOperation("scenario", value_column="Value", scenarios=(("base", 1), ("high", 1.2))))
    assert [row["scenario"] for row in scenarios.rows] == ["base", "high"]


def test_formula_without_cache_blocks_decision_critical_calculation(workbook_path):
    result = spreadsheet_read(workbook_path, SheetSelection(tables=(("Demand", "DemandTable"),)))
    formula = next(item for item in result.measurements if item.formula)
    with pytest.raises(ToolbeltError, match="BLOCKED_RECALCULATION"):
        calculation([formula], formula=__import__("foresight_os.runtime.local_toolbelt", fromlist=["FormulaSpec"]).FormulaSpec("formula", "sum"), units=__import__("foresight_os.runtime.local_toolbelt", fromlist=["UnitSpec"]).UnitSpec("units"))


def test_formula_cache_and_manual_recalculation_state_are_truthful(workbook_path, tmp_path):
    cached_path = tmp_path / "cached.xlsx"
    cached_path.write_bytes(workbook_path.read_bytes())
    with zipfile.ZipFile(cached_path, "r") as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    sheet = entries["xl/worksheets/sheet1.xml"].decode("utf-8")
    sheet = sheet.replace('<c r="E3"><f>Assumptions!B2*C3</f><v></v></c>', '<c r="E3"><f>Assumptions!B2*C3</f><v>10</v></c>')
    entries["xl/worksheets/sheet1.xml"] = sheet.encode("utf-8")
    workbook_xml = entries["xl/workbook.xml"].decode("utf-8").replace('<calcPr calcId="124519"/>', '<calcPr calcId="124519" calcMode="manual"/>')
    entries["xl/workbook.xml"] = workbook_xml.encode("utf-8")
    with zipfile.ZipFile(cached_path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    result = spreadsheet_read(cached_path, SheetSelection(tables=(("Demand", "DemandTable"),)))
    formula = next(item for item in result.measurements if item.coordinate == "E3") if False else next(item for item in result.measurements if item.formula and item.provenance.coordinate == "E3")
    assert formula.cached_value == 10
    assert formula.formula_status == FormulaStatus.FORMULA_STALE_OR_UNKNOWN


def test_analysis_supports_filters_and_duplicate_join_key_guard(workbook_path):
    result = spreadsheet_read(workbook_path, SheetSelection(tables=(("Demand", "DemandTable"),), include_hidden_rows=True))
    demand = next(table for table in result.tables if table.sheet == "Demand")
    filtered = data_analysis(demand, AnalysisOperation("missing", filters=(("Region", "eq", "North"),)))
    assert filtered.rows[0]["column"] == "Region"
    with pytest.raises(ToolbeltError, match="duplicate join keys"):
        data_analysis(demand, AnalysisOperation("join", join_table=demand, join_keys=("Region", "Region")))


def test_spreadsheet_and_analysis_honor_cancellation_checkpoints(workbook_path):
    cancelled = lambda: True
    with pytest.raises(ToolbeltError, match="cancelled"):
        spreadsheet_read(workbook_path, cancel_check=cancelled)
    result = spreadsheet_read(workbook_path, SheetSelection(tables=(("Demand", "DemandTable"),)))
    with pytest.raises(ToolbeltError, match="cancelled"):
        data_analysis(result.tables[0], AnalysisOperation("duplicates"), cancel_check=cancelled)
