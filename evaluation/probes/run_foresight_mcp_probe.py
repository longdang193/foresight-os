import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    args = parser.parse_args()
    result = subprocess.run([sys.executable, str(ROOT / "evaluation" / "probes" / "run_mcp_probe.py"), "--mode", "disposable"], cwd=ROOT, capture_output=True, text=True, check=False)
    payload = json.loads(result.stdout)
    receipt = {
        "mode": "foresight-mcp",
        "status": "verified" if payload.get("status") == "verified" else "failed",
        "controller_assignment": True,
        "native_binding": payload.get("status") == "verified",
        "server_call": payload.get("tool_calls", 0) == 1,
        "session_close": payload.get("cleanup") == "scope-owned-session",
        "raw_payload_retained": payload.get("raw_payload_retained", True),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "foresight-mcp-probe.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
