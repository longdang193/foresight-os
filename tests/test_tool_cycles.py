import asyncio

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream

from foresight_os.controller.budgets import BudgetState
from foresight_os.controller.recipes import ExecutionPattern
from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.domain.models import CalculationRecord, MeasurementKey
from foresight_os.runtime.capabilities import (
    CapabilityBinding,
    CapabilityDefinition,
    CapabilityResolver,
    CapabilityScope,
)
from foresight_os.runtime.metrics import RunMetrics
from foresight_os.runtime.workflow import _run_native_stage


class ProtocolClient:
    additional_properties = {}

    def __init__(self):
        self.events: list[tuple[str, str]] = []

    def as_agent(self, **kwargs):
        return Agent(self, **kwargs)

    async def _tool_result(self, options):
        tools = options.get("tools", ())
        if not tools:
            self.events.append(("model_final", "no-tool"))
            return "no-tool"
        tool = tools[0]
        self.events.append(("model_tool_call", tool.name))
        result = await tool.invoke(arguments={"query": "capacity"})
        text = "\n".join(item.text or "" for item in result if item.type == "text")
        self.events.append(("tool_result", text))
        return text

    def get_response(self, messages, **kwargs):
        options = kwargs.get("options", {})
        if kwargs.get("stream"):
            async def updates():
                result = await self._tool_result(options)
                yield ChatResponseUpdate(contents=[Content("text", text=f"final:{result}")], role="assistant")

            return ResponseStream(
                updates(),
                finalizer=lambda _: ChatResponse(messages=[Message("assistant", ["completed"])]),
            )

        async def response():
            result = await self._tool_result(options)
            return ChatResponse(messages=[Message("assistant", [f"final:{result}"])])

        return response()


def _context(client, metrics, scope):
    async def retrieve(query: str) -> str:
        client.events.append(("tool_dispatch", query))
        return "public capacity result"

    resolver = CapabilityResolver({"web_search": CapabilityDefinition("web_search", "external_read")})
    return {
        "scope": scope,
        "metrics": metrics,
        "budget": BudgetState(10, 1, 10, max_tool_calls=10),
        "capability_resolver": resolver,
        "local_capabilities": {
            "web_search": CapabilityBinding(retrieve, fingerprint="test-web-search"),
        },
    }


def test_maf_tool_cycle_runs_through_native_patterns_and_scope_cleanup():
    for pattern in ExecutionPattern:
        client = ProtocolClient()
        metrics = RunMetrics(f"run-{pattern.value}", pattern.value, pattern.value)
        scope = CapabilityScope()
        roles = [
            {"id": "analyst", "role": "analyst", "purpose": "retrieve evidence", "capability_ids": ("web_search",)},
            {"id": "reviewer", "role": "reviewer", "purpose": "review result", "capability_ids": ("web_search",)},
        ]

        outputs = asyncio.run(_run_native_stage(pattern, "find capacity", client, roles, metrics, _context(client, metrics, scope)))
        asyncio.run(scope.close())

        assert outputs
        assert ("model_tool_call", "retrieve") in client.events
        assert ("tool_dispatch", "capacity") in client.events
        assert metrics.tool_calls >= 1
        assert metrics.cleanup_complete is False


def test_handoff_does_not_grant_sender_tool_to_receiver():
    client = ProtocolClient()
    metrics = RunMetrics("handoff", "HANDOFF", "handoff")
    scope = CapabilityScope()
    roles = [
        {"id": "sender", "role": "sender", "purpose": "retrieve evidence", "capability_ids": ("web_search",)},
        {"id": "receiver", "role": "receiver", "purpose": "review result", "capability_ids": ()},
    ]

    asyncio.run(_run_native_stage(ExecutionPattern.HANDOFF, "find capacity", client, roles, metrics, _context(client, metrics, scope)))
    asyncio.run(scope.close())

    assert [event for event in client.events if event[0] == "model_tool_call"] == [("model_tool_call", "retrieve")]


def test_external_candidate_is_typed_and_local_calculation_stays_a_calculation_record():
    evidence = normalize_evidence_candidate(
        {
            "candidate_id": "candidate-1",
            "capability_id": "web_search",
            "source": "public-source",
            "request": "capacity",
            "excerpt": "Capacity remains uncertain.",
            "query": "capacity",
            "context": "service network",
            "retrieved_at": "2030-01-01T00:00:00Z",
            "provenance": {"source_version": "v1", "date": "2030-01-01"},
            "raw_result": {"transient": True},
        }
    )
    calculation = CalculationRecord(
        "calculation-1",
        MeasurementKey("Northern Europe", "capacity", "2030", "index"),
        "a + b",
        ["a", "b"],
        3.0,
        "index",
        ["workbook.csv:A1"],
    )

    assert evidence.id == "candidate-1"
    assert not hasattr(evidence, "raw_result")
    assert calculation.output == 3.0
