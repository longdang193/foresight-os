from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evaluation"))

from participant_scope import ParticipantScope
from foresight_os.runtime.local_toolbelt import SheetSelection, spreadsheet_read


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    participant_root = args.output_root / "participant-inputs"
    participant_root.mkdir(parents=True, exist_ok=True)
    validator = args.exercise_root / "06_ForesightOS_Validator_Key.xlsx"
    participants = sorted(item for item in args.exercise_root.glob("*.xlsx") if item.name != validator.name)
    copied: list[Path] = []
    for source in participants:
        target = participant_root / source.name
        shutil.copy2(source, target)
        copied.append(target)
    scope = ParticipantScope(participant_root, denied_paths=(validator,))
    cases = []
    for workbook in copied:
        parsed = spreadsheet_read(scope.resolve(workbook), SheetSelection(include_hidden=True, include_hidden_rows=True))
        cases.append({"name": workbook.name, "sha256": hashlib.sha256(workbook.read_bytes()).hexdigest(), "sheet_count": len(parsed.sheets), "table_count": len(parsed.tables)})
    denied = False
    try:
        scope.resolve(validator)
    except PermissionError:
        denied = True
    report = {"passed": bool(cases and denied and all(item["name"] != validator.name for item in cases)), "validator_denied": denied, "cases": cases}
    (args.output_root / "strategic-exercise-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
