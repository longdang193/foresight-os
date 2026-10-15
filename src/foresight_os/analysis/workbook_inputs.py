from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Iterable

from foresight_os.domain.models import Evidence, SourceLocator
from foresight_os.runtime.local_toolbelt import ToolbeltError


def require_table(workbook: Any, sheet: str) -> Any:
    for table in getattr(workbook, "tables", ()):
        if table.sheet == sheet:
            return table
    raise ToolbeltError(f"required workbook sheet is missing: {sheet}")


def table_rows(table: Any) -> list[dict[str, Any]]:
    columns = tuple(getattr(table, "columns", ()))
    return [dict(zip(columns, row, strict=False)) for row in getattr(table, "rows", ())]


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
