import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_disposable_mcp_probe_is_sanitized_and_verified():
    result = subprocess.run(
        [sys.executable, "evaluation/probes/run_mcp_probe.py", "--mode", "disposable"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)

    assert report["status"] == "verified"
    assert report["mutation_tool_refused"]
    assert report["raw_payload_retained"] is False
    assert "Capacity remains uncertain" not in result.stdout


def test_real_probe_is_separate_and_blocks_without_approved_configuration():
    result = subprocess.run(
        [sys.executable, "evaluation/probes/run_mcp_probe.py", "--mode", "real-mcp"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={key: value for key, value in __import__("os").environ.items() if not key.startswith("FORESIGHT_REAL_MCP_")},
    )

    assert json.loads(result.stdout)["status"] == "BLOCKED_EXTERNAL"
