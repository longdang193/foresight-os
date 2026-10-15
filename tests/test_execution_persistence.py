import json
import os
from pathlib import Path
import subprocess
import sys

from foresight_os.analysis.result_committer import ANALYSIS_STAGE_RESULT_CONTRACT, CanonicalResultCommitter
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.wayfinding import create_work_brief
from foresight_os.domain.models import AnalysisState, CalculationRecord, Evidence, MeasurementKey, Revision, SourceLocator


def _payload():
    return {
        "contract": ANALYSIS_STAGE_RESULT_CONTRACT,
        "stage_id": "stage-1",
        "evidence": [
            {
                "id": "evidence-1",
                "source_locator": {
                    "file_version": "fixture-v1",
                    "sheet": "Summary",
                    "range": "B2",
                    "units": "percent",
                    "transformation": "none",
                    "calculation": "source value",
                },
                "version": "v1",
                "date": "2026-10-15",
                "excerpt": "Observed share is 42%.",
                "limitations": ["single period"],
            }
        ],
        "calculations": [],
        "claims": [],
        "implications": [],
        "recommendations": [],
        "artifacts": [
            {"id": "artifact-1", "kind": "executive report", "path": "artifacts/executive-report.md", "relationship_ids": []}
        ],
        "relationships": [],
        "assumptions": [],
        "uncertainty": [],
        "monitoring_indicators": [],
    }


def test_crash_window_replay_is_idempotent_and_does_not_create_false_receipt(tmp_path: Path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()

    first = committer(stage, _payload(), {})
    assert store.load_stage_receipts() == {}

    second = committer(stage, _payload(), {})
    state = store.load_pending()
    assert first.result_references == second.result_references
    assert first.result_hashes == second.result_hashes
    assert len(state.evidence) == 1
    assert len(state.artifacts) == 1


def test_fresh_process_reloads_canonical_state_and_deliverable_status_without_provider(tmp_path: Path):
    store = AnalysisStore(tmp_path / "case")
    store.save_brief(create_work_brief("Question", investigation_id="case", desired_deliverables=["executive report"]))
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    committer(stage, _payload(), {})

    script = """
import json
import sys
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.domain.challenge import derive_finding_views

store = AnalysisStore(sys.argv[1])
state = store.load_analysis()
brief = store.load_brief()
artifacts = {item.kind: item.path for item in state.artifacts}
print(json.dumps({
    "records": sorted(state.canonical_records()),
    "record_kinds": sorted(item.kind for item in state.artifacts) + ["evidence" for _ in state.evidence],
    "revision_status": state.revision_status.value,
    "deliverables": {item: ("PERSISTED" if any(item.lower() in value.lower() for value in [*artifacts, *artifacts.values()]) else "NOT_STARTED") for item in brief.desired_deliverables},
    "finding_views": len(derive_finding_views(state)),
}))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    completed = subprocess.run(
        [sys.executable, "-c", script, str(store.root)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(completed.stdout)
    assert len(payload["records"]) == 2
    assert payload["record_kinds"] == ["executive report", "evidence"]
    assert payload["revision_status"] == "PENDING_REVIEW"
    assert payload["deliverables"]["executive report"] == "PERSISTED"
    assert payload["finding_views"] == 0


def test_legacy_calculation_without_verification_status_reloads_unverified(tmp_path: Path):
    store = AnalysisStore(tmp_path / "legacy")
    state = AnalysisState(
        "legacy",
        1,
        evidence=[Evidence("e1", SourceLocator("hash", "Sheet", "A1", "units", "none", "source"), "v1", "2026", "1")],
        calculations=[CalculationRecord("calculation-1", MeasurementKey("scope", "measure", "2026", "units"), "x", ["e1"], 1.0, "units", ["hash:Sheet!A1"])],
        revisions=[Revision("revision-1", 1, "legacy", ["calculation-1"])],
    )
    store.save_analysis(state)
    value = json.loads(store.analysis_path.read_text(encoding="utf-8"))
    value["calculations"][0].pop("verification_status")
    store.analysis_path.write_text(json.dumps(value), encoding="utf-8")

    loaded = store.load_analysis()

    assert loaded.calculations[0].verification_status.value == "NOT_VERIFIED"
