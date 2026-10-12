from pathlib import Path

from foresight_os.artifacts.report import write_report
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.invalidation import invalidate_dependencies
from foresight_os.persistence.recovery import continue_investigation


class LocalClient:
    """Required v0.1 client; it owns no analytical state."""

    def continue_investigation(self, work_dir: Path, changed_ids: list[str] | None = None, reason: str | None = None):
        return continue_investigation(work_dir, changed_ids, reason)

    def challenge(self, work_dir: Path, record_id: str, reason: str):
        store = AnalysisStore(work_dir)
        state = invalidate_dependencies(store.load_analysis(), [record_id], f"challenge: {reason}")
        return store.commit_revision(state, expected_revision=store.load_analysis().revision, accepted=False)

    def scope_change(self, work_dir: Path, reason: str):
        store = AnalysisStore(work_dir)
        state = invalidate_dependencies(store.load_analysis(), ["scope-change"], f"scope change: {reason}")
        return store.commit_revision(state, expected_revision=store.load_analysis().revision, accepted=False)

    def report(self, work_dir: Path) -> Path:
        store = AnalysisStore(work_dir)
        state = store.load_analysis()
        path = work_dir / "artifacts" / "executive-report.md"
        write_report(path, state)
        return path
