import csv
from dataclasses import dataclass
from pathlib import Path

from foresight_os.domain.models import Evidence, SourceLocator


@dataclass(frozen=True)
class WorkbookRow:
    region: str
    period: str
    measure: str
    value: float
    units: str
    status: str
    row_number: int


def read_workbook(path: Path) -> list[WorkbookRow]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"region", "period", "measure", "value", "units", "status"}
    if not rows or set(rows[0]) != required:
        raise ValueError("workbook must contain the frozen case columns")
    return [
        WorkbookRow(
            row["region"],
            row["period"],
            row["measure"],
            float(row["value"]),
            row["units"],
            row["status"],
            index + 2,
        )
        for index, row in enumerate(rows)
    ]


def extract_evidence(path: Path, rows: list[WorkbookRow]) -> list[Evidence]:
    version = "case-001-v1"
    evidence = []
    for row in rows:
        evidence.append(
            Evidence(
                id=f"evidence-{row.region.lower().replace(' ', '-')}-{row.measure}-{row.period}",
                source_locator=SourceLocator(
                    file_version=version,
                    sheet="Demand",
                    range=f"A{row.row_number}:F{row.row_number}",
                    units=row.units,
                    transformation="none",
                    calculation="source value",
                ),
                version=version,
                date=f"{row.period}-01-01",
                excerpt=f"{row.region} {row.period} {row.measure}={row.value:g} {row.units} ({row.status}).",
                limitations=["Synthetic case; capacity expansion cost is not included."],
            )
        )
    return evidence
