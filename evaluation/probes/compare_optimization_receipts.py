import argparse
import json
from pathlib import Path

try:
    from .optimization_measurement import MANDATORY_XLSX_WORKLOADS, SCENARIO_XLSX_WORKLOADS
except ImportError:
    from optimization_measurement import MANDATORY_XLSX_WORKLOADS, SCENARIO_XLSX_WORKLOADS


SCHEMA_VERSION = 4
REQUIRED_PATTERNS = {"DIRECT", "ANALYZE", "CONCURRENT", "HANDOFF", "CHALLENGE_RECOMMENDATION"}
REQUIRED_TIMING_PATHS = (
    "cold_workbook",
    "same_view_repeat",
    "repeated_investigation",
    "analyst_validator_reuse",
    "approved_changed_brief",
    "history-10",
    "history-100",
    "selected_sheet_stress",
)
REQUIRED_SCENARIO_WORKLOADS = ("approved_changed_brief", "changed_brief", "history-10", "history-100", "selected_sheet_stress")
READER_COUNTERS = (
    "archive_sheets_scanned",
    "selected_sheet_count",
    "selected_row_count",
    "selected_cell_count",
    "formula_count",
    "openpyxl_load_count",
    "capture_count",
    "capture_hash_count",
)
PERSISTENCE_COUNTERS = (
    "pending_write_bytes",
    "pending_write_time_ms",
    "committed_write_bytes",
    "committed_write_time_ms",
)


def _same_revision_snapshot(left: dict, right: dict) -> bool:
    """Treat differing uncommitted worktree digests as distinct revisions."""
    left_revision = left.get("revision", {})
    right_revision = right.get("revision", {})
    if left_revision.get("commit") != right_revision.get("commit"):
        return False
    left_digest = left_revision.get("source_tree_sha256")
    right_digest = right_revision.get("source_tree_sha256")
    return not (left_digest and right_digest and left_digest != right_digest)
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
MEASUREMENT_STATUSES = {"VERIFIED", "FAILED", "NOT_MEASURED", "DEFERRED", "FINAL_ONLY"}


def _tool_calls(receipt: dict) -> int:
    return int(receipt.get("economics", {}).get("tool_calls_total", 0) or 0)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_nonnegative_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_measurement_receipt(receipt: dict) -> list[str]:
    missing: list[str] = []
    required = (
        "schema_version",
        "harness",
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
        "acceptance_matrix",
    )
    missing.extend(key for key in required if key not in receipt)
    if receipt.get("schema_version") != SCHEMA_VERSION:
        missing.append(f"schema_version={SCHEMA_VERSION}")
    harness = receipt.get("harness", {})
    for field in ("version", "source_tree_sha256"):
        if not isinstance(harness.get(field), str) or not harness[field].strip():
            missing.append(f"harness.{field}")
    evidence = receipt.get("evidence")
    evidence_statuses: dict[str, str] = {}
    for dimension in ("correctness", "latency", "allocation", "soak"):
        item = evidence.get(dimension, {}) if isinstance(evidence, dict) else {}
        status = item.get("status")
        evidence_statuses[dimension] = status
        if status not in MEASUREMENT_STATUSES:
            missing.append(f"evidence.{dimension}.status")
        elif status != "VERIFIED" and not isinstance(item.get("limitation"), str):
            missing.append(f"evidence.{dimension}.limitation")
    revision = receipt.get("revision", {})
    for field in ("commit", "repo_root", "package_path", "source_tree_sha256", "commit_source_tree_sha256"):
        if not isinstance(revision.get(field), str) or not revision[field].strip():
            missing.append(f"revision.{field}")
    if revision.get("dirty") is not False:
        missing.append("revision.dirty=false")
    if (
        isinstance(revision.get("source_tree_sha256"), str)
        and isinstance(revision.get("commit_source_tree_sha256"), str)
        and revision["source_tree_sha256"] != revision["commit_source_tree_sha256"]
    ):
        missing.append("revision.source_tree_sha256_matches_commit")
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
    if evidence_statuses.get("latency", "VERIFIED") == "VERIFIED" and (not _is_number(workbook.get("p95_ms")) or float(workbook.get("p95_ms", 0)) <= 0):
        missing.append("xlsx.p95_ms>0")
    if evidence_statuses.get("allocation", "VERIFIED") == "VERIFIED" and (not _is_number(workbook.get("peak_allocation_bytes")) or int(workbook.get("peak_allocation_bytes", 0)) <= 0):
        missing.append("xlsx.peak_allocation_bytes>0")
    acceptance = receipt.get("acceptance", {})
    if acceptance.get("gate_cold_noise_floor", False):
        cold = workbook.get("cold_noise_floor", {})
        if cold.get("status") != "VERIFIED" or int(cold.get("sample_count", 0) or 0) < 10:
            missing.append("xlsx.cold_noise_floor=VERIFIED with >=10 samples")
        for field in ("p50_ms", "p95_ms", "noise_floor_ms"):
            if not _is_number(cold.get(field)) or float(cold[field]) < 0:
                missing.append(f"xlsx.cold_noise_floor.{field}>=0")
    if acceptance.get("gate_reader_metrics", False):
        reader = workbook.get("run_owned_context", {})
        for field in READER_COUNTERS:
            if not _is_nonnegative_count(reader.get(field)):
                missing.append(f"xlsx.run_owned_context.{field}>=0")
        persistence = workbook.get("persistence", {})
        for field in PERSISTENCE_COUNTERS:
            if not _is_number(persistence.get(field)) or float(persistence[field]) < 0:
                missing.append(f"xlsx.persistence.{field}>=0")
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
    soak_verified = evidence_statuses.get("soak") == "VERIFIED"
    snapshots = soak.get("snapshots", ())
    if soak_verified and (not isinstance(snapshots, list) or len(snapshots) < required_soak_runs):
        missing.append("soak.snapshots")
    for index, snapshot in enumerate(snapshots if soak_verified else ()):
        for field in SOAK_FIELDS:
            value = snapshot.get(field)
            if not _is_number(value) or int(value) < 0:
                missing.append(f"soak.snapshots[{index}].{field}")
        if not _is_number(snapshot.get("event_loop_lag_ms")) or float(snapshot.get("event_loop_lag_ms", -1)) < 0:
            missing.append(f"soak.snapshots[{index}].event_loop_lag_ms")
    if soak_verified and soak.get("monotonic_growth") is not False:
        missing.append("soak.monotonic_growth=false")
    growth = soak.get("resource_growth", {})
    for field in SOAK_FIELDS if soak_verified else ():
        if field not in growth:
            missing.append(f"soak.resource_growth.{field}")
    native_status = receipt.get("native_mcp", {}).get("status")
    if native_status not in {"VERIFIED", "NOT_MEASURED", "FAILED", "DEFERRED"}:
        missing.append("native_mcp.status")
    elif native_status != "VERIFIED" and not isinstance(receipt.get("native_mcp", {}).get("limitation"), str):
        missing.append("native_mcp.limitation")
    if not receipt.get("workload", {}).get("patterns"):
        missing.append("workload.patterns")
    workloads = receipt.get("xlsx", {}).get("workloads", {})
    for name in MANDATORY_XLSX_WORKLOADS:
        item = workloads.get(name)
        if not isinstance(item, dict):
            missing.append(f"xlsx.workloads.{name}")
            continue
        if item.get("executed") is not True:
            missing.append(f"xlsx.workloads.{name}.executed=true")
        if item.get("status") != "VERIFIED":
            missing.append(f"xlsx.workloads.{name}.status=VERIFIED")
        if item.get("correctness") != "VERIFIED":
            missing.append(f"xlsx.workloads.{name}.correctness=VERIFIED")
    for name, item in workloads.items():
        status = item.get("status")
        if status not in MEASUREMENT_STATUSES:
            missing.append(f"xlsx.workloads.{name}.status")
        elif status == "FAILED":
            missing.append(f"xlsx.workloads.{name}.status=not_failed")
        elif status != "VERIFIED" and not isinstance(item.get("limitation"), str):
            missing.append(f"xlsx.workloads.{name}.limitation")
    candidate = workloads.get("public_workflow_context_reuse")
    if isinstance(candidate, dict):
        for field in ("capture_count", "xlsx_parse_count"):
            if not _is_nonnegative_count(candidate.get(field)):
                missing.append(f"xlsx.workloads.public_workflow_context_reuse.{field}>=0")
    else:
        missing.append("xlsx.workloads.public_workflow_context_reuse")
    timing_paths = workbook.get("timing_paths")
    if not isinstance(timing_paths, dict):
        missing.append("xlsx.timing_paths")
    else:
        for name in REQUIRED_TIMING_PATHS:
            item = timing_paths.get(name)
            if not isinstance(item, dict):
                missing.append(f"xlsx.timing_paths.{name}")
            elif not _is_number(item.get("wall_time_ms")) or float(item["wall_time_ms"]) <= 0:
                missing.append(f"xlsx.timing_paths.{name}.wall_time_ms>0")
            if isinstance(item, dict) and not _is_nonnegative_count(item.get("sample_count", 0)):
                missing.append(f"xlsx.timing_paths.{name}.sample_count>=10")
            elif isinstance(item, dict) and int(item.get("sample_count", 0)) < 10:
                missing.append(f"xlsx.timing_paths.{name}.sample_count>=10")
            if isinstance(item, dict) and (not isinstance(item.get("samples_ms"), list) or len(item["samples_ms"]) < 10):
                missing.append(f"xlsx.timing_paths.{name}.samples_ms>=10")
            if isinstance(item, dict) and (not _is_number(item.get("noise_floor_ms")) or float(item["noise_floor_ms"]) < 0):
                missing.append(f"xlsx.timing_paths.{name}.noise_floor_ms>=0")
    scenario_workloads = workbook.get("scenario_workloads", {})
    for name in REQUIRED_SCENARIO_WORKLOADS:
        item = scenario_workloads.get(name)
        if not isinstance(item, dict):
            missing.append(f"xlsx.scenario_workloads.{name}")
            continue
        if item.get("executed") is not True:
            missing.append(f"xlsx.scenario_workloads.{name}.executed=true")
        if item.get("status") != "VERIFIED":
            missing.append(f"xlsx.scenario_workloads.{name}.status=VERIFIED")
        if item.get("correctness") != "VERIFIED":
            missing.append(f"xlsx.scenario_workloads.{name}.correctness=VERIFIED")
    matrix = receipt.get("acceptance_matrix", {})
    for name in MANDATORY_XLSX_WORKLOADS:
        entry = matrix.get(name)
        if not isinstance(entry, dict):
            missing.append(f"acceptance_matrix.{name}")
            continue
        if entry.get("status") != "VERIFIED":
            missing.append(f"acceptance_matrix.{name}.status=VERIFIED")
        if entry.get("correctness") != "VERIFIED":
            missing.append(f"acceptance_matrix.{name}.correctness=VERIFIED")
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
        if first.get("harness") != second.get("harness"):
            errors.append(f"{label}.harness differs between repeats")
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
        if baseline_repeat[0].get("harness") != release_repeat[0].get("harness"):
            errors.append("baseline/release harness differs")
        if _same_revision_snapshot(baseline_repeat[0], release_repeat[0]):
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
    if _same_revision_snapshot(baseline, release):
        mismatches.append("revision")
    if baseline.get("harness") != release.get("harness"):
        mismatches.append("harness")
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

    release_evidence = release.get("evidence", {})
    unavailable_dimensions = [
        name
        for name in ("latency", "allocation", "soak")
        if release_evidence.get(name, {}).get("status") in {"FAILED", "NOT_MEASURED", "DEFERRED"}
    ]
    if baseline["acceptance"].get("gate_cold_noise_floor", False) or release["acceptance"].get("gate_cold_noise_floor", False):
        if not baseline["xlsx"].get("cold_noise_floor") or not release["xlsx"].get("cold_noise_floor"):
            unavailable_dimensions.append("cold_noise_floor")
    reader_metrics_available = all(
        field in baseline["xlsx"].get("run_owned_context", {}) and field in release["xlsx"].get("run_owned_context", {})
        for field in READER_COUNTERS
    ) and all(
        field in baseline["xlsx"].get("persistence", {}) and field in release["xlsx"].get("persistence", {})
        for field in PERSISTENCE_COUNTERS
    )

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
    latency_measured = release_evidence.get("latency", {}).get("status") == "VERIFIED"
    allocation_measured = release_evidence.get("allocation", {}).get("status") == "VERIFIED"
    p95_regression = _pct(float(release["xlsx"]["p95_ms"]), float(baseline["xlsx"]["p95_ms"])) if latency_measured else None
    allocation_regression = _pct(float(release["xlsx"]["peak_allocation_bytes"]), float(baseline["xlsx"]["peak_allocation_bytes"])) if allocation_measured else None
    rss_regression = _pct(float(release["resource"]["rss_bytes"]), float(baseline["resource"]["rss_bytes"]))
    timing_path_regressions = {}
    timing_path_comparisons = {}
    for name in REQUIRED_TIMING_PATHS:
        baseline_path = baseline["xlsx"]["timing_paths"][name]
        release_path = release["xlsx"]["timing_paths"][name]
        baseline_timing = float(baseline_path["wall_time_ms"])
        release_timing = float(release_path["wall_time_ms"])
        timing_path_regressions[name] = _pct(release_timing, baseline_timing)
        absolute_delta = release_timing - baseline_timing
        baseline_noise_floor = float(baseline_path["noise_floor_ms"])
        candidate_noise_floor = float(release_path["noise_floor_ms"])
        timing_path_comparisons[name] = {
            **_comparison_metric(baseline_timing, release_timing),
            "absolute_delta_ms": round(absolute_delta, 6),
            "baseline_noise_floor_ms": baseline_noise_floor,
            "candidate_noise_floor_ms": candidate_noise_floor,
            "noise_floor_gate": not (
                timing_path_regressions[name] > 20
                and absolute_delta > baseline_noise_floor
            ),
        }
    cold_comparison = None
    cold_regression = None
    cold_gate = True
    if baseline["xlsx"].get("cold_noise_floor") and release["xlsx"].get("cold_noise_floor"):
        baseline_cold = baseline["xlsx"]["cold_noise_floor"]
        release_cold = release["xlsx"]["cold_noise_floor"]
        baseline_p95 = float(baseline_cold["p95_ms"])
        release_p95 = float(release_cold["p95_ms"])
        cold_comparison = _comparison_metric(baseline_p95, release_p95)
        cold_regression = _pct(release_p95, baseline_p95)
        absolute_delta = release_p95 - baseline_p95
        baseline_noise_floor = float(baseline_cold["noise_floor_ms"])
        candidate_noise_floor = float(release_cold["noise_floor_ms"])
        cold_gate = not (cold_regression > 20 and absolute_delta > baseline_noise_floor)
        cold_comparison.update({
            "absolute_delta_ms": round(absolute_delta, 6),
            "baseline_noise_floor_ms": baseline_noise_floor,
            "candidate_noise_floor_ms": candidate_noise_floor,
            "noise_floor_gate": cold_gate,
        })
    absolute = {
        "xlsx": {
            "p95_ms": _comparison_metric(float(baseline["xlsx"]["p95_ms"]), float(release["xlsx"]["p95_ms"])) if latency_measured else None,
            "peak_allocation_bytes": _comparison_metric(float(baseline["xlsx"]["peak_allocation_bytes"]), float(release["xlsx"]["peak_allocation_bytes"])) if allocation_measured else None,
            "timing_paths": timing_path_comparisons,
            "cold_noise_floor": cold_comparison,
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
    threshold_accepted = (
        (p95_regression is None or p95_regression <= 20)
        and (allocation_regression is None or allocation_regression <= 15)
        and rss_regression <= 15
        and (not baseline["acceptance"].get("gate_pattern_latency", True) or all(value <= 20 for value in pattern_regressions.values()))
        and (
            not baseline["acceptance"].get("gate_timing_paths", True)
            or all(item["noise_floor_gate"] for item in timing_path_comparisons.values())
        )
        and (not baseline["acceptance"].get("gate_cold_noise_floor", False) or cold_gate)
        and non_regressive_economics
        and not reused_stage_new_calls
    )
    accepted = threshold_accepted and not unavailable_dimensions
    correctness_status = "VERIFIED" if baseline.get("evidence", {}).get("correctness", {}).get("status") == "VERIFIED" and release_evidence.get("correctness", {}).get("status") == "VERIFIED" else "FAILED"
    if unavailable_dimensions:
        regression_status = "NOT_MEASURED"
        regression_limitation = f"unavailable dimensions: {', '.join(unavailable_dimensions)}"
    else:
        regression_status = "VERIFIED" if threshold_accepted else "FAILED"
        regression_limitation = None if threshold_accepted else "one or more regression thresholds failed"
    candidate_name = "public_workflow_context_reuse"
    baseline_candidate = baseline.get("xlsx", {}).get("workloads", {}).get(candidate_name, {})
    release_candidate = release.get("xlsx", {}).get("workloads", {}).get(candidate_name, {})
    candidate_correctness = all(
        candidate.get("status") == "VERIFIED"
        and candidate.get("correctness") == "VERIFIED"
        and (
            not any(field in candidate for field in ("distinct_result_identity", "distinct_brief_results"))
            or candidate.get("distinct_result_identity") is True
            or candidate.get("distinct_brief_results") is True
        )
        and (candidate.get("source_identity_preserved", True) is True)
        and (candidate.get("reassessment_observed", True) is True)
        for candidate in (baseline_candidate, release_candidate)
    )
    correctness_status = (
        "VERIFIED"
        if correctness_status == "VERIFIED" and candidate_correctness
        else "FAILED"
    )
    accepted = accepted and correctness_status == "VERIFIED"
    candidate_fields = ("capture_count", "xlsx_parse_count")
    if baseline_candidate.get("status") == "VERIFIED" and release_candidate.get("status") == "VERIFIED":
        candidate_comparison = {
            field: _comparison_metric(float(baseline_candidate[field]), float(release_candidate[field]))
            for field in candidate_fields
        }
        candidate_improved = correctness_status == "VERIFIED" and candidate_correctness and all(
            float(release_candidate[field]) < float(baseline_candidate[field]) for field in candidate_fields
        )
        optimization_status = "VERIFIED" if candidate_improved else "NOT_MEASURED"
        optimization_limitation = None if candidate_improved else "selected candidate did not reduce every measured duplicate count"
    else:
        candidate_comparison = None
        optimization_status = "NOT_MEASURED"
        optimization_limitation = "selected candidate workload is unavailable or unverified"
    return {
        "accepted": accepted,
        "baseline": {"p95_ms": baseline["xlsx"]["p95_ms"], "peak_allocation_bytes": baseline["xlsx"]["peak_allocation_bytes"], "timing_paths": baseline["xlsx"]["timing_paths"], "economics_per_accepted_finding": baseline_economics["per_accepted_finding"]},
        "release": {"p95_ms": release["xlsx"]["p95_ms"], "peak_allocation_bytes": release["xlsx"]["peak_allocation_bytes"], "timing_paths": release["xlsx"]["timing_paths"], "economics_per_accepted_finding": release_economics["per_accepted_finding"]},
        "absolute": absolute,
        "regression": {"p95_pct": p95_regression, "peak_allocation_pct": allocation_regression, "rss_pct": rss_regression, "pattern_p95_pct": pattern_regressions, "timing_paths_pct": timing_path_regressions, "cold_p95_pct": cold_regression, "economics_per_accepted_finding_delta": economic_regressions},
        "instrumentation": {
            "available": reader_metrics_available,
            "reader": {
                field: _comparison_metric(float(baseline["xlsx"]["run_owned_context"][field]), float(release["xlsx"]["run_owned_context"][field]))
                for field in READER_COUNTERS
            } if reader_metrics_available else None,
            "persistence": {
                field: _comparison_metric(float(baseline["xlsx"]["persistence"][field]), float(release["xlsx"]["persistence"][field]))
                for field in PERSISTENCE_COUNTERS
            } if reader_metrics_available else None,
        },
        "accepted_finding_count": {"baseline": baseline_count, "release": int(release["accepted_finding_count"])},
        "workload": baseline["workload"],
        "native_mcp": {"baseline": baseline["native_mcp"]["status"], "release": release["native_mcp"]["status"]},
        "reused_stage_new_calls": reused_stage_new_calls,
        "evidence": {"release": release_evidence, "unavailable_dimensions": unavailable_dimensions},
        "outcomes": {
            "correctness": {"status": correctness_status, "limitation": None if correctness_status == "VERIFIED" else "local correctness was not verified for both receipts"},
            "regression_threshold": {
                "status": regression_status,
                "limitation": regression_limitation,
                "thresholds": baseline["acceptance"],
                "samples": {"baseline": baseline["workload"], "release": release["workload"]},
            },
            "optimization_demonstrated": {
                "status": optimization_status,
                "limitation": optimization_limitation,
                "candidate": candidate_name,
                "measurements": candidate_comparison,
            },
        },
        "gate": "PASS" if accepted else ("NOT_MEASURED" if unavailable_dimensions else "FAILED"),
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
