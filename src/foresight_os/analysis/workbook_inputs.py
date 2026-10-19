from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.domain.models import Evidence, SourceLocator
from foresight_os.runtime.local_toolbelt import (
    CellProvenance,
    MissingWorkbookInputError,
    SheetSelection,
    SourceSnapshot,
    ToolbeltError,
    ToolbeltLimits,
    TypedTable,
    WorkbookReadResult,
    spreadsheet_read,
)


def default_workbook_contract(domain: str) -> AnalysisInputContract:
    defaults = {
        "portfolio_resilience": AnalysisInputContract(
            domain="portfolio_resilience",
            required_tables=("Brief", "Sales_History", "Fixed_Costs", "Scenario_Assumptions", "Strategic_Options", "Reported_KPIs"),
            periods=("2026", "2025"),
            baseline_period="2026",
            comparison_period="2025",
            scenarios=("Downside", "Base", "Upside"),
            units="EUR",
            reporting_currency="EUR",
            compatibility_assumption="legacy workbook metadata defaults",
        ),
        "supplier_resilience": AnalysisInputContract(
            domain="supplier_resilience",
            required_tables=("Brief", "Supplier_Master", "Incidents", "Scenario_Assumptions", "Mitigation_Options"),
            units="EUR",
            reporting_currency="EUR",
            conversion_rates={"EUR": 1.0, "USD": 0.92, "CNY": 0.13},
            compatibility_assumption="legacy supplier workbook FX map: EUR=1.0, USD=0.92, CNY=0.13",
        ),
        "ev_capacity_investment": AnalysisInputContract(
            domain="ev_capacity_investment",
            required_tables=("Brief", "Demand_History", "Demand_Scenarios", "Capacity", "Infrastructure", "Policy_Signals", "Strategic_Options", "Reported_KPIs"),
            periods=("2025", "2026", "2030"),
            scenarios=("Low", "Base", "High"),
            units="units",
            compatibility_assumption="legacy workbook scenario defaults",
        ),
        "technology_radar": AnalysisInputContract(
            domain="technology_radar",
            required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
            units="index",
            compatibility_assumption="legacy technology radar scope",
        ),
        "powerbi_strategic_portfolio": AnalysisInputContract(
            domain="powerbi_strategic_portfolio",
            required_tables=("Brief", "Dim_Region", "Dim_Segment", "Fact_Performance", "Targets", "Forward_Signals", "Measure_Definitions", "Dashboard_Snapshot", "Strategic_Options", "Change_One_Input"),
            baseline_period="2025-01:2025-09",
            comparison_period="2026-01:2026-09",
            units="EUR",
            periods=("2025-01:2025-09", "2026-01:2026-09"),
            compatibility_assumption="legacy Power BI comparable-period defaults",
        ),
    }
    try:
        return defaults[str(domain)]
    except KeyError as exc:
        raise ValueError(f"unsupported workbook analysis domain: {domain}") from exc


_WORKBOOK_ANALYZER_VERSIONS = {
    "portfolio_resilience": "1",
    "supplier_resilience": "1",
    "ev_capacity_investment": "1",
    "technology_radar": "1",
    "powerbi_strategic_portfolio": "1",
}


def workbook_analyzer_version(domain: str) -> str:
    try:
        return _WORKBOOK_ANALYZER_VERSIONS[str(domain)]
    except KeyError as exc:
        raise ValueError(f"unsupported workbook analysis domain: {domain}") from exc


def workbook_analyzer_fingerprint(domain: str) -> str:
    payload = f"{domain}:{workbook_analyzer_version(domain)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class WorkbookLayoutSpec:
    """Logical workbook bindings required by one deterministic analyzer."""

    domain: str
    required_tables: tuple[str, ...] = ()
    table_aliases: tuple[tuple[str, str], ...] = ()
    required_columns: tuple[tuple[str, tuple[str, ...]], ...] = ()
    selection: SheetSelection | None = None
    scope_columns: tuple[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], ...] = ()
    required_scope_dimensions: tuple[tuple[str, tuple[str, ...]], ...] = ()
    unit_policy: str = "preserve"

    @classmethod
    def from_contract(cls, contract: AnalysisInputContract) -> "WorkbookLayoutSpec":
        raw_selection = dict(contract.workbook_selection)
        aliases = {str(key): str(value) for key, value in raw_selection.get("table_aliases", {}).items()}
        sheet_aliases = {str(key): str(value) for key, value in raw_selection.get("sheet_aliases", {}).items()}
        explicit_selection = any(
            key in raw_selection
            for key in ("sheet", "sheet_names", "ranges", "range", "tables", "table")
        )
        if explicit_selection:
            sheet_names = raw_selection.get("sheet_names", raw_selection.get("sheet", ())) or ()
            if isinstance(sheet_names, str):
                sheet_names = (sheet_names,)
            sheet_names = tuple(sheet_aliases.get(str(item), str(item)) for item in sheet_names)
            ranges = raw_selection.get("ranges", raw_selection.get("range", ())) or ()
            if isinstance(ranges, str):
                ranges = ((raw_selection.get("sheet", ""), ranges),)
            if ranges and isinstance(ranges[0], str):
                ranges = ((raw_selection.get("sheet", ""), ranges[0]),)
            normalized_ranges = tuple((sheet_aliases.get(str(item[0]), str(item[0])), str(item[1])) for item in ranges)
            tables = raw_selection.get("tables", raw_selection.get("table", ())) or ()
            if isinstance(tables, str):
                tables = (tables,)
            if tables and isinstance(tables[0], str):
                tables = (tables,)
            normalized_tables = tuple(
                (sheet_aliases.get(str(item[0]), str(item[0])), aliases.get(str(item[1]), str(item[1])))
                for item in tables
            )
            selection = SheetSelection(
                sheet_names=sheet_names,
                ranges=normalized_ranges,
                tables=normalized_tables,
                include_hidden=bool(raw_selection.get("include_hidden", False)),
                include_hidden_rows=bool(raw_selection.get("include_hidden_rows", False)),
            )
        else:
            physical_names = tuple(dict.fromkeys(aliases.get(str(item), str(item)) for item in contract.required_tables))
            selection = SheetSelection(
                sheet_names=physical_names,
                include_hidden=bool(raw_selection.get("include_hidden", True)),
                include_hidden_rows=bool(raw_selection.get("include_hidden_rows", True)),
            ) if physical_names else None

        raw_scope_columns = raw_selection.get("scope_columns", {})
        scope_columns: list[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]]] = []
        if isinstance(raw_scope_columns, Mapping):
            for logical_name, dimensions in raw_scope_columns.items():
                normalized_dimensions: list[tuple[str, tuple[str, ...]]] = []
                if isinstance(dimensions, Mapping):
                    for dimension, columns in dimensions.items():
                        if isinstance(columns, str):
                            columns = (columns,)
                        normalized_dimensions.append((str(dimension), tuple(str(column) for column in columns)))
                scope_columns.append((str(logical_name), tuple(sorted(normalized_dimensions))))
        raw_required_scope = raw_selection.get("required_scope_dimensions", {})
        required_scope_dimensions: list[tuple[str, tuple[str, ...]]] = []
        if isinstance(raw_required_scope, Mapping):
            for logical_name, dimensions in raw_required_scope.items():
                if isinstance(dimensions, str):
                    dimensions = (dimensions,)
                required_scope_dimensions.append((str(logical_name), tuple(str(item) for item in dimensions)))
        return cls(
            domain=contract.domain,
            required_tables=tuple(contract.required_tables),
            table_aliases=tuple(sorted(aliases.items())),
            required_columns=tuple(
                sorted((str(key), tuple(str(item) for item in value)) for key, value in raw_selection.get("required_columns", {}).items())
            ),
            selection=selection,
            scope_columns=tuple(sorted(scope_columns)),
            required_scope_dimensions=tuple(sorted(required_scope_dimensions)),
            unit_policy="preserve",
        )


@dataclass(frozen=True)
class ResolvedWorkbookLayout:
    source: str
    source_sha256: str
    domain: str
    bindings: tuple[tuple[str, TypedTable], ...]
    scope_columns: tuple[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], ...] = ()
    required_scope_dimensions: tuple[tuple[str, tuple[str, ...]], ...] = ()
    unit_policy: str = "preserve"
    fingerprint: str = field(default="", init=False)

    def __post_init__(self) -> None:
        payload = {
            "source": self.source,
            "source_sha256": self.source_sha256,
            "domain": self.domain,
            "bindings": [(logical, table.sheet, table.name, table.source_range, table.material_fingerprint) for logical, table in self.bindings],
            "scope_columns": self.scope_columns,
            "required_scope_dimensions": self.required_scope_dimensions,
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
        scope_columns=spec.scope_columns,
        required_scope_dimensions=spec.required_scope_dimensions,
        unit_policy=spec.unit_policy,
    )


_MISSING = object()


def _scope_value(row: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        if name in normalized:
            return normalized[name]
    return _MISSING


def _period_interval(value: Any) -> tuple[tuple[int, int], tuple[int, int]] | None:
    text = str(value).strip()
    match = re.fullmatch(r"(\d{4})(?:-Q([1-4])|-(\d{2}))?(?::(\d{4})(?:-Q([1-4])|-(\d{2}))?)?", text)
    if match is None:
        return None
    start_year = int(match.group(1))
    start_quarter = int(match.group(2)) if match.group(2) else None
    start_month = int(match.group(3)) if match.group(3) else None
    end_year = int(match.group(4) or start_year)
    end_quarter = int(match.group(5)) if match.group(5) else None
    end_month = int(match.group(6)) if match.group(6) else None
    start_key = (start_year, (start_quarter - 1) * 3 + 1 if start_quarter else start_month or 1)
    end_key = (end_year, end_quarter * 3 if end_quarter else end_month or 12)
    return start_key, end_key


def _scope_matches(value: Any, allowed: tuple[str, ...], label: str) -> bool:
    observed = str(value).strip()
    permitted = {str(item).strip() for item in allowed}
    if observed in permitted:
        return True
    if label == "period":
        observed_interval = _period_interval(observed)
        if observed_interval is None:
            return False
        observed_start, observed_end = observed_interval
        for item in permitted:
            permitted_interval = _period_interval(item)
            if permitted_interval is None:
                continue
            permitted_start, permitted_end = permitted_interval
            if permitted_start <= observed_end and observed_start <= permitted_end:
                return True
    return False


def _row_matches_scope(
    row: Mapping[str, Any],
    contract: AnalysisInputContract,
    *,
    scope_columns: Mapping[str, tuple[str, ...]] | None = None,
    required_dimensions: tuple[str, ...] = (),
) -> tuple[bool, str]:
    scope_columns = dict(scope_columns or {})
    checks = (
        (contract.entity_scope, ("entity", "entity_name", "company", "supplier", "region", "market"), "entity"),
        (contract.periods, ("period", "year", "date", "period_name", "quarter"), "period"),
        (contract.scenarios, ("scenario", "scenario_name"), "scenario"),
        ((contract.units,) if contract.units else (), ("unit", "units", "currency"), "unit"),
    )
    for allowed, names, label in checks:
        if not allowed:
            continue
        explicitly_bound = label in scope_columns or label in required_dimensions
        if label == "unit" and not explicitly_bound:
            continue
        bound_names = tuple(scope_columns[label]) if label in scope_columns else names
        value = _scope_value(row, bound_names)
        if value is _MISSING:
            if label in required_dimensions:
                return False, f"required_scope_{label}_missing"
            continue
        if value in (None, ""):
            if label in required_dimensions:
                return False, f"required_scope_{label}_missing"
            continue
        if not _scope_matches(value, allowed, label):
            if label == "period" and not explicitly_bound and _period_interval(value) is None:
                continue
            return False, f"out_of_scope_{label}"
    return True, ""


def build_material_view(workbook: WorkbookReadResult, layout: ResolvedWorkbookLayout, contract: AnalysisInputContract) -> MaterialView:
    material_tables: list[tuple[str, TypedTable]] = []
    rejected: list[tuple[str, int, str, tuple[CellProvenance, ...]]] = []
    scope_columns_by_table = dict(layout_scope for layout_scope in layout.scope_columns) if hasattr(layout, "scope_columns") else {}
    required_dimensions_by_table = dict(layout_required for layout_required in layout.required_scope_dimensions) if hasattr(layout, "required_scope_dimensions") else {}
    for logical_name, table in layout.bindings:
        retained_rows: list[tuple[Any, ...]] = []
        retained_provenance: list[tuple[CellProvenance, ...]] = []
        retained_measurements: list[tuple[Any, ...]] = []
        for index, row in enumerate(table.rows):
            row_mapping = dict(zip(table.columns, row, strict=False))
            keep, reason = _row_matches_scope(
                row_mapping,
                contract,
                scope_columns=dict(scope_columns_by_table.get(logical_name, ())),
                required_dimensions=required_dimensions_by_table.get(logical_name, ()),
            )
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
