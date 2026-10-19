import asyncio
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from foresight_os.artifacts.approval import build_approval_package
from foresight_os.controller.recipes import ExecutionPattern
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalRecord, ApprovalStatus
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.domain.models import WorkStage
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.execution_gate import ExecutionAdmissionError, ExecutionGate
from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership
from foresight_os.runtime.local_toolbelt import SourceSnapshot
from foresight_os.wayfinding import create_work_brief


def prepared_store(tmp_path):
    brief = create_work_brief("Question", investigation_id="gate")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "gate")
    store.save_brief(brief)
    store.save_recipe(recipe)
    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))
    return store


def approve_recipe(store, recipe):
    brief = store.load_brief()
    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))


def test_missing_approval_is_denied(tmp_path):
    store = AnalysisStore(tmp_path / "missing")
    brief = create_work_brief("Question", investigation_id="missing")
    store.save_brief(brief)
    store.save_recipe(build_execution_recipe(brief).recipe)
    with pytest.raises(ExecutionAdmissionError, match="approved ApprovalRecord"):
        ExecutionGate(store).admit(prompt="Question")


def test_mutated_recipe_is_denied_after_approval(tmp_path):
    store = prepared_store(tmp_path)
    recipe = store.load_recipe()
    store.save_recipe(type(recipe)(**{**recipe.__dict__, "max_agent_steps": recipe.max_agent_steps + 1}))
    with pytest.raises(ExecutionAdmissionError, match="approved projection"):
        ExecutionGate(store).admit(prompt="Question")


def test_admitted_execution_passes_immutable_context(monkeypatch, tmp_path):
    store = prepared_store(tmp_path)
    seen = {}

    async def fake_run(recipe, prompt, client=None, run_id=None, run_context=None):
        seen.update(run_context)
        return type("Result", (), {"run_id": run_id})()

    monkeypatch.setattr("foresight_os.runtime.execution_gate.run_recipe_async", fake_run)
    result = asyncio.run(ExecutionGate(store).execute(prompt="Question", client=object(), run_id="run-1"))
    assert result.run_id == "run-1"
    assert seen["execution_admitted"] is True
    assert seen["approved_recipe_fingerprint"] == canonical_json_hash(store.load_recipe().to_dict())
    assert seen["fallback_on_stale_reuse"] == "stop"
    assert seen["require_structured_output"] is True
    assert seen["canonical_result_committer"]


def test_admission_reads_the_persisted_recipe_once(monkeypatch, tmp_path):
    store = prepared_store(tmp_path)
    original_read_text = Path.read_text
    reads = 0

    def counted_read_text(path, *args, **kwargs):
        nonlocal reads
        if path == store.execution_recipe_path:
            reads += 1
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read_text)

    ExecutionGate(store).admit(prompt="Question")

    assert reads == 2


def test_admitted_execution_forwards_persisted_analysis_contract_identity(monkeypatch, tmp_path):
    brief = create_work_brief(
        "Question",
        investigation_id="contract-gate",
        analysis_inputs={
            "portfolio_resilience": AnalysisInputContract(
                domain="portfolio_resilience",
                baseline_period="2025",
                units="EUR",
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "contract-gate")
    store.save_brief(brief)
    store.save_recipe(recipe)
    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))
    seen = {}

    async def fake_run(recipe, prompt, client=None, run_id=None, run_context=None):
        seen.update(run_context)
        return type("Result", (), {"run_id": run_id})()

    monkeypatch.setattr("foresight_os.runtime.execution_gate.run_recipe_async", fake_run)
    asyncio.run(ExecutionGate(store).execute(prompt="Question", client=object(), run_id="run-contract"))

    assert seen["analysis_contract_fingerprints"]["portfolio_resilience"]
    assert seen["analysis_analyzer_fingerprints"]["portfolio_resilience"]


def test_admitted_execution_resolves_partial_workbook_contract_before_dispatch(monkeypatch, tmp_path):
    source = Path("tests/fixtures/exercise/04_Technology_Radar.xlsx").resolve()
    brief = create_work_brief(
        "Assess technology readiness",
        investigation_id="partial-contract-gate",
        stages=[WorkStage("stage-1", "Assess technology readiness")],
        analysis_inputs={
            "technology_radar": AnalysisInputContract(
                domain="technology_radar",
                stage_id="stage-1",
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "partial-contract-gate")
    store.save_brief(brief)
    store.save_recipe(recipe)
    approve_recipe(store, recipe)
    seen = {}

    async def fake_run(recipe, prompt, client=None, run_id=None, run_context=None):
        seen.update(run_context)
        return type("Result", (), {"run_id": run_id})()

    monkeypatch.setattr("foresight_os.runtime.execution_gate.run_recipe_async", fake_run)
    asyncio.run(ExecutionGate(store).execute(
        prompt=brief.decision_question,
        client=None,
        workbook_source=source,
    ))

    effective = seen["analysis_contracts"]["stage-1:technology_radar"]
    assert effective["required_tables"]
    assert seen["analysis_contract_fingerprints"]["stage-1:technology_radar"]


def test_admission_rejects_brief_mutation_during_workbook_capture(monkeypatch, tmp_path):
    source = Path("tests/fixtures/exercise/04_Technology_Radar.xlsx").resolve()
    brief = create_work_brief(
        "Assess technology readiness",
        investigation_id="brief-capture-mutation",
        stages=[WorkStage("stage-1", "Assess technology readiness")],
        analysis_inputs={
            "technology_radar": AnalysisInputContract(
                domain="technology_radar",
                stage_id="stage-1",
                required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "brief-capture-mutation")
    store.save_brief(brief)
    store.save_recipe(recipe)
    approve_recipe(store, recipe)
    original_capture = SourceSnapshot.capture

    def capture_and_mutate(*args, **kwargs):
        snapshot = original_capture(*args, **kwargs)
        store.save_brief(replace(brief, decision_question="mutated after admission began"))
        return snapshot

    monkeypatch.setattr(SourceSnapshot, "capture", capture_and_mutate)
    with pytest.raises(ExecutionAdmissionError, match="WorkBrief changed"):
        ExecutionGate(store).admit(prompt=brief.decision_question, workbook_source=source)


def test_admission_rejects_recipe_mutation_during_workbook_capture(monkeypatch, tmp_path):
    source = Path("tests/fixtures/exercise/04_Technology_Radar.xlsx").resolve()
    brief = create_work_brief(
        "Assess technology readiness",
        investigation_id="recipe-capture-mutation",
        stages=[WorkStage("stage-1", "Assess technology readiness")],
        analysis_inputs={
            "technology_radar": AnalysisInputContract(
                domain="technology_radar",
                stage_id="stage-1",
                required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "recipe-capture-mutation")
    store.save_brief(brief)
    store.save_recipe(recipe)
    approve_recipe(store, recipe)
    original_capture = SourceSnapshot.capture

    def capture_and_mutate(*args, **kwargs):
        snapshot = original_capture(*args, **kwargs)
        mutated = replace(recipe, max_agent_steps=recipe.max_agent_steps + 1)
        store.save_recipe(mutated)
        return snapshot

    monkeypatch.setattr(SourceSnapshot, "capture", capture_and_mutate)
    with pytest.raises(ExecutionAdmissionError, match="ExecutionRecipe changed"):
        ExecutionGate(store).admit(prompt=brief.decision_question, workbook_source=source)


def test_all_local_approved_workbook_execution_commits_source_sha_without_client(tmp_path):
    source = Path("tests/fixtures/exercise/04_Technology_Radar.xlsx").resolve()
    brief = create_work_brief(
        "Assess technology readiness",
        investigation_id="local-workbook-gate",
        stages=[WorkStage("stage-1", "Assess technology readiness")],
        analysis_inputs={
            "technology_radar": AnalysisInputContract(
                domain="technology_radar",
                stage_id="stage-1",
                required_tables=(
                    "Brief",
                    "Signals",
                    "Company_Relevance",
                    "Competitor_Actions",
                    "Scenario_Signposts",
                    "Priority_Scoring",
                ),
                units="index",
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "local-workbook-gate")
    store.save_brief(brief)
    store.save_recipe(recipe)
    approve_recipe(store, recipe)

    result = asyncio.run(ExecutionGate(store).execute(
        prompt=brief.decision_question,
        client=None,
        run_id="run-local-workbook-gate",
        workbook_source=source,
    ))

    receipt = store.load_stage_receipts()["stage-1"]
    assert result.metrics.runtime_status == "SETTLED"
    assert result.metrics.persistence_status == "PERSISTED"
    assert receipt.status == "committed"
    assert receipt.source_revision == SourceSnapshot.capture(source).sha256


def test_workbook_capture_runs_outside_persistence_lock(monkeypatch, tmp_path):
    source = Path("tests/fixtures/exercise/04_Technology_Radar.xlsx").resolve()
    brief = create_work_brief(
        "Assess technology readiness",
        investigation_id="lock-scope",
        stages=[WorkStage("stage-1", "Assess technology readiness")],
        analysis_inputs={
            "technology_radar": AnalysisInputContract(
                domain="technology_radar",
                stage_id="stage-1",
                required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
                units="index",
            ).to_dict(),
        },
    )
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "lock-scope")
    store.save_brief(brief)
    store.save_recipe(recipe)
    approve_recipe(store, recipe)
    events = []
    original_capture = SourceSnapshot.capture

    class RecordingLock:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            events.append("lock-enter")
            return self

        def __exit__(self, *_args):
            events.append("lock-exit")

    def capture(*args, **kwargs):
        events.append("capture")
        return original_capture(*args, **kwargs)

    monkeypatch.setattr("foresight_os.runtime.execution_gate.FileLock", RecordingLock)
    monkeypatch.setattr(SourceSnapshot, "capture", capture)

    ExecutionGate(store).admit(prompt=brief.decision_question, workbook_source=source)

    assert events.index("lock-exit") < events.index("capture")


def test_admitted_execution_without_client_is_blocked(tmp_path):
    store = prepared_store(tmp_path)

    with pytest.raises(ExecutionAdmissionError, match="configured client"):
        asyncio.run(ExecutionGate(store).execute(prompt="Question"))


def test_legacy_approved_recipe_without_analysis_domains_remains_admissible(tmp_path):
    brief = create_work_brief("Question", investigation_id="legacy-recipe")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "legacy-recipe")
    store.save_brief(brief)

    legacy_recipe = recipe.to_dict()
    for stage in legacy_recipe["stages"]:
        stage.pop("analysis_domains")
    store._atomic_write(store.execution_recipe_path, json.dumps(legacy_recipe, sort_keys=True, indent=2) + "\n")

    package = build_approval_package(brief, legacy_recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(legacy_recipe),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))

    admission = ExecutionGate(store).admit(prompt="Question")

    assert admission.recipe.stages[0].analysis_domains == ()


def test_legacy_approved_recipe_with_metadata_domains_remains_admissible(tmp_path):
    brief = create_work_brief("Question", investigation_id="legacy-metadata")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "legacy-metadata")
    store.save_brief(brief)

    legacy_recipe = recipe.to_dict()
    legacy_recipe["metadata"]["analysis_contract_domains"] = '{"stage-1": ["market"]}'
    for stage in legacy_recipe["stages"]:
        stage.pop("analysis_domains")
    store._atomic_write(store.execution_recipe_path, json.dumps(legacy_recipe, sort_keys=True, indent=2) + "\n")

    package = build_approval_package(brief, legacy_recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(legacy_recipe),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))

    admission = ExecutionGate(store).admit(prompt="Question")

    assert admission.recipe.stages[0].analysis_domains == ("market",)


def test_legacy_approved_recipe_material_mutation_is_denied(tmp_path):
    brief = create_work_brief("Question", investigation_id="legacy-mutation")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "legacy-mutation")
    store.save_brief(brief)

    legacy_recipe = recipe.to_dict()
    legacy_recipe["metadata"]["analysis_contract_domains"] = '{"stage-1": ["market"]}'
    for stage in legacy_recipe["stages"]:
        stage.pop("analysis_domains")
    store._atomic_write(store.execution_recipe_path, json.dumps(legacy_recipe, sort_keys=True, indent=2) + "\n")

    package = build_approval_package(brief, legacy_recipe, AdaptationEnvelope())
    store.save_execution_approval(ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(legacy_recipe),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    ))

    legacy_recipe["max_agent_steps"] += 1
    store._atomic_write(store.execution_recipe_path, json.dumps(legacy_recipe, sort_keys=True, indent=2) + "\n")

    with pytest.raises(ExecutionAdmissionError, match="approved projection"):
        ExecutionGate(store).admit(prompt="Question")


def test_superseded_approval_blocks_dispatch(tmp_path):
    store = prepared_store(tmp_path)
    store.save_execution_approval(store.load_execution_approval().superseded())
    with pytest.raises(ExecutionAdmissionError, match="approval is superseded"):
        ExecutionGate(store).admit(prompt="Question")


def test_unsupported_result_contract_blocks_before_provider_dispatch(tmp_path):
    store = prepared_store(tmp_path)
    recipe = store.load_recipe()
    store.save_recipe(replace(recipe, stages=tuple(replace(stage, result_contract="unsupported/v9") for stage in recipe.stages)))
    approve_recipe(store, store.load_recipe())
    provider_calls = 0

    class Client:
        def as_agent(self, **kwargs):
            nonlocal provider_calls
            provider_calls += 1
            return object()

    with pytest.raises(ExecutionAdmissionError, match="unsupported result contract"):
        asyncio.run(ExecutionGate(store).execute(prompt="Question", client=Client()))
    assert provider_calls == 0


def test_concurrent_canonical_stage_requires_synthesis_before_provider_dispatch(tmp_path):
    store = prepared_store(tmp_path)
    recipe = store.load_recipe()
    store.save_recipe(replace(recipe, stages=tuple(replace(stage, pattern=ExecutionPattern.CONCURRENT, synthesis_policy="single-output") for stage in recipe.stages)))
    approve_recipe(store, store.load_recipe())
    provider_calls = 0

    class Client:
        def as_agent(self, **kwargs):
            nonlocal provider_calls
            provider_calls += 1
            return object()

    with pytest.raises(ExecutionAdmissionError, match="requires an explicit synthesis policy"):
        asyncio.run(ExecutionGate(store).execute(prompt="Question", client=Client()))
    assert provider_calls == 0


def test_gate_admits_local_document_and_artifact_capabilities_with_workspace_scope(tmp_path):
    store = prepared_store(tmp_path)
    recipe = store.load_recipe()
    store.save_recipe(replace(
        recipe,
        max_total_agent_calls=6,
        stages=tuple(
            replace(
                stage,
                capabilities=("document_read", "artifact_generation"),
                limits={**stage.limits, "max_total_agent_calls": 6},
            )
            for stage in recipe.stages
        ),
    ))
    approve_recipe(store, store.load_recipe())

    admitted = ExecutionGate(store).admit(prompt="Question")

    assert admitted.recipe.stages[0].capabilities == ("document_read", "artifact_generation")


def test_gate_admission_does_not_activate_resource_factories(tmp_path):
    store = prepared_store(tmp_path)
    recipe = store.load_recipe()
    store.save_recipe(replace(
        recipe,
        max_total_agent_calls=6,
        stages=tuple(
            replace(
                stage,
                capabilities=("spreadsheet_read",),
                limits={**stage.limits, "max_total_agent_calls": 6},
            )
            for stage in recipe.stages
        ),
    ))
    approve_recipe(store, store.load_recipe())
    calls = []

    def factory(_context):
        calls.append(True)
        return object()

    ExecutionGate(store).admit(
        prompt="Question",
        run_context={
            "local_capabilities": {
                "spreadsheet_read": CapabilityBinding(
                    factory,
                    CapabilityBindingKind.RESOURCE_FACTORY,
                    CapabilityOwnership.OWNED,
                ),
            },
        },
    )

    assert calls == []
