from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from foresight_os.artifacts.approval import build_approval_package, render_approval_markdown
from foresight_os.artifacts.brief import render_work_brief_markdown
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.domain.approval import ApprovalRecord, ApprovalStatus
from foresight_os.domain.models import ExecutionIntent, ResearchNeed, ResearchNeedKind, WorkBrief, WorkStage
from foresight_os.domain.validation import validate_work_brief
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.execution_gate import ExecutionAdmissionError, ExecutionGate


FIXTURE = Path("tests/fixtures/wayfinding/ncc-2022-brief.yaml")


def _brief_from_fixture() -> WorkBrief:
    value = validate_work_brief(yaml.safe_load(FIXTURE.read_text(encoding="utf-8")))
    stages = [
        WorkStage(
            stage_id=stage["stage_id"],
            objective=stage["objective"],
            participants=stage.get("participants", []),
            subtasks=stage.get("subtasks", []),
            dependencies=stage.get("dependencies", []),
            expected_result=stage.get("expected_result", ""),
            research_needs=[ResearchNeed(ResearchNeedKind(need["kind"]), need["query"], need.get("source_hint")) for need in stage.get("research_needs", [])],
        )
        for stage in value["stages"]
    ]
    return WorkBrief(
        investigation_id=value["investigation_id"],
        decision_question=value["decision_question"],
        scope=value["scope"],
        desired_deliverables=value["desired_deliverables"],
        assumptions=value["assumptions"],
        open_dependencies=value["open_dependencies"],
        current_direction=value["current_direction"],
        next_useful_step=value["next_useful_step"],
        stages=stages,
        horizon=value["horizon"],
        consequence_level=value["consequence_level"],
        user_preferences=value["user_preferences"],
    )


def test_ncc_fixture_round_trips_through_canonical_execution_path(tmp_path):
    brief = _brief_from_fixture()
    assert brief.execution_intent is None
    assert all(stage.execution_intent is None for stage in brief.stages)
    assert [stage.stage_id for stage in brief.stages] == ["source-audit", "category-screen", "channel-screen", "joint-validation", "challenge-synthesis"]
    assert brief.stages[3].dependencies == ["category-screen", "channel-screen"]
    assert any("Trad.Trade" in need.source_hint for stage in brief.stages for need in stage.research_needs if need.source_hint)
    assert "hidden Others sheet" in brief.stages[0].research_needs[-1].query
    assert "conditional growth bridge" in brief.desired_deliverables[3]

    store = AnalysisStore(tmp_path / "ncc")
    store.save_brief(brief)
    loaded = store.load_brief()
    recipe = build_execution_recipe(loaded).recipe
    package = build_approval_package(loaded, recipe)
    rendered_brief = store.brief_path.read_text(encoding="utf-8")
    rendered_approval = render_approval_markdown(package, detailed=True)

    assert loaded == brief
    assert "Trad.Trade" in rendered_brief
    assert "conditional growth bridge" in rendered_brief
    assert "category-screen" in rendered_approval
    assert "joint-validation" in rendered_approval
    assert "map.md" not in rendered_brief


def test_human_brief_renders_global_execution_intent():
    brief = replace(
        _brief_from_fixture(),
        execution_intent=ExecutionIntent(
            required_patterns=("sequential",),
            required_capabilities=("spreadsheet_read",),
        ),
    )

    rendered = render_work_brief_markdown(brief)

    assert "## Execution intent" in rendered
    assert "Required patterns: sequential" in rendered
    assert "Required capabilities: spreadsheet_read" in rendered


def test_human_brief_renders_global_and_stage_execution_intent():
    brief = _brief_from_fixture()
    brief = replace(
        brief,
        execution_intent=ExecutionIntent(required_participants=("reviewer",)),
        stages=[
            replace(
                brief.stages[0],
                execution_intent=ExecutionIntent(preferred_patterns=("sequential",)),
            ),
            *brief.stages[1:],
        ],
    )

    rendered = render_work_brief_markdown(brief)

    assert rendered.count("## Execution intent") == 1
    assert rendered.count("- Execution intent:") == 5
    assert "Required participants: reviewer" in rendered
    assert "Preferred patterns: sequential" in rendered


def test_ncc_material_brief_change_changes_approval_fingerprint(tmp_path):
    brief = _brief_from_fixture()
    recipe = build_execution_recipe(brief).recipe
    before = build_approval_package(brief, recipe)
    changed = replace(brief, scope=[*brief.scope, "A material client constraint"])
    after = build_approval_package(changed, recipe)

    assert after.fingerprint != before.fingerprint


def test_ncc_material_brief_change_invalidates_persisted_approval(tmp_path):
    brief = _brief_from_fixture()
    store = AnalysisStore(tmp_path / "ncc-stale")
    recipe = build_execution_recipe(brief).recipe
    package = build_approval_package(brief, recipe)
    store.save_brief(brief)
    store.save_recipe(recipe)
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))

    store.save_brief(replace(brief, scope=[*brief.scope, "A material client constraint"]))

    with pytest.raises(ExecutionAdmissionError, match="approved projection"):
        ExecutionGate(store).admit(prompt="Question")
