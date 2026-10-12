from pathlib import Path

import pytest
from agent_framework import WorkflowCheckpoint

from foresight_os.artifacts.report import render_report
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.invalidation import invalidate_dependencies
from foresight_os.persistence.recovery import continue_investigation, resume_checkpoint
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_fresh_process_continuation_preserves_ids_and_revision(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    state = continue_investigation(work_dir, ["assumption-2030-horizon"], "planning horizon changed")
    reloaded = AnalysisStore(work_dir).load_analysis()

    assert reloaded.investigation_id == "case-001"
    assert reloaded.revision == state.revision == 2
    assert {item.id for item in reloaded.evidence} == {item.id for item in state.evidence}


def test_incompatible_checkpoint_topology_is_rejected():
    checkpoint = WorkflowCheckpoint("workflow-a", "topology-a", state={"ok": True})

    assert resume_checkpoint(checkpoint, "workflow-a", "topology-a") == checkpoint
    with pytest.raises(ValueError, match="incompatible workflow topology"):
        resume_checkpoint(checkpoint, "workflow-b", "topology-b")


def test_stale_artifact_cannot_be_rendered_as_current(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    state = AnalysisStore(work_dir).load_analysis()
    changed_evidence = next(item for item in state.evidence if "capacity_index-2030" in item.id)
    stale = invalidate_dependencies(state, [changed_evidence.id], "source evidence changed")

    with pytest.raises(ValueError, match="stale artifacts"):
        render_report(stale)
