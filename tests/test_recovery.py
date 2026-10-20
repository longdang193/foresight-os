from pathlib import Path
import json
import subprocess
import sys

import pytest
from agent_framework import WorkflowCheckpoint

from foresight_os.artifacts.report import render_report
from foresight_os.domain.models import AnalysisState, Revision
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


def test_pending_review_recovers_from_analysis_state_in_fresh_process(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    store = AnalysisStore(work_dir)
    pending = store.save_pending(store.load_analysis())
    script = """
import json, sys
from pathlib import Path
from foresight_os.persistence.analysis_store import AnalysisStore
state = AnalysisStore(Path(sys.argv[1])).load_analysis()
print(json.dumps({'revision': state.revision, 'status': state.revision_status.value, 'evidence': sorted(item.id for item in state.evidence)}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(work_dir)],
        check=True,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(Path.cwd() / "src")},
    )
    restored = json.loads(result.stdout)

    assert pending.revision == restored["revision"]
    assert restored["status"] == "PENDING_REVIEW"
    assert restored["evidence"] == sorted(item.id for item in pending.evidence)


def test_restore_revision_snapshot_writes_revision_scoped_token_ledger(tmp_path: Path):
    store = AnalysisStore(tmp_path / "snapshot-tokens")
    accepted = AnalysisState(
        "snapshot-tokens",
        7,
        revisions=[Revision(f"revision-{number}", number, "accepted", []) for number in range(1, 8)],
    )
    store.save_analysis(accepted)
    accepted_snapshot = store.capture_revision_snapshot()
    pending = store.save_pending(accepted)
    current_snapshot = store.capture_revision_snapshot()

    assert store.restore_revision_snapshot(accepted_snapshot, expected_current=current_snapshot)

    ledger = json.loads(store.pending_tokens_path.read_text(encoding="utf-8"))
    assert ledger == {"revision": 7, "tokens": [pending.pending_token]}
    with pytest.raises(ValueError, match="stale pending identity"):
        store.commit_revision(pending, expected_revision=7, accepted=True)


def test_stale_artifact_cannot_be_rendered_as_current(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    state = AnalysisStore(work_dir).load_analysis()
    changed_evidence = next(item for item in state.evidence if "capacity_index-2030" in item.id)
    stale = invalidate_dependencies(state, [changed_evidence.id], "source evidence changed")

    with pytest.raises(ValueError, match="stale artifacts"):
        render_report(stale)
