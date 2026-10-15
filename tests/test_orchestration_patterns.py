import asyncio
from types import SimpleNamespace

import pytest

from agent_framework import Agent, AgentResponse, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
from agent_framework.orchestrations import HandoffBuilder

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.controller.budgets import BudgetState
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.domain.validation import ValidationError
from foresight_os.analysis.result_committer import decode_stage_output
from foresight_os.runtime.workflow import CanonicalStageResult, _canonical_result_hash, _close_agents, _run_native_stage, _synthesize_stage_outputs, _workflow_output_value, run_recipe_async
from foresight_os.runtime.metrics import RunMetrics


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


def test_handoff_uses_native_builder_and_allowed_route():
    client = FakeChatClient()
    agents = [client.as_agent(id=f"participant-{i}", instructions="test", require_per_service_call_history_persistence=True) for i in (1, 2)]
    workflow = HandoffBuilder(participants=agents, output_from="all").with_start_agent(agents[0]).add_handoff(agents[0], [agents[1]]).build()
    assert len(workflow.get_executors_list()) >= 2


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
