import asyncio
import json
import subprocess
import sys
from pathlib import Path

from evaluation.probes.run_anomaly_probe import run_probe


ROOT = Path(__file__).parents[1]


def test_anomaly_probe_is_deterministic_for_short_run():
    report = asyncio.run(run_probe(3, "test-seed"))

    assert report["status"] == "verified"
    assert report["state_hash_stable"]
    assert not report["failures"]


def test_anomaly_probe_cli_emits_sanitized_measurement_report():
    result = subprocess.run(
        [sys.executable, "evaluation/probes/run_anomaly_probe.py", "--runs", "3", "--seed", "test-seed"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(result.stdout)
    assert report["status"] == "verified"
    assert report["runs"] == 3
