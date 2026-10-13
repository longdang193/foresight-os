from foresight_os.controller.policy import select_recipe
from foresight_os.domain.models import ResearchNeed, ResearchNeedKind, WorkBrief, WorkStage
from foresight_os.domain.validation import validate_work_brief


def _brief(needs):
    return WorkBrief(
        investigation_id="research-needs",
        decision_question="What should we do?",
        scope=["test"],
        desired_deliverables=["answer"],
        assumptions=[],
        open_dependencies=[],
        current_direction="inspect",
        next_useful_step="retrieve",
        stages=[WorkStage("stage-1", "research", research_needs=needs)],
    )


def test_typed_requirements_map_exactly_to_semantic_capabilities():
    recipe = select_recipe(_brief([
        ResearchNeed(ResearchNeedKind.QUANTITATIVE_ANALYSIS, "growth"),
        ResearchNeed(ResearchNeedKind.STRUCTURED_DATA, "workbook"),
    ]))

    assert recipe.stages[0].participants[0]["capability_ids"] == (
        "data_analysis",
        "calculation",
        "spreadsheet_read",
    )
    assert recipe.metadata["unresolved_capabilities"] == ""


def test_unknown_and_legacy_requirements_are_explicitly_unresolved():
    typed = _brief([ResearchNeed("NOT_A_REAL_KIND", "legacy source")])
    legacy = _brief(["capacity expansion cost"])

    assert validate_work_brief(typed.to_dict())["stages"][0]["research_needs"] == [
        {"kind": "NOT_A_REAL_KIND", "query": "legacy source", "source_hint": None}
    ]
    assert validate_work_brief(legacy.to_dict())["stages"][0]["research_needs"] == [
        {"kind": "UNRESOLVED_CAPABILITY", "query": "capacity expansion cost"}
    ]
    assert "NOT_A_REAL_KIND:legacy source" in select_recipe(typed).metadata["unresolved_capabilities"]
    assert "UNRESOLVED_CAPABILITY:capacity expansion cost" in select_recipe(legacy).metadata["unresolved_capabilities"]


def test_unavailable_capabilities_are_registered_without_being_invented():
    recipe = select_recipe(_brief([
        ResearchNeed(ResearchNeedKind.DOCUMENT_REVIEW, "read the report"),
        ResearchNeed(ResearchNeedKind.ARTIFACT_OUTPUT, "export result"),
    ]))

    assert recipe.stages[0].participants[0]["capability_ids"] == (
        "document_read",
        "artifact_generation",
    )
