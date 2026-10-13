import argparse
import json
from pathlib import Path


def _tool_calls(receipt: dict) -> int:
    maf_calls = sum(item.get("model_calls", 0) for item in receipt.get("maf_patterns", {}).values())
    return (
        maf_calls
        + receipt.get("native_mcp", {}).get("tool_calls", 0)
        + receipt.get("external_fixture", {}).get("tool_calls", 0)
    )


def _validate_measurement_receipt(receipt: dict) -> list[str]:
    required = ("schema_version", "accepted_finding_count", "stage_metrics", "resource", "maf_patterns", "xlsx", "native_mcp")
    missing = [key for key in required if key not in receipt]
    if receipt.get("schema_version") != 1:
        missing.append("schema_version=1")
    if receipt.get("accepted_finding_count") is None:
        missing.append("accepted_finding_count")
    if not receipt.get("stage_metrics"):
        missing.append("stage_metrics")
    if receipt.get("resource", {}).get("rss_bytes") is None or int(receipt.get("resource", {}).get("rss_bytes", 0) or 0) <= 0:
        missing.append("resource.rss_bytes>0")
    if int(receipt.get("accepted_finding_count", 0) or 0) <= 0:
        missing.append("accepted_finding_count>0")
    if any(item.get("failure_class") for item in receipt.get("stage_metrics", ())):
        missing.append("stage_metrics.successful")
    soak = receipt.get("soak", {})
    required_soak_runs = int(receipt.get("acceptance", {}).get("soak_runs", 0) or 0)
    if int(soak.get("runs", 0) or 0) < required_soak_runs:
        missing.append("soak.runs")
    if soak.get("monotonic_growth") is not False:
        missing.append("soak.monotonic_growth=false")
    if soak.get("resource_counts", {}).get("owned_after_cleanup") != 0:
        missing.append("soak.resource_counts.owned_after_cleanup=0")
    if not receipt.get("maf_patterns") or any(not item.get("cleanup_complete", False) for item in receipt["maf_patterns"].values()):
        missing.append("maf_patterns.cleanup_complete")
    if receipt.get("native_mcp", {}).get("status") != "VERIFIED":
        missing.append("native_mcp.status=VERIFIED")
    return sorted(set(missing))


def compare(baseline: dict, release: dict) -> dict:
    missing_baseline = _validate_measurement_receipt(baseline)
    missing_release = _validate_measurement_receipt(release)
    if missing_baseline or missing_release:
        return {"accepted": False, "missing_required_evidence": {"baseline": missing_baseline, "release": missing_release}}
    if baseline["workload"] != release["workload"]:
        raise ValueError("baseline and release workloads differ")
    if baseline["xlsx"]["deterministic_key"] != release["xlsx"]["deterministic_key"]:
        raise ValueError("baseline and release XLSX deterministic keys differ")
    baseline_finding_count = int(baseline["accepted_finding_count"])
    release_finding_count = int(release["accepted_finding_count"])
    baseline_tool_calls = _tool_calls(baseline) / baseline_finding_count if baseline_finding_count else 0.0
    release_tool_calls = _tool_calls(release) / release_finding_count if release_finding_count else 0.0
    p95_regression = (release["xlsx"]["p95_ms"] / baseline["xlsx"]["p95_ms"] - 1) * 100
    allocation_regression = (release["xlsx"]["peak_allocation_bytes"] / baseline["xlsx"]["peak_allocation_bytes"] - 1) * 100
    rss_regression = (release["resource"]["rss_bytes"] / baseline["resource"]["rss_bytes"] - 1) * 100
    result = {
        "baseline": {"p95_ms": baseline["xlsx"]["p95_ms"], "peak_allocation_bytes": baseline["xlsx"]["peak_allocation_bytes"], "tool_calls_per_finding": baseline_tool_calls},
        "release": {"p95_ms": release["xlsx"]["p95_ms"], "peak_allocation_bytes": release["xlsx"]["peak_allocation_bytes"], "tool_calls_per_finding": release_tool_calls},
        "regression": {
            "p95_pct": round(p95_regression, 3),
            "peak_allocation_pct": round(allocation_regression, 3),
            "rss_pct": round(rss_regression, 3),
            "tool_calls_per_finding": round(release_tool_calls - baseline_tool_calls, 3),
        },
        "accepted": p95_regression <= 20 and allocation_regression <= 15 and rss_regression <= 15 and release_tool_calls <= baseline_tool_calls and baseline.get("native_mcp", {}).get("status") == "VERIFIED" and release.get("native_mcp", {}).get("status") == "VERIFIED",
        "accepted_finding_count": {"baseline": baseline_finding_count, "release": release_finding_count},
        "workload": baseline["workload"],
        "native_mcp": {"baseline": baseline.get("native_mcp", {}).get("status"), "release": release.get("native_mcp", {}).get("status")},
    }
    return result


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
