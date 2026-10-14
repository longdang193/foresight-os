from foresight_os.controller.proposal import apply_execution_overrides, build_execution_recipe
from foresight_os.domain.models import WorkStage
from foresight_os.wayfinding import create_work_brief


def test_build_execution_recipe_is_complete_and_explainable():
    result = build_execution_recipe(create_work_brief("Question", stages=[WorkStage("stage-1", "Assess", expected_result="answer")]))
    assert result.accepted
    stage = result.recipe.stages[0]
    assert stage.rationale
    assert stage.completion_rule
    assert stage.reuse_policy


def test_invalid_group_chat_override_is_rejected_without_mutating_recipe():
    result = build_execution_recipe(create_work_brief("Question"))
    original = result.recipe
    updated = apply_execution_overrides(original, {"stages": [{"stage_id": "stage-1", "pattern": "group_chat", "participants": [{"id": "one"}]}]})
    assert not updated.accepted
    assert any(item.code == "insufficient_participants" for item in updated.diagnostics)
    assert original.stages[0].pattern.value != "group_chat"


def test_human_override_is_applied_exactly_or_reported():
    result = build_execution_recipe(create_work_brief("Question"))
    updated = apply_execution_overrides(result.recipe, {"max_agent_steps": 7})
    assert updated.accepted
    assert updated.recipe.max_agent_steps == 7
