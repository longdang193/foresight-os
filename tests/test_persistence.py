from pathlib import Path

import pytest

from foresight_os.domain.models import AnalysisState, Invalidation, WorkBrief
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


def test_malformed_analysis_does_not_replace_existing_file(tmp_path: Path):
    store = AnalysisStore(tmp_path / "case-001")
    existing = '{"existing": true}\n'
    store.analysis_path.parent.mkdir(parents=True)
    store.analysis_path.write_text(existing, encoding="utf-8")
    invalid = AnalysisState("case-001", 1, invalidation=Invalidation())

    with pytest.raises(ValidationError):
        store.save_analysis(invalid)

    assert store.analysis_path.read_text(encoding="utf-8") == existing
