import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from foresight_os.artifacts.approval import build_approval_package
from foresight_os.controller.recipes import ExecutionPattern
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalRecord, ApprovalStatus
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.execution_gate import ExecutionAdmissionError, ExecutionGate
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


def test_admitted_execution_without_client_is_blocked(tmp_path):
    store = prepared_store(tmp_path)

    with pytest.raises(ExecutionAdmissionError, match="configured client"):
        asyncio.run(ExecutionGate(store).execute(prompt="Question"))


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
