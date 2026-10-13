from foresight_os.controller.budgets import BudgetState
from foresight_os.controller.policy import probe_pattern_status, select_recipe
from foresight_os.controller.recipes import ExecutionPattern, RecipeName
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkStage
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
    candidates = probe_pattern_status()

    assert {candidate.name for candidate in candidates} == {"Concurrent", "Handoff"}
    assert all(not candidate.quality_passed for candidate in candidates)
    assert all(candidate.supported and candidate.available for candidate in candidates)
    assert all(candidate.status == "contract_passed" for candidate in candidates)


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


def test_override_preserves_required_review_and_rejects_only_direct_topology():
    brief = create_work_brief("review")
    shape = TaskShape(review_required=True)

    recipe = select_recipe(brief, shape, override="concurrent")
    assert any(role["purpose"] == "review" for role in recipe.stages[-1].participants)

    try:
        select_recipe(brief, shape, override="direct")
    except ValueError as error:
        assert "review_required" in str(error)
    else:
        raise AssertionError("direct topology bypassed required review")

    repeated = select_recipe(brief, override=["concurrent", "concurrent"])
    assert [stage.pattern for stage in repeated.stages] == [ExecutionPattern.CONCURRENT, ExecutionPattern.CONCURRENT]


def test_work_stages_assign_capabilities_and_handoff_routes_explicitly():
    recipe = select_recipe(
        create_work_brief(
            "review",
            stages=[
                WorkStage("assess-capacity", "assess capacity", participants=["analyst"]),
                WorkStage("validate-contradiction", "review evidence", participants=["reviewer"], dependencies=["assess-capacity"], research_needs=[ResearchNeed(ResearchNeedKind.EXTERNAL_FACT, "capacity expansion cost"), ResearchNeed(ResearchNeedKind.SOURCE_DETAIL, "source details")]),
            ],
        ),
        TaskShape(dynamic_specialist_routing=True, ordered_dependencies=True),
    )

    assert recipe.stages[0].stage_id == "assess-capacity"
    assert recipe.stages[1].participants[0]["capability_ids"] == ("web_search", "page_retrieval")
    assert recipe.stages[0].participants[0]["handoff_targets"] == ("participant-2",)
