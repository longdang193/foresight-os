from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation"))

from participant_scope import ParticipantScope
from foresight_os.analysis.evidence_workflow import run_xlsx_finding_workflow
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, spreadsheet_read


def numeric_columns(table: Any) -> list[str]:
    columns: list[str] = []
    for index, column in enumerate(table.columns):
        values = [row[index] for row in table.rows if index < len(row) and row[index] is not None]
        if any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            columns.append(column)
    return columns


def _case_passes(case: dict[str, Any]) -> bool:
    return (
        case.get("status") == "accepted"
        and case.get("review_accepted") is True
        and case.get("finding_view_count") == 1
        and case.get("finding_view_statuses") == ["CURRENT"]
        and case.get("finding_view_accepted") == [True]
        and case.get("review_record_count", 0) >= 1
        and case.get("persisted_revision_status") == "ACCEPTED"
        and case.get("source_unchanged") is True
        and case.get("failure") is None
    )


def pipeline_passes(report: dict[str, Any]) -> bool:
    cases = report.get("cases", [])
    return (
        report.get("validator_denied") is True
        and len(cases) == report.get("expected_participant_count", 5)
        and all(_case_passes(case) for case in cases)
    )


def _run_case(source: Path, workbook: Path, scope: ParticipantScope, output_root: Path) -> dict[str, Any]:
    original_before = hashlib.sha256(source.read_bytes()).hexdigest()
    before = hashlib.sha256(workbook.read_bytes()).hexdigest()
    try:
        parsed = spreadsheet_read(scope.resolve(workbook), SheetSelection(include_hidden=True, include_hidden_rows=True))
        candidates = [(table, column) for table in parsed.tables for column in numeric_columns(table)]
        if not candidates:
            return {"name": workbook.name, "status": "failed", "failure": "no numeric table column"}
        table, value_column = candidates[0]
        case_root = output_root / workbook.stem
        store = AnalysisStore(case_root)
        workflow = run_xlsx_finding_workflow(
            store,
            scope.resolve(workbook),
            AnalysisOperation(kind="aggregate", value_column=value_column),
            selection=SheetSelection(
                tables=((table.sheet, table.name),),
                include_hidden=True,
                include_hidden_rows=True,
            ),
            investigation_id=f"exercise-{workbook.stem}",
            human_decision="ACCEPT",
        )
        persisted = store.load_analysis()
        views = derive_finding_views(persisted)
        after = hashlib.sha256(workbook.read_bytes()).hexdigest()
        original_after = hashlib.sha256(source.read_bytes()).hexdigest()
        return {
            "name": workbook.name,
            "sha256": before,
            "selected_sheet": table.sheet,
            "selected_table": table.name,
            "value_column": value_column,
            "status": workflow.status,
            "review_accepted": workflow.review.accepted if workflow.review else None,
            "review_issues": workflow.review.issues if workflow.review else [],
            "evidence_count": len(persisted.evidence),
            "finding_view_count": len(views),
            "finding_view_statuses": [view.review_status for view in views],
            "finding_view_accepted": [view.accepted for view in views],
            "review_record_count": len(persisted.review_records),
            "persisted_revision_status": persisted.revision_status.value,
            "source_unchanged": original_before == original_after == before == after,
            "failure": workflow.failure,
        }
    except Exception as error:
        return {"name": workbook.name, "status": "failed", "failure": f"{type(error).__name__}: {error}"}


def run(exercise_root: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    participant_root = output_root / "participant-inputs"
    participant_root.mkdir(parents=True, exist_ok=True)
    validator = exercise_root / "06_ForesightOS_Validator_Key.xlsx"
    participants = sorted(item for item in exercise_root.glob("*.xlsx") if item.name != validator.name)
    copied: list[Path] = []
    source_by_name: dict[str, Path] = {}
    for source in participants:
        target = participant_root / source.name
        shutil.copy2(source, target)
        copied.append(target)
        source_by_name[target.name] = source
    scope = ParticipantScope(participant_root, denied_paths=(validator,))
    cases = [_run_case(source_by_name[workbook.name], workbook, scope, output_root) for workbook in copied]
    validator_denied = False
    try:
        scope.resolve(validator)
    except PermissionError:
        validator_denied = True
    report = {
        "expected_participant_count": 5,
        "participant_count": len(cases),
        "validator_denied": validator_denied,
        "cases": cases,
    }
    report["passed"] = pipeline_passes(report)
    report_path = output_root / "full-pipeline-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.exercise_root, args.output_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
