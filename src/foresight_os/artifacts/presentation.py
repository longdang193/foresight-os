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
    review_category_statuses,
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
    profile: str = "executive-six"
    template_structure: tuple[str, ...] = ()

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


@dataclass(frozen=True)
class PptxDeliveryReceipt:
    provider: str
    artifact_path: str
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


def _citation_notes(state: AnalysisState, evidence_ids: tuple[str, ...]) -> tuple[str, ...]:
    evidence = {item.id: item for item in state.evidence}
    notes = []
    for evidence_id in evidence_ids:
        item = evidence.get(evidence_id)
        if item is None:
            continue
        locator = item.source_locator
        notes.append(
            f"Citation {evidence_id}: {locator.file_version}; {locator.sheet}!{locator.range}; units={locator.units}."
        )
    return tuple(notes)


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
        + list(_citation_notes(state, evidence_ids))
        + [f"Review {check_id}: {status} ({validity})." for finding_id in finding_ids for check_id, status, validity in review_category_statuses(state, finding_id)]
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
    profile: str = "executive-six",
    template_structure: tuple[str, ...] | list[str] | None = None,
) -> PresentationSpec:
    if profile not in {"executive-six", "case-competition", "user-template"}:
        raise ValueError(f"unsupported presentation profile: {profile}")
    structure = tuple(str(item) for item in (template_structure or ()))
    if profile == "user-template" and not structure:
        raise ValueError("user-template presentation requires a supplied structure")
    if structure and len(structure) != 6:
        raise ValueError("presentation template structure must define six slide titles")
    slide_titles = structure or SLIDE_TITLES
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
        _slide_for(1, slide_titles[0], "Frame the decision, scope, and time horizon.", [], state, (f"Decision question: {_shorten(decision_question or 'Not specified')}.", f"Horizon: {_shorten(horizon)}.")),
        _slide_for(2, slide_titles[1], "Show the canonical evidence and analytical signals.", claims + implications, state),
        _slide_for(3, slide_titles[2], "Expose assumptions, uncertainty, and disconfirmation conditions.", claims + implications, state),
        _slide_for(4, slide_titles[3], "Present canonical implications and available options.", implications + recommendations, state),
        _slide_for(5, slide_titles[4], "State the accepted recommendation and its qualifications.", recommendations, state),
        _slide_for(6, slide_titles[5], "Define what to monitor and when to reassess.", recommendations + implications, state, tuple(
            dict.fromkeys(
                [
                    *(f"Monitor: {item}" for view in recommendations + implications for item in view.monitoring_indicators),
                    *(f"Reassess if: {item}" for view in recommendations + implications for item in view.disconfirmation_conditions),
                ]
            )
        )),
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
        profile=profile,
        template_structure=structure,
    )
    spec = replace(spec, spec_hash=presentation_spec_fingerprint(spec))
    validate_presentation_spec(spec, state, provisional=provisional)
    return spec


def validate_presentation_spec(spec: PresentationSpec, state: AnalysisState, *, provisional: bool = False) -> None:
    if spec.profile not in {"executive-six", "case-competition", "user-template"}:
        raise ValueError("presentation spec has an unsupported profile")
    expected_titles = spec.template_structure or SLIDE_TITLES
    if len(spec.slides) != 6 or tuple(item.title for item in spec.slides) != expected_titles:
        raise ValueError("presentation spec must contain six declared slide titles")
    if spec.profile == "case-competition" and len(spec.slides) > 20:
        raise ValueError("case-competition presentation exceeds the twenty-slide limit")
    if spec.profile == "user-template" and not spec.template_structure:
        raise ValueError("user-template presentation requires a supplied structure")
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


def _validate_delivery_receipt(spec: PresentationSpec, receipt: CanvaDeliveryReceipt | PptxDeliveryReceipt, *, destination: str) -> None:
    if receipt.source_revision != spec.analysis_revision or receipt.presentation_spec_hash != spec.spec_hash:
        raise PresentationBoundaryError("delivery receipt does not match the presentation spec")
    if not receipt.provider or receipt.confirmed_state not in {"CONFIRMED", "SUCCEEDED"}:
        raise PresentationBoundaryError("delivery receipt is not successful")
    if not receipt.last_verified_at:
        raise PresentationBoundaryError("delivery receipt is missing verification time")
    try:
        verified_at = datetime.fromisoformat(receipt.last_verified_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise PresentationBoundaryError("delivery receipt has an invalid verification time") from error
    if verified_at.tzinfo is None:
        raise PresentationBoundaryError("delivery receipt verification time must include a timezone")
    if destination == "canva" and (not isinstance(receipt, CanvaDeliveryReceipt) or not receipt.design_id):
        raise PresentationBoundaryError("Canva receipt must include a design ID")
    if destination == "pptx" and (not isinstance(receipt, PptxDeliveryReceipt) or not receipt.artifact_path):
        raise PresentationBoundaryError("PPTX receipt must include an artifact path")


def persist_delivery_receipt(store: Any, spec: PresentationSpec, receipt: CanvaDeliveryReceipt | PptxDeliveryReceipt, *, destination: str) -> AnalysisState:
    if spec.status != "CURRENT":
        raise PresentationBoundaryError("provisional presentation specs cannot be delivered")
    _validate_delivery_receipt(spec, receipt, destination=destination)
    artifact_id = f"artifact-presentation-{spec.spec_hash[:16]}"
    payload = asdict(receipt)
    payload["destination"] = destination
    payload["presentation_artifact_id"] = artifact_id
    try:
        return store.save_delivery_receipt(artifact_id, payload)
    except ValueError as error:
        if "current accepted revision" in str(error) or "stale presentation artifact" in str(error):
            raise PresentationBoundaryError(str(error)) from error
        raise PresentationBoundaryError("delivery succeeded but its local receipt could not be persisted") from error
    except Exception as error:
        raise PresentationBoundaryError("delivery succeeded but its local receipt could not be persisted") from error


def verify_persisted_delivery_receipt(state: AnalysisState, spec: PresentationSpec, *, destination: str) -> None:
    artifact_id = f"artifact-presentation-{spec.spec_hash[:16]}"
    artifact = next((item for item in state.artifacts if item.id == artifact_id), None)
    if artifact is not None and (artifact.id in state.invalidation.stale_artifact_ids or artifact.lifecycle.value != "CURRENT"):
        raise PresentationBoundaryError("persisted delivery receipt is stale")
    if state.revision_status != RevisionStatus.ACCEPTED or state.revision != spec.analysis_revision:
        raise PresentationBoundaryError("persisted delivery receipt is not for the current accepted revision")
    receipt = artifact.delivery_receipt if artifact is not None else None
    if not isinstance(receipt, dict) or receipt.get("destination") != destination or receipt.get("presentation_spec_hash") != spec.spec_hash:
        raise PresentationBoundaryError("persisted delivery receipt is missing or stale")
    if receipt.get("source_revision") != spec.analysis_revision or receipt.get("confirmed_state") not in {"CONFIRMED", "SUCCEEDED"}:
        raise PresentationBoundaryError("persisted delivery receipt does not match the presentation spec")


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
    _validate_delivery_receipt(spec, receipt, destination="canva")
    return receipt
