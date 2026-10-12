from dataclasses import dataclass

from foresight_os.domain.models import AnalyticalRecord, Evidence


@dataclass(frozen=True)
class ReviewResult:
    accepted: bool
    issues: list[str]
    corrected: bool = False


def review_reasoning(evidence: list[Evidence], records: list[AnalyticalRecord]) -> ReviewResult:
    evidence_ids = {item.id for item in evidence}
    issues = []
    for record in records:
        if not record.evidence_ids:
            issues.append(f"{record.id}: missing evidence")
        elif not set(record.evidence_ids).issubset(evidence_ids):
            issues.append(f"{record.id}: unknown evidence reference")
        if record.basis == "DERIVED" and "forecast" not in record.statement.lower() and "capacity" not in record.statement.lower() and record.id.startswith("claim-"):
            issues.append(f"{record.id}: derived claim needs period and unit context")
    if any("capacity" in record.statement.lower() for record in records) and not any("conditional" in record.statement.lower() for record in records):
        issues.append("recommendation must address the capacity contradiction")
    return ReviewResult(not issues, issues)
