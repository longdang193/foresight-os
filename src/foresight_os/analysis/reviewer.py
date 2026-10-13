from dataclasses import dataclass

from foresight_os.domain.challenge import ChallengeObjection, ObjectionDisposition, ReviewOutcome
from foresight_os.domain.models import AnalyticalRecord, CalculationRecord, Evidence


@dataclass(frozen=True)
class ReviewResult:
    accepted: bool
    issues: list[str]
    corrected: bool = False
    objections: tuple[ChallengeObjection, ...] = ()
    outcome: ReviewOutcome = ReviewOutcome.PROVISIONAL
    policy_id: str = ""
    policy_version: str = ""
    skill_ids: tuple[str, ...] = ()
    skill_versions: tuple[str, ...] = ()
    skill_hashes: tuple[str, ...] = ()


def review_reasoning(
    evidence: list[Evidence],
    records: list[AnalyticalRecord],
    *,
    calculations: list[CalculationRecord] | None = None,
    policy: object | None = None,
) -> ReviewResult:
    evidence_ids = {item.id for item in evidence}
    issues = []
    objections: list[ChallengeObjection] = []
    for record in records:
        if not record.evidence_ids:
            message = f"{record.id}: missing evidence"
            issues.append(message)
            objections.append(ChallengeObjection("INSUFFICIENT_EVIDENCE", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
        elif not set(record.evidence_ids).issubset(evidence_ids):
            message = f"{record.id}: unknown evidence reference"
            issues.append(message)
            objections.append(ChallengeObjection("SOURCE_CONTRADICTION", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
        if record.basis == "DERIVED" and "forecast" not in record.statement.lower() and "capacity" not in record.statement.lower() and record.id.startswith("claim-"):
            message = f"{record.id}: derived claim needs period and unit context"
            issues.append(message)
            objections.append(ChallengeObjection("UNSUPPORTED_ASSUMPTION", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
    if any("capacity" in record.statement.lower() for record in records) and not any("conditional" in record.statement.lower() for record in records):
        message = "recommendation must address the capacity contradiction"
        issues.append(message)
        objections.append(ChallengeObjection("ALTERNATIVE_HYPOTHESIS", records[-1].id if records else "review", message, disposition=ObjectionDisposition.UNRESOLVED))
    if calculations is not None and any("formula" in item.statement.lower() for item in records) and not calculations:
        message = "calculation evidence is unavailable"
        issues.append(message)
        objections.append(ChallengeObjection("CALCULATION_ERROR", records[-1].id if records else "review", message, disposition=ObjectionDisposition.UNRESOLVED))
    policy_id = str(getattr(policy, "policy_id", ""))
    policy_version = str(getattr(policy, "version", ""))
    skill_ids = tuple(getattr(policy, "required_skill_ids", ()))
    unresolved_classification = getattr(policy, "unresolved_classification_issue", None)
    if unresolved_classification:
        issues.append(unresolved_classification)
        objections.append(ChallengeObjection("INSUFFICIENT_EVIDENCE", records[-1].id if records else "review", unresolved_classification, disposition=ObjectionDisposition.UNRESOLVED))
    accepted = not issues
    outcome = ReviewOutcome.ACCEPTED if accepted else ReviewOutcome.REJECTED
    return ReviewResult(accepted, issues, objections=tuple(objections), outcome=outcome, policy_id=policy_id, policy_version=policy_version, skill_ids=skill_ids)
