from pathlib import Path

from agent_framework import WorkflowCheckpoint

from foresight_os.domain.models import AnalysisState
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.invalidation import invalidate_dependencies


def continue_investigation(
    work_dir: Path,
    changed_ids: list[str] | None = None,
    reason: str | None = None,
) -> AnalysisState:
    store = AnalysisStore(work_dir)
    state = store.load_analysis()
    if changed_ids and reason:
        state = invalidate_dependencies(state, changed_ids, reason)
        store.save_analysis(state)
    return state


def resume_checkpoint(checkpoint: WorkflowCheckpoint, workflow_name: str, graph_signature_hash: str) -> WorkflowCheckpoint:
    if checkpoint.workflow_name != workflow_name or checkpoint.graph_signature_hash != graph_signature_hash:
        raise ValueError("incompatible workflow topology; start a new Run from analytical state")
    return checkpoint
