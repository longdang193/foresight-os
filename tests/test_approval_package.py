import json
from dataclasses import replace
from pathlib import Path

import yaml

from foresight_os.artifacts.approval import build_approval_package, render_approval_markdown
from foresight_os.controller.proposal import apply_execution_overrides, build_execution_recipe
from foresight_os.domain.approval import AdaptationEnvelope
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.analysis_store import StageReceipt
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.wayfinding import create_work_brief
from foresight_os.cli import main
from foresight_os.domain.validation import validate_work_brief


def test_primary_and_detailed_package_rendering_is_stable(tmp_path):
    brief = create_work_brief("Question", investigation_id="package")
    recipe = build_execution_recipe(brief).recipe
    package = build_approval_package(brief, recipe, AdaptationEnvelope(max_retries=1))
    assert package.fingerprint in render_approval_markdown(package)
    assert "Rationale:" in render_approval_markdown(package, detailed=True)
    store = AnalysisStore(tmp_path / "package")
    store.save_brief(brief)
    store.save_recipe(recipe)
    assert json.loads(json.dumps(package.to_dict()))["fingerprint"] == package.fingerprint


def test_exact_human_edited_recipe_persists(tmp_path):
    brief = create_work_brief("Question", investigation_id="edited")
    recipe = build_execution_recipe(brief).recipe
    edited = apply_execution_overrides(recipe, {"max_agent_steps": 9}).recipe
    store = AnalysisStore(tmp_path / "edited")
    store.save_brief(brief)
    store.save_recipe(edited)
    assert store.load_recipe() == edited


def test_displayed_fingerprint_race_rejects_mutated_recipe(tmp_path, capsys):
    work_dir = tmp_path / "race"
    assert main(["propose", "--work-dir", str(work_dir), "--question", "Question", "--investigation-id", "race", "--format", "json"]) == 0
    package = json.loads(capsys.readouterr().out)
    store = AnalysisStore(work_dir)
    recipe = store.load_recipe()
    store.save_recipe(replace(recipe, max_agent_steps=recipe.max_agent_steps + 1))
    assert main(["approve", "--work-dir", str(work_dir), "--fingerprint", package["fingerprint"]]) == 2
    assert store.load_execution_approval() is None


def test_propose_rerenders_persisted_recipe_without_dropping_revision(tmp_path, capsys):
    work_dir = tmp_path / "revised-proposal"
    assert main(["propose", "--work-dir", str(work_dir), "--question", "Question", "--investigation-id", "revised", "--format", "json"]) == 0
    capsys.readouterr()
    store = AnalysisStore(work_dir)
    revised = apply_execution_overrides(store.load_recipe(), {"max_total_agent_calls": 4}).recipe
    store.save_recipe(revised)

    assert main(["propose", "--work-dir", str(work_dir), "--format", "json"]) == 0
    package = json.loads(capsys.readouterr().out)

    assert package["projection"]["recipe"]["max_total_agent_calls"] == 4
    assert store.load_recipe().max_total_agent_calls == 4


def test_propose_does_not_call_a_receipt_matching_without_current_fingerprints(tmp_path, capsys):
    work_dir = tmp_path / "reuse-proposal"
    assert main(["propose", "--work-dir", str(work_dir), "--question", "Question", "--investigation-id", "reuse", "--format", "json"]) == 0
    capsys.readouterr()
    store = AnalysisStore(work_dir)
    store.save_stage_receipt(StageReceipt(
        "stage-1",
        "old-input",
        result_references=("claim-1",),
        result_hashes=(canonical_json_hash({"value": "old"}),),
        status="committed",
        committed=True,
        provenance_complete=True,
    ))

    assert main(["propose", "--work-dir", str(work_dir), "--format", "json"]) == 0
    package = json.loads(capsys.readouterr().out)

    assert package["reuse_candidates"][0]["status"] == "fresh"
    assert "runtime fingerprint comparison" in package["reuse_candidates"][0]["reason"]


def test_work_brief_template_validates_against_canonical_contract():
    text = Path("docs/templates/work-brief-template.md").read_text(encoding="utf-8")
    fenced = text.split("```yaml\n", 1)[1].split("\n```", 1)[0]
    assert validate_work_brief(yaml.safe_load(fenced))["investigation_id"] == "example-investigation"
