from pathlib import Path

import pytest

from foresight_os.clients.first_client_adapter import LocalClient
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_local_client_preserves_durable_state_across_all_required_flows(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    client = LocalClient()

    continued = client.continue_investigation(work_dir)
    challenged = client.challenge(work_dir, continued.recommendations[0].id, "test the sensitivity")
    scoped = client.scope_change(work_dir, "exclude Southern Europe")

    assert continued.investigation_id == challenged.investigation_id == scoped.investigation_id == "case-001"
    assert scoped.revision == 3
    assert AnalysisStore(work_dir).load_analysis().revision == 3


def test_client_does_not_present_stale_artifact_as_current(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    client = LocalClient()
    client.scope_change(work_dir, "exclude Southern Europe")

    with pytest.raises(ValueError, match="stale artifacts"):
        client.report(work_dir)
