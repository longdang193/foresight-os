import argparse
import asyncio
import json
from pathlib import Path

from run_anomaly_probe import run_probe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", default="20261012")
    parser.add_argument("--output-root", type=Path, default=Path("work/toolbelt-probes"))
    args = parser.parse_args()
    report = asyncio.run(run_probe(args.runs, args.seed, args.warmup))
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "toolbelt-anomaly-probe.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
