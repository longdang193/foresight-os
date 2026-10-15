import asyncio

import pytest

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.runtime.capabilities import CapabilityDefinition, CapabilityResolver, CapabilityScope
from foresight_os.runtime.metrics import BudgetExceededError
from foresight_os.runtime.participants import ParticipantConfig
from foresight_os.runtime.workflow import run_recipe_async


def _tool(name):
    def capability(request: str = ""):
        return {"tool": name, "request": request}

    capability.__name__ = name
    return capability


class ToolClient:
    def __init__(self):
        self.agents = []

    def as_agent(self, **kwargs):
        self.agents.append(kwargs)
        return Agent(self, **kwargs)

    def get_response(self, messages, **kwargs):
        async def updates():
            yield ChatResponseUpdate(contents=[Content("text", text="normalized result")], role="assistant")

        if kwargs.get("stream"):
            return ResponseStream(
                updates(),
                finalizer=lambda _: ChatResponse(messages=[Message("assistant", ["normalized result"])]),
            )

        async def response():
            return ChatResponse(messages=[Message("assistant", ["normalized result"])] )

        return response()


def _recipe(pattern, participants):
    base = make_recipe(RecipeName.DIRECT)
    return ExecutionRecipe(
        base.name,
        pattern.value,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(RecipeStage("tool-stage", pattern, tuple(participants), "typed-result", "typed-result", {}),),
    )


@pytest.mark.parametrize("pattern", [ExecutionPattern.SEQUENTIAL, ExecutionPattern.CONCURRENT, ExecutionPattern.HANDOFF, ExecutionPattern.GROUP_CHAT])
def test_native_patterns_receive_only_assigned_capabilities(pattern):
    client = ToolClient()
    resolver = CapabilityResolver({
        "alpha": CapabilityDefinition("alpha", "local_deterministic"),
        "beta": CapabilityDefinition("beta", "local_deterministic"),
    })
    participants = [
        ParticipantConfig("participant-1", "analyst", "analyze", capability_ids=("alpha",)),
        ParticipantConfig("participant-2", "reviewer", "review", capability_ids=("beta",)),
    ]

    result = asyncio.run(
        run_recipe_async(
            _recipe(pattern, participants),
            "hello",
            client,
            f"tool-{pattern.value}",
            {"capability_resolver": resolver, "scope": CapabilityScope(), "local_capabilities": {"alpha": _tool("alpha"), "beta": _tool("beta")}},
        )
    )

    assert result.metrics.cleanup_complete
    assert [kwargs["tools"][0].capability_id for kwargs in client.agents] == ["alpha", "beta"]
    if pattern == ExecutionPattern.GROUP_CHAT:
        assert result.metrics.model_calls == 3
        assert result.metrics.chat_rounds == 3


def test_structured_tool_group_chat_charges_run_round_budget():
    base = make_recipe(RecipeName.DIRECT)
    participants = (
        ParticipantConfig("participant-1", "analyst", "analyze", capability_ids=("alpha",)),
    )
    stages = (
        RecipeStage("first", ExecutionPattern.GROUP_CHAT, participants, "typed-result", "typed-result", {}),
        RecipeStage("second", ExecutionPattern.GROUP_CHAT, participants, "typed-result", "typed-result", {}),
    )
    recipe = ExecutionRecipe(
        base.name,
        ExecutionPattern.GROUP_CHAT.value,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=stages,
    )
    resolver = CapabilityResolver({"alpha": CapabilityDefinition("alpha", "local_deterministic")})

    with pytest.raises(BudgetExceededError) as caught:
        asyncio.run(
            run_recipe_async(
                recipe,
                "hello",
                ToolClient(),
                "structured-group-budget",
                {
                    "max_rounds": 1,
                    "require_structured_output": True,
                    "structured_output_schema": {"type": "object"},
                    "capability_resolver": resolver,
                    "scope": CapabilityScope(),
                    "local_capabilities": {"alpha": _tool("alpha")},
                },
            )
        )

    assert caught.value.metrics.chat_rounds == 1
