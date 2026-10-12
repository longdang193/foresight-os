import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from candidate_harness import run_candidate
from foresight_os.controller.policy import probe_optional_patterns, select_recipe
from foresight_os.persistence.recovery import continue_investigation
from foresight_os.wayfinding import create_work_brief


FROZEN_THRESHOLDS = {
    "supported_claim_precision": 0.90,
    "finding_coverage": 0.80,
    "contradiction_precision": 0.80,
    "contradiction_recall": 0.80,
    "traceability": 1.00,
}


def _score_candidate(candidate_result: dict, reference: dict) -> dict:
    state = candidate_result["state"]
    records = [*state.claims, *state.recommendations] if state else []
    reference_statements = {item["statement"] for item in reference["reference_findings"]}
    accepted = [item for item in records if item.assessment.value == "SUPPORTED"]
    matching = [item for item in accepted if item.statement in reference_statements]
    supported_claim_precision = len(matching) / len(accepted) if accepted else 0.0
    finding_coverage = len(matching) / len(reference_statements) if reference_statements else 1.0
    traceable = [item for item in accepted if item.evidence_ids and state.evidence]
    traceability = len(traceable) / len(accepted) if accepted else 0.0
    contradiction_found = bool(
        any("capacity" in item.statement.lower() for item in state.claims)
        and any("conditional" in item.statement.lower() for item in state.recommendations)
    ) if state else False
    metrics = dict(candidate_result["metrics"])
    return {
        "supported_claim_precision": round(supported_claim_precision, 4),
        "finding_coverage": round(finding_coverage, 4),
        "contradiction_precision": 1.0 if contradiction_found else 0.0,
        "contradiction_recall": 1.0 if contradiction_found and reference["contradictions"] else 0.0,
        "traceability": round(traceability, 4),
        "recovery_success": bool(candidate_result["outcome"].accepted and continue_investigation(candidate_result["outcome"].report_path.parent.parent).revision == 1),
        "human_correction_effort": 1 if candidate_result["outcome"].accepted else 0,
        "run_metrics": metrics,
        "admitted": all(
            [
                supported_claim_precision >= FROZEN_THRESHOLDS["supported_claim_precision"],
                finding_coverage >= FROZEN_THRESHOLDS["finding_coverage"],
                contradiction_found,
                traceability >= FROZEN_THRESHOLDS["traceability"],
            ]
        ),
    }


def compare_case(case_dir: Path, names: list[str]) -> dict:
    reference = json.loads((case_dir / "reference.json").read_text(encoding="utf-8"))
    brief = create_work_brief("Should the strategy team increase investment in the Northern Europe service network for 2030?")
    recipe = select_recipe(brief)
    comparison = {}
    for name in names:
        result = run_candidate(case_dir, name)
        comparison[name] = _score_candidate(result, reference)
    return {
        "case_id": case_dir.name,
        "thresholds": FROZEN_THRESHOLDS,
        "comparison": comparison,
        "controller_recipe": recipe.name.value,
        "controller_pattern": recipe.pattern,
        "admitted_pattern": next((name for name, metrics in comparison.items() if metrics["admitted"]), None),
        "limitations": ["Provider-backed calls are environment-gated; deterministic domain execution remains the local comparison baseline."],
    }


def probe_case(case_dir: Path) -> dict:
    report = compare_case(case_dir, ["semantic", "sequential"])
    report["candidate_probes"] = [asdict(probe) for probe in probe_optional_patterns()]
    return report


def render_markdown(report: dict) -> str:
    lines = [f"# Evaluation Report: {report['case_id']}", "", "## Thresholds", json.dumps(report["thresholds"], sort_keys=True), "", "## Comparison"]
    for name, metrics in report.get("comparison", {}).items():
        lines.append(f"- `{name}`: {json.dumps(metrics, sort_keys=True)}")
    lines.extend([
        "",
        f"- Controller recipe: `{report['controller_recipe']}`",
        f"- Admitted pattern: `{report['admitted_pattern']}`",
    ])
    lines.append("\n## Limitations")
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--compare", default="ordinary,semantic,sequential,controller")
    parser.add_argument("--probe-patterns", default="")
    parser.add_argument("--evaluation-only", action="store_true")
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args(argv)
    report = probe_case(args.case) if args.probe_patterns else compare_case(args.case, args.compare.split(","))
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
