from pathlib import Path

from evaluation.probes.run_case_portability_probe import run


ROOT = Path(__file__).parents[1]


def test_case_portability_probe_reports_three_local_shapes(tmp_path: Path):
    report = run(ROOT / "evaluation" / "cases", tmp_path / "portability")

    assert report["status"] == "VERIFIED"
    assert report["case_count"] == 3
    assert {item["shape"] for item in report["cases"]} == {
        "existing_supported",
        "mappings_only",
        "missing_or_contradictory",
    }
    assert len({item["source_sha256"] for item in report["cases"]}) == 3
    assert all(item["production_files_changed"] == [] for item in report["cases"])
    assert all(item["recovery"]["analysis_reloaded"] for item in report["cases"])
    contradictory = next(item for item in report["cases"] if item["case_id"] == "case-003")
    assert contradictory["expected_outcome_verified"]
    assert contradictory["metrics"]["workbook_hashes"] == 2
    assert contradictory["metrics"]["workbook_parse_count"] == 1
    assert contradictory["metrics"]["time_to_first_useful_finding_ms"] == "not_measured"


def test_case_portability_probe_fails_closed_for_missing_inputs(tmp_path: Path):
    report = run(tmp_path / "missing", tmp_path / "portability")

    assert report["status"] == "BLOCKED_INPUT"
