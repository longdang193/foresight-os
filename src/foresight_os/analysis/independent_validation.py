from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

from foresight_os.domain.challenge import ReviewCheckResult, ReviewSlotStatus
from foresight_os.runtime.local_toolbelt import SourceSnapshot, SheetSelection, WorkbookContext, WorkbookReadResult, spreadsheet_read


class ValidationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    NOT_RUN = "NOT_RUN"


@dataclass(frozen=True)
class IndependentValidationReport:
    workbook_sha256: str
    checks: tuple[ReviewCheckResult, ...]
    missing_inputs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        return bool(self.checks) and not self.missing_inputs and all(
            check.status == ReviewSlotStatus.PASS for check in self.checks
        )


def read_validation_source(
    source: str | Path,
    selection: SheetSelection | Mapping[str, Any] | None = None,
    *,
    snapshot: SourceSnapshot | None = None,
    workbook_context: WorkbookContext | None = None,
    _cache: Any = None,
) -> WorkbookReadResult:
    if snapshot is not None and workbook_context is not None:
        raise ValueError("snapshot and workbook_context are mutually exclusive")
    if workbook_context is not None:
        return workbook_context.read(str(source), selection or SheetSelection(include_hidden=True, include_hidden_rows=True))
    return spreadsheet_read(
        str(source),
        selection or SheetSelection(include_hidden=True, include_hidden_rows=True),
        _snapshot=snapshot,
        _cache=_cache,
    )


def source_fidelity_check(
    result: WorkbookReadResult,
    *,
    expected_sha256: str | None = None,
    expected_ranges: Sequence[tuple[str, str]] = (),
    check_id: str = "source_fidelity",
) -> ReviewCheckResult:
    observed_ranges = {(table.sheet, table.source_range) for table in result.tables}
    missing_ranges = tuple(f"{sheet}!{source_range}" for sheet, source_range in expected_ranges if (sheet, source_range) not in observed_ranges)
    fingerprint_matches = expected_sha256 is None or result.workbook_sha256 == expected_sha256
    status = ReviewSlotStatus.PASS if fingerprint_matches and not missing_ranges else ReviewSlotStatus.FAIL
    limitations = tuple([f"missing selected range: {item}" for item in missing_ranges])
    if expected_sha256 is not None and not fingerprint_matches:
        limitations += ("workbook SHA-256 differs from the declared source",)
    return ReviewCheckResult(
        check_id=check_id,
        status=status,
        expected=expected_sha256,
        actual=result.workbook_sha256,
        source_ids=tuple(f"{sheet}!{source_range}" for sheet, source_range in sorted(observed_ranges)),
        interpretation="source hash and selected ranges match" if status == ReviewSlotStatus.PASS else "source fidelity could not be established",
        limitations=limitations,
    )


def scope_reconciliation_check(
    result: WorkbookReadResult,
    *,
    expected_sheets: Sequence[str] = (),
    expected_ranges: Sequence[tuple[str, str]] = (),
    expected_periods: Mapping[str, str] | None = None,
    check_id: str = "scope_reconciliation",
) -> ReviewCheckResult:
    expected_periods = expected_periods or {}
    observed_sheets = {sheet.name for sheet in result.sheets}
    observed_ranges = {(table.sheet, table.source_range) for table in result.tables}
    missing_sheets = tuple(sheet for sheet in expected_sheets if sheet not in observed_sheets)
    missing_ranges = tuple(f"{sheet}!{source_range}" for sheet, source_range in expected_ranges if (sheet, source_range) not in observed_ranges)
    missing_periods = tuple(f"{key}={value}" for key, value in expected_periods.items() if value not in {str(cell.value) for cell in result.measurements})
    limitations = tuple(
        [f"missing sheet: {item}" for item in missing_sheets]
        + [f"missing range: {item}" for item in missing_ranges]
        + [f"missing period marker: {item}" for item in missing_periods]
    )
    status = ReviewSlotStatus.PASS if not limitations else ReviewSlotStatus.FAIL
    return ReviewCheckResult(
        check_id=check_id,
        status=status,
        expected={"sheets": list(expected_sheets), "ranges": [list(item) for item in expected_ranges], "periods": dict(expected_periods)},
        actual={"sheets": sorted(observed_sheets), "ranges": [list(item) for item in sorted(observed_ranges)]},
        source_ids=tuple(f"{sheet}!{source_range}" for sheet, source_range in sorted(observed_ranges)),
        interpretation="declared source scope is present" if status == ReviewSlotStatus.PASS else "declared source scope is incomplete",
        limitations=limitations,
    )


def reconcile_calculation(
    *,
    check_id: str,
    expected: float,
    actual: float | None,
    tolerance: float = 1e-9,
    input_ids: Sequence[str] = (),
    source_ids: Sequence[str] = (),
    interpretation: str = "independent arithmetic reconciliation",
) -> ReviewCheckResult:
    if actual is None or not isfinite(float(actual)):
        return ReviewCheckResult(
            check_id=check_id,
            status=ReviewSlotStatus.PENDING,
            expected=expected,
            actual=actual,
            tolerance=tolerance,
            source_ids=tuple(source_ids),
            input_ids=tuple(input_ids),
            interpretation=interpretation,
            limitations=("analyst actual is missing or non-numeric",),
        )
    delta = float(actual) - float(expected)
    status = ReviewSlotStatus.PASS if abs(delta) <= tolerance else ReviewSlotStatus.FAIL
    return ReviewCheckResult(
        check_id=check_id,
        status=status,
        expected=expected,
        actual=actual,
        delta=delta,
        tolerance=tolerance,
        source_ids=tuple(source_ids),
        input_ids=tuple(input_ids),
        interpretation=interpretation,
        limitations=(),
    )


def compound_threshold(initial: float, annual_rate: float, periods: int) -> float:
    if periods < 0:
        raise ValueError("periods must be non-negative")
    return float(initial) * (1.0 + float(annual_rate)) ** periods


def growth_rate(initial: float, final: float, periods: int) -> float:
    if periods <= 0:
        raise ValueError("periods must be positive")
    if initial == 0:
        raise ValueError("initial value must be non-zero")
    return (float(final) / float(initial)) ** (1.0 / periods) - 1.0


def conditional_check(check_id: str, missing_inputs: Sequence[str], *, interpretation: str) -> ReviewCheckResult:
    return ReviewCheckResult(
        check_id=check_id,
        status=ReviewSlotStatus.PENDING if missing_inputs else ReviewSlotStatus.PASS,
        interpretation=interpretation,
        limitations=tuple(f"missing feasibility input: {item}" for item in missing_inputs),
    )


def category_mapping_check(category: str, allowed_categories: Sequence[str], *, check_id: str = "scope_reconciliation") -> ReviewCheckResult:
    valid = category in set(allowed_categories)
    return ReviewCheckResult(
        check_id=check_id,
        status=ReviewSlotStatus.PASS if valid else ReviewSlotStatus.FAIL,
        expected=tuple(allowed_categories),
        actual=category,
        interpretation="category mapping is declared" if valid else "category mapping is invalid",
        limitations=() if valid else (f"unsupported category: {category}",),
    )


def channel_comparability_check(
    *,
    check_id: str = "scope_reconciliation",
    definitions: Mapping[str, Mapping[str, str]],
) -> ReviewCheckResult:
    fields = ("definition", "period", "units", "denominator")
    mismatches = tuple(
        field
        for field in fields
        if len({str(values.get(field, "")) for values in definitions.values()}) > 1
    )
    return ReviewCheckResult(
        check_id=check_id,
        status=ReviewSlotStatus.PASS if not mismatches else ReviewSlotStatus.FAIL,
        expected={channel: dict(values) for channel, values in definitions.items()},
        actual={"comparable": not mismatches},
        interpretation="channel measures are comparable" if not mismatches else "channel measures must remain separate",
        limitations=tuple(f"channel definitions disagree on {field}" for field in mismatches),
    )


def planning_threshold_check(
    *,
    initial: float,
    annual_rate: float,
    periods: int,
    analyst_actual: float | None,
    tolerance: float = 1e-9,
    source_ids: Sequence[str] = (),
) -> ReviewCheckResult:
    expected = compound_threshold(initial, annual_rate, periods)
    return reconcile_calculation(
        check_id="calculation_reconciliation",
        expected=expected,
        actual=analyst_actual,
        tolerance=tolerance,
        source_ids=source_ids,
        interpretation="planning threshold only; not observed business performance",
    )


def run_independent_validation(
    source: str | Path,
    *,
    selection: SheetSelection | Mapping[str, Any] | None = None,
    snapshot: SourceSnapshot | None = None,
    workbook_context: WorkbookContext | None = None,
    expected_sha256: str | None = None,
    expected_ranges: Sequence[tuple[str, str]] = (),
    expected_sheets: Sequence[str] = (),
    expected_periods: Mapping[str, str] | None = None,
    calculations: Sequence[ReviewCheckResult] = (),
    missing_inputs: Sequence[str] = (),
    required_check_ids: Sequence[str] | None = None,
    _cache: Any = None,
) -> IndependentValidationReport:
    result = read_validation_source(
        source,
        selection,
        snapshot=snapshot,
        workbook_context=workbook_context,
        _cache=_cache,
    )
    selected = tuple(dict.fromkeys(required_check_ids)) if required_check_ids is not None else (
        "source_fidelity",
        "scope_reconciliation",
        *(check.check_id for check in calculations),
    )
    calculation_checks = tuple(calculations)
    checks: list[ReviewCheckResult] = []
    if "source_fidelity" in selected:
        checks.append(source_fidelity_check(result, expected_sha256=expected_sha256, expected_ranges=expected_ranges))
    if "scope_reconciliation" in selected:
        checks.append(
            scope_reconciliation_check(
                result,
                expected_sheets=expected_sheets,
                expected_ranges=expected_ranges,
                expected_periods=expected_periods,
            )
        )
    for check_id in selected:
        matching = tuple(check for check in calculation_checks if check.check_id == check_id)
        if matching:
            checks.extend(matching)
        elif check_id not in {"source_fidelity", "scope_reconciliation"}:
            limitations = tuple(f"missing validation input: {item}" for item in missing_inputs)
            if not limitations:
                limitations = ("required validation check is unavailable",)
            checks.append(
                ReviewCheckResult(
                    check_id=check_id,
                    status=ReviewSlotStatus.PENDING,
                    interpretation="required validation check could not run",
                    limitations=limitations,
                )
            )
    return IndependentValidationReport(result.workbook_sha256, checks, tuple(missing_inputs))
