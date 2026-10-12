import importlib.util
import asyncio

from .capabilities import (
    CapabilityDecision,
    CapabilityResult,
    DEFERRED_CAPABILITIES,
    REQUIRED_CAPABILITIES,
    VerticalSliceGuardrail,
)


def maf_package_available() -> bool:
    return importlib.util.find_spec("agent_framework") is not None


def checkpoint_round_trip() -> bool:
    from agent_framework import InMemoryCheckpointStorage, WorkflowCheckpoint

    async def run() -> bool:
        storage = InMemoryCheckpointStorage()
        checkpoint = WorkflowCheckpoint(
            workflow_name="foresight-probe",
            graph_signature_hash="probe-topology-v1",
            state={"probe": "ok"},
        )
        checkpoint_id = await storage.save(checkpoint)
        restored = await storage.load(checkpoint_id)
        return restored.state == checkpoint.state

    return asyncio.run(run())


def probe_capabilities() -> tuple[CapabilityResult, ...]:
    available = maf_package_available()
    if not available:
        required = tuple(
            CapabilityResult(
                name,
                CapabilityDecision.UNSUPPORTED,
                False,
                "agent_framework is not installed; dependency installation is an approval boundary.",
            )
            for name in REQUIRED_CAPABILITIES
        )
    else:
        from agent_framework import Agent, AgentExecutorRequest, WorkflowBuilder

        checkpoint_ok = checkpoint_round_trip()
        native = {
            "single_agent": CapabilityResult(
                "single_agent",
                CapabilityDecision.ADAPT_AT_BOUNDARY,
                True,
                f"Agent API imported; provider execution is not exercised. {Agent.__name__} is available.",
            ),
            "sequential_review": CapabilityResult(
                "sequential_review",
                CapabilityDecision.USE_NATIVE,
                True,
                f"WorkflowBuilder chaining API imported: {WorkflowBuilder.__name__}.",
            ),
            "human_input": CapabilityResult(
                "human_input",
                CapabilityDecision.ADAPT_AT_BOUNDARY,
                True,
                f"HITL request boundary imported: {AgentExecutorRequest.__name__}.",
            ),
            "structured_output": CapabilityResult(
                "structured_output",
                CapabilityDecision.ADAPT_AT_BOUNDARY,
                True,
                "Agent.run exposes options for provider structured output; provider execution is not exercised.",
            ),
            "checkpoint_restart": CapabilityResult(
                "checkpoint_restart",
                CapabilityDecision.USE_NATIVE if checkpoint_ok else CapabilityDecision.UNSUPPORTED,
                checkpoint_ok,
                "WorkflowCheckpoint round-trip through InMemoryCheckpointStorage succeeded."
                if checkpoint_ok
                else "WorkflowCheckpoint round-trip failed.",
            ),
        }
        required = tuple(native[name] for name in REQUIRED_CAPABILITIES)
    deferred = tuple(
        CapabilityResult(
            name,
            CapabilityDecision.DEFER,
            False,
            "Deferred by the v0.1 scope; no implementation is admitted.",
        )
        for name in DEFERRED_CAPABILITIES
    )
    return required + deferred


def vertical_slice_guardrail() -> VerticalSliceGuardrail:
    return VerticalSliceGuardrail()
