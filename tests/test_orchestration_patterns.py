import asyncio
from types import SimpleNamespace

import pytest

from agent_framework import Agent, AgentResponse, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
from agent_framework.orchestrations import HandoffBuilder

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.budgets import BudgetState
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.domain.validation import ValidationError
from foresight_os.analysis.result_committer import ANALYSIS_STAGE_RESULT_CONTRACT, decode_stage_output
from foresight_os.runtime.workflow import CanonicalStageResult, _canonical_result_hash, _close_agents, _dependency_stage_ids, _expand_dependency_records, _run_native_stage, _synthesize_stage_outputs, _workflow_output_value, run_recipe_async
from foresight_os.runtime.metrics import BudgetExceededError, RunCanceledError, RunMetrics
import foresight_os.runtime.workflow as workflow_module


class FakeChatClient:
    additional_properties = {}

    def get_response(self, messages, **kwargs):
        if kwargs.get("stream"):
            async def updates():
                yield ChatResponseUpdate(contents=[Content("text", text="ok")], role="assistant")

            return ResponseStream(
                updates(),
                finalizer=lambda _: ChatResponse(messages=[Message("assistant", ["ok"])]),
            )

        async def response():
            return ChatResponse(messages=[Message("assistant", ["ok"])])

        return response()

    def as_agent(self, **kwargs):
        return Agent(self, **kwargs)


class CountingChatClient(FakeChatClient):
    def __init__(self):
        self.calls = 0

    def get_response(self, messages, **kwargs):
        self.calls += 1
        return super().get_response(messages, **kwargs)


def _typed_stage_result(stage_id: str, evidence_id: str, statement: str, *, contract: str = ANALYSIS_STAGE_RESULT_CONTRACT) -> dict:
    return {
        "contract": contract,
        "stage_id": stage_id,
        "evidence": [{
            "id": evidence_id,
            "source_locator": {
                "file_version": "fixture-v1",
                "sheet": "Summary",
                "range": "A1",
                "units": "count",
                "transformation": "none",
                "calculation": "none",
            },
            "version": "v1",
            "date": "2026-10-16",
            "excerpt": statement,
            "limitations": [],
        }],
        "calculations": [],
        "claims": [{
            "id": "claim-placeholder",
            "statement": statement,
            "basis": "OBSERVED",
            "assessment": "UNASSESSED",
            "lifecycle": "CURRENT",
            "evidence_ids": [evidence_id],
            "relationship_ids": ["support-placeholder"],
            "assumptions": [],
            "uncertainty": [],
            "confidence_rationale": "",
            "disconfirmation_conditions": [],
            "monitoring_indicators": [],
        }],
        "implications": [],
        "recommendations": [],
        "artifacts": [],
        "relationships": [{
            "id": "support-placeholder",
            "from_id": evidence_id,
            "to_id": "claim-placeholder",
            "relation_type": "supports",
        }],
        "assumptions": [],
        "uncertainty": [],
        "monitoring_indicators": [],
    }


def _analytical_record(record_id: str, statement: str, *, evidence_ids: list[str] | None = None, relationship_ids: list[str] | None = None) -> dict:
    return {
        "id": record_id,
        "statement": statement,
        "basis": "DERIVED",
        "assessment": "UNASSESSED",
        "lifecycle": "CURRENT",
        "evidence_ids": evidence_ids or [],
        "relationship_ids": relationship_ids or [],
        "assumptions": [],
        "uncertainty": [],
        "confidence_rationale": "",
        "disconfirmation_conditions": [],
        "monitoring_indicators": [],
    }


def _recipe(patterns: tuple[ExecutionPattern, ...]) -> ExecutionRecipe:
    base = make_recipe(RecipeName.ANALYZE_REVIEW)
    stages = tuple(
        RecipeStage(f"stage-{index}", pattern, tuple(base.roles), "typed-result", "typed-result", {})
        for index, pattern in enumerate(patterns, 1)
    )
    return ExecutionRecipe(
        base.name,
        patterns[0].value,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        12,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=stages,
    )


def test_native_sequential_concurrent_and_group_chat_execute_with_installed_builders():
    client = FakeChatClient()
    for pattern in (ExecutionPattern.SEQUENTIAL, ExecutionPattern.CONCURRENT, ExecutionPattern.GROUP_CHAT):
        outputs = asyncio.run(_run_native_stage(pattern, "hello", client, [{"purpose": "one"}, {"purpose": "two"}]))
        assert outputs


def test_typed_participants_are_canonicalized_before_merge_and_preserve_distinct_records():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    result = _synthesize_stage_outputs(
        stage,
        [
            _typed_stage_result("stage-1", "same-provider-id", "first observation"),
            _typed_stage_result("stage-1", "same-provider-id", "second observation"),
        ],
    )

    assert len(result["evidence"]) == 2
    assert len(result["claims"]) == 2
    assert {claim["evidence_ids"][0] for claim in result["claims"]} == {evidence["id"] for evidence in result["evidence"]}


def test_typed_equivalent_participant_graphs_deduplicate_without_dangling_references():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    first = _typed_stage_result("stage-1", "first-provider-id", "same observation")
    second = _typed_stage_result("stage-1", "second-provider-id", "same observation")
    result = _synthesize_stage_outputs(stage, [first, second])

    assert len(result["evidence"]) == 1
    assert len(result["claims"]) == 1
    assert result["claims"][0]["evidence_ids"] == [result["evidence"][0]["id"]]


def test_typed_participant_stage_contract_is_validated_before_merge():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    with pytest.raises(ValidationError, match="stage_id must be stage-1"):
        _synthesize_stage_outputs(stage, [_typed_stage_result("stage-1", "one", "ok"), _typed_stage_result("other-stage", "two", "bad")])


def test_typed_synthesis_uses_one_bounded_normalization_pass(monkeypatch):
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}, {"id": "three"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    calls = 0
    original = workflow_module.normalize_stage_result

    def counting_normalize(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(workflow_module, "normalize_stage_result", counting_normalize)

    outputs = [_typed_stage_result("stage-1", f"provider-{index}", f"observation-{index}") for index in range(3)]
    _synthesize_stage_outputs(stage, outputs)

    assert calls <= len(outputs) + 1


def test_typed_synthesis_preflights_payload_bytes_before_normalization():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {"max_synthesis_payload_bytes": 32},
        synthesis_policy="aggregate-typed-results",
    )

    with pytest.raises(ValidationError) as caught:
        _synthesize_stage_outputs(
            stage,
            [
                _typed_stage_result("stage-1", "provider-one", "large observation"),
                _typed_stage_result("stage-1", "provider-two", "large observation"),
            ],
        )

    assert caught.value.code == "BUDGET_EXHAUSTED"


def test_typed_synthesis_honors_cancellation_checkpoint():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    with pytest.raises(RunCanceledError):
        _synthesize_stage_outputs(
            stage,
            [
                _typed_stage_result("stage-1", "provider-one", "observation"),
                _typed_stage_result("stage-1", "provider-two", "observation"),
            ],
            cancel_check=lambda: True,
        )


def test_native_sequential_reviewer_retains_original_stage_context(monkeypatch):
    prompts = []

    class ToolAgent:
        def __init__(self, agent_id):
            self.id = agent_id
            self.client = SimpleNamespace()
            self.default_options = {"tools": [object()]}

    async def fake_run_agent(agent, prompt, options, **kwargs):
        prompts.append(prompt)
        return {"stage_id": "stage-1", "status": "ready"}

    class ToolClient(FakeChatClient):
        def as_agent(self, **kwargs):
            return ToolAgent(kwargs["id"])

    class Builder:
        def __init__(self, **kwargs):
            pass

        def build(self):
            return None

    monkeypatch.setattr("agent_framework.orchestrations.SequentialBuilder", Builder)
    monkeypatch.setattr(workflow_module, "run_agent_with_tool_fallback", fake_run_agent)

    asyncio.run(
        _run_native_stage(
            ExecutionPattern.SEQUENTIAL,
            "exact workbook path: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx",
            ToolClient(),
            [{"purpose": "one"}, {"purpose": "two"}],
            run_context={"require_structured_output": True, "structured_output_schema": {}},
        )
    )

    assert len(prompts) == 2
    assert "exact workbook path" in prompts[0]
    assert "exact workbook path" in prompts[1]
    assert "Review this proposal" in prompts[1]


def test_dependency_records_include_referenced_canonical_ancestors():
    canonical_records = {
        "evidence-1": {"id": "evidence-1"},
        "claim-1": {"id": "claim-1", "evidence_ids": ["evidence-1"], "relationship_ids": []},
    }

    expanded = _expand_dependency_records({"claim-1": canonical_records["claim-1"]}, canonical_records)

    assert set(expanded) == {"claim-1", "evidence-1"}


def test_dependency_stage_ids_include_declared_ancestors():
    stages = {
        "source": SimpleNamespace(stage_id="source", dependencies=()),
        "screen": SimpleNamespace(stage_id="screen", dependencies=("source",)),
        "challenge": SimpleNamespace(stage_id="challenge", dependencies=("screen",)),
    }

    assert _dependency_stage_ids(stages["challenge"], stages) == ("screen", "source")


def test_native_provider_budget_is_reserved_before_model_dispatch():
    client = CountingChatClient()
    metrics = RunMetrics("budget-boundary", "SEQUENTIAL", "sequential")
    budget = BudgetState(5, 1, 0)

    with pytest.raises(BudgetExceededError, match="agent calls"):
        asyncio.run(
            _run_native_stage(
                ExecutionPattern.SEQUENTIAL,
                "hello",
                client,
                [{"purpose": "one"}],
                metrics,
                {"budget": budget, "reserve_agent_call": budget.call},
            )
        )

    assert client.calls == 0
    assert metrics.model_calls == 0


def test_native_workflow_unwraps_structured_agent_response_values():
    response = AgentResponse(messages=[Message("assistant", ['{"stage_id": "stage-1"}'])], response_format={"type": "object"})

    assert _workflow_output_value(response) == {"stage_id": "stage-1"}


def test_native_workflow_unwraps_wrapped_json_text_and_preserves_prose():
    response = AgentResponse(messages=[Message("assistant", ['{"stage_id": "stage-1"}'])])
    wrapped = SimpleNamespace(agent_response=response)
    prose = AgentResponse(messages=[Message("assistant", ["plain text"])])

    assert _workflow_output_value(wrapped) == {"stage_id": "stage-1"}
    assert _workflow_output_value(prose) == "plain text"
    assert decode_stage_output(wrapped) == {"stage_id": "stage-1"}


def test_native_workflow_decodes_json_text_in_structured_value():
    response = SimpleNamespace(value='{"stage_id": "stage-1"}', text="")

    assert decode_stage_output(response) == {"stage_id": "stage-1"}


def test_handoff_uses_native_builder_and_allowed_route():
    client = FakeChatClient()
    agents = [client.as_agent(id=f"participant-{i}", instructions="test", require_per_service_call_history_persistence=True) for i in (1, 2)]
    workflow = HandoffBuilder(participants=agents, output_from="all").with_start_agent(agents[0]).add_handoff(agents[0], [agents[1]]).build()
    assert len(workflow.get_executors_list()) >= 2


def test_structured_tool_handoff_preserves_native_routing(monkeypatch):
    captured = {}

    class ToolAgent:
        def __init__(self, agent_id):
            self.id = agent_id
            self.client = SimpleNamespace()
            self.default_options = {"tools": [object()]}

        async def close(self):
            return None

    class ToolClient:
        def as_agent(self, **kwargs):
            agent = ToolAgent(kwargs["id"])
            captured.setdefault("agents", []).append(agent)
            return agent

    class Workflow:
        async def run(self, prompt):
            captured["prompt"] = prompt
            return SimpleNamespace(get_outputs=lambda: ["participant-1"])

    class Builder:
        def __init__(self, participants, output_from):
            captured["participants"] = participants

        def with_start_agent(self, agent):
            captured["start_agent"] = agent.id
            return self

        def add_handoff(self, source, targets):
            captured["handoffs"] = [(source.id, tuple(target.id for target in targets))]
            return self

        def build(self):
            return Workflow()

    monkeypatch.setattr("agent_framework.orchestrations.HandoffBuilder", Builder)

    outputs = asyncio.run(
        _run_native_stage(
            ExecutionPattern.HANDOFF,
            "hello",
            ToolClient(),
            [
                {"id": "participant-1", "purpose": "one", "handoff_targets": ("participant-2",)},
                {"id": "participant-2", "purpose": "two"},
                {"id": "participant-3", "purpose": "three"},
            ],
            run_context={"require_structured_output": True, "structured_output_schema": {"type": "object"}},
        )
    )

    assert outputs == ["participant-1"]
    assert captured["start_agent"] == "participant-1"
    assert captured["handoffs"] == [("participant-1", ("participant-2",))]


def test_composed_native_stages_pass_outputs_and_settle_metrics():
    result = asyncio.run(
        run_recipe_async(
            _recipe((ExecutionPattern.CONCURRENT, ExecutionPattern.GROUP_CHAT, ExecutionPattern.SEQUENTIAL)),
            "hello",
            FakeChatClient(),
            "composed",
        )
    )
    assert result.outputs
    assert result.metrics.branches == 2
    assert result.metrics.chat_rounds == 4
    assert result.metrics.cleanup_complete


def test_stage_call_limits_do_not_shrink_run_wide_call_budget():
    base = make_recipe(RecipeName.DIRECT)
    stages = (
        RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "one"},), "typed-result", "typed-result", {"max_total_agent_calls": 1}),
        RecipeStage("stage-2", ExecutionPattern.DIRECT, ({"id": "two"},), "typed-result", "typed-result", {"max_total_agent_calls": 1}),
    )
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        2,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=stages,
    )
    client = CountingChatClient()

    result = asyncio.run(run_recipe_async(recipe, "hello", client, "stage-local-budget"))

    assert result.metrics.runtime_status == "SETTLED"
    assert client.calls == 2


def test_multi_participant_stage_synthesizes_typed_outputs_before_commit():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    from foresight_os.runtime.workflow import _synthesize_stage_outputs

    result = _synthesize_stage_outputs(
        stage,
        [
            {"evidence": [{"id": "e1"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
            {"evidence": [{"id": "e2"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
        ],
    )

    assert [item["id"] for item in result["evidence"]] == ["e1", "e2"]


def test_multi_participant_stage_deduplicates_identical_canonical_records():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    result = _synthesize_stage_outputs(
        stage,
        [
            {"evidence": [{"id": "e1", "statement": "same"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
            {"evidence": [{"id": "e1", "statement": "same"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
        ],
    )

    assert result["evidence"] == [{"id": "e1", "statement": "same"}]


def test_multi_participant_stage_rejects_conflicting_canonical_records():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )

    with pytest.raises(ValidationError, match="conflicting canonical record"):
        _synthesize_stage_outputs(
            stage,
            [
                {"evidence": [{"id": "e1", "statement": "first"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
                {"evidence": [{"id": "e1", "statement": "second"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
            ],
        )


def test_multi_participant_stage_deduplicates_equivalent_records_with_different_aliases():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    common = {
        "contract": "analysis-stage-result/v1",
        "stage_id": "stage-1",
        "calculations": [],
        "claims": [],
        "implications": [],
        "recommendations": [],
        "artifacts": [],
        "relationships": [],
        "assumptions": [],
        "uncertainty": [],
        "monitoring_indicators": [],
        "evidence": [{
            "source_locator": {"file_version": "workbook-v1", "sheet": "Summary", "range": "B2", "units": "percent", "transformation": "none", "calculation": "observed"},
            "version": "v1",
            "date": "2026-01-01",
            "excerpt": "same signal",
            "limitations": [],
            "measurement_key": None,
        }],
    }
    first = {**common, "evidence": [{**common["evidence"][0], "id": "analyst-evidence"}]}
    second = {**common, "evidence": [{**common["evidence"][0], "id": "reviewer-evidence"}]}

    result = _synthesize_stage_outputs(stage, [first, second])

    assert len(result["evidence"]) == 1


def test_multi_participant_typed_synthesis_allows_cross_participant_relationships():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    first = {
        "contract": "analysis-stage-result/v1",
        "stage_id": "stage-1",
        "evidence": [{
            "id": "evidence-one",
            "source_locator": {"file_version": "v1", "sheet": "Summary", "range": "A1", "units": "count", "transformation": "none", "calculation": "observed"},
            "version": "v1",
            "date": "2026-10-16",
            "excerpt": "First participant evidence.",
            "limitations": [],
        }],
        "calculations": [], "claims": [], "implications": [], "recommendations": [], "artifacts": [],
        "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": [],
    }
    second = {
        "contract": "analysis-stage-result/v1",
        "stage_id": "stage-1",
        "evidence": [],
        "calculations": [],
        "claims": [{
            "id": "claim-two",
            "statement": "The first participant evidence supports this claim.",
            "basis": "DERIVED",
            "assessment": "UNASSESSED",
            "evidence_ids": ["evidence-one"],
            "relationship_ids": ["relationship-two"],
        }],
        "implications": [], "recommendations": [], "artifacts": [],
        "relationships": [{
            "id": "relationship-two",
            "from_id": "evidence-one",
            "to_id": "claim-two",
            "relation_type": "supports",
        }],
        "assumptions": [], "uncertainty": [], "monitoring_indicators": [],
    }

    result = _synthesize_stage_outputs(stage, [first, second])

    assert len(result["relationships"]) == 1
    assert result["claims"][0]["relationship_ids"] == [result["relationships"][0]["id"]]


def test_typed_participant_peer_kinds_preserve_implication_and_recommendation_relationships():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}, {"id": "three"}),
        "typed-result",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    evidence = _typed_stage_result("stage-1", "evidence-one", "Observed evidence")
    implication = _typed_stage_result("stage-1", "evidence-placeholder", "Implication placeholder")
    implication["evidence"] = []
    implication["claims"] = []
    implication["relationships"] = [{
        "id": "supports-implication",
        "from_id": "evidence-one",
        "to_id": "implication-two",
        "relation_type": "supports",
    }]
    implication["implications"] = [_analytical_record("implication-two", "The evidence supports an implication.", evidence_ids=["evidence-one"], relationship_ids=["supports-implication"])]
    recommendation = _typed_stage_result("stage-1", "evidence-placeholder-2", "Recommendation placeholder")
    recommendation["evidence"] = []
    recommendation["claims"] = []
    recommendation["relationships"] = [{
        "id": "informs-recommendation",
        "from_id": "implication-two",
        "to_id": "recommendation-three",
        "relation_type": "informs",
    }]
    recommendation["recommendations"] = [_analytical_record("recommendation-three", "The implication informs a recommendation.", relationship_ids=["informs-recommendation"])]

    result = _synthesize_stage_outputs(stage, [evidence, implication, recommendation])

    assert {item["relation_type"] for item in result["relationships"]} == {"supports", "informs"}
    assert {item["to_id"] for item in result["relationships"]} == {
        result["claims"][0]["id"],
        result["implications"][0]["id"],
        result["recommendations"][0]["id"],
    }


def test_admitted_native_execution_validates_the_approved_recipe_snapshot():
    recipe = _recipe((ExecutionPattern.SEQUENTIAL,))

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "hello",
            FakeChatClient(),
            "approved-native",
            {
                "execution_admitted": True,
                "approved_recipe_fingerprint": canonical_json_hash(recipe.to_dict()),
            },
        )
    )

    assert result.outputs


def test_stage_context_binds_recipe_contract_and_structured_output_mode():
    captured = {}

    def committer(stage, output, context):
        captured.update(context)
        canonical = {"stage_id": stage.stage_id, "output": output}
        return CanonicalStageResult(("canonical-1",), (_canonical_result_hash(canonical),), canonical)

    recipe = _recipe((ExecutionPattern.SEQUENTIAL,))
    asyncio.run(
        run_recipe_async(
            recipe,
            "hello",
            FakeChatClient(),
            "contract-context",
            {
                "require_structured_output": True,
                "canonical_result_committer": committer,
            },
        )
    )

    assert captured["result_contract"] == "analysis-stage-result/v1"
    assert captured["require_structured_output"] is True
    assert captured["structured_output_schema"]["json_schema"]["schema"]["additionalProperties"] is False


def test_handoff_metrics_report_observed_transfer_not_recipe_shape():
    result = asyncio.run(
        run_recipe_async(
            _recipe((ExecutionPattern.HANDOFF,)),
            "hello",
            FakeChatClient(),
            "handoff-metrics",
        )
    )

    assert result.metrics.model_calls == 1
    assert result.metrics.handoffs == 0


def test_handoff_metrics_count_real_transfer_event(monkeypatch):
    class TransferAgent:
        def __init__(self, agent_id):
            self.id = agent_id

        async def close(self):
            return None

    class TransferClient:
        def as_agent(self, **kwargs):
            return TransferAgent(kwargs["id"])

    class TransferStream:
        def __aiter__(self):
            async def events():
                yield SimpleNamespace(type="executor_invoked", executor_id="participant-1")
                yield SimpleNamespace(type="handoff_sent", executor_id=None)

            return events()

        async def get_final_response(self):
            return SimpleNamespace(get_outputs=lambda: ["transferred"])

    class TransferWorkflow:
        async def run(self, prompt, stream=False):
            return TransferStream()

    class TransferBuilder:
        def __init__(self, **kwargs):
            pass

        def with_start_agent(self, agent):
            return self

        def add_handoff(self, source, targets):
            return self

        def build(self):
            return TransferWorkflow()

    monkeypatch.setattr("agent_framework.orchestrations.HandoffBuilder", TransferBuilder)
    metrics = RunMetrics("handoff-transfer", "HANDOFF", "handoff")
    outputs = asyncio.run(_run_native_stage(ExecutionPattern.HANDOFF, "hello", TransferClient(), [{"purpose": "one"}, {"purpose": "two"}], metrics))

    assert outputs == ["transferred"]
    assert metrics.handoffs == 1


def test_group_chat_metrics_report_observed_rounds():
    result = asyncio.run(
        run_recipe_async(
            _recipe((ExecutionPattern.GROUP_CHAT,)),
            "hello",
            FakeChatClient(),
            "group-chat-metrics",
        )
    )

    assert result.metrics.chat_rounds == 4


def test_native_group_chat_receives_effective_round_limit_and_charges_observed_rounds(monkeypatch):
    captured = {}

    class GroupChatRequestSentEvent:
        def __init__(self, round_index):
            self.round_index = round_index

    class Stream:
        def __aiter__(self):
            async def events():
                yield SimpleNamespace(type="group_chat", data=GroupChatRequestSentEvent(0))
                yield SimpleNamespace(type="group_chat", data=GroupChatRequestSentEvent(1))

            return events()

        async def get_final_response(self):
            return SimpleNamespace(get_outputs=lambda: ["native"])

    class Workflow:
        async def run(self, prompt, stream=False):
            return Stream()

    class Builder:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def build(self):
            return Workflow()

    monkeypatch.setattr("agent_framework.orchestrations.GroupChatBuilder", Builder)
    metrics = RunMetrics("native-rounds", "GROUP_CHAT", "group_chat")
    budget = BudgetState(5, 1, 5, max_rounds=2)
    outputs = asyncio.run(
        _run_native_stage(
            ExecutionPattern.GROUP_CHAT,
            "hello",
            FakeChatClient(),
            [{"purpose": "one"}, {"purpose": "two"}],
            metrics,
            {"budget": budget, "max_rounds": 2},
        )
    )

    assert outputs == ["native"]
    assert captured["max_rounds"] == 2
    assert metrics.chat_rounds == 2
    assert budget.rounds == 2


def test_close_agents_attempts_every_agent_and_reports_failures():
    class Closeable:
        def __init__(self, fails=False):
            self.fails = fails
            self.closed = False

        async def close(self):
            self.closed = True
            if self.fails:
                raise RuntimeError("close failed")

    first = Closeable(fails=True)
    second = Closeable()

    errors = asyncio.run(_close_agents([first, second]))

    assert first.closed and second.closed
    assert len(errors) == 1


def test_fallback_execution_does_not_claim_handoff_without_native_client():
    result = asyncio.run(
        run_recipe_async(
            _recipe((ExecutionPattern.HANDOFF,)),
            "hello",
            None,
            "fallback-handoff",
        )
    )

    assert result.metrics.handoffs == 0
