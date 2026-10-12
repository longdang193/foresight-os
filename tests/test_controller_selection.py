from foresight_os.controller.budgets import BudgetState
from foresight_os.controller.policy import probe_optional_patterns, select_recipe
from foresight_os.controller.recipes import ExecutionPattern, RecipeName
from foresight_os.controller.task_shape import TaskShape
from foresight_os.wayfinding import create_work_brief


def test_controller_selects_bounded_analysis_review_recipe():
    recipe = select_recipe(create_work_brief("Should investment increase?"))

    assert recipe.name == RecipeName.ANALYZE_REVIEW
    assert recipe.pattern == "sequential"
    assert recipe.max_agent_steps == 5
    assert recipe.max_correction_rounds == 1
    assert recipe.max_total_agent_calls == 3
    assert {role["purpose"] for role in recipe.roles} == {"execute", "review"}


def test_budget_exhaustion_prevents_extra_call_or_correction():
    budget = BudgetState(5, 1, 3)

    assert [budget.call() for _ in range(4)] == [True, True, True, False]
    assert budget.correct()
    assert not budget.correct()


def test_optional_patterns_are_probe_only_and_deferred():
    candidates = probe_optional_patterns()

    assert {candidate.name for candidate in candidates} == {"Concurrent", "Handoff"}
    assert all(not candidate.production_admitted for candidate in candidates)
    assert all(not candidate.accepted for candidate in candidates)


def test_task_shape_composition_is_deterministic_and_bounded():
    recipe = select_recipe(
        create_work_brief("compose"),
        TaskShape(independent_subtasks=True, interactive_deliberation=True, review_required=True),
    )

    assert [stage.pattern for stage in recipe.stages] == [
        ExecutionPattern.CONCURRENT,
        ExecutionPattern.GROUP_CHAT,
        ExecutionPattern.SEQUENTIAL,
    ]
    assert recipe.metadata["selection_source"] == "task_shape"


def test_override_cannot_remove_required_review_or_repeat_patterns():
    brief = create_work_brief("review")
    shape = TaskShape(review_required=True)

    try:
        select_recipe(brief, shape, override="concurrent")
    except ValueError as error:
        assert "review_required" in str(error)
    else:
        raise AssertionError("required review override was accepted")

    try:
        select_recipe(brief, override=["concurrent", "concurrent"])
    except ValueError as error:
        assert "repeat" in str(error)
    else:
        raise AssertionError("duplicate pattern override was accepted")
