from copy import deepcopy

from evaluation.probes.compare_optimization_receipts import compare, compare_repeats, validate_stability
from evaluation.probes.optimization_measurement import MANDATORY_XLSX_WORKLOADS, SCENARIO_XLSX_WORKLOADS, SCHEMA_VERSION
from foresight_os.runtime.metrics import RunMetrics


PATTERNS = ("DIRECT", "ANALYZE", "CONCURRENT", "HANDOFF", "CHALLENGE_RECOMMENDATION")


def _receipt() -> dict:
    economics = {
        "model_calls": 10,
        "tool_calls_total": 4,
        "local_tool_calls": 2,
        "mcp_tool_calls": 1,
        "external_http_requests": 1,
        "input_tokens": 100,
        "output_tokens": 50,
    }
    economics["per_accepted_finding"] = {key: value / 2 for key, value in economics.items()}
    snapshot = {
        "rss_bytes": 100,
        "active_python_tasks": 1,
        "thread_count": 1,
        "child_process_count": 0,
        "owned_capability_resources": 0,
        "mcp_session_count": 0,
        "event_loop_lag_ms": 0.1,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "harness": {
            "version": "optimization-harness-v1",
            "source_tree_sha256": "harness",
            "paths": [
                "evaluation/probes/optimization_measurement.py",
                "evaluation/probes/run_optimization_probe.py",
                "evaluation/probes/compare_optimization_receipts.py",
            ],
        },
        "revision": {
            "commit": "commit",
            "repo_root": "repo",
            "package_path": "repo/src/foresight_os/__init__.py",
            "dirty": False,
            "source_tree_sha256": "source-tree-commit",
            "commit_source_tree_sha256": "source-tree-commit",
        },
        "accepted_finding_count": 2,
        "economics": economics,
        "stage_metrics": [
            {
                "stage_id": "stage-1",
                "failure_class": None,
                "model_calls": 0,
                "tool_calls_total": 0,
                "reused_stages": 0,
                "latency": {
                    "wall_time_ms_p95": 10,
                    "queue_wait_ms_p95": 1,
                    "tool_latency_ms_p95": 1,
                    "execution_time_ms_p95": 1,
                    "event_loop_lag_ms_p95": 1,
                },
            }
        ],
        "resource": {"rss_bytes": 100},
        "xlsx": {
            "p95_ms": 10,
            "peak_allocation_bytes": 100,
            "deterministic_key": "same",
            "timing_paths": {
                name: {"wall_time_ms": 10, "sample_count": 10}
                for name in (
                    "cold_workbook",
                    "same_view_repeat",
                    "repeated_investigation",
                    "analyst_validator_reuse",
                    "changed_brief",
                    "history-10",
                    "history-100",
                    "selected_sheet_stress",
                )
            },
            "workloads": {
                **{
                    name: {"executed": True, "status": "VERIFIED", "correctness": "VERIFIED", "limitation": None}
                    for name in MANDATORY_XLSX_WORKLOADS
                },
                "public_workflow_context_reuse": {
                    "executed": True,
                    "status": "VERIFIED",
                    "correctness": "VERIFIED",
                    "capture_count": 1,
                    "xlsx_parse_count": 1,
                    "distinct_brief_results": True,
                },
                **{
                    name: {
                        "executed": True,
                        "status": "VERIFIED",
                        "correctness": "VERIFIED",
                        "limitation": None,
                        "sample_count": 10,
                    }
                    for name in SCENARIO_XLSX_WORKLOADS
                    if name in {"changed_brief", "history-10", "history-100"}
                },
            },
            "scenario_workloads": {
                name: {"executed": True, "status": "VERIFIED", "correctness": "VERIFIED", "limitation": None}
                for name in SCENARIO_XLSX_WORKLOADS
            },
        },
        "workload": {"fixture_sha256": "same", "warmups": 2, "measured_runs": 10, "patterns": list(PATTERNS)},
        "acceptance": {
            "p95_regression_pct": 20,
            "peak_allocation_regression_pct": 15,
            "soak_runs": 2,
            "tool_calls_per_finding_increase": 0,
            "gate_timing_paths": True,
        },
        "maf_patterns": {
            name: {
                "cleanup_complete": True,
                "latency": {"wall_time_ms_p95": 10},
            }
            for name in PATTERNS
        },
        "soak": {
            "runs": 2,
            "snapshots": [deepcopy(snapshot), deepcopy(snapshot)],
            "resource_growth": {
                field: {"first": 0 if field != "rss_bytes" else 100, "last": 0 if field != "rss_bytes" else 100, "max": 0 if field != "rss_bytes" else 100, "monotonic_non_decreasing": True}
                for field in ("rss_bytes", "active_python_tasks", "thread_count", "child_process_count", "owned_capability_resources", "mcp_session_count")
            },
            "monotonic_growth": False,
        },
        "native_mcp": {"status": "VERIFIED", "tool_calls": 1},
        "evidence": {
            "correctness": {"status": "VERIFIED", "limitation": None},
            "latency": {"status": "VERIFIED", "limitation": None},
            "allocation": {"status": "VERIFIED", "limitation": None},
            "soak": {"status": "VERIFIED", "limitation": None},
        },
        "acceptance_matrix": {
            name: {"status": "VERIFIED", "correctness": "VERIFIED", "limitation": None}
            for name in MANDATORY_XLSX_WORKLOADS
        },
        "scenario_matrix": {
            name: {"status": "VERIFIED", "correctness": "VERIFIED", "limitation": None}
            for name in SCENARIO_XLSX_WORKLOADS
        },
    }


def test_run_metrics_keeps_tool_call_dimensions_non_additive():
    metrics = RunMetrics("test", "DIRECT", "direct")
    metrics.record_tool_call("local")
    metrics.record_tool_call("mcp")
    metrics.record_tool_call("external_http")

    assert metrics.tool_calls == 3
    assert metrics.local_tool_calls == 1
    assert metrics.mcp_tool_calls == 1
    assert metrics.external_http_requests == 1


def test_comparator_rejects_missing_or_zero_denominator_without_raising():
    baseline = _receipt()
    release = deepcopy(baseline)
    del release["economics"]
    assert not compare(baseline, release)["accepted"]

    release = deepcopy(baseline)
    release["accepted_finding_count"] = 0
    assert not compare(baseline, release)["accepted"]

    release = deepcopy(baseline)
    del release["revision"]
    assert not compare(baseline, release)["accepted"]


def test_comparator_rejects_missing_or_mismatched_harness_identity():
    baseline = _receipt()
    release = deepcopy(baseline)
    del release["harness"]

    missing = compare(baseline, release)
    assert not missing["accepted"]
    assert "harness.version" in missing["missing_required_evidence"]["release"]

    release = deepcopy(baseline)
    release["harness"]["source_tree_sha256"] = "different-harness"
    release["revision"]["commit"] = "release-commit"

    mismatched = compare(baseline, release)
    assert mismatched == {"accepted": False, "mismatched_comparison_inputs": ["harness"]}


def test_comparator_rejects_missing_evidence_statuses():
    baseline = _receipt()
    release = deepcopy(baseline)
    del release["evidence"]

    result = compare(baseline, release)

    assert result["accepted"] is False
    assert "evidence.correctness.status" in result["missing_required_evidence"]["release"]
    assert "evidence.latency.status" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_unverified_mandatory_workloads():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    assert compare(baseline, release)["accepted"]

    release["xlsx"]["workloads"]["blocking_cancellation"]["status"] = "FINAL_ONLY"
    result = compare(baseline, release)
    assert not result["accepted"]
    assert "xlsx.workloads.blocking_cancellation.status=VERIFIED" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_same_commit_with_distinct_worktree_digests():
    baseline = _receipt()
    release = deepcopy(baseline)
    baseline["revision"]["source_tree_sha256"] = "baseline-tree"
    release["revision"]["source_tree_sha256"] = "release-tree"

    result = compare(baseline, release)

    assert not result["accepted"]
    assert "revision.source_tree_sha256_matches_commit" in result["missing_required_evidence"]["baseline"]
    assert "revision.source_tree_sha256_matches_commit" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_dirty_receipts_before_comparison():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    release["revision"]["dirty"] = True

    result = compare(baseline, release)

    assert not result["accepted"]
    assert "revision.dirty=false" in result["missing_required_evidence"]["release"]


def test_comparator_requires_changed_brief_and_history_evidence():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    del release["xlsx"]["scenario_workloads"]["changed_brief"]

    result = compare(baseline, release)

    assert not result["accepted"]
    assert "xlsx.scenario_workloads.changed_brief" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_workload_pattern_and_resource_regressions():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["workload"]["fixture_sha256"] = "different"
    release["revision"]["commit"] = "release-commit"
    assert compare(baseline, release) == {"accepted": False, "mismatched_comparison_inputs": ["workload"]}

    release = deepcopy(baseline)
    release["maf_patterns"]["CONCURRENT"]["latency"]["wall_time_ms_p95"] = 13
    release["soak"]["monotonic_growth"] = True
    release["revision"]["commit"] = "release-commit"
    result = compare(baseline, release)
    assert not result["accepted"]
    assert "soak.monotonic_growth=false" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_large_warm_and_repeated_timing_path_regressions():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    release["xlsx"]["timing_paths"]["same_view_repeat"]["wall_time_ms"] = 25
    release["xlsx"]["timing_paths"]["repeated_investigation"]["wall_time_ms"] = 25

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["regression"]["timing_paths_pct"]["same_view_repeat"] == 150.0
    assert result["regression"]["timing_paths_pct"]["repeated_investigation"] == 150.0


def test_comparator_rejects_cold_regression_above_empirical_noise_floor():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release"
    baseline["acceptance"]["gate_cold_noise_floor"] = True
    release["acceptance"]["gate_cold_noise_floor"] = True
    baseline["xlsx"]["cold_noise_floor"] = {"status": "VERIFIED", "sample_count": 10, "p50_ms": 10, "p95_ms": 11, "noise_floor_ms": 1}
    release["xlsx"]["cold_noise_floor"] = {"status": "VERIFIED", "sample_count": 10, "p50_ms": 28, "p95_ms": 30, "noise_floor_ms": 2}

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["regression"]["cold_p95_pct"] == 172.727


def test_comparator_rejects_new_calls_for_reused_stage():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    release["stage_metrics"][0]["reused_stages"] = 1
    release["stage_metrics"][0]["model_calls"] = 1

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["reused_stage_new_calls"] == ["stage-1"]


def test_repeat_comparator_requires_stable_group_chat_p95_and_metadata():
    baseline = _receipt()
    baseline_repeat = deepcopy(baseline)
    release = deepcopy(baseline)
    release_repeat = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    release_repeat["revision"]["commit"] = "release-commit"
    release["maf_patterns"]["CHALLENGE_RECOMMENDATION"]["latency"]["wall_time_ms_p95"] = 12
    release_repeat["maf_patterns"]["CHALLENGE_RECOMMENDATION"]["latency"]["wall_time_ms_p95"] = 12
    assert validate_stability([baseline, baseline_repeat], [release, release_repeat])["accepted"]
    assert compare_repeats([baseline, baseline_repeat], [release, release_repeat])["accepted"]

    unstable = deepcopy(baseline_repeat)
    unstable["maf_patterns"]["CHALLENGE_RECOMMENDATION"]["latency"]["wall_time_ms_p95"] = 12
    unstable_result = validate_stability([baseline, unstable], [release, release_repeat])
    assert not unstable_result["accepted"]
    assert any("group_chat_p95" in error for error in unstable_result["errors"])

    mismatched = deepcopy(baseline_repeat)
    mismatched["workload"]["fixture_sha256"] = "different"
    mismatch_result = validate_stability([baseline, mismatched], [release, release_repeat])
    assert not mismatch_result["accepted"]
    assert any("workload" in error for error in mismatch_result["errors"])

    mismatched_revision = deepcopy(release_repeat)
    mismatched_revision["revision"]["commit"] = "other-commit"
    revision_result = validate_stability([baseline, baseline_repeat], [release, mismatched_revision])
    assert not revision_result["accepted"]
    assert any("revision" in error for error in revision_result["errors"])

    identical_revision = compare_repeats([baseline, baseline_repeat], [baseline, baseline_repeat])
    assert not identical_revision["accepted"]
    assert "baseline/release revision is identical" in identical_revision["stability"]["errors"]

    same_commit_different_paths = deepcopy(baseline)
    same_commit_different_paths["revision"]["repo_root"] = "another-repo"
    same_commit_different_paths["revision"]["package_path"] = "another-repo/src/foresight_os/__init__.py"
    same_commit_result = compare_repeats(
        [baseline, baseline_repeat],
        [same_commit_different_paths, deepcopy(same_commit_different_paths)],
    )
    assert not same_commit_result["accepted"]
    assert "baseline/release revision is identical" in same_commit_result["stability"]["errors"]


def test_comparator_reports_optimization_evidence_separately_from_regression_gate():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 2,
        "xlsx_parse_count": 2,
        "distinct_brief_results": True,
    }
    release["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 1,
        "xlsx_parse_count": 1,
        "distinct_brief_results": True,
    }

    result = compare(baseline, release)

    assert result["accepted"]
    assert result["outcomes"]["correctness"]["status"] == "VERIFIED"
    assert result["outcomes"]["regression_threshold"]["status"] == "VERIFIED"
    assert result["outcomes"]["optimization_demonstrated"]["status"] == "VERIFIED"
    assert result["outcomes"]["optimization_demonstrated"]["candidate"] == "public_workflow_context_reuse"


def test_comparator_rejects_improvement_claim_from_identical_revision():
    baseline = _receipt()
    release = deepcopy(baseline)
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 2,
        "xlsx_parse_count": 2,
        "distinct_brief_results": True,
    }
    release["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 1,
        "xlsx_parse_count": 1,
        "distinct_brief_results": True,
    }

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["mismatched_comparison_inputs"] == ["revision"]


def test_comparator_rejects_collapsed_brief_results_as_incorrect():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 2,
        "xlsx_parse_count": 2,
        "distinct_brief_results": True,
    }
    release["xlsx"]["workloads"]["public_workflow_context_reuse"] = {
        "status": "VERIFIED",
        "correctness": "VERIFIED",
        "capture_count": 1,
        "xlsx_parse_count": 1,
        "distinct_brief_results": False,
    }

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["outcomes"]["correctness"]["status"] == "FAILED"
    assert result["outcomes"]["optimization_demonstrated"]["status"] == "NOT_MEASURED"


def test_comparator_does_not_claim_optimization_when_overall_correctness_fails():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"]["capture_count"] = 2
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"]["xlsx_parse_count"] = 2
    release["evidence"]["correctness"] = {"status": "FAILED", "limitation": "analytical result mismatch"}

    result = compare(baseline, release)

    assert not result["accepted"]
    assert result["outcomes"]["correctness"]["status"] == "FAILED"
    assert result["outcomes"]["optimization_demonstrated"]["status"] == "NOT_MEASURED"


def test_comparator_rejects_malformed_candidate_counters():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    baseline["xlsx"]["workloads"]["public_workflow_context_reuse"]["capture_count"] = -1

    negative = compare(baseline, release)

    assert not negative["accepted"]
    assert "xlsx.workloads.public_workflow_context_reuse.capture_count>=0" in negative["missing_required_evidence"]["baseline"]

    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    del release["xlsx"]["workloads"]["public_workflow_context_reuse"]["xlsx_parse_count"]

    missing = compare(_receipt(), release)

    assert not missing["accepted"]
    assert "xlsx.workloads.public_workflow_context_reuse.xlsx_parse_count>=0" in missing["missing_required_evidence"]["release"]


def test_comparator_reports_unavailable_dimensions_without_treating_them_as_passes():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["revision"]["commit"] = "release-commit"
    release["evidence"] = {
        "correctness": {"status": "VERIFIED", "limitation": None},
        "latency": {"status": "NOT_MEASURED", "limitation": "timing was not run"},
        "allocation": {"status": "DEFERRED", "limitation": "allocation remains deferred"},
        "soak": {"status": "NOT_MEASURED", "limitation": "soak was not run"},
    }
    release["xlsx"]["p95_ms"] = None
    release["xlsx"]["peak_allocation_bytes"] = None
    release["soak"] = {}

    result = compare(baseline, release)

    assert result["accepted"] is False
    assert result["gate"] == "NOT_MEASURED"
    assert result["evidence"]["unavailable_dimensions"] == ["latency", "allocation", "soak"]
    assert "xlsx.p95_ms>0" not in result.get("missing_required_evidence", {}).get("release", [])
