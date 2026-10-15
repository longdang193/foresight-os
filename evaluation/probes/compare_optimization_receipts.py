import argparse
import json
from pathlib import Path


SCHEMA_VERSION = 3
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
SESSION_PHASES = ("cold", "warm_identical", "different_selection", "analyst_to_validator", "explicit_currentness")
SESSION_COUNTERS = ("capture_count", "capture_hash_count", "currentness_hash_count", "xlsx_parse_count", "openpyxl_load_count")


def _tool_calls(receipt: dict) -> int:
    return int(receipt.get("economics", {}).get("tool_calls_total", 0) or 0)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_measurement_receipt(receipt: dict) -> list[str]:
    missing: list[str] = []
    required = (
        "schema_version",
        "benchmark",
        "revision",
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
    revision = receipt.get("revision", {})
    for field in ("commit", "repo_root", "package_path", "source_tree_fingerprint", "implementation_fingerprint", "harness_fingerprint", "measurement_mode"):
        if not isinstance(revision.get(field), str) or not revision[field].strip():
            missing.append(f"revision.{field}")
    if not isinstance(revision.get("dirty_paths"), list):
        missing.append("revision.dirty_paths")
    benchmark = receipt.get("benchmark", {})
    for field in ("workload_id", "schema_version"):
        if not benchmark.get(field):
            missing.append(f"benchmark.{field}")
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
    session_reuse = workbook.get("session_reuse")
    if not isinstance(session_reuse, dict):
        missing.append("xlsx.session_reuse")
    else:
        for phase in SESSION_PHASES:
            counters = session_reuse.get(phase)
            if not isinstance(counters, dict):
                missing.append(f"xlsx.session_reuse.{phase}")
                continue
            for field in SESSION_COUNTERS:
                value = counters.get(field)
                if not _is_number(value) or int(value) < 0:
                    missing.append(f"xlsx.session_reuse.{phase}.{field}")
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
    workload = receipt.get("workload", {})
    if not workload.get("patterns"):
        missing.append("workload.patterns")
    if workload.get("workload_id") != benchmark.get("workload_id"):
        missing.append("workload.workload_id")
    return sorted(set(missing))


def _pct(release: float, baseline: float) -> float:
    if baseline <= 0:
        raise ValueError("comparison baseline must be positive")
    return round((release / baseline - 1) * 100, 3)


def _safe_pct(release: float, baseline: float) -> float | None:
    if baseline == 0:
        return 0.0 if release == 0 else None
    return _pct(release, baseline)


def _comparison_metric(baseline: float, release: float) -> dict[str, float | None]:
    return {
        "baseline": baseline,
        "release": release,
        "delta": round(release - baseline, 6),
        "pct": _safe_pct(release, baseline),
    }


def validate_stability(baseline_repeat: list[dict], release_repeat: list[dict]) -> dict:
    errors: list[str] = []
    if len(baseline_repeat) != 2 or len(release_repeat) != 2:
        errors.append("exactly two receipts are required per revision")
    for label, receipts in (("baseline", baseline_repeat), ("release", release_repeat)):
        if len(receipts) != 2:
            continue
        first, second = receipts
        if first.get("workload") != second.get("workload"):
            errors.append(f"{label}.workload differs between repeats")
        if first.get("environment") != second.get("environment"):
            errors.append(f"{label}.environment differs between repeats")
        if first.get("revision") != second.get("revision"):
            errors.append(f"{label}.revision differs between repeats")
        if first.get("benchmark") != second.get("benchmark"):
            errors.append(f"{label}.benchmark differs between repeats")
        try:
            drift = _safe_pct(
                float(second["maf_patterns"]["CHALLENGE_RECOMMENDATION"]["latency"]["wall_time_ms_p95"]),
                float(first["maf_patterns"]["CHALLENGE_RECOMMENDATION"]["latency"]["wall_time_ms_p95"]),
            )
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            errors.append(f"{label}.group_chat_p95 is unavailable")
        else:
            if drift is None:
                errors.append(f"{label}.group_chat_p95 is unavailable")
                continue
            drift = abs(drift)
            if drift > 10:
                errors.append(f"{label}.group_chat_p95 drift exceeds 10%: {drift}")
    if len(baseline_repeat) == 2 and len(release_repeat) == 2:
        if baseline_repeat[0].get("workload") != release_repeat[0].get("workload"):
            errors.append("baseline/release workload differs")
        if baseline_repeat[0].get("environment") != release_repeat[0].get("environment"):
            errors.append("baseline/release environment differs")
        if baseline_repeat[0].get("benchmark") != release_repeat[0].get("benchmark"):
            errors.append("baseline/release benchmark differs")
        if baseline_repeat[0].get("revision", {}).get("harness_fingerprint") != release_repeat[0].get("revision", {}).get("harness_fingerprint"):
            errors.append("baseline/release harness differs")
        if (
            baseline_repeat[0].get("revision", {}).get("commit")
            == release_repeat[0].get("revision", {}).get("commit")
        ):
            errors.append("baseline/release revision is identical")
    return {"accepted": not errors, "errors": errors}


def compare_repeats(baseline_repeat: list[dict], release_repeat: list[dict]) -> dict:
    stability = validate_stability(baseline_repeat, release_repeat)
    comparisons = [compare(baseline, release) for baseline, release in zip(baseline_repeat, release_repeat, strict=False)]
    return {
        "accepted": stability["accepted"] and len(comparisons) == 2 and all(item.get("accepted") is True for item in comparisons),
        "stability": stability,
        "comparisons": comparisons,
    }


def compare(baseline: dict, release: dict) -> dict:
    missing_baseline = _validate_measurement_receipt(baseline)
    missing_release = _validate_measurement_receipt(release)
    if missing_baseline or missing_release:
        return {"accepted": False, "missing_required_evidence": {"baseline": missing_baseline, "release": missing_release}}

    mismatches: list[str] = []
    if baseline.get("benchmark") != release.get("benchmark"):
        mismatches.append("benchmark")
    if baseline.get("environment") != release.get("environment"):
        mismatches.append("environment")
    if baseline.get("revision", {}).get("harness_fingerprint") != release.get("revision", {}).get("harness_fingerprint"):
        mismatches.append("harness")
    if baseline.get("revision", {}).get("implementation_fingerprint") == release.get("revision", {}).get("implementation_fingerprint"):
        mismatches.append("implementation_fingerprint")
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
    pattern_comparisons = {}
    for name in sorted(REQUIRED_PATTERNS):
        baseline_latency = float(baseline["maf_patterns"][name]["latency"]["wall_time_ms_p95"])
        release_latency = float(release["maf_patterns"][name]["latency"]["wall_time_ms_p95"])
        pattern_regressions[name] = _pct(release_latency, baseline_latency)
        pattern_comparisons[name] = _comparison_metric(baseline_latency, release_latency)
    p95_regression = _pct(float(release["xlsx"]["p95_ms"]), float(baseline["xlsx"]["p95_ms"]))
    allocation_regression = _pct(float(release["xlsx"]["peak_allocation_bytes"]), float(baseline["xlsx"]["peak_allocation_bytes"]))
    rss_regression = _pct(float(release["resource"]["rss_bytes"]), float(baseline["resource"]["rss_bytes"]))
    absolute = {
        "xlsx": {
            "p95_ms": _comparison_metric(float(baseline["xlsx"]["p95_ms"]), float(release["xlsx"]["p95_ms"])),
            "peak_allocation_bytes": _comparison_metric(float(baseline["xlsx"]["peak_allocation_bytes"]), float(release["xlsx"]["peak_allocation_bytes"])),
        },
        "resource": {
            "rss_bytes": _comparison_metric(float(baseline["resource"]["rss_bytes"]), float(release["resource"]["rss_bytes"])),
        },
        "maf_patterns": pattern_comparisons,
        "economics_per_accepted_finding": {
            field: _comparison_metric(
                float(baseline_economics["per_accepted_finding"][field]),
                float(release_economics["per_accepted_finding"][field]),
            )
            for field in ECONOMIC_FIELDS
        },
    }
    reused_stage_new_calls = [
        metric["stage_id"]
        for metric in release.get("stage_metrics", ())
        if int(metric.get("reused_stages", 0) or 0) > 0 and (int(metric.get("model_calls", 0) or 0) > 0 or int(metric.get("tool_calls_total", 0) or 0) > 0)
    ]
    non_regressive_economics = all(
        float(release_economics["per_accepted_finding"][field]) <= float(baseline_economics["per_accepted_finding"][field])
        for field in {"model_calls", "tool_calls_total", "local_tool_calls", "mcp_tool_calls", "external_http_requests"}
    )
    release_session = release["xlsx"]["session_reuse"]
    session_gate_failures: list[str] = []
    if not release_session.get("available", False):
        session_gate_failures.append("session_reuse.available")
    cold = release_session["cold"]
    if cold["capture_count"] != 1 or cold["capture_hash_count"] != 1:
        session_gate_failures.append("session_reuse.cold.capture")
    if cold["xlsx_parse_count"] < 1 or cold["openpyxl_load_count"] < 2:
        session_gate_failures.append("session_reuse.cold.parse")
    for phase in ("warm_identical", "different_selection", "analyst_to_validator", "explicit_currentness"):
        counters = release_session[phase]
        if counters["capture_count"] != 0 or counters["capture_hash_count"] != 0:
            session_gate_failures.append(f"session_reuse.{phase}.capture")
    if any(release_session["warm_identical"][field] != 0 for field in ("currentness_hash_count", "xlsx_parse_count", "openpyxl_load_count")):
        session_gate_failures.append("session_reuse.warm_identical.reuse")
    if release_session["analyst_to_validator"]["xlsx_parse_count"] != 0 or release_session["analyst_to_validator"]["openpyxl_load_count"] != 0:
        session_gate_failures.append("session_reuse.analyst_to_validator.reuse")
    if release_session["explicit_currentness"]["currentness_hash_count"] != 1:
        session_gate_failures.append("session_reuse.explicit_currentness")
    if not release_session.get("resource_observations", {}).get("same_view_sha_matches", False):
        session_gate_failures.append("session_reuse.same_view_sha_matches")
    accepted = (
        p95_regression <= 20
        and allocation_regression <= 15
        and rss_regression <= 15
        and all(value <= 20 for value in pattern_regressions.values())
        and non_regressive_economics
        and not reused_stage_new_calls
        and not session_gate_failures
    )
    return {
        "accepted": accepted,
        "baseline": {"p95_ms": baseline["xlsx"]["p95_ms"], "peak_allocation_bytes": baseline["xlsx"]["peak_allocation_bytes"], "economics_per_accepted_finding": baseline_economics["per_accepted_finding"]},
        "release": {"p95_ms": release["xlsx"]["p95_ms"], "peak_allocation_bytes": release["xlsx"]["peak_allocation_bytes"], "economics_per_accepted_finding": release_economics["per_accepted_finding"]},
        "absolute": absolute,
        "regression": {"p95_pct": p95_regression, "peak_allocation_pct": allocation_regression, "rss_pct": rss_regression, "pattern_p95_pct": pattern_regressions, "economics_per_accepted_finding_delta": economic_regressions},
        "accepted_finding_count": {"baseline": baseline_count, "release": int(release["accepted_finding_count"])},
        "workload": baseline["workload"],
        "native_mcp": {"baseline": baseline["native_mcp"]["status"], "release": release["native_mcp"]["status"]},
        "reused_stage_new_calls": reused_stage_new_calls,
        "session_reuse": {"release": release_session, "gate_failures": session_gate_failures},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--baseline-repeat", type=Path, nargs=2)
    parser.add_argument("--release-repeat", type=Path, nargs=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.baseline_repeat or args.release_repeat:
        if not args.baseline_repeat or not args.release_repeat:
            parser.error("--baseline-repeat and --release-repeat must be supplied together")
        result = compare_repeats(
            [json.loads(path.read_text(encoding="utf-8")) for path in args.baseline_repeat],
            [json.loads(path.read_text(encoding="utf-8")) for path in args.release_repeat],
        )
    else:
        if not args.baseline or not args.release:
            parser.error("--baseline and --release are required without repeat inputs")
        result = compare(json.loads(args.baseline.read_text(encoding="utf-8")), json.loads(args.release.read_text(encoding="utf-8")))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
