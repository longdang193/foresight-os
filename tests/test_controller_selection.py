from foresight_os.controller.budgets import BudgetState
from foresight_os.controller.policy import probe_optional_patterns, select_recipe
from foresight_os.controller.recipes import RecipeName
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
