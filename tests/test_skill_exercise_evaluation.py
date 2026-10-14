import asyncio
import json
from pathlib import Path

from foresight_os.controller.skills import SkillRegistry
from evaluation.probes.run_skill_exercise_evaluation import run_structural


ROOT = Path(__file__).parents[1]
CASE = ROOT / "evaluation" / "cases" / "case-001"
FIXTURE_ROOT = ROOT / "evaluation" / "skills"
EXPECTED_SKILL_FIXTURE_KEYS = {
    "skill_id",
    "version",
    "positive_cases",
    "near_miss",
    "expected_observable_properties",
}
EXPECTED_METRIC_CLASSES = {"deterministic_reference", "provider_runtime", "human_rubric"}
ALLOWED_STATUSES = {"VERIFIED", "BLOCKED_INPUT", "BLOCKED_EXTERNAL", "FAILED", "NOT_RUN", "not_measured"}


def test_each_skill_fixture_has_three_positive_cases_and_one_near_miss():
    registry = SkillRegistry()
    manifest = json.loads((ROOT / "src" / "foresight_os" / "skills" / "manifest.json").read_text(encoding="utf-8"))
    manifest_ids = {item["id"] for item in manifest["skills"]}
    fixtures = sorted(FIXTURE_ROOT.glob("*.json"))

    assert {path.stem for path in fixtures} == manifest_ids
    seen = set()
    for path in fixtures:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        assert set(fixture) == EXPECTED_SKILL_FIXTURE_KEYS
        assert fixture["skill_id"] == path.stem
        assert fixture["skill_id"] not in seen
        seen.add(fixture["skill_id"])
        assert fixture["version"] == registry.manifest(fixture["skill_id"]).version
        assert len(fixture["positive_cases"]) == 3
        assert all(isinstance(item, dict) and item["prompt"].strip() for item in fixture["positive_cases"])
        assert isinstance(fixture["near_miss"], dict)
        assert fixture["near_miss"]["prompt"].strip()
        properties = fixture["expected_observable_properties"]
        assert set(properties) == {"required_output_fields", "routing_boundary"}
        assert all(isinstance(item, str) and item for item in properties["required_output_fields"])
        assert properties["routing_boundary"].strip()


def test_evaluation_metric_classes_and_statuses_are_explicit():
    assert EXPECTED_METRIC_CLASSES == {
        "deterministic_reference",
        "provider_runtime",
        "human_rubric",
    }
    assert "BLOCKED_EXTERNAL" in ALLOWED_STATUSES
    assert "BLOCKED_INPUT" in ALLOWED_STATUSES
    assert "not_measured" in ALLOWED_STATUSES


def test_structural_report_preserves_metric_boundaries_and_optional_input_status(tmp_path):
    report = run_structural(ROOT / "evaluation" / "cases", FIXTURE_ROOT, tmp_path)

    assert report["status"] == "VERIFIED"
    assert len(report["cases"]) == 5
    assert report["extended_exercise"]["status"] == "BLOCKED_INPUT"
    assert report["metric_classes"]["deterministic_reference"]["status"] == "VERIFIED"
    assert report["metric_classes"]["provider_runtime"]["status"] == "NOT_RUN"
    assert report["metric_classes"]["human_rubric"]["status"] == "not_measured"
    assert report["metric_classes"]["human_rubric"]["correction_effort"] is None


def test_provider_case_classification_keeps_code_failures_distinct_from_transport_blocks(monkeypatch):
    import evaluation.probes.run_skill_exercise_evaluation as evaluation_probe

    async def fail_with_connection(*args, **kwargs):
        raise ConnectionError("provider unavailable")

    async def fail_with_code_defect(*args, **kwargs):
        raise AssertionError("injected evaluator defect")

    registry = SkillRegistry()
    monkeypatch.setattr(evaluation_probe, "run_recipe_async", fail_with_connection)
    blocked = asyncio.run(evaluation_probe._run_provider_cases([CASE], ("source-appraisal",), registry, object()))
    monkeypatch.setattr(evaluation_probe, "run_recipe_async", fail_with_code_defect)
    failed = asyncio.run(evaluation_probe._run_provider_cases([CASE], ("source-appraisal",), registry, object()))

    assert blocked[0]["status"] == "BLOCKED_EXTERNAL"
    assert failed[0]["status"] == "FAILED"


def test_sanitize_error_redacts_bearer_and_json_credentials():
    import evaluation.probes.run_skill_exercise_evaluation as evaluation_probe

    error = RuntimeError('Authorization: Bearer abc.def; {"apiKey":"secret-value"}')

    sanitized = evaluation_probe._sanitize_error(error)

    assert "abc.def" not in sanitized
    assert "secret-value" not in sanitized
    assert sanitized == "RuntimeError: message redacted"


def test_evaluator_cli_fails_for_failed_report(monkeypatch, tmp_path):
    import evaluation.probes.run_skill_exercise_evaluation as evaluation_probe

    monkeypatch.setattr(evaluation_probe, "run_provider", lambda *args, **kwargs: {"status": "FAILED"})

    assert evaluation_probe.main(["--mode", "provider", "--output-root", str(tmp_path)]) == 1

    monkeypatch.setattr(evaluation_probe, "run_provider", lambda *args, **kwargs: {"status": "BLOCKED_EXTERNAL"})
    assert evaluation_probe.main(["--mode", "provider", "--output-root", str(tmp_path)]) == 0
