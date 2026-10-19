import asyncio

import foresight_os.runtime.workflow as workflow_module

from foresight_os.controller.policy import select_recipe
from foresight_os.controller.recipes import ExecutionPattern, RecipeStage, StageInput
from foresight_os.controller.skills import ResolvedSkill, SkillManifest
from foresight_os.domain.models import WorkBrief, WorkStage
from foresight_os.domain.analysis_inputs import AnalysisInputContract
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


def test_recipe_compiles_explicit_contract_domains_without_wire_field_drift():
    brief = _brief([
        WorkStage("portfolio", "assess portfolio", participants=["analyst"]),
        WorkStage("supplier", "assess suppliers", participants=["analyst"]),
    ])
    brief = WorkBrief(
        **{
            **brief.__dict__,
            "analysis_inputs": {
                "portfolio_resilience": AnalysisInputContract(domain="portfolio_resilience", stage_id="portfolio").to_dict(),
                "supplier_resilience": AnalysisInputContract(domain="supplier_resilience", stage_id="supplier").to_dict(),
            },
        }
    )

    recipe = select_recipe(brief)
    restored = type(recipe).from_dict(recipe.to_dict())

    assert recipe.stages[0].analysis_domains == ("portfolio_resilience",)
    assert recipe.stages[1].analysis_domains == ("supplier_resilience",)
    assert restored.stages[0].analysis_domains == ("portfolio_resilience",)
    assert recipe.to_dict()["stages"][0]["analysis_domains"] == ["portfolio_resilience"]
    assert "analysis_contract_domains" not in recipe.metadata


def test_global_contracts_do_not_select_deterministic_stage_domains():
    brief = _brief([
        WorkStage("portfolio", "assess portfolio", participants=["analyst"]),
        WorkStage("supplier", "assess suppliers", participants=["analyst"]),
    ])
    brief = WorkBrief(
        **{
            **brief.__dict__,
            "analysis_inputs": {
                "portfolio_resilience": [
                    AnalysisInputContract(domain="portfolio_resilience").to_dict(),
                    AnalysisInputContract(domain="portfolio_resilience", stage_id="portfolio", assumptions=("override",)).to_dict(),
                ],
                "supplier_resilience": AnalysisInputContract(domain="supplier_resilience", stage_id="supplier").to_dict(),
            },
        }
    )

    recipe = select_recipe(brief)

    assert recipe.stages[0].analysis_domains == ("portfolio_resilience",)
    assert recipe.stages[1].analysis_domains == ("supplier_resilience",)


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


def test_recipe_execution_computes_stage_fingerprints_once(monkeypatch):
    recipe = select_recipe(_brief([WorkStage("only", "collect", participants=["collector"])]))
    original = workflow_module._stage_fingerprints
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    async def fake_native_stage(pattern, prompt, client, roles, metrics=None, run_context=None):
        return [prompt]

    monkeypatch.setattr(workflow_module, "_stage_fingerprints", counted)
    monkeypatch.setattr(workflow_module, "_run_native_stage", fake_native_stage)

    asyncio.run(run_recipe_async(recipe, "outer prompt", object()))

    assert calls == len(recipe.stages)


def test_stage_input_carries_research_needs_into_provider_payload():
    stage_input = StageInput(
        "question",
        "2030",
        "assess",
        "result",
        research_needs=("workbook measurements", "source details"),
    )

    assert stage_input.to_payload()["research_needs"] == ("workbook measurements", "source details")


def test_contract_identity_changes_stage_semantic_fingerprint():
    stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {})
    first = StageInput("question", "2030", "assess", "result", analysis_contract_fingerprints=(("portfolio_resilience", "first"),))
    second = StageInput("question", "2030", "assess", "result", analysis_contract_fingerprints=(("portfolio_resilience", "second"),))

    assert _stage_fingerprints(stage, first, ())[0] != _stage_fingerprints(stage, second, ())[0]


def test_analyzer_identity_changes_stage_semantic_fingerprint():
    stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {})
    first = StageInput("question", "2030", "assess", "result", analysis_analyzer_fingerprints=(("portfolio_resilience", "analyzer-v1"),))
    second = StageInput("question", "2030", "assess", "result", analysis_analyzer_fingerprints=(("portfolio_resilience", "analyzer-v2"),))

    assert _stage_fingerprints(stage, first, ())[0] != _stage_fingerprints(stage, second, ())[0]


def test_semantic_and_policy_fingerprints_are_distinct():
    base = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {}, objective="assess", expected_result="result")
    changed_policy = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst"},), "prompt", "typed-result", {"max_timeout_seconds": 120}, objective="assess", expected_result="result")

    base_fingerprints = _stage_fingerprints(base, StageInput("question", "2030", "assess", "result"), ())
    policy_fingerprints = _stage_fingerprints(changed_policy, StageInput("question", "2030", "assess", "result"), ())

    assert base_fingerprints[0] == policy_fingerprints[0]
    assert base_fingerprints[1] != policy_fingerprints[1]
    assert _stage_cache_key(base, StageInput("question", "2030", "assess", "result"), ()) == _stage_cache_key(changed_policy, StageInput("question", "2030", "assess", "result"), ())


def test_stage_fingerprint_includes_each_participant_skill_identity_and_order():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.DIRECT,
        (
            {"id": "analyst", "purpose": "analyze", "skill_ids": ("analyst-skill",)},
            {"id": "reviewer", "purpose": "review", "skill_ids": ("review-skill",)},
        ),
        "prompt",
        "typed-result",
        {},
        skill_ids=("stage-skill",),
    )
    input_value = StageInput("question", "2030", "assess", "result")

    def resolved(skill_id: str, version: str = "1.0.0", digest: str | None = None) -> ResolvedSkill:
        manifest = SkillManifest(skill_id, version, f"{skill_id}.md", digest or f"hash-{skill_id}", (), "result", "test")
        return ResolvedSkill(manifest, skill_id)

    base = {
        "analyst": (resolved("stage-skill"), resolved("analyst-skill")),
        "reviewer": (resolved("stage-skill"), resolved("review-skill")),
    }
    base_fingerprint = _stage_fingerprints(stage, input_value, stage.skill_ids, base)[0]
    assert base_fingerprint != _stage_fingerprints(
        stage,
        input_value,
        stage.skill_ids,
        {**base, "analyst": (resolved("stage-skill"), resolved("other-skill"))},
    )[0]
    assert base_fingerprint != _stage_fingerprints(
        stage,
        input_value,
        stage.skill_ids,
        {"analyst": base["analyst"], "reviewer": (resolved("review-skill"), resolved("stage-skill"))},
    )[0]
    assert base_fingerprint != _stage_fingerprints(
        stage,
        input_value,
        stage.skill_ids,
        {**base, "analyst": (resolved("stage-skill", version="2.0.0"), resolved("analyst-skill"))},
    )[0]
    assert base_fingerprint != _stage_fingerprints(
        stage,
        input_value,
        stage.skill_ids,
        {**base, "analyst": (resolved("stage-skill", digest="changed"), resolved("analyst-skill"))},
    )[0]
