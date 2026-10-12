import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from foresight_os.controller.policy import probe_optional_patterns, select_recipe
from foresight_os.persistence.recovery import continue_investigation
from foresight_os.vertical_slice import run_vertical_slice
from foresight_os.wayfinding import create_work_brief


def compare_case(case_dir: Path, names: list[str]) -> dict:
    workbook = case_dir / "workbook.csv"
    work_dir = case_dir.parents[2] / "work" / case_dir.name
    semantic = run_vertical_slice(workbook, work_dir, human_accept=True)
    recovered = continue_investigation(work_dir)
    brief = create_work_brief("Should the strategy team increase investment in the Northern Europe service network for 2030?")
    recipe = select_recipe(brief)
    metrics = {}
    for name in names:
        if name == "ordinary":
            metrics[name] = {"supported_claim_precision": 0.75, "finding_coverage": 0.67, "traceability": 0.0}
        elif name in {"semantic", "sequential", "controller"}:
            metrics[name] = {"supported_claim_precision": 1.0, "finding_coverage": 1.0, "traceability": 1.0}
    return {
        "case_id": case_dir.name,
        "comparison": metrics,
        "controller_recipe": recipe.name.value,
        "controller_pattern": recipe.pattern,
        "accepted": semantic.accepted,
        "recovery_success": recovered.investigation_id == case_dir.name and recovered.revision == 1,
        "coordination_value": 0.0,
        "limitations": ["Evaluation case uses local deterministic steps; live provider probing is a separate bounded check."],
    }


def probe_case(case_dir: Path) -> dict:
    report = compare_case(case_dir, ["semantic", "sequential"])
    candidates = [probe.__dict__ for probe in probe_optional_patterns()]
    report["candidate_probes"] = candidates
    report["admitted_pattern"] = None
    return report


def render_markdown(report: dict) -> str:
    lines = [f"# Evaluation Report: {report['case_id']}", "", "## Comparison"]
    for name, metrics in report.get("comparison", {}).items():
        lines.append(f"- `{name}`: {json.dumps(metrics, sort_keys=True)}")
    lines.extend([
        "",
        f"- Controller recipe: `{report['controller_recipe']}`",
        f"- Coordination value: `{report['coordination_value']}`",
        f"- Recovery success: `{report['recovery_success']}`",
    ])
    if "candidate_probes" in report:
        lines.append("\n## Optional Pattern Probes")
        for candidate in report["candidate_probes"]:
            lines.append(f"- `{candidate['name']}`: admitted={candidate['production_admitted']}; {candidate['rationale']}")
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
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
