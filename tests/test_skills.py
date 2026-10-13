import asyncio

import pytest

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.skills import SkillRegistry
from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
from foresight_os.runtime.workflow import run_recipe_async


def test_registry_resolves_all_bundled_skills_and_rejects_unknown_ids():
    registry = SkillRegistry()
    skills = registry.resolve((
        "source-appraisal",
        "key-assumptions-check",
        "quantitative-sanity-check",
        "red-team-claim",
        "abstain-or-escalate",
        "scenario-planning",
    ))

    assert len(skills) == 6
    assert all(skill.content and skill.content_sha256 for skill in skills)
    with pytest.raises(ValueError, match="unknown skill"):
        registry.resolve(("missing-skill",))


def test_registry_reuses_verified_skill_resolution_within_process():
    registry = SkillRegistry()

    first = registry.resolve(("source-appraisal",))
    second = registry.resolve(("source-appraisal",))

    assert first is second


def test_skill_capability_denial_happens_before_agent_construction():
    class Client:
        def as_agent(self, **kwargs):
            raise AssertionError("agent construction must not occur")

    with pytest.raises(RuntimeError, match="unavailable"):
        AgentFactory(Client()).create(
            ParticipantConfig("source", "analyst", "appraise", skill_ids=("source-appraisal",)),
            {"skill_registry": SkillRegistry(), "capability_resolver": CapabilityResolver(), "scope": CapabilityScope()},
        )


def test_stage_local_skills_do_not_leak_between_stages():
    class Agent:
        async def run(self, prompt):
            return type("Response", (), {"text": prompt})()

    class Client:
        def __init__(self):
            self.instructions = []

        def as_agent(self, **kwargs):
            self.instructions.append(kwargs["instructions"])
            return Agent()

    base = make_recipe(RecipeName.DIRECT)
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
        stages=(
            RecipeStage("one", ExecutionPattern.DIRECT, ({"id": "one", "purpose": "first"},), "prompt", "typed-result", {}, ("key-assumptions-check",)),
            RecipeStage("two", ExecutionPattern.DIRECT, ({"id": "two", "purpose": "second"},), "prompt", "typed-result", {}, ("red-team-claim",)),
        ),
    )
    client = Client()
    asyncio.run(run_recipe_async(recipe, "start", client, "skill-local"))

    assert "# Key Assumptions Check" in client.instructions[0]
    assert "# Red-Team Claim" not in client.instructions[0]
    assert "# Red-Team Claim" in client.instructions[1]
    assert "# Key Assumptions Check" not in client.instructions[1]
