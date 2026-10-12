import csv
import re
from dataclasses import dataclass
from pathlib import Path

from foresight_os.domain.models import CalculationRecord, Evidence, MeasurementKey, SourceLocator


@dataclass(frozen=True)
class WorkbookRow:
    region: str
    period: str
    measure: str
    value: float
    units: str
    status: str
    row_number: int
    scenario: str = "default"
    version: str = "v1"

    @property
    def measurement_key(self) -> MeasurementKey:
        return MeasurementKey(self.region, self.measure, self.period, self.units, self.scenario, self.version)


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
                measurement_key=row.measurement_key,
            )
        )
    return evidence


def calculate_case_metrics(evidence: list[Evidence] | list[WorkbookRow]) -> dict[str, CalculationRecord]:
    if evidence and isinstance(evidence[0], WorkbookRow):
        evidence = extract_evidence(Path("workbook.csv"), evidence)
    values: dict[MeasurementKey, tuple[Evidence, float]] = {}
    for item in evidence:
        if item.measurement_key is None:
            raise ValueError(f"evidence {item.id} is missing measurement identity")
        match = re.search(r"=([-+]?[0-9]+(?:\.[0-9]+)?)", item.excerpt)
        if not match:
            raise ValueError(f"evidence {item.id} is missing a numeric value")
        if item.measurement_key in values:
            raise ValueError(f"duplicate measurement key: {item.measurement_key}")
        values[item.measurement_key] = (item, float(match.group(1)))

    def find(region: str, measure: str, period: str) -> tuple[Evidence, float]:
        matches = [(item, value) for key, (item, value) in values.items() if key.region == region and key.measure == measure and key.period == period]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one {measure} measurement for {period}")
        return matches[0]

    demand_2024, demand_start = find("Northern Europe", "demand_index", "2024")
    demand_2030, demand_end = find("Northern Europe", "demand_index", "2030")
    capacity_2030, capacity_end = find("Northern Europe", "capacity_index", "2030")
    return {
        "northern-demand-growth": CalculationRecord(
            "calculation-northern-demand-growth",
            MeasurementKey("Northern Europe", "demand_growth", "2024-2030", demand_2030.source_locator.units, demand_2030.measurement_key.scenario, demand_2030.measurement_key.version),
            "demand_2030 - demand_2024",
            [demand_2024.id, demand_2030.id],
            demand_end - demand_start,
            demand_2030.source_locator.units,
            [demand_2024.source_locator.range, demand_2030.source_locator.range],
        ),
        "northern-capacity-gap": CalculationRecord(
            "calculation-northern-capacity-gap",
            MeasurementKey("Northern Europe", "capacity_gap", "2030", demand_2030.source_locator.units, demand_2030.measurement_key.scenario, demand_2030.measurement_key.version),
            "demand_2030 - capacity_2030",
            [demand_2030.id, capacity_2030.id],
            demand_end - capacity_end,
            demand_2030.source_locator.units,
            [demand_2030.source_locator.range, capacity_2030.source_locator.range],
        ),
    }
