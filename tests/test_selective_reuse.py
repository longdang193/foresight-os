import asyncio

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.persistence.analysis_store import StageReceipt
from foresight_os.runtime.workflow import _stage_cache_key, run_recipe_async


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


def test_committed_stage_cache_hits_complete_ordered_stages_without_new_calls():
    base = make_recipe(RecipeName.DIRECT)
    first = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    second = RecipeStage("second", ExecutionPattern.DIRECT, ({"id": "second", "purpose": "second"},), "prompt", "typed-result", {})
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
    stage_cache = {
        _stage_cache_key(first, "start", ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-first"], "result_hashes": ["hash-first"], "output": first_output},
        _stage_cache_key(second, first_output, ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-second"], "result_hashes": ["hash-second"], "output": {"stage": "second"}},
    }

    result = asyncio.run(run_recipe_async(recipe, "start", run_context={"stage_cache": stage_cache}))

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
    key = _stage_cache_key(stage, "start", ())
    result = asyncio.run(run_recipe_async(recipe, "start", run_context={"stage_cache": {key: {"status": "pending", "provenance_complete": True, "output": "old"}}}))

    assert result.metrics.cache_hits == 0
    assert result.metrics.reassessed_stages == 1
