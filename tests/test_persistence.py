from pathlib import Path
import os
import subprocess
import sys

import pytest

from foresight_os.domain.models import AnalysisState, Invalidation, MethodProvenance, ResearchNeed, ResearchNeedKind, Revision, WorkBrief, WorkStage
from foresight_os.controller.policy import select_recipe
from foresight_os.controller.recipes import ExecutionPattern
from foresight_os.domain.validation import ValidationError
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import deterministic_id


def test_deterministic_id_is_stable():
    assert deterministic_id("Evidence", {"a": 1, "b": 2}) == deterministic_id("Evidence", {"b": 2, "a": 1})


def test_brief_round_trips_through_brief_md(tmp_path: Path):
    store = AnalysisStore(tmp_path / "case-001")
    brief = WorkBrief("case-001", "Should investment increase?", ["Northern Europe"], ["report"], ["2030"], [], "Assess capacity.", "Review contradiction.")

    store.save_brief(brief)

    assert store.load_brief() == brief


def test_saved_brief_contains_generated_human_view_without_changing_round_trip(tmp_path: Path):
    store = AnalysisStore(tmp_path / "human-brief")
    brief = WorkBrief(
        "human-brief",
        "Which option should we choose?",
        ["included scope"],
        ["recommendation"],
        ["one assumption"],
        ["one unknown"],
        "Assess alternatives.",
        "Inspect the source.",
        stages=[WorkStage("source-audit", "Reconcile source definitions", expected_result="source dictionary")],
    )

    store.save_brief(brief)
    saved = store.brief_path.read_text(encoding="utf-8")

    assert saved.startswith("---\n")
    assert "# Work Brief" in saved
    assert "Generated from the canonical WorkBrief fields." in saved
    assert "## Decision" in saved
    assert "## Assumptions" in saved
    assert "## Proposed investigation" in saved
    assert store.load_brief() == brief

    frontmatter, _, body = saved[4:].partition("\n---\n")
    store.brief_path.write_text(f"---\n{frontmatter}\n---\n{body}\nManual body edit\n", encoding="utf-8")
    assert store.load_brief() == brief


def test_generated_brief_body_does_not_render_untrusted_preference_payloads(tmp_path: Path):
    store = AnalysisStore(tmp_path / "safe-human-brief")
    brief = WorkBrief(
        "safe-human-brief",
        "Question",
        ["scope"],
        ["answer"],
        [],
        [],
        "direction",
        "next step",
        user_preferences={
            "credential": "secret-token",
            "raw_provider_payload": {"authorization": "Bearer secret-token"},
        },
    )

    store.save_brief(brief)
    body = store.brief_path.read_text(encoding="utf-8").split("\n---\n", 1)[1]

    assert "secret-token" not in body
    assert "raw_provider_payload" not in body


def test_typed_brief_stages_round_trip_and_preserve_routing_inputs(tmp_path: Path):
    store = AnalysisStore(tmp_path / "typed-brief")
    brief = WorkBrief(
        "typed-brief",
        "What should we do?",
        ["scope"],
        ["answer"],
        [],
        [],
        "inspect",
        "retrieve",
        stages=[WorkStage("stage-1", "analyze", research_needs=[ResearchNeed(ResearchNeedKind.STRUCTURED_DATA, "workbook")])],
    )
    store.save_brief(brief)
    assert store.load_brief() == brief


def test_method_provenance_round_trips_without_becoming_execution_intent(tmp_path: Path):
    store = AnalysisStore(tmp_path / "provenance")
    brief = WorkBrief(
        "provenance",
        "What should we do?",
        ["scope"],
        ["answer"],
        [],
        [],
        "inspect",
        "retrieve",
        producer=MethodProvenance("foresight-wayfinding", ".agents/skills/foresight-wayfinding/SKILL.md", "1", "abc123"),
    )

    store.save_brief(brief)

    assert store.load_brief() == brief
    assert store.load_brief().execution_intent is None


def test_stage_execution_intent_preserves_pattern_selection_after_round_trip(tmp_path: Path):
    store = AnalysisStore(tmp_path / "stage-intent")
    brief = WorkBrief(
        "stage-intent",
        "What should we do?",
        ["scope"],
        ["answer"],
        [],
        [],
        "inspect",
        "retrieve",
        stages=[WorkStage("stage-1", "collect", execution_pattern_override=ExecutionPattern.CONCURRENT.value)],
    )

    store.save_brief(brief)

    loaded_recipe = select_recipe(store.load_brief())

    assert loaded_recipe.stages[0].pattern is ExecutionPattern.CONCURRENT


def test_malformed_analysis_does_not_replace_existing_file(tmp_path: Path):
    store = AnalysisStore(tmp_path / "case-001")
    existing = '{"existing": true}\n'
    store.analysis_path.parent.mkdir(parents=True)
    store.analysis_path.write_text(existing, encoding="utf-8")
    invalid = AnalysisState("case-001", 1, invalidation=Invalidation())

    with pytest.raises(ValidationError):
        store.save_analysis(invalid)

    assert store.analysis_path.read_text(encoding="utf-8") == existing


def test_two_processes_commit_one_revision_and_one_conflict(tmp_path: Path):
    work_dir = tmp_path / "race"
    store = AnalysisStore(work_dir)
    store.save_analysis(AnalysisState("race", 1, revisions=[Revision("revision-1", 1, "initial state")]))
    barrier = tmp_path / "ready"
    script = """
import os, sys, time
from pathlib import Path
from foresight_os.domain.models import AnalysisState
from foresight_os.persistence.analysis_store import AnalysisStore
work = Path(sys.argv[1]); barrier = Path(sys.argv[2]); store = AnalysisStore(work)
state = store.load_analysis(); marker = barrier / str(os.getpid()); marker.write_text('ready')
while len(list(barrier.glob('*'))) < 2: time.sleep(0.01)
try:
    store.commit_revision(state, 1, True)
    print('committed')
except ValueError as error:
    print('conflict' if 'stale revision' in str(error) else type(error).__name__)
"""
    barrier.mkdir()
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    processes = [
        subprocess.Popen([sys.executable, "-c", script, str(work_dir), str(barrier)], stdout=subprocess.PIPE, text=True, env=env)
        for _ in range(2)
    ]
    outputs = [process.communicate(timeout=10)[0].strip() for process in processes]

    assert sorted(outputs) == ["committed", "conflict"]
    assert store.load_analysis().revision == 2
