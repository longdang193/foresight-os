from pathlib import Path

import openpyxl

from foresight_os.analysis.workbook_inputs import (
    MaterialView,
    WorkbookLayoutSpec,
    build_material_view,
    resolve_workbook_layout,
)
from foresight_os.analysis.workbook_engine import DomainAnalysis, WorkbookAnalysisEngine
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.runtime.local_toolbelt import SheetSelection, spreadsheet_read


def _workbook(tmp_path: Path) -> Path:
    source = tmp_path / "material-view.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["Entity", "Value", "Scenario"])
    sheet.append(["North", 10, "Base"])
    sheet.append(["South", 20, "Base"])
    workbook.save(source)
    return source


def test_material_view_resolves_layout_and_retains_row_provenance(tmp_path):
    source = _workbook(tmp_path)
    contract = AnalysisInputContract(
        domain="test",
        required_tables=("Data",),
        entity_scope=("North",),
        scenarios=("Base",),
        workbook_selection={"sheet": "Data"},
    )
    workbook = spreadsheet_read(source, SheetSelection(sheet_names=("Data",)))
    layout = resolve_workbook_layout(workbook, WorkbookLayoutSpec.from_contract(contract))
    material = build_material_view(workbook, layout, contract)

    assert isinstance(material, MaterialView)
    assert material.table("Data").rows == (("North", 10, "Base"),)
    assert material.table("Data").row_provenance[0][0].workbook_sha256 == workbook.workbook_sha256
    assert material.scope_fingerprint
    assert material.layout_fingerprint


def test_material_view_changes_scope_without_recapturing_source(tmp_path):
    source = _workbook(tmp_path)
    first_contract = AnalysisInputContract(domain="test", required_tables=("Data",), entity_scope=("North",))
    second_contract = AnalysisInputContract(domain="test", required_tables=("Data",), entity_scope=("South",))
    workbook = spreadsheet_read(source, SheetSelection(sheet_names=("Data",)))
    layout = resolve_workbook_layout(workbook, WorkbookLayoutSpec.from_contract(first_contract))

    first = build_material_view(workbook, layout, first_contract)
    second = build_material_view(workbook, layout, second_contract)

    assert first.source_sha256 == second.source_sha256 == workbook.workbook_sha256
    assert first.table("Data").rows != second.table("Data").rows
    assert first.scope_fingerprint != second.scope_fingerprint


def test_engine_returns_typed_domain_result_without_persistence_side_effects(tmp_path):
    source = _workbook(tmp_path)
    contract = AnalysisInputContract(domain="test", required_tables=("Data",))
    engine = WorkbookAnalysisEngine()

    result = engine.run(
        source,
        contract,
        lambda material, normalized: DomainAnalysis(
            result=material.table("Data").rows[0][1],
            diagnostics=(normalized.domain,),
        ),
    )

    assert result.status == "completed"
    assert result.domain_result is not None
    assert result.domain_result.result == 10
    assert result.diagnostics == ("test",)
    assert result.metrics["capture_count"] == 1


def test_engine_maps_missing_selection_to_blocked_input(tmp_path):
    source = _workbook(tmp_path)
    contract = AnalysisInputContract(
        domain="test",
        required_tables=("Missing",),
        workbook_selection={"sheet": "Missing"},
    )

    result = WorkbookAnalysisEngine().run(source, contract, lambda material, normalized: material)

    assert result.status == "blocked_input"
    assert "missing workbook sheet" in (result.failure or "")
