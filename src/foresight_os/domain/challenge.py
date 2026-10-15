from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any

from .models import AnalysisState, AnalyticalRecord, CalculationRecord, Evidence
from .relationships import RelationIndex, relationship_rule


class ObjectionDisposition(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class ReviewOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    PROVISIONAL = "PROVISIONAL"
    REJECTED = "REJECTED"


class ReviewValidity(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class ReviewSlotStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    STALE = "STALE"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class ChallengeObjection:
    kind: str
    target_id: str
    statement: str
    evidence_ids: tuple[str, ...] = ()
    disposition: ObjectionDisposition = ObjectionDisposition.UNRESOLVED

    def validate(self, known_evidence_ids: set[str], known_calculation_ids: set[str] | None = None) -> None:
        known_calculation_ids = known_calculation_ids or set()
        if not self.kind or not self.target_id or not self.statement:
            raise ValueError("typed objection requires kind, target, and statement")
        if not set(self.evidence_ids).issubset(known_evidence_ids | known_calculation_ids):
            raise ValueError("objection references unknown provenance")
        if self.kind in {"SOURCE_CONTRADICTION", "CALCULATION_ERROR"} and not self.evidence_ids:
            raise ValueError(f"{self.kind} requires evidence or calculation provenance")


@dataclass(frozen=True)
class ReviewCheckResult:
    check_id: str
    status: ReviewSlotStatus | str
    expected: Any = None
    actual: Any = None
    delta: Any = None
    tolerance: Any = None
    source_ids: tuple[str, ...] = ()
    input_ids: tuple[str, ...] = ()
    interpretation: str = ""
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    target_ids: tuple[str, ...]
    reviewed_state_revision: int
    input_fingerprint: str
    skill_ids: tuple[str, ...] = ()
    skill_versions: tuple[str, ...] = ()
    objections: tuple[ChallengeObjection, ...] = ()
    outcome: ReviewOutcome = ReviewOutcome.PROVISIONAL
    limitations: tuple[str, ...] = ()
    unresolved_issues: tuple[str, ...] = ()
    policy_id: str = ""
    policy_version: str = ""
    skill_hashes: tuple[str, ...] = ()
    check_id: str = ""
    reviewer_id: str = ""
    execution_id: str = ""
    attempt_id: str = ""
    method: str = ""
    source_fingerprints: tuple[str, ...] = ()
    dependency_fingerprints: tuple[tuple[str, str], ...] = ()
    slot_key: str = ""
    supersedes_review_id: str | None = None
    superseded_by_review_id: str | None = None
    conflict_review_ids: tuple[str, ...] = ()
    check_results: tuple[ReviewCheckResult, ...] = ()
    legacy: bool = False

    @property
    def is_legacy(self) -> bool:
        return self.legacy or not all((self.check_id, self.reviewer_id, self.execution_id, self.attempt_id, self.method))

    @property
    def effective_slot_key(self) -> str:
        return self.slot_key or "|".join((self.check_id, self.policy_id, self.policy_version, self.input_fingerprint, self.method))


@dataclass(frozen=True)
class FindingView:
    target_id: str
    statement: str
    assessment: str
    evidence_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    uncertainty: tuple[str, ...]
    review_status: str
    review_outcome: str | None
    limitations: tuple[str, ...]
    accepted: bool
    counterevidence_ids: tuple[str, ...] = ()
    confidence_rationale: str = ""
    disconfirmation_conditions: tuple[str, ...] = ()
    unresolved_issues: tuple[str, ...] = ()
    implications: tuple[str, ...] = ()
    monitoring_indicators: tuple[str, ...] = ()


def finding_summary_status(finding: FindingView) -> str:
    if finding.unresolved_issues:
        return "correction-needed"
    if finding.review_status != ReviewValidity.CURRENT.value or finding.review_outcome != ReviewOutcome.ACCEPTED.value:
        return "human-review-pending"
    if finding.limitations or finding.uncertainty or finding.counterevidence_ids or not finding.accepted:
        return "uncertain"
    return "supported"


@dataclass(frozen=True)
class ChallengeProposal:
    agreements: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    counterevidence: tuple[str, ...] = ()
    unsupported_assumptions: tuple[str, ...] = ()
    proposed_changes: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def validate(self, known_evidence_ids: set[str]) -> None:
        if not self.evidence_ids:
            raise ValueError("challenge proposal requires evidence")
        if not set(self.evidence_ids).issubset(known_evidence_ids):
            raise ValueError("challenge proposal references unknown evidence")
        if self.unsupported_assumptions and not self.unresolved_questions:
            raise ValueError("unsupported assumptions require unresolved questions")


def _records(state: AnalysisState) -> dict[str, Any]:
    return {
        item.id: item
        for collection in (state.evidence, state.claims, state.implications, state.recommendations, state.artifacts, state.calculations)
        for item in collection
    }


def collect_material_inputs(state: AnalysisState, target_ids: tuple[str, ...] | list[str]) -> dict[str, Any]:
    records = _records(state)
    targets = tuple(sorted(set(target_ids)))
    index = RelationIndex.from_state(state)
    visited = {item for item in index.material_closure(targets) if item in records}
    visited.update(targets)

    evidence_ids: set[str] = set()
    assumptions: set[str] = set()
    uncertainty: set[str] = set()
    for record_id in sorted(visited):
        record = records.get(record_id)
        if isinstance(record, AnalyticalRecord):
            evidence_ids.update(record.evidence_ids)
            assumptions.update(record.assumptions)
            uncertainty.update(record.uncertainty)

    calculation_ids = set(item for item in targets if isinstance(records.get(item), CalculationRecord))
    known_inputs = set(evidence_ids) | calculation_ids | visited
    missing_inputs: set[str] = set()
    changed = True
    while changed:
        changed = False
        for calculation in sorted(state.calculations, key=lambda item: item.id):
            selected = calculation.id in calculation_ids or bool(set(calculation.input_ids) & known_inputs)
            if not selected:
                continue
            if calculation.id not in calculation_ids:
                calculation_ids.add(calculation.id)
                known_inputs.add(calculation.id)
                changed = True
            for input_id in calculation.input_ids:
                if input_id in records:
                    known_inputs.add(input_id)
                    if isinstance(records[input_id], Evidence):
                        evidence_ids.add(input_id)
                    elif isinstance(records[input_id], AnalyticalRecord):
                        evidence_ids.update(records[input_id].evidence_ids)
                        assumptions.update(records[input_id].assumptions)
                        uncertainty.update(records[input_id].uncertainty)
                else:
                    missing_inputs.add(input_id)
    missing_inputs.update(item for item in evidence_ids if item not in records)
    counterevidence = set(index.counterevidence_context(tuple(sorted(visited))))
    material_records = {
        record_id: records[record_id]
        for record_id in sorted(visited)
        if record_id in records and record_id not in evidence_ids and record_id not in calculation_ids
    }
    direct_record_ids = tuple(sorted(item for item in targets if item in records))
    derived_record_ids = tuple(sorted(set(material_records) - set(direct_record_ids)))
    return {
        "target_ids": targets,
        "records": material_records,
        "evidence": {item.id: item for item in state.evidence if item.id in evidence_ids},
        "calculations": {item.id: item for item in state.calculations if item.id in calculation_ids},
        "assumptions": tuple(sorted(assumptions)),
        "uncertainty": tuple(sorted(uncertainty)),
        "counterevidence": tuple(sorted(counterevidence)),
        "missing_inputs": tuple(sorted(missing_inputs)),
        "provenance": {
            "direct": direct_record_ids,
            "derived": derived_record_ids,
        },
        "direct_record_ids": direct_record_ids,
        "derived_record_ids": derived_record_ids,
    }


def build_material_fingerprint(
    state: AnalysisState,
    target_ids: tuple[str, ...] | list[str],
    skill_ids: tuple[str, ...] | list[str] = (),
    skill_versions: tuple[str, ...] | list[str] = (),
    skill_hashes: tuple[str, ...] | list[str] = (),
    policy_identity: tuple[str, str] | None = None,
    source_fingerprints: tuple[str, ...] | list[str] = (),
    dependency_fingerprints: tuple[tuple[str, str], ...] | list[tuple[str, str]] = (),
) -> str:
    material = collect_material_inputs(state, target_ids)
    payload = {
        "target_ids": material["target_ids"],
        "records": {key: asdict(value) for key, value in sorted(material["records"].items())},
        "evidence": {key: asdict(value) for key, value in sorted(material["evidence"].items())},
        "calculations": {key: asdict(value) for key, value in sorted(material["calculations"].items())},
        "assumptions": material["assumptions"],
        "uncertainty": material["uncertainty"],
        "counterevidence": material["counterevidence"],
        "missing_inputs": material["missing_inputs"],
        "provenance": material["provenance"],
        "skill_ids": tuple(sorted(set(skill_ids))),
        "skill_versions": tuple(sorted(set(skill_versions))),
        "skill_hashes": tuple(sorted(set(skill_hashes))),
        "source_fingerprints": tuple(sorted(set(source_fingerprints))),
        "dependency_fingerprints": tuple(sorted(set(tuple(item) for item in dependency_fingerprints))),
    }
    if policy_identity is not None:
        payload["policy_identity"] = policy_identity
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def review_validity(state: AnalysisState, review: ReviewRecord) -> ReviewValidity:
    current = build_material_fingerprint(
        state,
        review.target_ids,
        review.skill_ids,
        review.skill_versions,
        review.skill_hashes,
        (review.policy_id, review.policy_version) if review.policy_id and review.policy_version else None,
        review.source_fingerprints,
        review.dependency_fingerprints,
    )
    return ReviewValidity.CURRENT if current == review.input_fingerprint else ReviewValidity.STALE


def select_review_record(
    state: AnalysisState,
    target_ids: tuple[str, ...] | list[str],
    skill_ids: tuple[str, ...] | list[str] = (),
    *,
    check_id: str | None = None,
    policy_id: str | None = None,
    policy_version: str | None = None,
    reviewer_id: str | None = None,
    include_legacy: bool = True,
) -> ReviewRecord | None:
    target_key = set(target_ids)
    candidates = [
        review
        for review in state.review_records
        if target_key.issubset(set(review.target_ids))
        and (not skill_ids or tuple(sorted(review.skill_ids)) == tuple(sorted(set(skill_ids))))
        and (check_id is None or review.check_id == check_id)
        and (policy_id is None or review.policy_id == policy_id)
        and (policy_version is None or review.policy_version == policy_version)
        and (reviewer_id is None or review.reviewer_id == reviewer_id)
        and (include_legacy or not review.is_legacy)
        and review.superseded_by_review_id is None
        and not review.conflict_review_ids
        and review_validity(state, review) == ReviewValidity.CURRENT
    ]
    return min(candidates, key=lambda item: (-item.reviewed_state_revision, item.review_id), default=None)


@dataclass(frozen=True)
class ReviewCoverage:
    target_id: str
    required_check_ids: tuple[str, ...]
    statuses: tuple[tuple[str, ReviewSlotStatus], ...]

    @property
    def complete(self) -> bool:
        return all(status == ReviewSlotStatus.PASS for _, status in self.statuses)

    @property
    def blocking(self) -> bool:
        return any(status in {ReviewSlotStatus.FAIL, ReviewSlotStatus.CONFLICT} for _, status in self.statuses)


def derive_review_coverage(
    state: AnalysisState,
    target_ids: tuple[str, ...] | list[str],
    required_check_ids: tuple[str, ...] | list[str],
    *,
    policy_id: str = "",
    policy_version: str = "",
) -> tuple[ReviewCoverage, ...]:
    coverages = []
    for target_id in target_ids:
        statuses = []
        for check_id in required_check_ids:
            records = [
                review
                for review in state.review_records
                if target_id in review.target_ids
                and review.check_id == check_id
                and not review.is_legacy
                and (not policy_id or review.policy_id == policy_id)
                and (not policy_version or review.policy_version == policy_version)
                and review.superseded_by_review_id is None
            ]
            if any(review.conflict_review_ids for review in records):
                status = ReviewSlotStatus.CONFLICT
            elif not records:
                status = ReviewSlotStatus.PENDING
            else:
                current = [review for review in records if review_validity(state, review) == ReviewValidity.CURRENT]
                if not current:
                    status = ReviewSlotStatus.STALE
                elif any(
                    review.outcome == ReviewOutcome.ACCEPTED
                    and not review.unresolved_issues
                    and _check_result_status(review, check_id) == ReviewSlotStatus.PASS
                    for review in current
                ):
                    status = ReviewSlotStatus.PASS
                elif any(
                    review.outcome == ReviewOutcome.REJECTED
                    or review.unresolved_issues
                    or _check_result_status(review, check_id) == ReviewSlotStatus.FAIL
                    for review in current
                ):
                    status = ReviewSlotStatus.FAIL
                else:
                    status = ReviewSlotStatus.PENDING
            statuses.append((check_id, status))
        coverages.append(ReviewCoverage(str(target_id), tuple(required_check_ids), tuple(statuses)))
    return tuple(coverages)


def _check_result_status(review: ReviewRecord, check_id: str) -> ReviewSlotStatus:
    result = next((item for item in review.check_results if item.check_id == check_id), None)
    if result is None:
        return ReviewSlotStatus.PASS if review.outcome == ReviewOutcome.ACCEPTED and not review.unresolved_issues else ReviewSlotStatus.FAIL
    try:
        return ReviewSlotStatus(result.status)
    except ValueError:
        return ReviewSlotStatus.PENDING


def derive_finding_views(
    state: AnalysisState,
    target_ids: tuple[str, ...] | list[str] | None = None,
    skill_ids: tuple[str, ...] | list[str] = (),
    required_check_ids: tuple[str, ...] | list[str] = (),
    *,
    policy_id: str = "",
    policy_version: str = "",
) -> tuple[FindingView, ...]:
    records = [*state.claims, *state.implications, *state.recommendations]
    selected = set(target_ids) if target_ids is not None else {record.id for record in records}
    coverage_by_target = {
        item.target_id: item
        for item in derive_review_coverage(
            state,
            tuple(selected),
            tuple(required_check_ids),
            policy_id=policy_id,
            policy_version=policy_version,
        )
    } if required_check_ids else {}
    views = []
    for record in records:
        if record.id not in selected:
            continue
        review = select_review_record(state, (record.id,), skill_ids)
        unresolved = tuple(
            objection.statement
            for objection in review.objections
            if objection.disposition == ObjectionDisposition.UNRESOLVED
        ) if review else ()
        accepted = bool(
            review
            and review.outcome == ReviewOutcome.ACCEPTED
            and not unresolved
            and not review.unresolved_issues
        )
        coverage = coverage_by_target.get(record.id)
        coverage_issues = tuple(
            f"required review check {check_id} is {status.value}"
            for check_id, status in coverage.statuses
            if status != ReviewSlotStatus.PASS
        ) if coverage else ()
        accepted = accepted and (coverage.complete if coverage else True)
        views.append(
            FindingView(
                target_id=record.id,
                statement=record.statement,
                assessment=record.assessment.value,
                evidence_ids=tuple(sorted(record.evidence_ids)),
                assumptions=tuple(record.assumptions),
                uncertainty=tuple(record.uncertainty),
                review_status=ReviewValidity.CURRENT.value if review else "PENDING_REVIEW",
                review_outcome=review.outcome.value if review else None,
                limitations=tuple(review.limitations) if review else (),
                accepted=accepted,
                counterevidence_ids=tuple(material_counterevidence(state, (record.id,))),
                confidence_rationale=record.confidence_rationale,
                disconfirmation_conditions=record.disconfirmation_conditions,
                unresolved_issues=(tuple(review.unresolved_issues) if review else tuple(material_missing_inputs(state, (record.id,)))) + coverage_issues,
                implications=tuple(item.id for item in state.implications if any(record.id == source for source in _relationship_sources(state, item.id, "informs"))),
                monitoring_indicators=record.monitoring_indicators,
            )
        )
    return tuple(views)


def review_category_statuses(state: AnalysisState, target_id: str) -> tuple[tuple[str, str, str], ...]:
    statuses: list[tuple[str, str, str]] = []
    for review in state.review_records:
        if review.is_legacy or target_id not in review.target_ids or review.superseded_by_review_id is not None:
            continue
        status = _check_result_status(review, review.check_id).value
        validity = review_validity(state, review).value
        statuses.append((review.check_id, status if validity == ReviewValidity.CURRENT.value else ReviewSlotStatus.STALE.value, validity))
    return tuple(sorted(statuses, key=lambda item: (item[0], item[2], item[1])))


def material_counterevidence(state: AnalysisState, target_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return RelationIndex.from_state(state).counterevidence_ids(target_ids)


def material_missing_inputs(state: AnalysisState, target_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(collect_material_inputs(state, target_ids)["missing_inputs"])


def _relationship_sources(state: AnalysisState, target_id: str, relation_type: str) -> tuple[str, ...]:
    return tuple(sorted(item.from_id for item in state.relationships if item.to_id == target_id and item.relation_type.lower() == relation_type))


def accepted_consequential_recommendation(state: AnalysisState, recommendation_id: str) -> bool:
    record = next((item for item in state.recommendations if item.id == recommendation_id), None)
    if record is None:
        raise ValueError(f"unknown recommendation: {recommendation_id}")
    if collect_material_inputs(state, (recommendation_id,))["missing_inputs"]:
        return False
    view = next(iter(derive_finding_views(state, (recommendation_id,))), None)
    return bool(view and view.accepted)
