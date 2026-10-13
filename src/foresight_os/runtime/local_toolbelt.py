from __future__ import annotations

import ast
import csv
import hashlib
import operator
import re
import zipfile
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import openpyxl

from foresight_os.domain.models import CalculationRecord, Evidence, MeasurementKey, SourceLocator
from foresight_os.domain.validation import validate_analysis, validate_evidence_candidate


class ToolbeltError(ValueError):
    pass


class FormulaStatus(StrEnum):
    VALUE = "VALUE"
    FORMULA_WITH_CACHE = "FORMULA_WITH_CACHE"
    FORMULA_WITHOUT_CACHE = "FORMULA_WITHOUT_CACHE"
    FORMULA_RECALCULATED = "FORMULA_RECALCULATED"
    FORMULA_STALE_OR_UNKNOWN = "FORMULA_STALE_OR_UNKNOWN"
    ERROR = "ERROR"


class ExcelError:
    def __init__(self, value: str):
        self.value = value

    def __repr__(self) -> str:
        return f"ExcelError({self.value!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ExcelError) and self.value == other.value


@dataclass(frozen=True)
class ToolbeltLimits:
    max_bytes: int = 25_000_000
    max_expanded_bytes: int = 100_000_000
    max_rows: int = 50_000
    max_cells: int = 250_000
    max_result_rows: int = 10_000


@dataclass(frozen=True)
class SheetSelection:
    sheet_names: tuple[str, ...] = ()
    ranges: tuple[tuple[str, str], ...] = ()
    tables: tuple[tuple[str, str], ...] = ()
    include_hidden: bool = False
    include_hidden_rows: bool = False


@dataclass(frozen=True)
class CellProvenance:
    workbook_sha256: str
    sheet: str
    coordinate: str
    range: str


@dataclass(frozen=True)
class TypedMeasurement:
    id: str
    value: Any
    data_type: str
    formula: str | None
    cached_value: Any
    formula_status: FormulaStatus
    provenance: CellProvenance
    cross_sheet_references: tuple[str, ...] = ()
    cross_sheet_cells: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class TypedTable:
    id: str
    name: str
    sheet: str
    headers: tuple[tuple[str, ...], ...]
    rows: tuple[tuple[Any, ...], ...]
    row_provenance: tuple[tuple[CellProvenance, ...], ...]
    hidden: bool = False
    source_range: str = ""
    related_provenance: tuple[CellProvenance, ...] = ()

    @property
    def columns(self) -> tuple[str, ...]:
        if not self.headers:
            return ()
        if len(self.headers) == 1:
            return tuple(str(item).strip() for item in self.headers[0])
        return tuple(" ".join(str(part) for part in parts if str(part).strip()).strip() for parts in zip(*self.headers, strict=False))


@dataclass(frozen=True)
class SheetSummary:
    name: str
    state: str
    max_row: int
    max_column: int
    hidden_rows: tuple[int, ...]
    merged_ranges: tuple[str, ...]
    tables: tuple[str, ...]


@dataclass(frozen=True)
class WorkbookReadResult:
    source: str
    workbook_sha256: str
    sheets: tuple[SheetSummary, ...]
    tables: tuple[TypedTable, ...]
    measurements: tuple[TypedMeasurement, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisOperation:
    kind: str
    columns: tuple[str, ...] = ()
    key_columns: tuple[str, ...] = ()
    value_column: str | None = None
    scenarios: tuple[tuple[str, float], ...] = ()
    sensitivity: tuple[tuple[str, tuple[float, ...]], ...] = ()
    many_to_many: bool = False
    filters: tuple[tuple[str, str, Any], ...] = ()
    join_table: TypedTable | None = None
    join_keys: tuple[str, str] = ()


@dataclass(frozen=True)
class AnalysisResult:
    operation: str
    rows: tuple[dict[str, Any], ...]
    provenance: tuple[CellProvenance, ...]
    deterministic_key: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormulaSpec:
    expression: str
    operation: str = "sum"


@dataclass(frozen=True)
class UnitSpec:
    units: str
    relative_tolerance: float = 1e-9


def _excel_type(value: Any) -> str:
    if isinstance(value, ExcelError):
        return "error"
    if value is None:
        return "blank"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (datetime, date)):
        return "date"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str) and value.startswith("#"):
        return "error"
    return "string"


def _coerce(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, str) and value.startswith("#"):
        return ExcelError(value)
    return value


def _range_cells(ws, cell_range: str) -> list[list[Any]]:
    return [list(row) for row in ws[cell_range]]


def _range_bounds(cell_range: str) -> tuple[int, int, int, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?", cell_range.upper())
    if not match:
        raise ToolbeltError(f"invalid cell range: {cell_range}")
    def col(value: str) -> int:
        result = 0
        for char in value:
            result = result * 26 + ord(char) - 64
        return result
    return col(match.group(1)), int(match.group(2)), col(match.group(3) or match.group(1)), int(match.group(4) or match.group(2))


def _formula_references(formula: str | None) -> tuple[tuple[str, str], ...]:
    if not formula:
        return ()
    matches = re.findall(r"(?:'([^']+)'|([A-Za-z0-9_ ]+))!\$?([A-Z]{1,3})\$?(\d+)", formula)
    return tuple(sorted({((quoted or bare).strip(), f"{column}{row}") for quoted, bare, column, row in matches}))


def _in_selection(sheet: str, selection: SheetSelection | None) -> bool:
    return selection is None or not selection.sheet_names or sheet in selection.sheet_names


def _check_cancel(cancel_check: Callable[[], bool] | None) -> None:
    if cancel_check and cancel_check():
        raise ToolbeltError("cancelled")


def _delimited_value(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if value.startswith("#"):
        return ExcelError(value)
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _read_delimited(source: Path, selection: SheetSelection | None, limits: ToolbeltLimits, cancel_check: Callable[[], bool] | None) -> WorkbookReadResult:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    sheet = source.stem
    if selection and selection.sheet_names and sheet not in selection.sheet_names:
        return WorkbookReadResult(str(source), digest, (), (), ())
    delimiter = "\t" if source.suffix.lower() == ".tsv" else ","
    selected_range = next((cell_range for selected_sheet, cell_range in (selection.ranges if selection else ()) if selected_sheet == sheet), None)
    range_bounds = _range_bounds(selected_range) if selected_range else None
    row_start = range_bounds[1] if range_bounds else 1
    col_start = range_bounds[0] if range_bounds else 1
    raw_rows: list[tuple[Any, ...]] = []
    cell_count = 0
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.reader(handle, delimiter=delimiter), 1):
            _check_cancel(cancel_check)
            if range_bounds and row_number > range_bounds[3]:
                break
            if range_bounds and row_number < range_bounds[1]:
                continue
            if not range_bounds and row_number > limits.max_rows:
                raise ToolbeltError("workbook selection exceeds row limit")
            values = tuple(_delimited_value(value) for value in row)
            if range_bounds:
                values = values[range_bounds[0] - 1:range_bounds[2]]
            cell_count += len(values)
            if cell_count > limits.max_cells:
                raise ToolbeltError("workbook selection exceeds cell limit")
            raw_rows.append(values)
    if selection and selection.ranges:
        ranges = [cell_range for selected_sheet, cell_range in selection.ranges if selected_sheet == sheet]
        if ranges:
            if selected_range is None:
                raise ToolbeltError("invalid CSV selection")
    if selection and selection.tables and not any(selected_sheet == sheet and table_name == source.stem for selected_sheet, table_name in selection.tables):
        return WorkbookReadResult(str(source), digest, (), (), ())
    cell_count = sum(len(row) for row in raw_rows)
    if cell_count > limits.max_cells:
        raise ToolbeltError("workbook selection exceeds cell limit")
    hidden_rows: tuple[int, ...] = ()
    summary = SheetSummary(sheet, "visible", len(raw_rows), max((len(row) for row in raw_rows), default=0), hidden_rows, (), (source.stem,))
    measurements: list[TypedMeasurement] = []
    provenance_rows: list[tuple[CellProvenance, ...]] = []
    for row_number, row in enumerate(raw_rows, 1):
        _check_cancel(cancel_check)
        row_provenance = []
        for column_number, value in enumerate(row, 1):
            coordinate = f"{openpyxl.utils.get_column_letter(col_start + column_number - 1)}{row_start + row_number - 1}"
            locator = CellProvenance(digest, sheet, coordinate, f"{sheet}!{coordinate}")
            measurements.append(TypedMeasurement(f"{digest[:12]}:{sheet}:{coordinate}", value, _excel_type(value), None, None, FormulaStatus.VALUE, locator))
            row_provenance.append(locator)
        provenance_rows.append(tuple(row_provenance))
    header_rows = min(1, len(raw_rows))
    if len(raw_rows) > 1 and sum(value not in (None, "") for value in raw_rows[0]) <= 1 and sum(value not in (None, "") for value in raw_rows[1]) > 1:
        header_rows = 2
    headers = tuple(tuple("" if value is None else str(value) for value in raw_rows[index]) for index in range(header_rows))
    source_range = f"{openpyxl.utils.get_column_letter(col_start)}{row_start}:{openpyxl.utils.get_column_letter(col_start + summary.max_column - 1)}{row_start + summary.max_row - 1}" if raw_rows else ""
    table = TypedTable(f"{digest[:12]}:{sheet}:{source_range}", source.stem, sheet, headers, tuple(raw_rows[header_rows:]), tuple(provenance_rows[header_rows:]), False, source_range)
    return WorkbookReadResult(str(source), digest, (summary,), (table,), tuple(measurements))


def spreadsheet_read(
    source: Path,
    selection: SheetSelection | None = None,
    limits: ToolbeltLimits | None = None,
    *,
    cancel_check: Callable[[], bool] | None = None,
) -> WorkbookReadResult:
    limits = limits or ToolbeltLimits()
    source = Path(source)
    _check_cancel(cancel_check)
    if source.stat().st_size > limits.max_bytes:
        raise ToolbeltError("workbook exceeds byte limit")
    if source.suffix.lower() in {".csv", ".tsv"}:
        return _read_delimited(source, selection, limits, cancel_check)
    if source.suffix.lower() not in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        raise ToolbeltError("unsupported spreadsheet format")
    try:
        with zipfile.ZipFile(source) as archive:
            expanded_bytes = sum(item.file_size for item in archive.infolist())
    except zipfile.BadZipFile as error:
        raise ToolbeltError("invalid workbook archive") from error
    if expanded_bytes > limits.max_expanded_bytes:
        raise ToolbeltError("workbook expanded content exceeds byte limit")
    dimension_workbook = openpyxl.load_workbook(source, data_only=False, read_only=True, keep_links=False)
    try:
        for ws in dimension_workbook.worksheets:
            if ws.sheet_state != "visible" and not (selection and selection.include_hidden):
                continue
            selected_ranges = [cell_range for sheet, cell_range in (selection.ranges if selection else ()) if sheet == ws.title]
            if not selected_ranges:
                selected_ranges = [f"A1:{openpyxl.utils.get_column_letter(ws.max_column)}{ws.max_row}"] if ws.max_row and ws.max_column else []
            for source_range in selected_ranges:
                min_col, min_row, max_col, max_row = _range_bounds(source_range)
                if max_row - min_row + 1 > limits.max_rows:
                    raise ToolbeltError("workbook selection exceeds row limit")
                if (max_row - min_row + 1) * (max_col - min_col + 1) > limits.max_cells:
                    raise ToolbeltError("workbook selection exceeds cell limit")
    finally:
        dimension_workbook.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    workbook = openpyxl.load_workbook(source, data_only=False, read_only=False)
    cached = openpyxl.load_workbook(source, data_only=True, read_only=True)
    sheets: list[SheetSummary] = []
    tables: list[TypedTable] = []
    measurements: list[TypedMeasurement] = []
    cell_count = 0
    for ws in workbook.worksheets:
        _check_cancel(cancel_check)
        if ws.sheet_state != "visible" and not (selection and selection.include_hidden):
            continue
        hidden_rows = tuple(row for row, dimension in ws.row_dimensions.items() if dimension.hidden)
        summary = SheetSummary(ws.title, ws.sheet_state, ws.max_row, ws.max_column, hidden_rows, tuple(str(item) for item in ws.merged_cells.ranges), tuple(ws.tables))
        sheets.append(summary)
        if not _in_selection(ws.title, selection):
            continue
        selected_tables = [table_name for sheet, table_name in (selection.tables if selection else ()) if sheet == ws.title]
        if selected_tables:
            selected_ranges = [ws.tables[name].ref for name in selected_tables if name in ws.tables]
        else:
            selected_ranges = [cell_range for sheet, cell_range in (selection.ranges if selection else ()) if sheet == ws.title]
        if not selected_ranges:
            selected_ranges = [f"A1:{openpyxl.utils.get_column_letter(ws.max_column)}{ws.max_row}"] if ws.max_row and ws.max_column else []
        for source_range in selected_ranges:
            min_col, min_row, max_col, max_row = _range_bounds(source_range)
            if max_row - min_row + 1 > limits.max_rows:
                raise ToolbeltError("workbook selection exceeds row limit")
            rows: list[tuple[Any, ...]] = []
            row_provenance: list[tuple[CellProvenance, ...]] = []
            for row in range(min_row, max_row + 1):
                _check_cancel(cancel_check)
                if row in hidden_rows and not (selection and selection.include_hidden_rows):
                    continue
                values: list[Any] = []
                provenance: list[CellProvenance] = []
                for column in range(min_col, max_col + 1):
                    _check_cancel(cancel_check)
                    cell = ws.cell(row, column)
                    cached_cell = cached[ws.title].cell(row, column)
                    formula = cell.value if isinstance(cell.value, str) and cell.value.startswith("=") else None
                    cached_value = _coerce(cached_cell.value) if formula else None
                    raw_value = cached_value if formula and cached_value is not None else cell.value
                    value = _coerce(raw_value)
                    if formula:
                        if isinstance(cached_value, ExcelError):
                            status = FormulaStatus.ERROR
                        elif cached_value is None:
                            status = FormulaStatus.FORMULA_WITHOUT_CACHE
                        else:
                            calculation = getattr(workbook, "calculation", None)
                            stale = bool(
                                calculation
                                and (
                                    getattr(calculation, "calcMode", None) == "manual"
                                    or getattr(calculation, "fullCalcOnLoad", False)
                                    or getattr(calculation, "forceFullCalc", False)
                                )
                            )
                            status = FormulaStatus.FORMULA_STALE_OR_UNKNOWN if stale else FormulaStatus.FORMULA_WITH_CACHE
                    else:
                        status = FormulaStatus.ERROR if isinstance(value, ExcelError) else FormulaStatus.VALUE
                    locator = CellProvenance(digest, ws.title, cell.coordinate, source_range)
                    measurement_id = f"{digest[:12]}:{ws.title}:{cell.coordinate}"
                    referenced_cells = _formula_references(formula)
                    references = tuple(sorted({sheet for sheet, _ in referenced_cells}))
                    measurements.append(TypedMeasurement(measurement_id, value, _excel_type(raw_value), formula, cached_value, status, locator, references, referenced_cells))
                    values.append(value)
                    provenance.append(locator)
                    cell_count += 1
                    if cell_count > limits.max_cells:
                        raise ToolbeltError("workbook selection exceeds cell limit")
                rows.append(tuple(values))
                row_provenance.append(tuple(provenance))
            header_rows = min(1, len(rows))
            if len(rows) > 1 and sum(value not in (None, "") for value in rows[0]) <= 1 and sum(value not in (None, "") for value in rows[1]) > 1:
                header_rows = 2
            headers = tuple(tuple("" if value is None else str(value) for value in rows[index]) for index in range(header_rows))
            table_id = f"{digest[:12]}:{ws.title}:{source_range}"
            related = tuple(
                measurement.provenance
                for measurement in measurements
                if measurement.formula and measurement.provenance.sheet == ws.title and measurement.provenance.range == source_range
            )
            tables.append(TypedTable(table_id, selected_tables[0] if selected_tables else source_range, ws.title, headers, tuple(rows[header_rows:]), tuple(row_provenance[header_rows:]), ws.sheet_state != "visible", source_range, related))
    finalized_tables = []
    for table in tables:
        related = list(table.related_provenance)
        for measurement in measurements:
            if measurement.provenance.range != table.source_range or measurement.provenance.sheet != table.sheet:
                continue
            related.extend(CellProvenance(digest, sheet, coordinate, f"{sheet}!{coordinate}") for sheet, coordinate in measurement.cross_sheet_cells)
        finalized_tables.append(replace(table, related_provenance=tuple(dict.fromkeys(related))))
    cached.close()
    workbook.close()
    return WorkbookReadResult(str(source), digest, tuple(sheets), tuple(finalized_tables), tuple(measurements))


def _rows(table: TypedTable) -> list[dict[str, Any]]:
    columns = table.columns
    return [dict(zip(columns, row, strict=False)) for row in table.rows]


def data_analysis(
    table: TypedTable,
    operation: AnalysisOperation,
    limits: ToolbeltLimits | None = None,
    *,
    cancel_check: Callable[[], bool] | None = None,
) -> AnalysisResult:
    limits = limits or ToolbeltLimits()
    _check_cancel(cancel_check)
    rows = _rows(table)
    kind = operation.kind.lower()
    warnings: list[str] = []
    if operation.filters:
        for column, comparator, expected in operation.filters:
            if comparator == "eq":
                rows = [row for row in rows if row.get(column) == expected]
            elif comparator == "neq":
                rows = [row for row in rows if row.get(column) != expected]
            elif comparator == "gt":
                rows = [row for row in rows if row.get(column) is not None and row.get(column) > expected]
            elif comparator == "gte":
                rows = [row for row in rows if row.get(column) is not None and row.get(column) >= expected]
            elif comparator == "lt":
                rows = [row for row in rows if row.get(column) is not None and row.get(column) < expected]
            elif comparator == "lte":
                rows = [row for row in rows if row.get(column) is not None and row.get(column) <= expected]
            else:
                raise ToolbeltError(f"unsupported filter comparator: {comparator}")
    if kind == "join":
        if operation.join_table is None or len(operation.join_keys) != 2:
            raise ToolbeltError("join requires join_table and two join keys")
        right_rows = _rows(operation.join_table)
        left_key, right_key = operation.join_keys
        right_index: dict[Any, list[dict[str, Any]]] = {}
        for row in right_rows:
            right_index.setdefault(row.get(right_key), []).append(row)
        duplicate_keys = sorted((key for key, matches in right_index.items() if len(matches) > 1), key=repr)
        if duplicate_keys and not operation.many_to_many:
            raise ToolbeltError("duplicate join keys require many_to_many=True")
        result = []
        for row in rows:
            matches = right_index.get(row.get(left_key), [])
            for match in matches:
                result.append({**row, **{f"right.{name}": value for name, value in match.items()}})
                if len(result) > limits.max_result_rows:
                    raise ToolbeltError("analysis result exceeds row limit")
        if duplicate_keys:
            warnings.append("many-to-many join expanded duplicate right-side keys")
    elif kind in {"nulls", "missing"}:
        result = [{"column": column, "missing": sum(row.get(column) is None for row in rows)} for column in table.columns]
    elif kind == "duplicates":
        seen: dict[tuple[Any, ...], int] = {}
        for row in rows:
            key = tuple(row.get(column) for column in (operation.key_columns or table.columns))
            seen[key] = seen.get(key, 0) + 1
        result = [{"key": key, "count": count} for key, count in sorted(seen.items(), key=lambda item: repr(item[0])) if count > 1]
    elif kind in {"aggregate", "sum", "mean"}:
        if not operation.value_column:
            raise ToolbeltError("aggregate requires value_column")
        values = [row.get(operation.value_column) for row in rows if row.get(operation.value_column) is not None]
        if any(isinstance(value, ExcelError) for value in values):
            raise ToolbeltError("cannot aggregate Excel errors")
        total = sum(float(value) for value in values)
        result = [{"count": len(values), "sum": total, "mean": total / len(values) if values else None}]
        if len(values) != len(rows):
            warnings.append("null values reported and excluded from aggregate")
    elif kind in {"scenario", "sensitivity"}:
        if not operation.value_column:
            raise ToolbeltError("scenario analysis requires value_column")
        base = sum(float(row[operation.value_column]) for row in rows if row.get(operation.value_column) is not None)
        if kind == "scenario":
            result = [{"scenario": name, "value": base * float(multiplier)} for name, multiplier in operation.scenarios]
        else:
            result = [{"parameter": name, "value": base * float(value)} for name, values in operation.sensitivity for value in values]
    elif kind == "compare":
        if len(operation.columns) != 2:
            raise ToolbeltError("compare requires two columns")
        result = [{"left": row.get(operation.columns[0]), "right": row.get(operation.columns[1]), "delta": (row.get(operation.columns[1]) or 0) - (row.get(operation.columns[0]) or 0)} for row in rows]
    else:
        raise ToolbeltError(f"unsupported analysis operation: {operation.kind}")
    if len(result) > limits.max_result_rows:
        raise ToolbeltError("analysis result exceeds row limit")
    _check_cancel(cancel_check)
    provenance = tuple(dict.fromkeys((*[locator for row in table.row_provenance for locator in row], *table.related_provenance)))
    if kind == "join" and operation.join_table is not None:
        provenance = tuple(dict.fromkeys((*provenance, *[locator for row in operation.join_table.row_provenance for locator in row], *operation.join_table.related_provenance)))
    key = hashlib.sha256(repr((operation, result, provenance)).encode()).hexdigest()
    return AnalysisResult(operation.kind, tuple(result), provenance, key, tuple(warnings))


def _numeric(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, ExcelError) or value is None:
        raise ToolbeltError("calculation input is unavailable")
    match = re.search(r"=([-+]?[0-9]+(?:\.[0-9]+)?)", str(value))
    if not match:
        raise ToolbeltError("calculation input is not numeric")
    return float(match.group(1))


def calculation(inputs: Sequence[Evidence | CalculationRecord | TypedMeasurement], formula: FormulaSpec, units: UnitSpec) -> CalculationRecord:
    if any(isinstance(item, TypedMeasurement) and item.formula_status in {FormulaStatus.FORMULA_WITHOUT_CACHE, FormulaStatus.FORMULA_STALE_OR_UNKNOWN, FormulaStatus.ERROR} for item in inputs):
        raise ToolbeltError("BLOCKED_RECALCULATION: formula input is not trustworthy")
    values = [_numeric(item.value if isinstance(item, TypedMeasurement) else item.output if isinstance(item, CalculationRecord) else item.excerpt) for item in inputs]
    input_units = {
        item.source_locator.units for item in inputs if isinstance(item, Evidence)
    } | {
        item.units for item in inputs if isinstance(item, CalculationRecord)
    }
    if input_units and any(value != units.units for value in input_units):
        raise ToolbeltError("unit mismatch")
    operations = {"sum": sum, "subtract": lambda values: values[0] - values[1], "multiply": lambda values: operator.mul(*values), "divide": lambda values: values[0] / values[1]}
    try:
        output = float(operations[formula.operation](values))
    except KeyError as error:
        raise ToolbeltError(f"unsupported formula operation: {formula.operation}") from error
    except ZeroDivisionError as error:
        raise ToolbeltError("divide by zero") from error
    record_id = "calculation-" + hashlib.sha256(f"{formula.expression}:{values}:{units.units}".encode()).hexdigest()[:16]
    locators = [f"{item.provenance.workbook_sha256}:{item.provenance.sheet}!{item.provenance.coordinate}" for item in inputs if isinstance(item, TypedMeasurement)]
    input_ids = [item.id for item in inputs]
    return CalculationRecord(record_id, MeasurementKey("toolbelt", formula.expression, "current", units.units), formula.expression, input_ids, output, units.units, locators)


def graph_context(graph: Any, record_id: str, limit: int = 50) -> dict[str, Any]:
    from foresight_os.graph.queries import get_context
    if limit < 1:
        raise ToolbeltError("graph limit must be positive")
    return get_context(graph, record_id, limit=min(limit, 500))


def domain_validation(value: Any) -> dict[str, Any]:
    if isinstance(value, Evidence):
        return {"valid": bool(value.id and value.excerpt and value.source_locator.file_version), "kind": "evidence"}
    if isinstance(value, dict) and {"evidence", "claims"}.issubset(value):
        validate_analysis(value)
        return {"valid": True, "kind": "analysis"}
    candidate = validate_evidence_candidate(value)
    return {"valid": True, "kind": "candidate", "candidate_id": candidate.candidate_id}


def bind_local_toolbelt() -> dict[str, Any]:
    from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership

    return {
        name: CapabilityBinding(function, kind=CapabilityBindingKind.TOOL, ownership=CapabilityOwnership.BORROWED, fingerprint=f"{name}-v1")
        for name, function in {
            "spreadsheet_read": spreadsheet_read,
            "data_analysis": data_analysis,
            "calculation": calculation,
            "graph_context": graph_context,
            "domain_validation": domain_validation,
        }.items()
    }
