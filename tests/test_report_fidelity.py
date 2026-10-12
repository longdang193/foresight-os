from pathlib import Path

from foresight_os.artifacts.report import render_report
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_report_material_statements_retain_source_record_ids(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    report = outcome.report_path.read_text(encoding="utf-8")
    analysis = AnalysisStore(tmp_path / "case-001").load_analysis()

    for record in [*analysis.claims, *analysis.implications, *analysis.recommendations]:
        assert record.statement in report
        for evidence_id in record.evidence_ids:
            assert evidence_id in report
    assert render_report(analysis) == report
