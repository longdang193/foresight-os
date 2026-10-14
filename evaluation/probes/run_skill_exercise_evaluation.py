"""Evaluate bundled analytical skills against the tracked exercise contract."""

import argparse
import asyncio
import json
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.controller.skills import SkillRegistry
from foresight_os.runtime.maf_probe import load_provider_settings
from foresight_os.runtime.participants import ParticipantConfig
from foresight_os.runtime.workflow import run_recipe_async


ROOT = Path(__file__).parents[2]
METRIC_CLASSES = ("deterministic_reference", "provider_runtime", "human_rubric")
ALLOWED_STATUSES = {"VERIFIED", "BLOCKED_INPUT", "BLOCKED_EXTERNAL", "FAILED", "NOT_RUN", "not_measured"}
FIXTURE_KEYS = {
    "skill_id",
    "version",
    "positive_cases",
    "near_miss",
    "expected_observable_properties",
}


def _sanitize_error(error: BaseException) -> str:
    return f"{type(error).__name__}: message redacted"


def _provider_error_status(error: BaseException) -> str:
    if isinstance(error, (FileNotFoundError, ImportError, ConnectionError, TimeoutError, OSError)):
        return "BLOCKED_EXTERNAL"
    module = type(error).__module__.lower()
    name = type(error).__name__.lower()
    if module.startswith(("httpx", "openai", "agent_framework")) and any(
        marker in name for marker in ("connection", "connect", "timeout", "transport", "api")
    ):
        return "BLOCKED_EXTERNAL"
    return "FAILED"


def _combine_status(base_status: str, provider_status: str) -> str:
    if "FAILED" in {base_status, provider_status}:
        return "FAILED"
    if base_status == "BLOCKED_INPUT":
        return base_status
    if provider_status in {"BLOCKED_EXTERNAL", "BLOCKED_INPUT"}:
        return provider_status
    return base_status


def _load_skill_fixtures(registry: SkillRegistry, fixture_root: Path) -> dict[str, dict[str, Any]]:
    fixtures: dict[str, dict[str, Any]] = {}
    for path in sorted(fixture_root.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        if set(fixture) != FIXTURE_KEYS:
            raise ValueError(f"invalid fixture keys: {path}")
        skill_id = fixture.get("skill_id")
        if skill_id != path.stem or skill_id in fixtures:
            raise ValueError(f"invalid or duplicate fixture id: {path}")
        manifest = registry.manifest(skill_id)
        if fixture.get("version") != manifest.version:
            raise ValueError(f"fixture version mismatch: {skill_id}")
        if len(fixture.get("positive_cases", ())) != 3 or not fixture.get("near_miss", {}).get("prompt", "").strip():
            raise ValueError(f"fixture routing cases are incomplete: {skill_id}")
        properties = fixture.get("expected_observable_properties", {})
        if set(properties) != {"required_output_fields", "routing_boundary"}:
            raise ValueError(f"fixture observable properties are incomplete: {skill_id}")
        fixtures[skill_id] = fixture
    expected_ids = {item.skill_id for item in (registry.manifest(skill_id) for skill_id in registry._manifests)}
    if set(fixtures) != expected_ids:
        raise ValueError(f"fixture ids do not match manifest: {sorted(expected_ids ^ set(fixtures))}")
    return fixtures


def _validate_case(case_dir: Path, reference: dict[str, Any]) -> dict[str, Any]:
    required_locator_keys = {"file_version", "sheet", "range", "units", "transformation", "calculation"}
    checks = [
        (reference.get("case_id") == case_dir.name, "case_id"),
        ((case_dir / "decision.md").is_file(), "decision"),
        ((case_dir / "workbook.csv").is_file(), "workbook"),
        (bool(reference.get("source_version")), "source_version"),
    ]
    for finding in reference.get("reference_findings", ()):
        locator = finding.get("source_locator", {})
        checks.append((set(locator) == required_locator_keys and all(locator.values()), f"locator:{finding.get('id', '')}"))
    passed = sum(1 for result, _ in checks if result)
    failed = [name for result, name in checks if not result]
    return {
        "case_id": case_dir.name,
        "status": "VERIFIED" if not failed else "BLOCKED_INPUT",
        "checks_passed": passed,
        "checks_total": len(checks),
        "failed_checks": failed,
        "reference_findings": len(reference.get("reference_findings", ())),
        "contradictions": len(reference.get("contradictions", ())),
    }


def _skill_records(registry: SkillRegistry, fixtures: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for skill_id in fixtures:
        skill = registry.resolve((skill_id,))[0]
        instructions = registry.instructions((skill,))
        records.append({
            "skill_id": skill.skill_id,
            "version": skill.version,
            "content_sha256": skill.content_sha256,
            "fixture_version": fixtures[skill_id]["version"],
            "prompt_size": {
                "word_count": len(instructions.split()),
                "utf8_bytes": len(instructions.encode("utf-8")),
            },
        })
    return records


def _base_report(registry: SkillRegistry, fixtures: dict[str, dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    reference_checks = sum(item["checks_total"] for item in cases)
    reference_passed = sum(item["checks_passed"] for item in cases)
    deterministic_status = "VERIFIED" if reference_passed == reference_checks else "BLOCKED_INPUT"
    return {
        "schema_version": 1,
        "status": deterministic_status,
        "skills": _skill_records(registry, fixtures),
        "cases": cases,
        "metric_classes": {
            "deterministic_reference": {
                "status": deterministic_status,
                "checks_passed": reference_passed,
                "checks_total": reference_checks,
                "reference_findings": sum(item["reference_findings"] for item in cases),
                "contradictions": sum(item["contradictions"] for item in cases),
            },
            "provider_runtime": {
                "status": "NOT_RUN",
                "runs": [],
                "human_correction": None,
            },
            "human_rubric": {
                "status": "not_measured",
                "measured": False,
                "correction_effort": None,
            },
        },
        "limitations": [
            "Deterministic scores validate package and reference completeness, not model quality.",
            "Provider runtime and human/rubric metrics are independent evidence classes.",
            "The separate Group Chat / CHALLENGE_RECOMMENDATION p95 follow-up is outside this evaluation.",
        ],
    }


def validate_report_contract(report: dict[str, Any]) -> None:
    if report.get("status") not in ALLOWED_STATUSES:
        raise ValueError("evaluation report has invalid top-level status")
    metric_classes = report.get("metric_classes", {})
    if set(metric_classes) != set(METRIC_CLASSES):
        raise ValueError("evaluation report must separate all metric classes")
    for name, record in metric_classes.items():
        if record.get("status") not in ALLOWED_STATUSES:
            raise ValueError(f"invalid status for {name}")
    if metric_classes["human_rubric"].get("status") == "not_measured":
        if metric_classes["human_rubric"].get("measured"):
            raise ValueError("human metrics cannot be measured while status is not_measured")
        if metric_classes["human_rubric"].get("correction_effort") is not None:
            raise ValueError("human correction effort cannot be inferred")


def run_structural(
    exercise_root: Path,
    fixture_root: Path,
    output_root: Path,
    extended_exercise_root: Path | None = None,
    registry: SkillRegistry | None = None,
) -> dict[str, Any]:
    if registry is None:
        registry = SkillRegistry()
    fixtures = _load_skill_fixtures(registry, fixture_root)
    cases = []
    for case_dir in sorted(exercise_root.glob("case-*")):
        reference_path = case_dir / "reference.json"
        if not reference_path.is_file():
            continue
        cases.append(_validate_case(case_dir, json.loads(reference_path.read_text(encoding="utf-8"))))
    report = _base_report(registry, fixtures, cases)
    report["extended_exercise"] = {
        "status": "VERIFIED" if extended_exercise_root and extended_exercise_root.exists() else "BLOCKED_INPUT",
        "root": str(extended_exercise_root or ROOT / "data" / "exercise"),
        "reason": "optional extended workbook pack is available" if extended_exercise_root and extended_exercise_root.exists() else "optional extended workbook pack is absent",
    }
    validate_report_contract(report)
    _write_report(report, output_root)
    return report


async def _run_provider_cases(
    cases: list[Path],
    skill_ids: tuple[str, ...],
    registry: SkillRegistry,
    client: Any,
) -> list[dict[str, Any]]:
    reports = []
    base_recipe = make_recipe(RecipeName.DIRECT)
    participant = ParticipantConfig(
        "skill-exercise",
        "analyst",
        "evaluate the tracked strategic exercise with explicit evidence boundaries",
        skill_ids=skill_ids,
    )
    stage = replace(base_recipe.stages[0], participants=(participant,), skill_ids=skill_ids)
    recipe = replace(base_recipe, stages=(stage,))
    for case_dir in cases:
        prompt = (case_dir / "decision.md").read_text(encoding="utf-8")
        prompt += "\n\nWorkbook evidence:\n" + (case_dir / "workbook.csv").read_text(encoding="utf-8")
        started = time.perf_counter()
        try:
            result = await run_recipe_async(
                recipe,
                prompt,
                client,
                run_id=f"skill-exercise-{case_dir.name}",
                run_context={"skill_registry": registry},
            )
            reports.append({
                "case_id": case_dir.name,
                "status": "VERIFIED",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "metrics": asdict(result.metrics),
            })
        except Exception as error:
            status = _provider_error_status(error)
            reports.append({
                "case_id": case_dir.name,
                "status": status,
                "error_type": type(error).__name__,
                "error": _sanitize_error(error),
            })
    return reports


def run_provider(
    exercise_root: Path,
    fixture_root: Path,
    output_root: Path,
    env_file: Path,
    config_file: Path,
    extended_exercise_root: Path | None = None,
) -> dict[str, Any]:
    registry = SkillRegistry()
    report = run_structural(exercise_root, fixture_root, output_root, extended_exercise_root, registry)
    fixtures = _load_skill_fixtures(registry, fixture_root)
    case_dirs = [path for path in sorted(exercise_root.glob("case-*")) if (path / "reference.json").is_file()]
    try:
        settings = load_provider_settings(env_file, config_file)
        from agent_framework.openai import OpenAIChatClient
    except Exception as error:
        status = _provider_error_status(error) if not isinstance(error, ValueError) else "BLOCKED_EXTERNAL"
        report["status"] = _combine_status(report["status"], status)
        report["metric_classes"]["provider_runtime"] = {
            "status": status,
            "runs": [],
            "boundary": type(error).__name__,
            "message": _sanitize_error(error),
            "human_correction": None,
        }
        report["provider"] = {"status": status}
        validate_report_contract(report)
        _write_report(report, output_root)
        return report

    client = OpenAIChatClient(model=settings.model, api_key=settings.api_key, base_url=settings.base_url)
    try:
        runs = asyncio.run(_run_provider_cases(case_dirs, tuple(fixtures), registry, client))
    finally:
        close = getattr(client, "close", None)
        if close is not None:
            asyncio.run(close())
    if any(item["status"] == "FAILED" for item in runs):
        provider_status = "FAILED"
    elif any(item["status"] == "BLOCKED_EXTERNAL" for item in runs):
        provider_status = "BLOCKED_EXTERNAL"
    else:
        provider_status = "VERIFIED"
    report["status"] = _combine_status(report["status"], provider_status)
    report["provider"] = {"provider": settings.provider, "model": settings.model, "base_url": settings.base_url}
    report["metric_classes"]["provider_runtime"] = {
        "status": provider_status,
        "runs": runs,
        "human_correction": None,
    }
    validate_report_contract(report)
    _write_report(report, output_root)
    return report


def _write_report(report: dict[str, Any], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Skill Exercise Evaluation",
        "",
        f"- Status: `{report['status']}`",
        f"- Cases: `{len(report.get('cases', []))}`",
        "",
        "## Metric Classes",
    ]
    for name in METRIC_CLASSES:
        lines.append(f"- `{name}`: `{report['metric_classes'][name]['status']}`")
    lines.extend(["", "## Limitations"])
    lines.extend(f"- {item}" for item in report.get("limitations", ()))
    (output_root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("structural", "provider"), required=True)
    parser.add_argument("--exercise-root", type=Path, default=ROOT / "evaluation" / "cases")
    parser.add_argument("--skill-fixture-root", type=Path, default=ROOT / "evaluation" / "skills")
    parser.add_argument("--extended-exercise-root", type=Path, default=ROOT / "data" / "exercise")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--config-file", type=Path, default=Path.home() / ".codex" / "config.toml")
    args = parser.parse_args(argv)
    if args.mode == "structural":
        report = run_structural(args.exercise_root, args.skill_fixture_root, args.output_root, args.extended_exercise_root)
    else:
        report = run_provider(
            args.exercise_root,
            args.skill_fixture_root,
            args.output_root,
            args.env_file,
            args.config_file,
            args.extended_exercise_root,
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report.get("status") == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
