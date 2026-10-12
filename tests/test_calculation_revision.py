from pathlib import Path

import pytest

from foresight_os.analysis.analyst import draft_analysis
from foresight_os.analysis.workbook import extract_evidence, read_workbook
from foresight_os.domain.models import RevisionStatus
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_workbook_mutation_changes_calculation_backed_claim(tmp_path: Path):
    mutated = tmp_path / "workbook.csv"
    mutated.write_text(WORKBOOK.read_text(encoding="utf-8").replace(",140,", ",999,"), encoding="utf-8")

    original = draft_analysis(extract_evidence(WORKBOOK, read_workbook(WORKBOOK)))
    changed = draft_analysis(extract_evidence(mutated, read_workbook(mutated)))

    assert "140" in original.claims[0].statement
    assert "999" in changed.claims[0].statement
    assert "999" in changed.claims[1].statement


def test_loaded_analysis_has_explicit_schema_and_revision_status(tmp_path: Path):
    outcome = run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()

    assert outcome.accepted
    assert state.schema_version == 1
    assert state.revision_status == RevisionStatus.ACCEPTED


def test_stale_revision_cannot_replace_durable_state(tmp_path: Path):
    work_dir = tmp_path / "case-001"
    run_vertical_slice(WORKBOOK, work_dir, human_accept=True)
    store = AnalysisStore(work_dir)
    state = store.load_analysis()

    with pytest.raises(ValueError, match="stale revision"):
        store.commit_revision(state, expected_revision=0, accepted=True)

    assert store.load_analysis().revision == 1
