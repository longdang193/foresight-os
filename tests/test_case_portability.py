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


def test_case_portability_probe_fails_closed_for_missing_inputs(tmp_path: Path):
    report = run(tmp_path / "missing", tmp_path / "portability")

    assert report["status"] == "BLOCKED_INPUT"
