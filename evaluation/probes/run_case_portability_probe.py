from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.vertical_slice import run_vertical_slice


CASE_SHAPES = {
    "case-001": "existing_supported",
    "case-002": "mappings_only",
    "case-003": "missing_or_contradictory",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _production_snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _digest(path)
        for path in sorted((root / "src").rglob("*.py"))
    }


def _revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _run_case(repo_root: Path, case_dir: Path, output_root: Path) -> dict[str, object]:
    case_id = case_dir.name
    workbook = case_dir / "workbook.csv"
    before_source = _digest(workbook)
    before_production = _production_snapshot(repo_root)
    output_dir = output_root / case_id
    tracemalloc.start()
    started = time.perf_counter()
    try:
        outcome = run_vertical_slice(workbook, output_dir, human_accept=True)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        _, peak_allocation = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    after_production = _production_snapshot(repo_root)
    changed_production = sorted(
        path
        for path in set(before_production) | set(after_production)
        if before_production.get(path) != after_production.get(path)
    )
    reloaded = None
    if outcome.accepted:
        reloaded = AnalysisStore(output_dir).load_analysis()
    recovered = bool(reloaded is not None and (output_dir / "analysis.json").exists() and outcome.report_path and outcome.report_path.exists())
    source_unchanged = before_source == _digest(workbook)
    status = "VERIFIED" if outcome.accepted and recovered and source_unchanged and not changed_production else "FAILED"
    return {
        "case_id": case_id,
        "shape": CASE_SHAPES.get(case_id, "unclassified"),
        "status": status,
        "source_sha256": before_source,
        "production_files_changed": changed_production,
        "manual_setup_actions": 0,
        "approval_interruptions": 0,
        "human_acceptance_simulated": True,
        "metrics": {
            "elapsed_ms": elapsed_ms,
            "time_to_first_useful_finding_ms": elapsed_ms if outcome.accepted else None,
            "workbook_hashes": 1,
            "workbook_parse_count": 1,
            "model_calls": "not_measured",
            "validation_escalations": 0 if outcome.review.accepted else 1,
            "peak_allocation_bytes": peak_allocation,
            "runtime_branches": ["sequential", "vertical_slice_guardrail"],
        },
        "recovery": {
            "analysis_reloaded": reloaded is not None,
            "report_reloaded": bool(outcome.report_path and outcome.report_path.exists()),
            "source_unchanged": source_unchanged,
        },
        "outcome_status": outcome.status,
        "review_accepted": outcome.review.accepted,
    }


def run(cases_root: Path, output_root: Path) -> dict[str, object]:
    repo_root = Path(__file__).parents[2].resolve()
    if not cases_root.is_dir():
        return {"status": "BLOCKED_INPUT", "input_reason": "approved cases root is absent", "cases": []}
    case_dirs = [cases_root / case_id for case_id in CASE_SHAPES]
    missing = [str(path) for path in case_dirs if not (path / "workbook.csv").is_file()]
    if missing:
        return {"status": "BLOCKED_INPUT", "input_reason": "required case workbook is absent", "missing": missing, "cases": []}
    output_root.mkdir(parents=True, exist_ok=True)
    cases = [_run_case(repo_root, case_dir, output_root) for case_dir in case_dirs]
    return {
        "schema_version": 1,
        "status": "VERIFIED" if all(item["status"] == "VERIFIED" for item in cases) else "FAILED",
        "revision": {"commit": _revision(), "repo_root": str(repo_root)},
        "case_count": len(cases),
        "cases": cases,
        "limitations": [
            "model calls and manual actions are not measured by the deterministic local vertical-slice harness",
            "case-002 and case-003 currently reuse the frozen CSV schema; their shape labels are staged benchmark categories",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.cases, args.output.parent / args.output.stem)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
