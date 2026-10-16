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
            ParticipantConfig("source", "analyst", "calculate", skill_ids=("quantitative-sanity-check",)),
            {"skill_registry": SkillRegistry(), "capability_resolver": CapabilityResolver(), "scope": CapabilityScope()},
        )


def test_factory_injects_recipe_bound_structured_output_schema():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    schema = {"type": "json_schema", "json_schema": {"name": "test"}}

    AgentFactory(Client()).create(
        ParticipantConfig("source", "analyst", "calculate"),
        {"require_structured_output": True, "structured_output_schema": schema},
    )

    assert captured["default_options"]["response_format"] == schema


def test_factory_binds_exact_stage_id_for_structured_results():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    AgentFactory(Client()).create(
        ParticipantConfig("source", "analyst", "audit sources"),
        {"require_structured_output": True, "stage_id": "source-audit"},
    )

    assert "stage_id must be exactly 'source-audit'" in captured["instructions"]
    assert "Return only one JSON object matching analysis-stage-result/v1" in captured["instructions"]
    assert "informs: claim/evidence/implication -> implication/recommendation" in captured["instructions"]
    assert "produces only from claim/implication/recommendation to artifact" in captured["instructions"]
    assert "omit the edge rather than inventing a relationship" in captured["instructions"]
    assert "stage result must be self-contained" in captured["instructions"]
    assert "never reference dependency-only evidence" in captured["instructions"]
    assert "Every relationship_ids entry must refer to a relationship" in captured["instructions"]
    assert "never reference an ID that appears only in dependency_outputs" in captured["instructions"]
    assert "audit every evidence_ids" in captured["instructions"]
    assert "copy every field verbatim" in captured["instructions"]
    assert "use a new record ID for a revised interpretation" in captured["instructions"]
    assert "never use a spreadsheet coordinate" in captured["instructions"]
    assert "Do not emit duplicate relationship edges" in captured["instructions"]


def test_factory_documents_spreadsheet_selection_shape():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    AgentFactory(Client()).create(
        ParticipantConfig("source", "analyst", "audit workbook", capability_ids=("spreadsheet_read",)),
        {
            "require_structured_output": True,
            "stage_id": "source-audit",
            "capability_resolver": CapabilityResolver(),
            "local_capabilities": {"spreadsheet_read": lambda source, selection=None, limits=None: None},
        },
    )

    assert "ranges as a list of [sheet_name, cell_range] pairs" in captured["instructions"]
    assert "also provide sheet_names for every selected sheet" in captured["instructions"]
    assert "do not request a blanket workbook read" in captured["instructions"]
    assert "Read one sheet per call" in captured["instructions"]
    assert "never use workbook_sha256" in captured["instructions"]


def test_factory_documents_supported_data_analysis_operations():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    AgentFactory(Client()).create(
        ParticipantConfig("analyst", "analyst", "analyze workbook", capability_ids=("data_analysis",)),
        {"tools_by_participant": {"analyst": []}},
    )

    assert "operation kind must be one of aggregate, sum, mean" in captured["instructions"]
    assert "summary is unsupported" in captured["instructions"]


def test_factory_documents_domain_validation_candidate_contract():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    AgentFactory(Client()).create(
        ParticipantConfig("validator", "validator", "validate evidence", capability_ids=("domain_validation",)),
        {"tools_by_participant": {"validator": []}},
    )

    assert "with only candidate_id, capability_id, source, request, excerpt" in captured["instructions"]
    assert "do not pass scorecard weights" in captured["instructions"]
    assert "stage results" in captured["instructions"]
    assert "dependency_outputs" in captured["instructions"]


def test_factory_documents_calculation_input_contract():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    AgentFactory(Client()).create(
        ParticipantConfig("analyst", "analyst", "calculate metrics", capability_ids=("calculation",)),
        {"tools_by_participant": {"analyst": []}},
    )

    assert "only spreadsheet measurements returned by spreadsheet_read" in captured["instructions"]
    assert "never pass domain Evidence" in captured["instructions"]


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
