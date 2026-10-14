from dataclasses import replace
from copy import deepcopy

import pytest

from foresight_os.controller.recipes import RecipeName, make_recipe
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


def test_recipe_rejects_global_call_budget_below_stage_count():
    recipe = make_recipe(RecipeName.DIRECT).to_dict()
    second_stage = deepcopy(recipe["stages"][0])
    second_stage["stage_id"] = "stage-2"
    recipe["stages"].append(second_stage)
    recipe["max_total_agent_calls"] = 1

    with pytest.raises(ValidationError, match="stage count"):
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
