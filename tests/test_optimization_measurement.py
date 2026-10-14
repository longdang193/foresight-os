from copy import deepcopy

from evaluation.probes.compare_optimization_receipts import compare, compare_repeats, validate_stability
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
        "schema_version": 2,
        "revision": {
            "commit": "commit",
            "repo_root": "repo",
            "package_path": "repo/src/foresight_os/__init__.py",
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
        "xlsx": {"p95_ms": 10, "peak_allocation_bytes": 100, "deterministic_key": "same"},
        "workload": {"fixture_sha256": "same", "warmups": 2, "measured_runs": 10, "patterns": list(PATTERNS)},
        "acceptance": {"p95_regression_pct": 20, "peak_allocation_regression_pct": 15, "soak_runs": 2, "tool_calls_per_finding_increase": 0},
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


def test_comparator_rejects_workload_pattern_and_resource_regressions():
    baseline = _receipt()
    release = deepcopy(baseline)
    release["workload"]["fixture_sha256"] = "different"
    assert compare(baseline, release) == {"accepted": False, "mismatched_comparison_inputs": ["workload"]}

    release = deepcopy(baseline)
    release["maf_patterns"]["CONCURRENT"]["latency"]["wall_time_ms_p95"] = 13
    release["soak"]["monotonic_growth"] = True
    result = compare(baseline, release)
    assert not result["accepted"]
    assert "soak.monotonic_growth=false" in result["missing_required_evidence"]["release"]


def test_comparator_rejects_new_calls_for_reused_stage():
    baseline = _receipt()
    release = deepcopy(baseline)
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
