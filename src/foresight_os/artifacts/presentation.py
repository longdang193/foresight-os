from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Protocol

from foresight_os.domain.challenge import (
    ReviewValidity,
    accepted_consequential_recommendation,
    collect_material_inputs,
    derive_finding_views,
)
from foresight_os.domain.models import AnalysisState, Artifact, Relationship, RevisionStatus


SLIDE_TITLES = (
    "Decision and scope",
    "Evidence and signals",
    "Scenarios and uncertainties",
    "Strategic options",
    "Recommendation",
    "Reassessment plan",
)


@dataclass(frozen=True)
class SlideSpec:
    number: int
    title: str
    purpose: str
    bullets: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    calculation_ids: tuple[str, ...] = ()
    counterevidence_ids: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    disconfirmation_conditions: tuple[str, ...] = ()
    speaker_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PresentationSpec:
    investigation_id: str
    analysis_revision: int
    audience: str
    decision_question: str
    horizon: str
    title: str
    status: str
    slides: tuple[SlideSpec, ...]
    source_finding_ids: tuple[str, ...]
    spec_hash: str = ""

    def to_payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_hash:
            payload.pop("spec_hash", None)
        return payload


@dataclass(frozen=True)
class CanvaDeliveryReceipt:
    provider: str
    design_id: str
    source_revision: int
    presentation_spec_hash: str
    confirmed_state: str
    last_verified_at: str


class CanvaAdapter(Protocol):
    def publish(self, spec: PresentationSpec) -> CanvaDeliveryReceipt:
        ...


class PresentationBoundaryError(RuntimeError):
    pass


def presentation_spec_fingerprint(spec: PresentationSpec) -> str:
    encoded = json.dumps(spec.to_payload(include_hash=False), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _shorten(value: str, limit: int = 220) -> str:
    value = " ".join(str(value).split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _normal_state_error(state: AnalysisState) -> str | None:
    if state.invalidation.stale_artifact_ids:
        return "stale artifacts require reassessment before presentation compilation"
    if state.revision_status != RevisionStatus.ACCEPTED:
        return "normal presentations require an accepted revision"
    if any(record.assessment.value == "UNASSESSED" for record in [*state.claims, *state.implications, *state.recommendations]):
        return "normal presentations require assessed analytical records"
    if any(not accepted_consequential_recommendation(state, record.id) for record in state.recommendations):
        return "normal presentations require current accepted reviews for recommendations"
    return None


def _slide_for(
    number: int,
    title: str,
    purpose: str,
    views: list[Any],
    state: AnalysisState,
    extra_bullets: tuple[str, ...] = (),
) -> SlideSpec:
    finding_ids = tuple(item.target_id for item in views)
    material = collect_material_inputs(state, finding_ids) if finding_ids else {"evidence": {}, "calculations": {}, "uncertainty": (), "counterevidence": ()}
    evidence_ids = tuple(sorted({item for view in views for item in view.evidence_ids} | set(material["evidence"])))
    calculation_ids = tuple(sorted(material["calculations"]))
    counterevidence_ids = tuple(sorted({item for view in views for item in view.counterevidence_ids} | set(material.get("counterevidence", ()))))
    uncertainty = tuple(sorted({item for view in views for item in view.uncertainty} | set(material.get("uncertainty", ()))))
    disconfirmation = tuple(sorted({item for view in views for item in view.disconfirmation_conditions}))
    bullets = tuple(extra_bullets) + tuple(_shorten(item.statement) for item in views)
    notes = tuple(
        [
            f"Finding IDs: {', '.join(finding_ids) or 'none'}.",
            f"Evidence IDs: {', '.join(evidence_ids) or 'none'}.",
        ]
        + ([f"Calculation IDs: {', '.join(calculation_ids)}."] if calculation_ids else [])
    )
    return SlideSpec(number, title, purpose, bullets, finding_ids, evidence_ids, calculation_ids, counterevidence_ids, uncertainty, disconfirmation, notes)


def compile_presentation(
    state: AnalysisState,
    *,
    decision_question: str = "",
    horizon: str = "unspecified",
    audience: str = "decision makers",
    title: str | None = None,
    provisional: bool = False,
) -> PresentationSpec:
    if not provisional:
        error = _normal_state_error(state)
        if error:
            raise ValueError(error)
    views = list(derive_finding_views(state))
    by_id = {item.target_id: item for item in views}
    claims = [by_id[item.id] for item in state.claims if item.id in by_id]
    implications = [by_id[item.id] for item in state.implications if item.id in by_id]
    recommendations = [by_id[item.id] for item in state.recommendations if item.id in by_id]
    slides = (
        _slide_for(1, SLIDE_TITLES[0], "Frame the decision, scope, and time horizon.", [], state, (f"Decision question: {_shorten(decision_question or 'Not specified')}.", f"Horizon: {_shorten(horizon)}.")),
        _slide_for(2, SLIDE_TITLES[1], "Show the canonical evidence and analytical signals.", claims + implications, state),
        _slide_for(3, SLIDE_TITLES[2], "Expose assumptions, uncertainty, and disconfirmation conditions.", claims + implications, state),
        _slide_for(4, SLIDE_TITLES[3], "Present canonical implications and available options.", implications + recommendations, state),
        _slide_for(5, SLIDE_TITLES[4], "State the accepted recommendation and its qualifications.", recommendations, state),
        _slide_for(6, SLIDE_TITLES[5], "Define what to monitor and when to reassess.", recommendations + implications, state),
    )
    spec = PresentationSpec(
        investigation_id=state.investigation_id,
        analysis_revision=state.revision,
        audience=audience,
        decision_question=decision_question,
        horizon=horizon,
        title=title or f"{state.investigation_id} decision brief",
        status="DRAFT / UNVALIDATED" if provisional else "CURRENT",
        slides=slides,
        source_finding_ids=tuple(item.target_id for item in views),
    )
    spec = replace(spec, spec_hash=presentation_spec_fingerprint(spec))
    validate_presentation_spec(spec, state, provisional=provisional)
    return spec


def validate_presentation_spec(spec: PresentationSpec, state: AnalysisState, *, provisional: bool = False) -> None:
    if len(spec.slides) != 6 or tuple(item.title for item in spec.slides) != SLIDE_TITLES:
        raise ValueError("presentation spec must contain the fixed six-slide template")
    if spec.analysis_revision != state.revision:
        raise ValueError("presentation spec revision is stale")
    if spec.spec_hash != presentation_spec_fingerprint(spec):
        raise ValueError("presentation spec hash does not match its content")
    record_ids = {item.id for item in [*state.claims, *state.implications, *state.recommendations]}
    evidence_ids = {item.id for item in state.evidence}
    calculation_ids = {item.id for item in state.calculations}
    if not set(spec.source_finding_ids).issubset(record_ids):
        raise ValueError("presentation spec references unsupported findings")
    for slide in spec.slides:
        if not set(slide.finding_ids).issubset(record_ids) or not set(slide.evidence_ids).issubset(evidence_ids) or not set(slide.calculation_ids).issubset(calculation_ids):
            raise ValueError("presentation slide contains unsupported provenance")
    if provisional:
        if spec.status != "DRAFT / UNVALIDATED":
            raise ValueError("provisional presentation must be marked DRAFT / UNVALIDATED")
    elif spec.status != "CURRENT":
        raise ValueError("normal presentation must be marked CURRENT")
    if not provisional:
        error = _normal_state_error(state)
        if error:
            raise ValueError(error)


def presentation_artifact(state: AnalysisState, spec: PresentationSpec, path: str) -> tuple[Artifact, tuple[Relationship, ...]]:
    validate_presentation_spec(spec, state, provisional=spec.status != "CURRENT")
    relationship_ids = tuple(f"{finding_id}-produces-{spec.spec_hash[:16]}" for finding_id in spec.source_finding_ids)
    relationships = tuple(
        Relationship(relationship_id, finding_id, f"artifact-presentation-{spec.spec_hash[:16]}", "produces")
        for relationship_id, finding_id in zip(relationship_ids, spec.source_finding_ids, strict=True)
    )
    artifact = Artifact(
        f"artifact-presentation-{spec.spec_hash[:16]}",
        "presentation_spec",
        path,
        relationship_ids=list(relationship_ids),
    )
    return artifact, relationships


def publish_to_canva(spec: PresentationSpec, adapter: CanvaAdapter | None = None, *, human_approved: bool = False) -> CanvaDeliveryReceipt:
    if spec.status != "CURRENT":
        raise PresentationBoundaryError("provisional presentation specs cannot be published")
    if not human_approved:
        raise PermissionError("human approval is required before Canva mutation")
    if adapter is None:
        raise PresentationBoundaryError("Canva adapter is unavailable")
    receipt = adapter.publish(spec)
    if not isinstance(receipt, CanvaDeliveryReceipt):
        raise PresentationBoundaryError("Canva adapter must return a durable CanvaDeliveryReceipt")
    if receipt.source_revision != spec.analysis_revision or receipt.presentation_spec_hash != spec.spec_hash or not receipt.design_id:
        raise PresentationBoundaryError("Canva receipt does not match the presentation spec")
    return receipt
