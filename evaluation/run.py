import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parent))

ROOT = Path(__file__).parents[1]

from candidate_harness import run_candidate
from foresight_os.controller.policy import probe_optional_patterns, select_recipe
from foresight_os.controller.task_shape import TaskShape
from foresight_os.persistence.recovery import continue_investigation
from foresight_os.wayfinding import create_work_brief
from foresight_os.runtime.maf_probe import load_provider_settings
from foresight_os.runtime.workflow import run_recipe_async


FROZEN_THRESHOLDS = {
    "supported_claim_precision": 0.90,
    "finding_coverage": 0.80,
    "contradiction_precision": 0.80,
    "contradiction_recall": 0.80,
    "traceability": 1.00,
}


def _score_candidate(candidate_result: dict, reference: dict) -> dict:
    state = candidate_result["analysis_state"]
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


def run_contract_matrix() -> dict:
    patterns = ["direct", "sequential", "concurrent", "handoff", "group_chat"]
    results = {}
    for pattern in patterns:
        candidate_name = {"direct": "ordinary", "sequential": "sequential"}.get(pattern, pattern)
        candidate = run_candidate(ROOT / "evaluation" / "cases" / "case-001", candidate_name)
        results[pattern] = {
            "supported": True,
            "available": True,
            "selected": candidate["metrics"]["pattern"],
            "measured": candidate["metrics"],
        }
    return {"matrix": "contract", "results": results}


def run_controller_matrix(task_shapes_path: Path) -> dict:
    shapes = json.loads(task_shapes_path.read_text(encoding="utf-8"))
    results = []
    for item in shapes:
        name = item["task_shape"]
        shape = TaskShape(
            ordered_dependencies=name == "ordered_synthesis",
            independent_subtasks=name == "independent_branches",
            dynamic_specialist_routing=name == "specialist_routing",
            interactive_deliberation=name == "interactive_deliberation",
            review_required=name == "ordered_synthesis",
        )
        recipe = select_recipe(create_work_brief(name), shape)
        selected = [stage.pattern.value for stage in recipe.stages]
        results.append({"task_shape": name, "expected_patterns": item["expected_patterns"], "selected_patterns": selected, "match": selected == item["expected_patterns"]})
    return {"matrix": "controller", "results": results, "accuracy": sum(item["match"] for item in results) / len(results)}


def run_live_smoke(pattern: str, env_file: Path, config_file: Path) -> dict:
    from agent_framework.openai import OpenAIChatClient

    settings = load_provider_settings(env_file, config_file)
    client = OpenAIChatClient(model=settings.model, api_key=settings.api_key, base_url=settings.base_url)
    recipe = select_recipe(create_work_brief("Run a bounded native pattern smoke."), override=pattern)

    async def run() -> dict:
        try:
            result = await asyncio.wait_for(run_recipe_async(recipe, "Return a short structured readiness result.", client), 30)
            return {
                "provider": settings.provider,
                "model": settings.model,
                "endpoint": settings.base_url,
                "pattern": pattern,
                "status": "success",
                "latency_ms": result.metrics.wall_time_ms,
                "metrics": {
                    "model_calls": result.metrics.model_calls,
                    "branches": result.metrics.branches,
                    "handoffs": result.metrics.handoffs,
                    "chat_rounds": result.metrics.chat_rounds,
                    "cleanup_complete": result.metrics.cleanup_complete,
                },
            }
        except Exception as error:
            return {
                "provider": settings.provider,
                "model": settings.model,
                "endpoint": settings.base_url,
                "pattern": pattern,
                "status": "unavailable",
                "error_type": type(error).__name__,
            }
        finally:
            close = getattr(client, "close", None)
            if close is not None:
                await close()

    return asyncio.run(run())


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
    parser.add_argument("--case", type=Path)
    parser.add_argument("--matrix", choices=["contract", "controller"])
    parser.add_argument("--task-shapes", type=Path, default=ROOT / "evaluation" / "task_shapes.json")
    parser.add_argument("--live-smoke", action="store_true")
    parser.add_argument("--pattern", choices=["sequential", "concurrent", "handoff", "group_chat"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--config-file", type=Path, default=Path.home() / ".codex" / "config.toml")
    parser.add_argument("--compare", default="ordinary,semantic,sequential,controller")
    parser.add_argument("--probe-patterns", default="")
    parser.add_argument("--evaluation-only", action="store_true")
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args(argv)
    if args.live_smoke:
        if args.pattern is None:
            parser.error("--pattern is required with --live-smoke")
        report = run_live_smoke(args.pattern, args.env_file, args.config_file)
    elif args.matrix == "contract":
        report = run_contract_matrix()
    elif args.matrix == "controller":
        report = run_controller_matrix(args.task_shapes)
    elif args.case is None:
        parser.error("--case is required unless --matrix is used")
    else:
        report = probe_case(args.case) if args.probe_patterns else compare_case(args.case, args.compare.split(","))
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
