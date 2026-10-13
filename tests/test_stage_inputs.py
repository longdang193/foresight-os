import asyncio

from foresight_os.controller.policy import select_recipe
from foresight_os.controller.recipes import ExecutionPattern, RecipeStage, StageInput
from foresight_os.domain.models import WorkBrief, WorkStage
from foresight_os.runtime.workflow import _stage_cache_key, _stage_fingerprints, run_recipe_async


def _brief(stages):
    return WorkBrief(
        investigation_id="stage-inputs",
        decision_question="Should we proceed?",
        scope=["bounded scope"],
        desired_deliverables=["decision"],
        assumptions=["known constraint"],
        open_dependencies=[],
        current_direction="inspect",
        next_useful_step="execute",
        horizon="2030",
        stages=stages,
    )


def test_work_stage_specialist_ids_survive_recipe_compilation():
    recipe = select_recipe(_brief([WorkStage("stage-1", "assess", participants=["market-analyst"])]))

    assert recipe.stages[0].participants[0]["id"] == "market-analyst"
    assert recipe.stages[0].decision_question == "Should we proceed?"
    assert recipe.stages[0].horizon == "2030"


def test_stage_input_contains_only_declared_dependency_outputs(monkeypatch):
    recipe = select_recipe(
        _brief(
            [
                WorkStage("first", "collect", participants=["collector"]),
                WorkStage("second", "assess", participants=["assessor"], dependencies=["first"]),
            ]
        )
    )
    observed = []

    async def fake_native_stage(pattern, prompt, client, roles, metrics=None, run_context=None):
        observed.append(prompt)
        return [prompt]

    monkeypatch.setattr("foresight_os.runtime.workflow._run_native_stage", fake_native_stage)

    result = asyncio.run(run_recipe_async(recipe, "outer prompt", object()))

    assert result.outputs
    assert any('"dependency_outputs":{}' in item for item in observed if isinstance(item, str))
    assert any('"first"' in item for item in observed if isinstance(item, str))
    assert all("outer prompt" not in item for item in observed if isinstance(item, str) and '"dependency_outputs"' in item)


def test_semantic_and_policy_fingerprints_are_distinct():
    base = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {}, objective="assess", expected_result="result")
    changed_policy = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {"max_timeout_seconds": 120}, objective="assess", expected_result="result")

    base_fingerprints = _stage_fingerprints(base, StageInput("question", "2030", "assess", "result"), ())
    policy_fingerprints = _stage_fingerprints(changed_policy, StageInput("question", "2030", "assess", "result"), ())

    assert base_fingerprints[0] == policy_fingerprints[0]
    assert base_fingerprints[1] != policy_fingerprints[1]
    assert _stage_cache_key(base, StageInput("question", "2030", "assess", "result"), ()) == _stage_cache_key(changed_policy, StageInput("question", "2030", "assess", "result"), ())
