import asyncio

from agent_framework import Agent, ChatResponse, Message
from agent_framework.orchestrations import HandoffBuilder

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.runtime.workflow import _run_native_stage, run_recipe_async


class FakeChatClient:
    additional_properties = {}

    async def get_response(self, messages, **kwargs):
        return ChatResponse(messages=[Message("assistant", ["ok"])])

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
        base.max_total_agent_calls,
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
    assert result.metrics.chat_rounds == 1
    assert result.metrics.cleanup_complete
