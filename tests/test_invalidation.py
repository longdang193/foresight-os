from pathlib import Path

from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.invalidation import invalidate_dependencies
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_evidence_change_invalidates_reachable_outputs_without_deleting_history(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()

    changed_evidence = next(item for item in state.evidence if "capacity_index-2030" in item.id)
    changed = invalidate_dependencies(state, [changed_evidence.id], "source evidence changed")

    assert changed.revision == 2
    assert changed_evidence.id in [item.id for item in changed.evidence]
    assert changed.revisions[0].number == 1
    assert changed.invalidation.reassessment_ids
    assert changed.invalidation.stale_artifact_ids


def test_assumption_change_invalidates_dependents_and_repeated_recovery_is_idempotent(tmp_path: Path):
    run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    store = AnalysisStore(tmp_path / "case-001")
    state = store.load_analysis()
    first = invalidate_dependencies(state, ["assumption-2030-horizon"], "planning horizon changed")
    second = invalidate_dependencies(first, ["assumption-2030-horizon"], "planning horizon changed")

    assert first.revision == 2
    assert second == first
