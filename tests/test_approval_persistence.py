from dataclasses import replace
from datetime import datetime, timezone

import pytest

from foresight_os.artifacts.approval import build_approval_package
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalProjection, ApprovalRecord, ApprovalStatus
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.execution_gate import ExecutionAdmissionError, ExecutionGate
from foresight_os.wayfinding import create_work_brief


def test_approval_round_trip_and_stale_display_rejection(tmp_path):
    brief = create_work_brief("Question", investigation_id="persist")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "persist")
    store.save_brief(brief)
    store.save_recipe(recipe)
    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    record = ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    )
    store.save_execution_approval(record)
    assert store.load_execution_approval() == record
    with pytest.raises(ValueError):
        ApprovalRecord(
            brief.investigation_id,
            ApprovalStatus.APPROVED,
            package.projection,
            package.fingerprint,
            "stale",
            canonical_json_hash(recipe.to_dict()),
            "local_cli",
            "now",
        )


def test_approval_compatibility_fingerprint_canonicalizes_equivalent_input_aliases():
    aliased = {
        "brief": {"investigation_id": "alias", "analysis_inputs": [{"name": "supplier_resilience", "tables": ["Supplier_Master"]}]},
        "recipe": {},
        "adaptation_envelope": {},
    }
    canonical = {
        "brief": {"investigation_id": "alias", "analysis_inputs": [{"domain": "supplier_resilience", "required_tables": ["Supplier_Master"]}]},
        "recipe": {},
        "adaptation_envelope": {},
    }

    assert ApprovalProjection.compatibility_fingerprint_for_dict(aliased) == ApprovalProjection.compatibility_fingerprint_for_dict(canonical)


def test_persisted_approval_accepts_equivalent_aliases_but_rejects_material_contract_change(tmp_path):
    brief = create_work_brief(
        "Question",
        investigation_id="persisted-alias-admission",
        analysis_inputs={"supplier_resilience": {"required_tables": ["Supplier_Master"]}},
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "persisted-alias-admission")
    store.save_brief(brief)
    store.save_recipe(recipe)

    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    aliased_projection_value = package.projection.to_dict()
    aliased_projection_value["brief"]["analysis_inputs"] = [
        {"name": "supplier_resilience", "tables": ["Supplier_Master"]}
    ]
    aliased_projection = ApprovalProjection(
        dict(aliased_projection_value["brief"]),
        dict(aliased_projection_value["recipe"]),
        dict(aliased_projection_value["adaptation_envelope"]),
    )
    store.save_execution_approval(
        ApprovalRecord(
            brief.investigation_id,
            ApprovalStatus.APPROVED,
            aliased_projection,
            aliased_projection.fingerprint,
            aliased_projection.fingerprint,
            canonical_json_hash(recipe.to_dict()),
            "local_cli",
            datetime.now(timezone.utc).isoformat(),
        )
    )

    admission = ExecutionGate(store).admit(prompt="Question")

    assert admission.effective_contracts["supplier_resilience"].required_tables == ("Supplier_Master",)

    store.save_brief(
        replace(
            brief,
            analysis_inputs={"supplier_resilience": {"required_tables": ["Different_Table"]}},
        )
    )
    with pytest.raises(ExecutionAdmissionError, match="approved projection"):
        ExecutionGate(store).admit(prompt="Question")
