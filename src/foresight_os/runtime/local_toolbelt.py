from __future__ import annotations

import ast
import csv
import hashlib
import operator
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

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
    max_merged_ranges: int = 10_000
    max_merged_cells_per_range: int = 100_000
    max_total_merged_cells: int = 500_000
    max_result_rows: int = 10_000


class WorkbookReadCache:
    def __init__(self, max_entries: int = 8, max_bytes: int = 50_000_000) -> None:
        self.max_entries = max(1, max_entries)
        self.max_bytes = max(1, max_bytes)
        self._entries: dict[tuple[Any, ...], tuple[WorkbookReadResult, int]] = {}
        self._analysis_entries: dict[tuple[Any, ...], tuple[AnalysisResult, int]] = {}
        self._bytes = 0

    def key(self, source: Path, selection: SheetSelection | None, limits: ToolbeltLimits) -> tuple[Any, ...]:
        canonical = str(source.resolve())
        selection_key = repr(selection)
        limit_key = repr(limits)
        return canonical, _sha256_file(source), selection_key, limit_key

    def get(self, key: tuple[Any, ...]) -> WorkbookReadResult | None:
        entry = self._entries.get(key)
        return entry[0] if entry is not None else None

    def put(self, key: tuple[Any, ...], result: WorkbookReadResult) -> None:
        estimated = max(1, len(repr(result)))
        if estimated > self.max_bytes:
            return
        previous = self._entries.pop(key, None)
        if previous is not None:
            self._bytes -= previous[1]
        while self._entries and (len(self._entries) >= self.max_entries or self._bytes + estimated > self.max_bytes):
            _, (_, size) = self._entries.pop(next(iter(self._entries)))
            self._bytes -= size
        self._entries[key] = (result, estimated)
        self._bytes += estimated

    def analysis_key(self, table: TypedTable, operation: AnalysisOperation, limits: ToolbeltLimits) -> tuple[Any, ...]:
        return ("analysis", table.id, repr(operation), repr(limits))

    def get_analysis(self, key: tuple[Any, ...]) -> AnalysisResult | None:
        entry = self._analysis_entries.get(key)
        return entry[0] if entry is not None else None

    def put_analysis(self, key: tuple[Any, ...], result: AnalysisResult) -> None:
        estimated = max(1, len(repr(result)))
        if estimated > self.max_bytes:
            return
        previous = self._analysis_entries.pop(key, None)
        if previous is not None:
            self._bytes -= previous[1]
        while self._analysis_entries and (len(self._analysis_entries) >= self.max_entries or self._bytes + estimated > self.max_bytes):
            _, (_, size) = self._analysis_entries.pop(next(iter(self._analysis_entries)))
            self._bytes -= size
        self._analysis_entries[key] = (result, estimated)
        self._bytes += estimated

    def clear(self) -> None:
        self._entries.clear()
        self._analysis_entries.clear()
        self._bytes = 0

    @property
    def size(self) -> int:
        return len(self._entries) + len(self._analysis_entries)


def _sha256_file(source: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    row_measurements: tuple[tuple[TypedMeasurement, ...], ...] = ()

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
    selected_row_count = 0
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.reader(handle, delimiter=delimiter), 1):
            _check_cancel(cancel_check)
            if range_bounds and row_number > range_bounds[3]:
                break
            if range_bounds and row_number < range_bounds[1]:
                continue
            selected_row_count += 1
            if selected_row_count > limits.max_rows:
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


def _preflight_xlsx_archive(source: Path, selection: SheetSelection | None, limits: ToolbeltLimits, cancel_check: Callable[[], bool] | None) -> None:
    namespaces = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(source) as archive:
        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships.findall("pkg:Relationship", namespaces)}
        total_row_count = 0
        total_cell_count = 0
        total_merged_range_count = 0
        total_merged_cell_count = 0
        for sheet in workbook_root.findall("main:sheets/main:sheet", namespaces):
            title = sheet.attrib["name"]
            target = targets.get(sheet.attrib.get(f"{{{namespaces['rel']}}}id"))
            if not target:
                continue
            normalized_target = target.lstrip("/")
            sheet_path = posixpath.normpath(normalized_target if normalized_target.startswith("xl/") else posixpath.join("xl", normalized_target))
            selected_ranges = [cell_range for selected_sheet, cell_range in (selection.ranges if selection else ()) if selected_sheet == title]
            bounds = [_range_bounds(cell_range) for cell_range in selected_ranges]
            for range_bounds in bounds:
                if range_bounds[3] - range_bounds[1] + 1 > limits.max_rows:
                    raise ToolbeltError("workbook selection exceeds row limit")
                if (range_bounds[3] - range_bounds[1] + 1) * (range_bounds[2] - range_bounds[0] + 1) > limits.max_cells:
                    raise ToolbeltError("workbook selection exceeds cell limit")
            with archive.open(sheet_path) as handle:
                for _, element in ET.iterparse(handle, events=("end",)):
                    _check_cancel(cancel_check)
                    if element.tag == f"{{{namespaces['main']}}}row":
                        total_row_count += 1
                        if total_row_count > limits.max_rows:
                            raise ToolbeltError("workbook allocation exceeds row limit")
                    elif element.tag == f"{{{namespaces['main']}}}c":
                        coordinate = element.attrib.get("r", "")
                        match = re.fullmatch(r"([A-Z]+)(\d+)", coordinate.upper())
                        if match:
                            total_cell_count += 1
                            if total_cell_count > limits.max_cells:
                                raise ToolbeltError("workbook allocation exceeds cell limit")
                    elif element.tag == f"{{{namespaces['main']}}}mergeCell":
                        total_merged_range_count += 1
                        if total_merged_range_count > limits.max_merged_ranges:
                            raise ToolbeltError("workbook merged range limit exceeded")
                        merged_ref = element.attrib.get("ref")
                        if merged_ref:
                            start_col, start_row, end_col, end_row = _range_bounds(merged_ref)
                            area = (end_col - start_col + 1) * (end_row - start_row + 1)
                            if area > limits.max_merged_cells_per_range:
                                raise ToolbeltError("workbook merged area exceeds per-range limit")
                            total_merged_cell_count += area
                            if total_merged_cell_count > limits.max_total_merged_cells:
                                raise ToolbeltError("workbook merged area exceeds total limit")
                    element.clear()


def spreadsheet_read(
    source: Path,
    selection: SheetSelection | None = None,
    limits: ToolbeltLimits | None = None,
    *,
    cancel_check: Callable[[], bool] | None = None,
    _cache: Any = None,
) -> WorkbookReadResult:
    limits = limits or ToolbeltLimits()
    source = Path(source)
    _check_cancel(cancel_check)
    cache_key = None
    if _cache is not None:
        cache_key = _cache.key(source, selection, limits)
        cached_result = _cache.get(cache_key)
        if cached_result is not None:
            return replace(cached_result, source=str(source))
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
    _preflight_xlsx_archive(source, selection, limits, cancel_check)
    digest = _sha256_file(source)
    workbook = None
    cached = None
    try:
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
                row_measurements: list[tuple[TypedMeasurement, ...]] = []
                source_rows = ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col)
                cached_rows = cached[ws.title].iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col)
                for source_row, cached_row in zip(source_rows, cached_rows, strict=True):
                    _check_cancel(cancel_check)
                    row = source_row[0].row
                    if row in hidden_rows and not (selection and selection.include_hidden_rows):
                        continue
                    values: list[Any] = []
                    provenance: list[CellProvenance] = []
                    row_cells: list[TypedMeasurement] = []
                    for cell, cached_cell in zip(source_row, cached_row, strict=True):
                        _check_cancel(cancel_check)
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
                        row_cells.append(measurements[-1])
                        values.append(value)
                        provenance.append(locator)
                        cell_count += 1
                        if cell_count > limits.max_cells:
                            raise ToolbeltError("workbook selection exceeds cell limit")
                    rows.append(tuple(values))
                    row_provenance.append(tuple(provenance))
                    row_measurements.append(tuple(row_cells))
                nonempty_counts = [sum(value not in (None, "") for value in row) for row in rows]
                first_dense_row = next((index for index, count in enumerate(nonempty_counts) if count > 1), None)
                if first_dense_row is not None and first_dense_row > 0 and any(count == 0 for count in nonempty_counts[:first_dense_row]):
                    rows = rows[first_dense_row:]
                    row_provenance = row_provenance[first_dense_row:]
                    row_measurements = row_measurements[first_dense_row:]
                    nonempty_counts = nonempty_counts[first_dense_row:]
                header_rows = min(1, len(rows))
                if len(rows) > 1 and nonempty_counts[0] <= 1 and nonempty_counts[1] > 1:
                    header_rows = 2
                headers = tuple(tuple("" if value is None else str(value) for value in rows[index]) for index in range(header_rows))
                table_id = f"{digest[:12]}:{ws.title}:{source_range}"
                related = tuple(
                    measurement.provenance
                    for measurement in measurements
                    if measurement.formula and measurement.provenance.sheet == ws.title and measurement.provenance.range == source_range
                )
                tables.append(TypedTable(table_id, selected_tables[0] if selected_tables else source_range, ws.title, headers, tuple(rows[header_rows:]), tuple(row_provenance[header_rows:]), ws.sheet_state != "visible", source_range, related, tuple(row_measurements[header_rows:])))
        finalized_tables = []
        for table in tables:
            related = list(table.related_provenance)
            for measurement in measurements:
                if measurement.provenance.range != table.source_range or measurement.provenance.sheet != table.sheet:
                    continue
                related.extend(CellProvenance(digest, sheet, coordinate, f"{sheet}!{coordinate}") for sheet, coordinate in measurement.cross_sheet_cells)
            finalized_tables.append(replace(table, related_provenance=tuple(dict.fromkeys(related))))
        result = WorkbookReadResult(str(source), digest, tuple(sheets), tuple(finalized_tables), tuple(measurements))
        if _cache is not None and cache_key is not None:
            _cache.put(cache_key, result)
        return result
    finally:
        if cached is not None:
            cached.close()
        if workbook is not None:
            workbook.close()


def _rows(table: TypedTable) -> list[dict[str, Any]]:
    columns = table.columns
    return [dict(zip(columns, row, strict=False)) for row in table.rows]


def _ensure_homogeneous_units(rows: Sequence[dict[str, Any]], table: TypedTable, value_column: str) -> None:
    unit_column = next((column for column in table.columns if column.strip().lower() == "unit"), None)
    if unit_column is None or not rows:
        return
    contributing_rows = [row for row in rows if row.get(value_column) is not None]
    if not contributing_rows:
        return
    units = {row.get(unit_column) for row in contributing_rows}
    if None in units or "" in units:
        raise ToolbeltError("unit unavailable for numeric analysis")
    if len(units) > 1:
        raise ToolbeltError("unit mismatch across numeric analysis rows")


def data_analysis(
    table: TypedTable,
    operation: AnalysisOperation,
    limits: ToolbeltLimits | None = None,
    *,
    cancel_check: Callable[[], bool] | None = None,
    _cache: Any = None,
) -> AnalysisResult:
    limits = limits or ToolbeltLimits()
    _check_cancel(cancel_check)
    analysis_cache_key = None
    if _cache is not None and hasattr(_cache, "analysis_key"):
        analysis_cache_key = _cache.analysis_key(table, operation, limits)
        cached_result = _cache.get_analysis(analysis_cache_key)
        if cached_result is not None:
            return cached_result
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
        _ensure_homogeneous_units(rows, table, operation.value_column)
        value_index = table.columns.index(operation.value_column)
        selected_measurements = [
            row[value_index]
            for row in table.row_measurements
            if len(row) > value_index
        ]
        if any(item.formula_status in {FormulaStatus.FORMULA_WITHOUT_CACHE, FormulaStatus.FORMULA_STALE_OR_UNKNOWN, FormulaStatus.ERROR} for item in selected_measurements):
            raise ToolbeltError("BLOCKED_RECALCULATION: formula input is not trustworthy")
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
        _ensure_homogeneous_units(rows, table, operation.value_column)
        base = sum(float(row[operation.value_column]) for row in rows if row.get(operation.value_column) is not None)
        if kind == "scenario":
            result = [{"scenario": name, "value": base * float(multiplier)} for name, multiplier in operation.scenarios]
        else:
            result = [{"parameter": name, "value": base * float(value)} for name, values in operation.sensitivity for value in values]
    elif kind == "compare":
        if len(operation.columns) != 2:
            raise ToolbeltError("compare requires two columns")
        left_column, right_column = operation.columns
        result = []
        for row in rows:
            left = row.get(left_column)
            right = row.get(right_column)
            result.append({
                "left": left,
                "right": right,
                "delta": None if left is None or right is None else right - left,
                "status": "INCOMPLETE_INPUT" if left is None or right is None else "COMPLETE",
            })
    else:
        raise ToolbeltError(f"unsupported analysis operation: {operation.kind}")
    if len(result) > limits.max_result_rows:
        raise ToolbeltError("analysis result exceeds row limit")
    _check_cancel(cancel_check)
    provenance = tuple(dict.fromkeys((*[locator for row in table.row_provenance for locator in row], *table.related_provenance)))
    if kind == "join" and operation.join_table is not None:
        provenance = tuple(dict.fromkeys((*provenance, *[locator for row in operation.join_table.row_provenance for locator in row], *operation.join_table.related_provenance)))
    key = hashlib.sha256(repr((operation, result, provenance)).encode()).hexdigest()
    analysis_result = AnalysisResult(operation.kind, tuple(result), provenance, key, tuple(warnings))
    if _cache is not None and analysis_cache_key is not None:
        _cache.put_analysis(analysis_cache_key, analysis_result)
    return analysis_result


def _numeric(value: Any, *, allow_legacy_prose: bool = False) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, ExcelError) or value is None:
        raise ToolbeltError("calculation input is unavailable")
    if not allow_legacy_prose:
        raise ToolbeltError("calculation input is not structured numeric evidence")
    match = re.search(r"=([-+]?[0-9]+(?:\.[0-9]+)?)", str(value))
    if not match:
        raise ToolbeltError("calculation input is not numeric")
    return float(match.group(1))


def _coerce_cell_provenance(value: CellProvenance | Mapping[str, Any]) -> CellProvenance:
    if isinstance(value, CellProvenance):
        return value
    if not isinstance(value, Mapping):
        raise ToolbeltError("calculation measurement provenance is unavailable")
    return CellProvenance(
        workbook_sha256=str(value.get("workbook_sha256", "")),
        sheet=str(value.get("sheet", "")),
        coordinate=str(value.get("coordinate", "")),
        range=str(value.get("range", "")),
    )


def _coerce_calculation_input(value: Evidence | CalculationRecord | TypedMeasurement | Mapping[str, Any]) -> Evidence | CalculationRecord | TypedMeasurement:
    if isinstance(value, (Evidence, CalculationRecord, TypedMeasurement)):
        return value
    if not isinstance(value, Mapping):
        raise ToolbeltError("calculation input must be structured evidence")
    if "output" in value and "key" in value:
        key_value = value["key"]
        if not isinstance(key_value, Mapping):
            raise ToolbeltError("calculation record key is unavailable")
        return CalculationRecord(
            id=str(value.get("id", "")),
            key=MeasurementKey(**{name: key_value.get(name, "") for name in ("region", "measure", "period", "units", "scenario", "version")}),
            formula=str(value.get("formula", "")),
            input_ids=[str(item) for item in value.get("input_ids", ())],
            output=float(value["output"]),
            units=str(value.get("units", "")),
            source_locators=[str(item) for item in value.get("source_locators", ())],
        )
    if "value" in value and "provenance" in value:
        status = value.get("formula_status", FormulaStatus.VALUE)
        return TypedMeasurement(
            id=str(value.get("id", "")),
            value=value.get("value"),
            data_type=str(value.get("data_type", "")),
            formula=value.get("formula"),
            cached_value=value.get("cached_value"),
            formula_status=status if isinstance(status, FormulaStatus) else FormulaStatus(str(status)),
            provenance=_coerce_cell_provenance(value["provenance"]),
            cross_sheet_references=tuple(str(item) for item in value.get("cross_sheet_references", ())),
            cross_sheet_cells=tuple(tuple(str(part) for part in item) for item in value.get("cross_sheet_cells", ())),
        )
    if "excerpt" in value and "source_locator" in value:
        locator_value = value["source_locator"]
        if not isinstance(locator_value, Mapping):
            raise ToolbeltError("evidence source locator is unavailable")
        measurement_key = value.get("measurement_key")
        return Evidence(
            id=str(value.get("id", "")),
            source_locator=SourceLocator(**{name: str(locator_value.get(name, "")) for name in ("file_version", "sheet", "range", "units", "transformation", "calculation")}),
            version=str(value.get("version", "")),
            date=str(value.get("date", "")),
            excerpt=str(value.get("excerpt", "")),
            limitations=[str(item) for item in value.get("limitations", ())],
            measurement_key=MeasurementKey(**measurement_key) if isinstance(measurement_key, Mapping) else None,
        )
    raise ToolbeltError("calculation input must be structured evidence")


def _coerce_formula_spec(value: FormulaSpec | Mapping[str, Any]) -> FormulaSpec:
    if isinstance(value, FormulaSpec):
        return value
    if not isinstance(value, Mapping):
        raise ToolbeltError("calculation formula is unavailable")
    return FormulaSpec(str(value.get("expression", "")), str(value.get("operation", "sum")))


def _coerce_unit_spec(value: UnitSpec | Mapping[str, Any]) -> UnitSpec:
    if isinstance(value, UnitSpec):
        return value
    if not isinstance(value, Mapping):
        raise ToolbeltError("calculation units are unavailable")
    return UnitSpec(str(value.get("units", "")), float(value.get("relative_tolerance", 1e-9)))


def calculation(
    inputs: Sequence[Evidence | CalculationRecord | TypedMeasurement | Mapping[str, Any]],
    formula: FormulaSpec | Mapping[str, Any],
    units: UnitSpec | Mapping[str, Any],
) -> CalculationRecord:
    inputs = tuple(_coerce_calculation_input(item) for item in inputs)
    formula = _coerce_formula_spec(formula)
    units = _coerce_unit_spec(units)
    if any(isinstance(item, TypedMeasurement) and item.formula_status in {FormulaStatus.FORMULA_WITHOUT_CACHE, FormulaStatus.FORMULA_STALE_OR_UNKNOWN, FormulaStatus.ERROR} for item in inputs):
        raise ToolbeltError("BLOCKED_RECALCULATION: formula input is not trustworthy")
    values = [
        _numeric(item.value if isinstance(item, TypedMeasurement) else item.output, allow_legacy_prose=False)
        if isinstance(item, (TypedMeasurement, CalculationRecord))
        else _numeric(item.excerpt, allow_legacy_prose=True)
        for item in inputs
    ]
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


def powerbi_project_read(source: Path | str, limits: Any = None) -> Any:
    from foresight_os.analysis.powerbi import read_powerbi_project

    return read_powerbi_project(source, limits)


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
            "powerbi_project_read": powerbi_project_read,
        }.items()
    }
