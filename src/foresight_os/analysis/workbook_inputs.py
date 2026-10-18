from __future__ import annotations

import hashlib
import json
from datetime import date
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.domain.models import Evidence, SourceLocator
from foresight_os.runtime.local_toolbelt import (
    CellProvenance,
    MissingWorkbookInputError,
    SourceSnapshot,
    ToolbeltError,
    ToolbeltLimits,
    TypedTable,
    WorkbookReadResult,
    spreadsheet_read,
)


@dataclass(frozen=True)
class WorkbookLayoutSpec:
    """Logical workbook bindings required by one deterministic analyzer."""

    domain: str
    required_tables: tuple[str, ...] = ()
    table_aliases: tuple[tuple[str, str], ...] = ()
    required_columns: tuple[tuple[str, tuple[str, ...]], ...] = ()
    unit_policy: str = "preserve"

    @classmethod
    def from_contract(cls, contract: AnalysisInputContract) -> "WorkbookLayoutSpec":
        return cls(
            domain=contract.domain,
            required_tables=tuple(contract.required_tables),
            table_aliases=tuple(sorted((str(key), str(value)) for key, value in contract.workbook_selection.get("table_aliases", {}).items())),
            required_columns=tuple(
                sorted((str(key), tuple(str(item) for item in value)) for key, value in contract.workbook_selection.get("required_columns", {}).items())
            ),
            unit_policy="preserve",
        )


@dataclass(frozen=True)
class ResolvedWorkbookLayout:
    source: str
    source_sha256: str
    domain: str
    bindings: tuple[tuple[str, TypedTable], ...]
    unit_policy: str = "preserve"
    fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        payload = {
            "source": self.source,
            "source_sha256": self.source_sha256,
            "domain": self.domain,
            "bindings": [(logical, table.sheet, table.name, table.source_range, table.material_fingerprint) for logical, table in self.bindings],
            "unit_policy": self.unit_policy,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        object.__setattr__(self, "fingerprint", hashlib.sha256(encoded).hexdigest())

    def table(self, logical_name: str) -> TypedTable:
        for name, table in self.bindings:
            if name == logical_name:
                return table
        raise MissingWorkbookInputError(f"missing resolved workbook table: {logical_name}")


@dataclass(frozen=True)
class MaterialView:
    source: str
    source_sha256: str
    layout_fingerprint: str
    contract_fingerprint: str
    scope_fingerprint: str
    tables: tuple[tuple[str, TypedTable], ...]
    data_quality_rows: tuple[tuple[str, int, str, tuple[CellProvenance, ...]], ...] = ()

    @property
    def workbook_sha256(self) -> str:
        return self.source_sha256

    def table(self, logical_name: str) -> TypedTable:
        for name, table in self.tables:
            if name == logical_name:
                return table
        raise MissingWorkbookInputError(f"missing materialized workbook table: {logical_name}")


def resolve_workbook_layout(workbook: WorkbookReadResult, spec: WorkbookLayoutSpec) -> ResolvedWorkbookLayout:
    available = tuple(workbook.tables)
    aliases = dict(spec.table_aliases)
    bindings: list[tuple[str, TypedTable]] = []
    required_columns = dict(spec.required_columns)
    for logical_name in spec.required_tables:
        physical_name = aliases.get(logical_name, logical_name)
        table = next((item for item in available if item.sheet == physical_name or item.name == physical_name), None)
        if table is None:
            raise MissingWorkbookInputError(f"missing workbook table: {physical_name}")
        required = required_columns.get(logical_name, ())
        missing = [column for column in required if column not in table.columns]
        if missing:
            raise MissingWorkbookInputError(f"missing workbook columns for {logical_name}: {', '.join(missing)}")
        bindings.append((logical_name, table))
    return ResolvedWorkbookLayout(
        source=workbook.source,
        source_sha256=workbook.workbook_sha256,
        domain=spec.domain,
        bindings=tuple(bindings),
        unit_policy=spec.unit_policy,
    )


def _scope_value(row: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        if name in normalized:
            return normalized[name]
    return None


def _scope_matches(value: Any, allowed: tuple[str, ...], label: str) -> bool:
    observed = str(value).strip()
    permitted = {str(item).strip() for item in allowed}
    if observed in permitted:
        return True
    if label == "unit" and any(item.lower() in {"unit", "units", "count"} for item in permitted):
        return True
    if label == "period":
        observed_year = observed[:4]
        return any(observed_year and observed_year == item[:4] for item in permitted)
    return False


def _row_matches_scope(row: Mapping[str, Any], contract: AnalysisInputContract) -> tuple[bool, str]:
    checks = (
        (contract.entity_scope, ("entity", "entity_name", "company", "supplier", "region", "market"), "entity"),
        (contract.periods, ("period", "year", "date", "period_name", "quarter"), "period"),
        (contract.scenarios, ("scenario", "scenario_name"), "scenario"),
    )
    for allowed, names, label in checks:
        if not allowed:
            continue
        value = _scope_value(row, names)
        if value is not None and not _scope_matches(value, allowed, label):
            return False, f"out_of_scope_{label}"
    return True, ""


def build_material_view(workbook: WorkbookReadResult, layout: ResolvedWorkbookLayout, contract: AnalysisInputContract) -> MaterialView:
    material_tables: list[tuple[str, TypedTable]] = []
    rejected: list[tuple[str, int, str, tuple[CellProvenance, ...]]] = []
    for logical_name, table in layout.bindings:
        retained_rows: list[tuple[Any, ...]] = []
        retained_provenance: list[tuple[CellProvenance, ...]] = []
        retained_measurements: list[tuple[Any, ...]] = []
        for index, row in enumerate(table.rows):
            row_mapping = dict(zip(table.columns, row, strict=False))
            keep, reason = _row_matches_scope(row_mapping, contract)
            provenance = table.row_provenance[index] if index < len(table.row_provenance) else ()
            if keep:
                retained_rows.append(row)
                retained_provenance.append(provenance)
                if index < len(table.row_measurements):
                    retained_measurements.append(table.row_measurements[index])
            else:
                rejected.append((logical_name, index, reason, provenance))
        material_tables.append(
            (
                logical_name,
                TypedTable(
                    id=f"{table.id}:material:{contract.fingerprint[:12]}",
                    name=table.name,
                    sheet=table.sheet,
                    headers=table.headers,
                    rows=tuple(retained_rows),
                    row_provenance=tuple(retained_provenance),
                    hidden=table.hidden,
                    source_range=table.source_range,
                    related_provenance=table.related_provenance,
                    row_measurements=tuple(retained_measurements),
                ),
            )
        )
    scope_payload = {
        "entity_scope": contract.entity_scope,
        "periods": contract.periods,
        "scenarios": contract.scenarios,
        "units": contract.units,
    }
    scope_fingerprint = hashlib.sha256(json.dumps(scope_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()
    return MaterialView(
        source=workbook.source,
        source_sha256=workbook.workbook_sha256,
        layout_fingerprint=layout.fingerprint,
        contract_fingerprint=contract.fingerprint,
        scope_fingerprint=scope_fingerprint,
        tables=tuple(material_tables),
        data_quality_rows=tuple(rejected),
    )


def read_workbook(
    source: Any,
    selection: Mapping[str, Any] | None = None,
    limits: Mapping[str, Any] | None = None,
    *,
    workbook_context: Any | None = None,
    cancel_check: Any | None = None,
) -> Any:
    if workbook_context is not None:
        return workbook_context.read(source, selection, limits, cancel_check=cancel_check)
    read_limits = limits or {}
    snapshot = SourceSnapshot.capture(
        source,
        cancel_check=cancel_check,
        max_bytes=int(read_limits.get("max_bytes", ToolbeltLimits().max_bytes)),
    )
    return spreadsheet_read(source, selection, limits, cancel_check=cancel_check, _snapshot=snapshot)


def require_table(workbook: Any, sheet: str) -> Any:
    if isinstance(workbook, MaterialView):
        return workbook.table(sheet)
    for table in getattr(workbook, "tables", ()):
        if table.sheet == sheet:
            return table
    raise ToolbeltError(f"required workbook sheet is missing: {sheet}")


def table_rows(table: Any) -> list[dict[str, Any]]:
    columns = tuple(getattr(table, "columns", ()))
    return [dict(zip(columns, row, strict=False)) for row in getattr(table, "rows", ())]


def validate_mapping_targets(headers: Iterable[str], mappings: Mapping[str, str] | None) -> None:
    if not mappings:
        return
    available = {str(header) for header in headers}
    missing = [
        (str(canonical), str(source))
        for canonical, source in mappings.items()
        if str(source) not in available
    ]
    if missing:
        details = ", ".join(f"{source} for canonical column {canonical}" for canonical, source in missing)
        raise ToolbeltError(f"MISSING_MAPPED_COLUMN: source column(s) {details} are absent")


def apply_column_mappings(
    rows: Iterable[dict[str, Any]],
    mappings: Mapping[str, str] | None,
    *,
    available_headers: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in rows]
    if not mappings:
        return rows
    validate_mapping_targets(
        available_headers if available_headers is not None else (column for row in rows for column in row),
        mappings,
    )
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for canonical, source in mappings.items():
            if source in row:
                item[str(canonical)] = row[source]
        normalized.append(item)
    return normalized


def apply_table_column_mappings(
    table: Any,
    rows: Iterable[dict[str, Any]],
    mappings: Mapping[str, str] | None,
    consumed_canonical_columns: Iterable[str],
) -> list[dict[str, Any]]:
    consumed = {str(column) for column in consumed_canonical_columns}
    table_mappings = {
        str(canonical): str(source)
        for canonical, source in (mappings or {}).items()
        if str(canonical) in consumed
    }
    return apply_column_mappings(
        rows,
        table_mappings,
        available_headers=getattr(table, "columns", ()),
    )


def require_row_columns(rows: Iterable[dict[str, Any]], sheet: str, columns: Iterable[str]) -> None:
    available = {str(column) for row in rows for column in row}
    missing = [str(column) for column in columns if str(column) not in available]
    if missing:
        raise ToolbeltError(f"MISSING_MAPPED_COLUMN: sheet {sheet} is missing required canonical column(s): {', '.join(missing)}")


def require_columns(table: Any, columns: Iterable[str]) -> None:
    available = set(str(item) for item in getattr(table, "columns", ()))
    missing = [str(column) for column in columns if str(column) not in available]
    if missing:
        raise ToolbeltError(f"sheet {getattr(table, 'sheet', '')} is missing required column(s): {', '.join(missing)}")


def row_range(table: Any, index: int) -> str:
    provenance = getattr(table, "row_provenance", ())[index]
    if not provenance:
        return f"row:{index + 1}"
    return f"{provenance[0].coordinate}:{provenance[-1].coordinate}"


def row_evidence(
    table: Any,
    index: int,
    digest: str,
    calculation: str,
    *,
    units: str = "unknown",
    transformation: str = "workbook_inputs",
    evidence_prefix: str | None = None,
) -> Evidence:
    values = dict(zip(getattr(table, "columns", ()), table.rows[index], strict=False))
    source_range = row_range(table, index)
    prefix = evidence_prefix or str(getattr(table, "sheet", "table")).lower()
    evidence_id = f"{prefix}-evidence-" + hashlib.sha256(f"{digest}:{table.sheet}:{source_range}:{calculation}".encode("utf-8")).hexdigest()[:16]
    return Evidence(
        evidence_id,
        SourceLocator(digest, str(table.sheet), source_range, units, transformation, calculation),
        digest,
        date.today().isoformat(),
        json.dumps(values, sort_keys=True, default=str),
    )


def brief_metadata(table: Any) -> dict[str, str]:
    metadata: dict[str, str] = {}
    rows = table_rows(table)
    for row in rows:
        if len(row) < 2:
            continue
        key = str(next(iter(row.values()), "")).strip()
        values = list(row.values())
        if key and len(values) > 1 and values[1] not in (None, ""):
            metadata[key] = str(values[1]).strip()
    return metadata
