from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any

from .models import AnalysisState, AnalyticalRecord, CalculationRecord, Evidence
from .relationships import relationship_rule


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


@dataclass(frozen=True)
class ChallengeObjection:
    kind: str
    target_id: str
    statement: str
    evidence_ids: tuple[str, ...] = ()
    disposition: ObjectionDisposition = ObjectionDisposition.UNRESOLVED


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
    visited = set(targets)
    queue = list(targets)
    while queue:
        current = queue.pop(0)
        for relationship in sorted(state.relationships, key=lambda item: (item.from_id, item.to_id, item.relation_type, item.id)):
            rule = relationship_rule(relationship.relation_type)
            if rule.provenance_direction == "forward" and relationship.to_id == current:
                candidate = relationship.from_id
            elif rule.provenance_direction == "reverse" and relationship.from_id == current:
                candidate = relationship.to_id
            else:
                continue
            if candidate in records and candidate not in visited:
                visited.add(candidate)
                queue.append(candidate)

    evidence_ids = set()
    assumptions: set[str] = set()
    for target_id in targets:
        target = records.get(target_id)
        if isinstance(target, AnalyticalRecord):
            evidence_ids.update(target.evidence_ids)
            assumptions.update(target.assumptions)

    calculation_ids = set(item for item in targets if isinstance(records.get(item), CalculationRecord))
    known_inputs = set(evidence_ids) | calculation_ids
    missing_inputs: set[str] = set()
    changed = True
    while changed:
        changed = False
        for calculation in sorted(state.calculations, key=lambda item: item.id):
            if calculation.id in calculation_ids or not set(calculation.input_ids) & known_inputs:
                continue
            calculation_ids.add(calculation.id)
            known_inputs.add(calculation.id)
            changed = True
            for input_id in calculation.input_ids:
                if input_id in records:
                    known_inputs.add(input_id)
                else:
                    missing_inputs.add(input_id)
    counterevidence = {
        relationship.from_id
        for relationship in state.relationships
        if relationship.relation_type.lower() == "contradicts" and relationship.to_id in visited
    }
    material_records = {
        record_id: records[record_id]
        for record_id in sorted(visited)
        if record_id in records and record_id not in evidence_ids and record_id not in calculation_ids
    }
    return {
        "target_ids": targets,
        "records": material_records,
        "evidence": {item.id: item for item in state.evidence if item.id in evidence_ids},
        "calculations": {item.id: item for item in state.calculations if item.id in calculation_ids},
        "assumptions": tuple(sorted(assumptions)),
        "counterevidence": tuple(sorted(counterevidence)),
        "missing_inputs": tuple(sorted(missing_inputs)),
    }


def build_material_fingerprint(state: AnalysisState, target_ids: tuple[str, ...] | list[str], skill_ids: tuple[str, ...] | list[str] = ()) -> str:
    material = collect_material_inputs(state, target_ids)
    payload = {
        "target_ids": material["target_ids"],
        "records": {key: asdict(value) for key, value in sorted(material["records"].items())},
        "evidence": {key: asdict(value) for key, value in sorted(material["evidence"].items())},
        "calculations": {key: asdict(value) for key, value in sorted(material["calculations"].items())},
        "assumptions": material["assumptions"],
        "counterevidence": material["counterevidence"],
        "missing_inputs": material["missing_inputs"],
        "skill_ids": tuple(sorted(set(skill_ids))),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def review_validity(state: AnalysisState, review: ReviewRecord) -> ReviewValidity:
    current = build_material_fingerprint(state, review.target_ids, review.skill_ids)
    return ReviewValidity.CURRENT if current == review.input_fingerprint else ReviewValidity.STALE


def select_review_record(state: AnalysisState, target_ids: tuple[str, ...] | list[str], skill_ids: tuple[str, ...] | list[str] = ()) -> ReviewRecord | None:
    target_key = set(target_ids)
    candidates = [
        review
        for review in state.review_records
        if target_key.issubset(set(review.target_ids))
        and tuple(sorted(review.skill_ids)) == tuple(sorted(set(skill_ids)))
        and review_validity(state, review) == ReviewValidity.CURRENT
    ]
    return min(candidates, key=lambda item: (-item.reviewed_state_revision, item.review_id), default=None)


def derive_finding_views(
    state: AnalysisState,
    target_ids: tuple[str, ...] | list[str] | None = None,
    skill_ids: tuple[str, ...] | list[str] = (),
) -> tuple[FindingView, ...]:
    records = [*state.claims, *state.implications, *state.recommendations]
    selected = set(target_ids) if target_ids is not None else {record.id for record in records}
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
            )
        )
    return tuple(views)


def accepted_consequential_recommendation(state: AnalysisState, recommendation_id: str) -> bool:
    record = next((item for item in state.recommendations if item.id == recommendation_id), None)
    if record is None:
        raise ValueError(f"unknown recommendation: {recommendation_id}")
    if collect_material_inputs(state, (recommendation_id,))["missing_inputs"]:
        return False
    view = next(iter(derive_finding_views(state, (recommendation_id,))), None)
    return bool(view and view.accepted)
