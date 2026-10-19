from dataclasses import replace
from copy import deepcopy

import pytest

from foresight_os.controller.recipes import RecipeName, make_recipe, normalize_legacy_recipe_dict
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalProjection, ApprovalRecord, ApprovalStatus
from foresight_os.domain.models import ExecutionIntent, MethodProvenance, WorkBrief
from foresight_os.domain.validation import ValidationError, validate_approval_record, validate_execution_recipe


def brief() -> WorkBrief:
    return WorkBrief("approval", "Question", ["scope"], ["answer"], [], [], "direction", "next")


def test_equivalent_projection_ordering_has_same_fingerprint():
    recipe = make_recipe(RecipeName.DIRECT)
    left = ApprovalProjection.from_values(brief(), recipe, AdaptationEnvelope())
    right = ApprovalProjection.from_values({**brief().to_dict(), "scope": ["scope"]}, recipe.to_dict(), {"allowed_operations": []})
    assert left.fingerprint == right.fingerprint


def test_approval_record_requires_local_cli_and_matching_displayed_fingerprint():
    projection = ApprovalProjection.from_values(brief(), make_recipe(RecipeName.DIRECT), AdaptationEnvelope())
    with pytest.raises(ValueError, match="local CLI"):
        ApprovalRecord("approval", ApprovalStatus.APPROVED, projection, projection.fingerprint, projection.fingerprint, "recipe", "remote", "now")


def test_recipe_rejects_negative_limits():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["stages"][0]["limits"]["max_agent_steps"] = -1
    with pytest.raises(ValidationError, match="negative"):
        validate_execution_recipe(recipe)


def test_recipe_rejects_multiple_domains_for_agent_stage():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["stages"][0]["analysis_domains"] = ["market", "retailer"]

    with pytest.raises(ValidationError, match="must not declare analysis domains"):
        validate_execution_recipe(recipe)


def test_recipe_rejects_invalid_deterministic_domain_cardinality():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["stages"][0]["executor_kind"] = "deterministic_local"
    recipe["stages"][0]["analysis_domains"] = []

    with pytest.raises(ValidationError, match="exactly one analysis domain"):
        validate_execution_recipe(recipe)


def test_legacy_analysis_contract_domains_are_loaded_into_stage_scope():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["metadata"]["analysis_contract_domains"] = '{"stage-1": ["market"]}'
    recipe["stages"][0].pop("analysis_domains")

    restored = make_recipe(RecipeName.DIRECT).from_dict(recipe)

    assert restored.stages[0].analysis_domains == ("market",)


def test_legacy_analysis_domains_do_not_override_explicit_empty_stage_scope():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["metadata"]["analysis_contract_domains"] = '{"stage-1": ["market"]}'
    recipe["stages"][0]["analysis_domains"] = []

    restored = make_recipe(RecipeName.DIRECT).from_dict(recipe)

    assert restored.stages[0].analysis_domains == ()


def test_malformed_legacy_analysis_domains_are_deterministically_empty():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["metadata"]["analysis_contract_domains"] = "not-json"
    recipe["stages"][0].pop("analysis_domains")

    restored = make_recipe(RecipeName.DIRECT).from_dict(recipe)

    assert restored.stages[0].analysis_domains == ()


def test_legacy_analysis_domains_use_canonical_string_coercion_and_are_not_serialized():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["metadata"]["analysis_contract_domains"] = '{"stage-1": [7, "market"]}'
    recipe["stages"][0].pop("analysis_domains")

    restored = make_recipe(RecipeName.DIRECT).from_dict(recipe)

    assert restored.stages[0].analysis_domains == ("7", "market")
    assert "analysis_contract_domains" not in restored.to_dict()["metadata"]


def test_recipe_rejects_global_call_budget_below_stage_count():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    second_stage = deepcopy(recipe["stages"][0])
    second_stage["stage_id"] = "stage-2"
    recipe["stages"].append(second_stage)
    recipe["max_total_agent_calls"] = 1

    with pytest.raises(ValidationError, match="stage count"):
        validate_execution_recipe(recipe)


def test_recipe_rejects_global_step_budget_below_stage_count():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    second_stage = deepcopy(recipe["stages"][0])
    second_stage["stage_id"] = "stage-2"
    recipe["stages"].extend([second_stage, deepcopy(second_stage)])
    recipe["stages"][2]["stage_id"] = "stage-3"
    recipe["max_agent_steps"] = 2
    recipe["max_total_agent_calls"] = 9

    with pytest.raises(ValidationError, match="global agent-step budget"):
        validate_execution_recipe(recipe)


def test_recipe_rejects_budget_below_tool_and_participant_requirements():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    recipe["max_correction_rounds"] = 1
    recipe["max_total_agent_calls"] = 1
    recipe["stages"][0]["capabilities"] = ["spreadsheet_read"]
    recipe["stages"][0]["participants"] = [
        {"id": "analyst", "purpose": "analyst"},
        {"id": "reviewer", "purpose": "review"},
    ]
    recipe["stages"][0]["limits"]["max_total_agent_calls"] = 1

    with pytest.raises(ValidationError, match="effective agent-call budget"):
        validate_execution_recipe(recipe)


def test_approval_projection_excludes_secret_fields():
    projection = ApprovalProjection.from_values({**brief().to_dict(), "api_token": "secret"}, make_recipe(RecipeName.DIRECT), AdaptationEnvelope())
    assert projection.to_dict()["brief"]["api_token"] == "[excluded]"
    assert "secret" not in projection.fingerprint


def test_producer_metadata_is_supplementary_and_excluded_from_material_fingerprint():
    recipe = make_recipe(RecipeName.DIRECT)
    plain = ApprovalProjection.from_values(brief(), recipe, AdaptationEnvelope())
    produced = ApprovalProjection.from_values(
        replace(brief(), producer=MethodProvenance("foresight-wayfinding", ".agents/skills/foresight-wayfinding/SKILL.md", "1", "changed")),
        recipe,
        AdaptationEnvelope(),
    )

    assert produced.to_dict()["brief"]["producer"]["id"] == "foresight-wayfinding"
    assert produced.fingerprint == plain.fingerprint


def test_material_brief_changes_still_change_approval_fingerprint():
    recipe = make_recipe(RecipeName.DIRECT)
    plain = ApprovalProjection.from_values(brief(), recipe, AdaptationEnvelope())
    changed = ApprovalProjection.from_values(
        replace(brief(), scope=["different"], execution_intent=ExecutionIntent(required_patterns=("sequential",))),
        recipe,
        AdaptationEnvelope(),
    )

    assert changed.fingerprint != plain.fingerprint
