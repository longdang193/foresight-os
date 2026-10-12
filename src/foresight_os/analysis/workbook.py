import csv
import re
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


@dataclass(frozen=True)
class CalculationRecord:
    id: str
    formula: str
    input_ids: tuple[str, ...]
    output: float
    units: str
    source_locators: tuple[str, ...]


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


def calculate_case_metrics(evidence: list[Evidence]) -> dict[str, CalculationRecord]:
    values: dict[str, tuple[Evidence, float]] = {}
    for item in evidence:
        match = re.search(r"=([0-9]+(?:\.[0-9]+)?)", item.excerpt)
        if match:
            values[item.id] = (item, float(match.group(1)))

    def find(measure: str, period: str) -> tuple[Evidence, float]:
        return next(value for item_id, value in values.items() if measure in item_id and period in item_id)

    demand_2024, demand_start = find("demand_index", "2024")
    demand_2030, demand_end = find("demand_index", "2030")
    capacity_2030, capacity_end = find("capacity_index", "2030")
    return {
        "northern-demand-growth": CalculationRecord(
            "calculation-northern-demand-growth",
            "demand_2030 - demand_2024",
            (demand_2024.id, demand_2030.id),
            demand_end - demand_start,
            demand_2030.source_locator.units,
            (demand_2024.source_locator.range, demand_2030.source_locator.range),
        ),
        "northern-capacity-gap": CalculationRecord(
            "calculation-northern-capacity-gap",
            "demand_2030 - capacity_2030",
            (demand_2030.id, capacity_2030.id),
            demand_end - capacity_end,
            demand_2030.source_locator.units,
            (demand_2030.source_locator.range, capacity_2030.source_locator.range),
        ),
    }
