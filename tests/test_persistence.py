from pathlib import Path
import os
import subprocess
import sys

import pytest

from foresight_os.domain.models import AnalysisState, Invalidation, ResearchNeed, ResearchNeedKind, Revision, WorkBrief, WorkStage
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
