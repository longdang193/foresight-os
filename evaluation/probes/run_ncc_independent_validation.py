from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from foresight_os.analysis.independent_validation import (
    category_mapping_check,
    conditional_check,
    growth_rate,
    planning_threshold_check,
    reconcile_calculation,
    read_validation_source,
    scope_reconciliation_check,
    source_fidelity_check,
)
from foresight_os.domain.challenge import ReviewCheckResult, ReviewSlotStatus, build_material_fingerprint
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _state_sha256(state: Any) -> str | None:
    for evidence in getattr(state, "evidence", ()):
        value = str(getattr(evidence.source_locator, "file_version", ""))
        match = re.search(r"(?i)([0-9a-f]{64})", value)
        if match:
            return match.group(1)
    return None


def _measurement_values(result: Any) -> dict[tuple[str, str], Any]:
    return {
        (measurement.provenance.sheet, measurement.provenance.coordinate): measurement.value
        for measurement in result.measurements
    }


def _raw_cell_check(
    result: Any,
    calculation: Any,
    definition: dict[str, Any],
    values: dict[tuple[str, str], Any],
) -> ReviewCheckResult:
    source_cells = tuple(str(item) for item in definition.get("source_cells", ()))
    missing = []
    resolved = []
    for source_cell in source_cells:
        sheet, coordinate = source_cell.split("!", 1)
        value = values.get((sheet, coordinate))
        if value is None or isinstance(value, str) and value.startswith("#"):
            missing.append(source_cell)
        else:
            resolved.append(float(value))
    if missing:
        return ReviewCheckResult(
            "calculation_reconciliation",
            ReviewSlotStatus.PENDING,
            actual=calculation.output,
            input_ids=(calculation.id,),
            source_ids=source_cells,
            interpretation="raw source inputs are incomplete",
            limitations=tuple(f"missing raw cell input: {item}" for item in missing),
        )
    operation = str(definition.get("operation", ""))
    if operation == "growth_rate" and len(resolved) == 2:
        expected = growth_rate(resolved[0], resolved[1], int(definition.get("periods", 1)))
    elif operation in {"ratio", "share"} and len(resolved) == 2 and resolved[1] != 0:
        expected = resolved[0] / resolved[1]
    else:
        return ReviewCheckResult(
            "calculation_reconciliation",
            ReviewSlotStatus.PENDING,
            actual=calculation.output,
            input_ids=(calculation.id,),
            source_ids=source_cells,
            interpretation="raw-cell calculation definition is incomplete",
            limitations=(f"unsupported operation or denominator: {operation}",),
        )
    return reconcile_calculation(
        check_id="calculation_reconciliation",
        expected=expected,
        actual=calculation.output,
        tolerance=float(definition.get("tolerance", 1e-9)),
        input_ids=(calculation.id,),
        source_ids=source_cells,
        interpretation="independent raw-cell arithmetic reconciliation",
    )


def _table_values(result: Any, sheet: str, category: str, period: str) -> tuple[float | None, str]:
    table = next((item for item in result.tables if item.sheet == sheet), None)
    if table is None or not table.rows:
        return None, f"{sheet}!unavailable"
    headers = [str(item) for item in table.headers[0]] if table.headers else []
    try:
        period_index = headers.index("Period")
        category_index = headers.index("Category")
        value_index = headers.index("Value")
    except ValueError:
        return None, f"{sheet}!headers"
    for row_index, row in enumerate(table.rows, start=2):
        if str(row[period_index]) == str(period) and str(row[category_index]) == str(category):
            try:
                return float(row[value_index]), f"{sheet}!{row_index}:{headers[value_index]}"
            except (TypeError, ValueError):
                return None, f"{sheet}!{row_index}:{headers[value_index]}"
    return None, f"{sheet}!missing:{period}:{category}"


def _calculation_checks(result: Any, state: Any, spec: dict[str, Any]) -> tuple[ReviewCheckResult, ...]:
    calculations = {item.id: item for item in getattr(state, "calculations", ())}
    values = _measurement_values(result)
    checks: list[ReviewCheckResult] = []
    for definition in spec.get("calculations", []):
        calculation_id = str(definition["calculation_id"])
        calculation = calculations.get(calculation_id)
        category = str(getattr(getattr(calculation, "key", None), "region", definition.get("category", "")))
        mapping = category_mapping_check(category, spec.get("source", {}).get("allowed_categories", ()))
        if mapping.status != ReviewSlotStatus.PASS:
            checks.append(ReviewCheckResult(
                "calculation_reconciliation",
                ReviewSlotStatus.FAIL,
                expected=mapping.expected,
                actual=mapping.actual,
                source_ids=tuple(definition.get("source_cells", ())),
                input_ids=(calculation_id,),
                interpretation="calculation cannot be reconciled with an invalid category mapping",
                limitations=mapping.limitations,
            ))
            continue
        if calculation is None:
            checks.append(ReviewCheckResult(
                "calculation_reconciliation",
                ReviewSlotStatus.PENDING,
                input_ids=(calculation_id,),
                interpretation="persisted analyst calculation is missing",
                limitations=(f"missing calculation: {calculation_id}",),
            ))
            continue
        if definition.get("operation"):
            checks.append(_raw_cell_check(result, calculation, definition, values))
            continue
        if definition.get("metric") == "growth_rate":
            baseline, baseline_source = _table_values(result, definition["sheet"], category, definition["baseline_period"])
            current, current_source = _table_values(result, definition["sheet"], category, definition["current_period"])
            expected = None if baseline is None or current is None else growth_rate(baseline, current, int(definition["periods"]))
            source_ids = (baseline_source, current_source)
        else:
            baseline, baseline_source = _table_values(result, definition["sheet"], category, str(definition["baseline_period"]))
            expected = None if baseline is None else float(baseline) * (1.0 + float(definition["annual_rate"])) ** int(definition["periods"])
            source_ids = (baseline_source,)
        if expected is None:
            checks.append(ReviewCheckResult(
                "calculation_reconciliation",
                ReviewSlotStatus.PENDING,
                actual=calculation.output,
                input_ids=(calculation_id,),
                source_ids=source_ids,
                interpretation="raw source inputs are incomplete",
                limitations=("missing raw cell input",),
            ))
            continue
        if definition.get("metric") == "growth_rate":
            check = ReviewCheckResult(
                "calculation_reconciliation",
                ReviewSlotStatus.PASS if abs(float(calculation.output) - expected) <= float(definition.get("tolerance", 1e-9)) else ReviewSlotStatus.FAIL,
                expected=expected,
                actual=calculation.output,
                delta=float(calculation.output) - expected,
                tolerance=float(definition.get("tolerance", 1e-9)),
                source_ids=source_ids,
                input_ids=(calculation_id,),
                interpretation="independent raw-cell arithmetic reconciliation",
            )
        else:
            check = planning_threshold_check(
                initial=float(baseline),
                annual_rate=float(definition["annual_rate"]),
                periods=int(definition["periods"]),
                analyst_actual=float(calculation.output),
                tolerance=float(definition.get("tolerance", 1e-9)),
                source_ids=source_ids,
            )
            check = ReviewCheckResult(
                check.check_id,
                check.status,
                check.expected,
                check.actual,
                check.delta,
                check.tolerance,
                tuple(source_ids),
                (calculation_id,),
                check.interpretation,
                check.limitations,
            )
        checks.append(check)
    return tuple(checks)


def run_probe(workbook: Path, analysis_dir: Path, review_spec: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    spec = _load_json(review_spec)
    receipt: dict[str, Any] = {
        "case_id": spec.get("case_id"),
        "policy_id": spec.get("policy_id"),
        "policy_version": "1",
        "review_checks": [item["check_id"] for item in spec.get("review_checks", ())],
        "reviewer_capabilities": sorted({capability for item in spec.get("review_checks", ()) for capability in item.get("capabilities", ())}),
        "reviewer_skill_ids": ["source-appraisal", "key-assumptions-check", "red-team-claim"],
        "workbook": str(workbook),
        "output_root": str(output_root),
    }
    if not workbook.exists() or not analysis_dir.exists():
        receipt.update({"status": "BLOCKED_INPUT", "verification": "NOT_VERIFIED", "reason": "workbook or persisted analysis directory is missing"})
        (output_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
    try:
        state = AnalysisStore(analysis_dir).load_analysis()
    except (FileNotFoundError, ValueError, OSError) as error:
        receipt.update({"status": "BLOCKED_INPUT", "verification": "NOT_VERIFIED", "reason": f"persisted analysis unavailable: {type(error).__name__}"})
        (output_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
    source = spec.get("source", {})
    selection = SheetSelection(
        ranges=tuple(tuple(item) for item in source.get("ranges", ())),
        include_hidden=True,
        include_hidden_rows=True,
    )
    result = read_validation_source(workbook, selection)
    declared_sha = _state_sha256(state)
    source_check = source_fidelity_check(result, expected_sha256=declared_sha, expected_ranges=selection.ranges)
    scope_check = scope_reconciliation_check(
        result,
        expected_sheets=source.get("sheets", ()),
        expected_ranges=selection.ranges,
        expected_periods=source.get("periods", {}),
    )
    calculation_checks = _calculation_checks(result, state, spec)
    decision_check = ReviewCheckResult(
        "decision_challenge",
        "NOT_RUN",
        interpretation="human or separately authorized reviewer challenge was not run by this deterministic probe",
        limitations=("decision challenge remains outside fixture-only validation",),
    )
    target_ids = tuple(item.id for collection in (state.claims, state.implications, state.recommendations) for item in collection)
    deterministic_pass = source_check.status == ReviewSlotStatus.PASS and scope_check.status == ReviewSlotStatus.PASS and all(item.status == ReviewSlotStatus.PASS for item in calculation_checks)
    receipt.update({
        "status": "NOT_VERIFIED" if deterministic_pass else "FAILED",
        "verification": "NOT_VERIFIED",
        "investigation_id": state.investigation_id,
        "state_revision": state.revision,
        "pending_state_fingerprint": build_material_fingerprint(state, target_ids),
        "execution_recipe_fingerprint": hashlib.sha256(review_spec.read_bytes()).hexdigest(),
        "target_record_ids": list(target_ids),
        "calculation_ids": [item.id for item in state.calculations],
        "workbook_sha256": result.workbook_sha256,
        "sheet_names": [item.name for item in result.sheets],
        "checks": [
            {"check_id": item.check_id, "status": str(item.status), "expected": item.expected, "actual": item.actual, "delta": item.delta, "tolerance": item.tolerance, "source_ids": list(item.source_ids), "input_ids": list(item.input_ids), "limitations": list(item.limitations)}
            for item in (source_check, scope_check, *calculation_checks, decision_check)
        ],
        "missing_inputs": list(spec.get("conditional_missing_inputs", ())),
        "automated_review_outcome": "PASS" if deterministic_pass else "FAIL",
        "human_acceptance": "NOT_RUN",
    })
    (output_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--review-spec", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    run_probe(args.workbook, args.analysis_dir, args.review_spec, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
