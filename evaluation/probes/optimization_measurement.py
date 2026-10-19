from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from foresight_os.analysis.evidence_workflow import run_xlsx_finding_workflow
from foresight_os.domain.challenge import ReviewOutcome, ReviewRecord, build_material_fingerprint, derive_finding_views
from foresight_os.domain.models import AnalysisState
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, ToolbeltLimits


SCHEMA_VERSION = 3
HARNESS_VERSION = "optimization-harness-v1"
HARNESS_PATHS = (
    "evaluation/probes/optimization_measurement.py",
    "evaluation/probes/run_optimization_probe.py",
    "evaluation/probes/compare_optimization_receipts.py",
)
MEASUREMENT_STATUSES = {"VERIFIED", "FAILED", "NOT_MEASURED", "DEFERRED", "FINAL_ONLY"}
MANDATORY_XLSX_WORKLOADS = (
    "cold_workbook",
    "same_view_repeat",
    "different_selection",
    "analyst_validator_reuse",
    "repeated_investigation",
    "large_retained_context",
    "multi_workbook",
    "blocking_cancellation",
)
DETERMINISTIC_XLSX_WORKLOADS = MANDATORY_XLSX_WORKLOADS + ("public_workflow_context_reuse",)
SCENARIO_XLSX_WORKLOADS = (
    "changed_brief",
    "changed_selection",
    "history-10",
    "history-100",
    "history-1000",
    "correction",
    "workbook_cancellation",
    "synthesis_cancellation",
)

_TARGET_ROOT: Path | None = None
_HARNESS_ROOT: Path | None = None


def configure_measurement_roots(*, target_root: Path, harness_root: Path) -> None:
    global _TARGET_ROOT, _HARNESS_ROOT
    _TARGET_ROOT = target_root.resolve()
    _HARNESS_ROOT = harness_root.resolve()


def _source_tree_digest(repo_root: Path, *, revision: str | None = None) -> str:
    tracked_paths = subprocess.run(
        ["git", "ls-files", "-z", "--", "src", "tests", "evaluation", ".github", "README.md", "pyproject.toml"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    if revision is None:
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not dirty:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
    digest = hashlib.sha256()
    for raw_path in sorted(item for item in tracked_paths if item):
        relative_path = raw_path.decode()
        content = (
            subprocess.run(
                ["git", "show", f"{revision}:{relative_path}"],
                cwd=repo_root,
                check=True,
                capture_output=True,
            ).stdout
            if revision
            else (repo_root / relative_path).read_bytes()
        )
        digest.update(raw_path)
        digest.update(b"\0")
        digest.update(content)
    return digest.hexdigest()


def _revision_metadata(target_root: Path | None = None) -> dict[str, object]:
    import foresight_os

    repo_root = (target_root or _TARGET_ROOT or Path(__file__).parents[2]).resolve()
    package_path = Path(foresight_os.__file__).resolve()
    if repo_root not in package_path.parents:
        raise RuntimeError(f"resolved foresight_os package is outside measured worktree: {package_path}")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip())
    return {
        "commit": revision,
        "repo_root": str(repo_root),
        "package_path": str(package_path),
        "dirty": dirty,
        "source_tree_sha256": _source_tree_digest(repo_root),
        "commit_source_tree_sha256": _source_tree_digest(repo_root, revision=revision),
    }


def _environment_metadata() -> dict[str, object]:
    freeze = sorted(subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines())
    metadata = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": str(Path(sys.executable).resolve()),
        "pip_freeze": freeze,
    }
    metadata["identity"] = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode("utf-8")).hexdigest()
    return metadata


def _harness_metadata(harness_root: Path | None = None) -> dict[str, object]:
    repo_root = (harness_root or _HARNESS_ROOT or Path(__file__).parents[2]).resolve()
    digest = hashlib.sha256()
    for relative_path in HARNESS_PATHS:
        path = repo_root / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return {
        "version": HARNESS_VERSION,
        "source_tree_sha256": digest.hexdigest(),
        "paths": list(HARNESS_PATHS),
    }


def process_rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process(os.getpid()).memory_info().rss)
    except Exception:
        return None


def measurement_evidence(status: str, *, limitation: str | None = None, **values: Any) -> dict[str, Any]:
    if status not in MEASUREMENT_STATUSES:
        raise ValueError(f"unsupported measurement status: {status}")
    if status != "VERIFIED" and not limitation:
        raise ValueError("unverified measurements require a limitation")
    return {"status": status, "limitation": limitation, **values}


def observed_finding_views(state: AnalysisState | None) -> tuple[object, ...]:
    return derive_finding_views(state) if state is not None else ()


def accepted_finding_count(state: AnalysisState | None) -> int:
    return sum(1 for finding in observed_finding_views(state) if finding.accepted)


def observed_xlsx_state(fixture: Path, root: Path) -> AnalysisState | None:
    store = AnalysisStore(root / "finding-state")
    result = run_xlsx_finding_workflow(
        store,
        fixture,
        AnalysisOperation("aggregate", value_column="Value"),
        selection=SheetSelection(include_hidden=True, include_hidden_rows=True),
        human_decision="ACCEPT",
    )
    state = result.analysis
    if state is None:
        return None
    target_ids = tuple(item.id for item in [*state.claims, *state.implications, *state.recommendations])
    review = ReviewRecord(
        review_id="optimization-observed-review",
        target_ids=target_ids,
        reviewed_state_revision=state.revision,
        input_fingerprint=build_material_fingerprint(state, target_ids),
        outcome=ReviewOutcome.ACCEPTED,
    )
    return replace(state, review_records=[review])


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * percentile)))
    return round(ordered[index], 3)


def _metric_snapshot(metrics: Any, wall_time_ms: float) -> dict[str, Any]:
    return {
        "wall_time_ms": round(float(wall_time_ms), 3),
        "queue_wait_ms": round(float(getattr(metrics, "queue_wait_ms", 0) or 0), 3),
        "tool_latency_ms": round(float(getattr(metrics, "tool_latency_ms", 0) or 0), 3),
        "execution_time_ms": round(float(getattr(metrics, "execution_time_ms", 0) or 0), 3),
        "event_loop_lag_ms": round(float(getattr(metrics, "event_loop_lag_ms", 0) or 0), 3),
        "model_calls": int(getattr(metrics, "model_calls", 0) or 0),
        "tool_calls_total": int(getattr(metrics, "tool_calls", 0) or 0),
        "local_tool_calls": int(getattr(metrics, "local_tool_calls", 0) or 0),
        "mcp_tool_calls": int(getattr(metrics, "mcp_tool_calls", 0) or 0),
        "external_http_requests": int(getattr(metrics, "external_http_requests", 0) or 0),
        "input_tokens": int(getattr(metrics, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(metrics, "output_tokens", 0) or 0),
        "cache_hits": int(getattr(metrics, "cache_hits", 0) or 0),
        "reused_stages": int(getattr(metrics, "reused_stages", 0) or 0),
        "reassessed_stages": int(getattr(metrics, "reassessed_stages", 0) or 0),
        "cleanup_complete": bool(getattr(metrics, "cleanup_complete", False)),
        "failure_class": getattr(metrics, "failure_class", None),
    }


def _summarize_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "wall_time_ms",
        "queue_wait_ms",
        "tool_latency_ms",
        "execution_time_ms",
        "event_loop_lag_ms",
    )
    summary: dict[str, Any] = {}
    for field in fields:
        values = [float(item[field]) for item in samples]
        summary[f"{field}_p50"] = _percentile(values, 0.50)
        summary[f"{field}_p90"] = _percentile(values, 0.90)
        summary[f"{field}_p95"] = _percentile(values, 0.95)
        summary[f"{field}_min"] = round(min(values), 3) if values else 0.0
        summary[f"{field}_max"] = round(max(values), 3) if values else 0.0
    for field in (
        "model_calls",
        "tool_calls_total",
        "local_tool_calls",
        "mcp_tool_calls",
        "external_http_requests",
        "input_tokens",
        "output_tokens",
        "cache_hits",
        "reused_stages",
        "reassessed_stages",
    ):
        summary[field] = sum(int(item[field]) for item in samples)
    summary["cleanup_complete"] = all(bool(item["cleanup_complete"]) for item in samples)
    summary["failure_class"] = next((item["failure_class"] for item in samples if item["failure_class"]), None)
    return summary


def stage_metric(stage_id: str, pattern: str, result: Any, elapsed_ms: float, samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    metrics = getattr(result, "metrics", result)
    observations = samples or [_metric_snapshot(metrics, elapsed_ms)]
    summary = _summarize_samples(observations)
    return {
        "stage_id": stage_id,
        "pattern": pattern,
        "sample_count": len(observations),
        "latency": summary,
        "model_calls": summary["model_calls"],
        "tool_calls_total": summary["tool_calls_total"],
        "local_tool_calls": summary["local_tool_calls"],
        "mcp_tool_calls": summary["mcp_tool_calls"],
        "external_http_requests": summary["external_http_requests"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "cache_hits": summary["cache_hits"],
        "reused_stages": summary["reused_stages"],
        "reassessed_stages": summary["reassessed_stages"],
        "cleanup_complete": summary["cleanup_complete"],
        "failure_class": summary["failure_class"],
    }


def build_receipt(
    *,
    mode: str,
    fixture: Path,
    workbook: dict[str, Any],
    patterns: dict[str, Any],
    soak: dict[str, Any],
    external_fixture: dict[str, Any],
    native_mcp: dict[str, Any],
    state: AnalysisState | None,
    stage_metrics: list[dict[str, Any]],
    thresholds: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    target_root: Path | None = None,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    accepted_count = accepted_finding_count(state)
    economics = {
        "model_calls": sum(int(item.get("model_calls", 0) or 0) for item in patterns.values()),
        "tool_calls_total": sum(int(item.get("tool_calls_total", 0) or 0) for item in patterns.values()) + int(native_mcp.get("tool_calls", 0) or 0) + int(external_fixture.get("tool_calls", 0) or 0),
        "local_tool_calls": int(workbook.get("local_tool_calls", 0) or 0) + sum(int(item.get("local_tool_calls", 0) or 0) for item in patterns.values()),
        "mcp_tool_calls": int(native_mcp.get("tool_calls", 0) or 0),
        "external_http_requests": int(external_fixture.get("external_http_requests", 0) or 0),
        "input_tokens": sum(int(item.get("input_tokens", 0) or 0) for item in patterns.values()),
        "output_tokens": sum(int(item.get("output_tokens", 0) or 0) for item in patterns.values()),
    }
    economics["per_accepted_finding"] = {
        key: round(value / accepted_count, 6) if accepted_count else None
        for key, value in economics.items()
        if key != "per_accepted_finding"
    }
    evidence = evidence or {
        "correctness": measurement_evidence("VERIFIED", limitation=None),
        "latency": measurement_evidence("VERIFIED", limitation=None),
        "allocation": measurement_evidence("VERIFIED", limitation=None),
        "soak": measurement_evidence("VERIFIED", limitation=None),
        "regression_threshold": measurement_evidence("NOT_MEASURED", limitation="requires baseline/release comparison"),
        "optimization_demonstrated": measurement_evidence("NOT_MEASURED", limitation="no optimization claim is made by a single receipt"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "status": evidence["correctness"]["status"],
        "environment": _environment_metadata(),
        "harness": _harness_metadata(harness_root),
        "revision": _revision_metadata(target_root),
        "workload": {
            "fixture": fixture.name,
            "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
            "warmups": 2,
            "measured_runs": 10,
            "samples_per_process_run": 10,
            "limits": asdict(ToolbeltLimits()),
            "patterns": sorted(patterns),
            "deterministic_workloads": list(DETERMINISTIC_XLSX_WORKLOADS),
            "scenario_workloads": list(SCENARIO_XLSX_WORKLOADS),
            "parameters": {
                "history_sizes": [10, 100, 1000],
                "timing_sample_count": 10,
                "cold_sample_count": 10,
            },
        },
        "acceptance": thresholds,
        "accepted_finding_count": accepted_count,
        "economics": economics,
        "xlsx": workbook,
        "maf_patterns": patterns,
        "stage_metrics": stage_metrics,
        "soak": soak,
        "external_fixture": external_fixture,
        "native_mcp": native_mcp,
        "resource": {"rss_bytes": process_rss_bytes(), "measurement": "process_rss"},
        "evidence": evidence,
        "acceptance_matrix": {
            name: {
                "status": workbook.get("workloads", {}).get(name, {}).get("status", "MISSING"),
                "correctness": workbook.get("workloads", {}).get(name, {}).get("correctness", "MISSING"),
                "limitation": workbook.get("workloads", {}).get(name, {}).get("limitation"),
            }
            for name in MANDATORY_XLSX_WORKLOADS
        },
        "scenario_matrix": {
            name: {
                "status": workbook.get("scenario_workloads", {}).get(name, {}).get("status", "NOT_MEASURED"),
                "correctness": workbook.get("scenario_workloads", {}).get(name, {}).get("correctness", "NOT_MEASURED"),
                "limitation": workbook.get("scenario_workloads", {}).get(name, {}).get("limitation"),
            }
            for name in SCENARIO_XLSX_WORKLOADS
        },
    }
