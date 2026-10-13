import argparse
import json
from pathlib import Path


SCHEMA_VERSION = 2
REQUIRED_PATTERNS = {"DIRECT", "ANALYZE", "CONCURRENT", "HANDOFF", "CHALLENGE_RECOMMENDATION"}
ECONOMIC_FIELDS = (
    "model_calls",
    "tool_calls_total",
    "local_tool_calls",
    "mcp_tool_calls",
    "external_http_requests",
    "input_tokens",
    "output_tokens",
)
SOAK_FIELDS = (
    "rss_bytes",
    "active_python_tasks",
    "thread_count",
    "child_process_count",
    "owned_capability_resources",
    "mcp_session_count",
)


def _tool_calls(receipt: dict) -> int:
    return int(receipt.get("economics", {}).get("tool_calls_total", 0) or 0)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_measurement_receipt(receipt: dict) -> list[str]:
    missing: list[str] = []
    required = (
        "schema_version",
        "accepted_finding_count",
        "economics",
        "stage_metrics",
        "resource",
        "maf_patterns",
        "xlsx",
        "soak",
        "native_mcp",
        "workload",
        "acceptance",
    )
    missing.extend(key for key in required if key not in receipt)
    if receipt.get("schema_version") != SCHEMA_VERSION:
        missing.append(f"schema_version={SCHEMA_VERSION}")
    accepted_count = receipt.get("accepted_finding_count")
    if not isinstance(accepted_count, int) or accepted_count <= 0:
        missing.append("accepted_finding_count>0")
    economics = receipt.get("economics", {})
    for field in ECONOMIC_FIELDS:
        if not _is_number(economics.get(field)) or int(economics[field]) < 0:
            missing.append(f"economics.{field}")
    per_finding = economics.get("per_accepted_finding", {})
    for field in ECONOMIC_FIELDS:
        if not _is_number(per_finding.get(field)):
            missing.append(f"economics.per_accepted_finding.{field}")
    if not receipt.get("stage_metrics"):
        missing.append("stage_metrics")
    for index, metric in enumerate(receipt.get("stage_metrics", ())):
        latency = metric.get("latency", {})
        if metric.get("failure_class"):
            missing.append(f"stage_metrics[{index}].successful")
        for field in ("wall_time_ms_p95", "queue_wait_ms_p95", "tool_latency_ms_p95", "execution_time_ms_p95", "event_loop_lag_ms_p95"):
            if not _is_number(latency.get(field)) or float(latency[field]) < 0:
                missing.append(f"stage_metrics[{index}].latency.{field}")
    rss = receipt.get("resource", {}).get("rss_bytes")
    if not _is_number(rss) or int(rss) <= 0:
        missing.append("resource.rss_bytes>0")
    workbook = receipt.get("xlsx", {})
    for field in ("p95_ms", "peak_allocation_bytes", "deterministic_key"):
        if field not in workbook:
            missing.append(f"xlsx.{field}")
    if not _is_number(workbook.get("p95_ms")) or float(workbook.get("p95_ms", 0)) <= 0:
        missing.append("xlsx.p95_ms>0")
    if not _is_number(workbook.get("peak_allocation_bytes")) or int(workbook.get("peak_allocation_bytes", 0)) <= 0:
        missing.append("xlsx.peak_allocation_bytes>0")
    patterns = receipt.get("maf_patterns", {})
    missing.extend(f"maf_patterns.{name}" for name in sorted(REQUIRED_PATTERNS - set(patterns)))
    for name, item in patterns.items():
        latency = item.get("latency", {})
        if not item.get("cleanup_complete", False):
            missing.append(f"maf_patterns.{name}.cleanup_complete")
        if not _is_number(latency.get("wall_time_ms_p95")) or float(latency.get("wall_time_ms_p95", 0)) <= 0:
            missing.append(f"maf_patterns.{name}.latency.wall_time_ms_p95>0")
    soak = receipt.get("soak", {})
    required_soak_runs = int(receipt.get("acceptance", {}).get("soak_runs", 0) or 0)
    snapshots = soak.get("snapshots", ())
    if not isinstance(snapshots, list) or len(snapshots) < required_soak_runs:
        missing.append("soak.snapshots")
    for index, snapshot in enumerate(snapshots):
        for field in SOAK_FIELDS:
            value = snapshot.get(field)
            if not _is_number(value) or int(value) < 0:
                missing.append(f"soak.snapshots[{index}].{field}")
        if not _is_number(snapshot.get("event_loop_lag_ms")) or float(snapshot.get("event_loop_lag_ms", -1)) < 0:
            missing.append(f"soak.snapshots[{index}].event_loop_lag_ms")
    if soak.get("monotonic_growth") is not False:
        missing.append("soak.monotonic_growth=false")
    growth = soak.get("resource_growth", {})
    for field in SOAK_FIELDS:
        if field not in growth:
            missing.append(f"soak.resource_growth.{field}")
    if receipt.get("native_mcp", {}).get("status") != "VERIFIED":
        missing.append("native_mcp.status=VERIFIED")
    if not receipt.get("workload", {}).get("patterns"):
        missing.append("workload.patterns")
    return sorted(set(missing))


def _pct(release: float, baseline: float) -> float:
    if baseline <= 0:
        raise ValueError("comparison baseline must be positive")
    return round((release / baseline - 1) * 100, 3)


def compare(baseline: dict, release: dict) -> dict:
    missing_baseline = _validate_measurement_receipt(baseline)
    missing_release = _validate_measurement_receipt(release)
    if missing_baseline or missing_release:
        return {"accepted": False, "missing_required_evidence": {"baseline": missing_baseline, "release": missing_release}}

    mismatches: list[str] = []
    if baseline.get("workload") != release.get("workload"):
        mismatches.append("workload")
    if baseline.get("xlsx", {}).get("deterministic_key") != release.get("xlsx", {}).get("deterministic_key"):
        mismatches.append("xlsx.deterministic_key")
    if baseline.get("accepted_finding_count") != release.get("accepted_finding_count"):
        mismatches.append("accepted_finding_count")
    if baseline.get("acceptance") != release.get("acceptance"):
        mismatches.append("acceptance")
    if mismatches:
        return {"accepted": False, "mismatched_comparison_inputs": mismatches}

    baseline_count = int(baseline["accepted_finding_count"])
    baseline_economics = baseline["economics"]
    release_economics = release["economics"]
    economic_regressions = {
        field: round(float(release_economics["per_accepted_finding"][field]) - float(baseline_economics["per_accepted_finding"][field]), 6)
        for field in ECONOMIC_FIELDS
    }
    pattern_regressions = {}
    for name in sorted(REQUIRED_PATTERNS):
        baseline_latency = float(baseline["maf_patterns"][name]["latency"]["wall_time_ms_p95"])
        release_latency = float(release["maf_patterns"][name]["latency"]["wall_time_ms_p95"])
        pattern_regressions[name] = _pct(release_latency, baseline_latency)
    p95_regression = _pct(float(release["xlsx"]["p95_ms"]), float(baseline["xlsx"]["p95_ms"]))
    allocation_regression = _pct(float(release["xlsx"]["peak_allocation_bytes"]), float(baseline["xlsx"]["peak_allocation_bytes"]))
    rss_regression = _pct(float(release["resource"]["rss_bytes"]), float(baseline["resource"]["rss_bytes"]))
    reused_stage_new_calls = [
        metric["stage_id"]
        for metric in release.get("stage_metrics", ())
        if int(metric.get("reused_stages", 0) or 0) > 0 and (int(metric.get("model_calls", 0) or 0) > 0 or int(metric.get("tool_calls_total", 0) or 0) > 0)
    ]
    accepted = (
        p95_regression <= 20
        and allocation_regression <= 15
        and rss_regression <= 15
        and all(value <= 20 for value in pattern_regressions.values())
        and all(value <= float(baseline_economics["per_accepted_finding"][field]) for field, value in ((field, float(release_economics["per_accepted_finding"][field])) for field in ECONOMIC_FIELDS if field in {"model_calls", "tool_calls_total", "local_tool_calls", "mcp_tool_calls", "external_http_requests"}))
        and not reused_stage_new_calls
    )
    return {
        "accepted": accepted,
        "baseline": {"p95_ms": baseline["xlsx"]["p95_ms"], "peak_allocation_bytes": baseline["xlsx"]["peak_allocation_bytes"], "economics_per_accepted_finding": baseline_economics["per_accepted_finding"]},
        "release": {"p95_ms": release["xlsx"]["p95_ms"], "peak_allocation_bytes": release["xlsx"]["peak_allocation_bytes"], "economics_per_accepted_finding": release_economics["per_accepted_finding"]},
        "regression": {"p95_pct": p95_regression, "peak_allocation_pct": allocation_regression, "rss_pct": rss_regression, "pattern_p95_pct": pattern_regressions, "economics_per_accepted_finding_delta": economic_regressions},
        "accepted_finding_count": {"baseline": baseline_count, "release": int(release["accepted_finding_count"])},
        "workload": baseline["workload"],
        "native_mcp": {"baseline": baseline["native_mcp"]["status"], "release": release["native_mcp"]["status"]},
        "reused_stage_new_calls": reused_stage_new_calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(json.loads(args.baseline.read_text(encoding="utf-8")), json.loads(args.release.read_text(encoding="utf-8")))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
