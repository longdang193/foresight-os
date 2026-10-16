from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Iterable, Mapping

from foresight_os.domain.models import Evidence, SourceLocator
from foresight_os.runtime.local_toolbelt import SourceSnapshot, ToolbeltError, ToolbeltLimits, spreadsheet_read


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
