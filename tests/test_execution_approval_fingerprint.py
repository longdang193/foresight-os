from dataclasses import replace

import pytest

from foresight_os.controller.policy import select_recipe
from foresight_os.controller.recipes import (
    INDEPENDENT_VALIDATION_POLICY,
    ExecutionPattern,
    RecipeName,
    ReviewCheckKind,
    make_recipe,
)
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalProjection
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief, WorkStage
from foresight_os.domain.validation import ValidationError, validate_execution_recipe
from foresight_os.wayfinding import create_work_brief


def test_approved_review_recipe_uses_typed_checks_and_separate_reviewer_requirements():
    recipe = select_recipe(create_work_brief("Should investment increase?"))

    assert recipe.review_policy == INDEPENDENT_VALIDATION_POLICY
    assert recipe.stages[0].review_checks == (
        ReviewCheckKind.SOURCE_FIDELITY.value,
        ReviewCheckKind.SCOPE_RECONCILIATION.value,
        ReviewCheckKind.DECISION_CHALLENGE.value,
    )
    reviewer = next(item for item in recipe.stages[0].participants if item["purpose"] == "review")
    assert reviewer["reviewer_capability_ids"] == recipe.stages[0].review_checks
    assert reviewer["review_check_ids"] == recipe.stages[0].review_checks
    assert reviewer["skill_ids"]
    assert reviewer["skill_ids"] != recipe.stages[0].skill_ids


def test_quantitative_review_adds_calculation_and_material_source_capabilities():
    brief = WorkBrief(
        "quantitative",
        "Which channel should launch first?",
        ["declared workbook"],
        ["recommendation"],
        [],
        [],
        "assess",
        "validate",
        stages=[
            WorkStage(
                "stage-1",
                "reconcile workbook metrics",
                research_needs=[
                    ResearchNeed(ResearchNeedKind.STRUCTURED_DATA, "workbook values"),
                    ResearchNeed(ResearchNeedKind.QUANTITATIVE_ANALYSIS, "growth calculation"),
                ],
            )
        ],
    )

    recipe = select_recipe(brief)
    reviewer = next(item for item in recipe.stages[0].participants if item["purpose"] == "review")

    assert ReviewCheckKind.CALCULATION_RECONCILIATION.value in recipe.stages[0].review_checks
    assert "spreadsheet_read" in reviewer["reviewer_capability_ids"]
    assert "calculation" in reviewer["reviewer_capability_ids"]
    assert "spreadsheet_read" in recipe.stages[0].capabilities


def test_legacy_review_labels_remain_readable_but_typed_policy_rejects_them():
    legacy = make_recipe(RecipeName.DIRECT).to_dict()
    legacy["stages"][0]["review_checks"] = ["independent review"]
    validate_execution_recipe(legacy)

    typed = select_recipe(create_work_brief("Question")).to_dict()
    typed["stages"][0]["review_checks"] = ["independent review"]
    with pytest.raises(ValidationError, match="does not support review check"):
        validate_execution_recipe(typed)


def test_typed_review_policy_requires_at_least_one_known_check():
    recipe = select_recipe(create_work_brief("Question")).to_dict()
    recipe["stages"][0]["review_checks"] = []

    with pytest.raises(ValidationError, match="at least one typed review check"):
        validate_execution_recipe(recipe)


def test_review_coverage_and_policy_changes_invalidate_approval_projection():
    brief = create_work_brief("Question", investigation_id="approval-review-policy")
    recipe = select_recipe(brief)
    plain = ApprovalProjection.from_values(brief, recipe, AdaptationEnvelope())

    changed_stage = replace(
        recipe.stages[0],
        review_checks=tuple(
            check
            for check in recipe.stages[0].review_checks
            if check != ReviewCheckKind.DECISION_CHALLENGE.value
        ),
    )
    changed_coverage = replace(recipe, stages=(changed_stage,))
    changed_policy = replace(recipe, review_policy="independent-validation/v2")

    assert ApprovalProjection.from_values(brief, changed_coverage, AdaptationEnvelope()).fingerprint != plain.fingerprint
    assert ApprovalProjection.from_values(brief, changed_policy, AdaptationEnvelope()).fingerprint != plain.fingerprint


def test_runtime_attempt_identity_is_not_part_of_recipe_approval_projection():
    brief = create_work_brief("Question", investigation_id="approval-attempt")
    recipe = select_recipe(brief)
    left = ApprovalProjection.from_values(brief, recipe, AdaptationEnvelope())
    right = ApprovalProjection.from_values(brief, recipe, AdaptationEnvelope())

    assert left.fingerprint == right.fingerprint
