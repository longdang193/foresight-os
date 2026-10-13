from dataclasses import replace

import pytest

from foresight_os.artifacts.presentation import (
    CanvaDeliveryReceipt,
    PresentationBoundaryError,
    compile_presentation,
    presentation_artifact,
    presentation_spec_fingerprint,
    publish_to_canva,
    validate_presentation_spec,
)
from foresight_os.domain.models import Relationship
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.invalidation import invalidate_dependencies
from foresight_os.vertical_slice import run_vertical_slice


def test_presentation_compiler_emits_deterministic_six_slide_provenance(tmp_path):
    workbook = __import__("pathlib").Path(__file__).parents[1] / "evaluation" / "cases" / "case-001" / "workbook.csv"
    run_vertical_slice(workbook, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()

    spec = compile_presentation(state, decision_question="Should we invest?", horizon="2030")
    same = compile_presentation(state, decision_question="Should we invest?", horizon="2030")

    assert len(spec.slides) == 6
    assert spec.spec_hash == presentation_spec_fingerprint(spec) == same.spec_hash
    assert all(set(slide.finding_ids).issubset(set(spec.source_finding_ids)) for slide in spec.slides)
    assert all(set(slide.evidence_ids).issubset({item.id for item in state.evidence}) for slide in spec.slides)
    artifact, relationships = presentation_artifact(state, spec, "presentation-spec.json")
    assert artifact.kind == "presentation_spec"
    assert all(item.relation_type == "produces" for item in relationships)


def test_provisional_spec_is_explicit_and_cannot_publish(tmp_path):
    workbook = __import__("pathlib").Path(__file__).parents[1] / "evaluation" / "cases" / "case-001" / "workbook.csv"
    outcome = run_vertical_slice(workbook, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()
    provisional = compile_presentation(state, provisional=True)

    assert provisional.status == "DRAFT / UNVALIDATED"
    with pytest.raises(PresentationBoundaryError, match="provisional"):
        publish_to_canva(provisional, human_approved=True)


def test_stale_presentation_artifact_blocks_normal_regeneration(tmp_path):
    workbook = __import__("pathlib").Path(__file__).parents[1] / "evaluation" / "cases" / "case-001" / "workbook.csv"
    run_vertical_slice(workbook, tmp_path / "case-001", human_accept=True)
    store = AnalysisStore(tmp_path / "case-001")
    state = store.load_analysis()
    spec = compile_presentation(state)
    artifact, relationships = presentation_artifact(state, spec, "presentation-spec.json")
    enriched = replace(state, artifacts=[*state.artifacts, artifact], relationships=[*state.relationships, *relationships])
    changed = invalidate_dependencies(enriched, [state.recommendations[0].evidence_ids[0]], "source changed")

    assert artifact.id in changed.invalidation.stale_artifact_ids
    with pytest.raises(ValueError, match="stale artifacts"):
        compile_presentation(changed)


def test_canva_requires_durable_receipt_and_human_approval():
    class Adapter:
        def publish(self, spec):
            return CanvaDeliveryReceipt("canva", "design-1", spec.analysis_revision, spec.spec_hash, "CONFIRMED", "2026-10-13T00:00:00Z")

    state = type("State", (), {"invalidation": type("Invalidation", (), {"stale_artifact_ids": ()})(), "revision": 1})()
    spec = type(
        "Spec",
        (),
        {"status": "CURRENT", "analysis_revision": 1, "spec_hash": "hash", "slides": (), "source_finding_ids": ()},
    )()
    with pytest.raises(PermissionError):
        publish_to_canva(spec, Adapter())
    with pytest.raises(PresentationBoundaryError, match="unavailable"):
        publish_to_canva(spec, human_approved=True)
