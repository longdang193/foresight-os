import asyncio

import pytest

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, StageInput, make_recipe
from foresight_os.persistence.analysis_store import StageReceipt
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.controller.proposal import classify_reuse
from foresight_os.runtime.workflow import CanonicalStageResult, StaleReuseError, _canonical_result_hash, _stage_cache_key, run_recipe_async


def test_stage_receipt_reuse_revalidates_semantic_scope_and_provenance():
    receipt = StageReceipt(
        "stage-1",
        "input-v1",
        skill_hashes=("skill-v1",),
        capability_fingerprints=("local-v1",),
        model_config_fingerprint="model-v1",
        authorization_scope_fingerprint="scope-v1",
        result_references=("claim-1",),
        result_hashes=("result-v1",),
        status="committed",
        committed=True,
        provenance_complete=True,
    )
    assert receipt.reusable_for(input_fingerprint="input-v1", skill_hashes=("skill-v1",), capability_fingerprints=("local-v1",), model_config_fingerprint="model-v1", authorization_scope_fingerprint="scope-v1")
    assert not receipt.reusable_for(input_fingerprint="input-v1", authorization_scope_fingerprint="scope-v2")
    assert not receipt.reusable_for(input_fingerprint="input-v1", execution_policy_fingerprint="policy-v2", skill_hashes=("skill-v1",), capability_fingerprints=("local-v1",), model_config_fingerprint="model-v1", authorization_scope_fingerprint="scope-v1")
    assert classify_reuse(receipt, reusable=True)["status"] == "reusable"
    assert classify_reuse(None, reusable=False)["status"] == "fresh"


def test_committed_stage_cache_hits_complete_ordered_stages_without_new_calls():
    base = make_recipe(RecipeName.DIRECT)
    first = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    second = RecipeStage("second", ExecutionPattern.DIRECT, ({"id": "second", "purpose": "second"},), "prompt", "typed-result", {}, dependencies=("first",))
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(first, second),
    )
    first_output = {"stage": "first"}
    second_output = {"stage": "second"}
    canonical_records = {"claim-first": first_output, "claim-second": second_output}
    stage_cache = {
        _stage_cache_key(first, StageInput("start", "unspecified", "execute declared stage", ""), ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-first"], "result_hashes": [_canonical_result_hash(first_output)], "output": {"tampered": True}},
        _stage_cache_key(second, StageInput("start", "unspecified", "execute declared stage", "", dependency_outputs=(("first", first_output),)), ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-second"], "result_hashes": [_canonical_result_hash(second_output)], "output": {"tampered": True}},
    }

    result = asyncio.run(run_recipe_async(recipe, "start", run_context={"stage_cache": stage_cache, "canonical_records": canonical_records}))

    assert result.outputs[-1] == {"stage": "second"}
    assert result.metrics.cache_hits == 2
    assert result.metrics.reassessed_stages == 0
    assert result.metrics.model_calls == 0
    assert result.metrics.tool_calls == 0


def test_pending_or_incomplete_cache_entries_are_not_reused():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    key = _stage_cache_key(stage, StageInput("start", "unspecified", "execute declared stage", ""), ())
    result = asyncio.run(run_recipe_async(recipe, "start", run_context={"stage_cache": {key: {"status": "pending", "provenance_complete": True, "output": "old"}}}))

    assert result.metrics.cache_hits == 0
    assert result.metrics.reassessed_stages == 1


def test_successful_canonical_stage_persists_receipt_and_reuses_after_restart(tmp_path):
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    store = AnalysisStore(tmp_path / "receipts")
    committed = {"stage": "canonical"}

    def commit_result(_stage, _output, _context):
        return CanonicalStageResult(("claim-1",), (_canonical_result_hash(committed),), committed)

    first = asyncio.run(
        run_recipe_async(
            recipe,
            "start",
            run_context={"analysis_store": store, "canonical_result_committer": commit_result},
        )
    )
    assert first.metrics.reassessed_stages == 1
    assert store.load_stage_receipts()["first"].reusable()

    second = asyncio.run(
        run_recipe_async(
            recipe,
            "start",
            run_context={"analysis_store": store, "canonical_records": {"claim-1": committed}},
        )
    )
    assert second.outputs[-1] == committed
    assert second.metrics.cache_hits == 1
    assert second.metrics.reassessed_stages == 0
    assert second.metrics.model_calls == 0


def test_temporary_stage_output_does_not_create_a_receipt(tmp_path):
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    store = AnalysisStore(tmp_path / "temporary")

    asyncio.run(run_recipe_async(recipe, "start", run_context={"analysis_store": store}))

    assert store.load_stage_receipts() == {}


def test_run_fresh_reassesses_selected_stage_and_descendants():
    base = make_recipe(RecipeName.DIRECT)
    first = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first"},), "prompt", "typed-result", {})
    second = RecipeStage("second", ExecutionPattern.DIRECT, ({"id": "second"},), "prompt", "typed-result", {}, dependencies=("first",))
    recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(first, second),
    )
    result = asyncio.run(run_recipe_async(recipe, "start", run_context={"run_fresh_stages": ("first",)}))
    assert result.metrics.reassessed_stages == 2


def test_run_fresh_does_not_reuse_matching_stage_receipt(tmp_path):
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(stage,),
    )
    store = AnalysisStore(tmp_path / "fresh")

    def commit_result(_stage, output, _context):
        return CanonicalStageResult(("claim-1",), (_canonical_result_hash(output),), output)

    first = asyncio.run(run_recipe_async(recipe, "start", run_context={
        "analysis_store": store,
        "canonical_result_committer": commit_result,
    }))

    result = asyncio.run(run_recipe_async(recipe, "start", run_context={
        "analysis_store": store,
        "canonical_records": {"claim-1": first.outputs[-1]},
        "run_fresh_stages": ("first",),
    }))

    assert result.metrics.cache_hits == 0
    assert result.metrics.reassessed_stages == 1


def test_run_fresh_ignores_stale_stop_fallback_for_selected_stage():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(stage,),
    )
    output = {"stage": "old"}
    receipt = StageReceipt(
        "first",
        "stale-input",
        result_references=("claim-1",),
        result_hashes=(_canonical_result_hash(output),),
        status="committed",
        committed=True,
        provenance_complete=True,
    )

    result = asyncio.run(run_recipe_async(recipe, "start", run_context={
        "stage_receipts": {"first": receipt},
        "canonical_outputs": {"first": output},
        "canonical_records": {"claim-1": output},
        "run_fresh_stages": ("first",),
        "fallback_on_stale_reuse": "stop",
    }))

    assert result.metrics.cache_hits == 0
    assert result.metrics.reassessed_stages == 1


def test_approved_stop_fallback_blocks_stale_receipt_before_provider_work():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(stage,),
    )
    output = {"stage": "old"}
    receipt = StageReceipt(
        "first",
        "stale-input",
        result_references=("claim-1",),
        result_hashes=(_canonical_result_hash(output),),
        status="committed",
        committed=True,
        provenance_complete=True,
    )

    with pytest.raises(StaleReuseError, match="stale stage receipt"):
        asyncio.run(run_recipe_async(recipe, "start", run_context={
            "stage_receipts": {"first": receipt},
            "canonical_outputs": {"first": output},
            "canonical_records": {"claim-1": output},
            "fallback_on_stale_reuse": "stop",
        }))


def test_changed_evidence_honors_stop_fallback_instead_of_discarding_receipt():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(stage,),
    )
    output = {"stage": "old"}
    stage_input = StageInput("start", "unspecified", "execute declared stage", "")
    receipt = StageReceipt(
        "first",
        _stage_cache_key(stage, stage_input, ()),
        result_references=("claim-1",),
        result_hashes=(_canonical_result_hash(output),),
        status="committed",
        committed=True,
        provenance_complete=True,
    )

    class RelationIndex:
        def impact_closure(self, changed_ids):
            return set(changed_ids) | {"claim-1"}

    with pytest.raises(StaleReuseError, match="stale stage receipt"):
        asyncio.run(run_recipe_async(recipe, "start", run_context={
            "stage_receipts": {"first": receipt},
            "canonical_outputs": {"first": output},
            "canonical_records": {"claim-1": output},
            "changed_record_ids": ("source-1",),
            "relation_index": RelationIndex(),
            "fallback_on_stale_reuse": "stop",
        }))


def test_effective_participant_controls_invalidate_old_receipts(tmp_path):
    base = make_recipe(RecipeName.DIRECT)
    first_stage = RecipeStage(
        "first", ExecutionPattern.DIRECT,
        ({"id": "first", "model": "model-a", "reasoning_controls": {"temperature": 0.1}},),
        "prompt", "typed-result", {},
    )
    first_recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(first_stage,),
    )
    store = AnalysisStore(tmp_path / "participant-controls")
    output = {"stage": "canonical"}

    def commit_result(_stage, _output, _context):
        return CanonicalStageResult(("claim-1",), (_canonical_result_hash(output),), output)

    asyncio.run(run_recipe_async(first_recipe, "start", run_context={
        "analysis_store": store,
        "canonical_result_committer": commit_result,
    }))
    changed_stage = RecipeStage(
        "first", ExecutionPattern.DIRECT,
        ({"id": "first", "model": "model-b", "reasoning_controls": {"temperature": 0.2}},),
        "prompt", "typed-result", {},
    )
    changed_recipe = ExecutionRecipe(
        base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds,
        base.max_total_agent_calls, base.completion, base.escalation, base.partial_result,
        stages=(changed_stage,),
    )

    with pytest.raises(StaleReuseError, match="stale stage receipt"):
        asyncio.run(run_recipe_async(changed_recipe, "start", run_context={
            "analysis_store": store,
            "canonical_records": {"claim-1": output},
            "fallback_on_stale_reuse": "stop",
        }))
