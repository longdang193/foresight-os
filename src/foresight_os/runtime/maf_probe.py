import importlib.util
import asyncio
import importlib.metadata
import json
import time
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .capabilities import (
    CapabilityDecision,
    CapabilityResult,
    DEFERRED_CAPABILITIES,
    REQUIRED_CAPABILITIES,
    VerticalSliceGuardrail,
)


def maf_package_available() -> bool:
    return importlib.util.find_spec("agent_framework") is not None


@dataclass(frozen=True)
class ProviderSettings:
    provider: str
    model: str
    base_url: str
    credential_env: str
    api_key: str = field(repr=False)


@dataclass(frozen=True)
class LiveProviderProbe:
    provider: str
    model: str
    base_url: str
    package_version: str
    success: bool
    structured_output: bool
    latency_ms: int | None = None
    response_length: int | None = None
    error_type: str | None = None


def load_provider_settings(env_file: Path, config_file: Path) -> ProviderSettings:
    assignments: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        if value:
            assignments[name] = value

    config = tomllib.loads(config_file.read_text(encoding="utf-8"))
    provider_name = config.get("model_provider")
    model = config.get("model")
    provider = config.get("model_providers", {}).get(provider_name, {})
    base_url = provider.get("base_url")
    credential_env = provider.get("credential_env") or f"{provider_name.upper().replace('-', '_')}_API_KEY"
    if not provider_name or not model or not base_url:
        raise ValueError("Codex config lacks model provider, model, or provider base URL")
    api_key = assignments.get(credential_env)
    if not api_key:
        raise ValueError(f"configured credential environment variable is missing: {credential_env}")
    return ProviderSettings(provider_name, model, base_url, credential_env, api_key)


def run_live_provider_probe(
    env_file: Path,
    config_file: Path,
    timeout_seconds: float = 25,
) -> LiveProviderProbe:
    settings = load_provider_settings(env_file, config_file)
    package_version = importlib.metadata.version("agent-framework")
    started = time.perf_counter()

    async def run() -> LiveProviderProbe:
        from typing import Literal
        from pydantic import BaseModel
        from agent_framework.openai import OpenAIChatClient

        class ProbeReply(BaseModel):
            status: Literal["ready"]

        client = OpenAIChatClient(
            model=settings.model,
            api_key=settings.api_key,
            base_url=settings.base_url,
        )
        agent = client.as_agent(instructions="Return JSON matching the requested schema.")
        try:
            response = await asyncio.wait_for(
                agent.run(
                    "Return status ready.",
                    options={"response_format": ProbeReply},
                ),
                timeout=timeout_seconds,
            )
            value = getattr(response, "value", None)
            text = getattr(response, "text", "") or ""
            return LiveProviderProbe(
                provider=settings.provider,
                model=settings.model,
                base_url=settings.base_url,
                package_version=package_version,
                success=getattr(value, "status", None) == "ready",
                structured_output=isinstance(value, ProbeReply),
                latency_ms=round((time.perf_counter() - started) * 1000),
                response_length=len(text),
            )
        except Exception as exc:
            return LiveProviderProbe(
                provider=settings.provider,
                model=settings.model,
                base_url=settings.base_url,
                package_version=package_version,
                success=False,
                structured_output=False,
                latency_ms=round((time.perf_counter() - started) * 1000),
                error_type=type(exc).__name__,
            )
        finally:
            await agent.close()

    return asyncio.run(run())


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
        from agent_framework.orchestrations import ConcurrentBuilder, GroupChatBuilder, HandoffBuilder, SequentialBuilder

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
        native.update({
            "pattern_sequential": CapabilityResult("pattern_sequential", CapabilityDecision.USE_NATIVE, True, SequentialBuilder.__name__),
            "pattern_concurrent": CapabilityResult("pattern_concurrent", CapabilityDecision.USE_NATIVE, True, ConcurrentBuilder.__name__),
            "pattern_handoff": CapabilityResult("pattern_handoff", CapabilityDecision.USE_NATIVE, True, HandoffBuilder.__name__),
            "pattern_group_chat": CapabilityResult("pattern_group_chat", CapabilityDecision.USE_NATIVE, True, GroupChatBuilder.__name__),
        })
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run one bounded live MAF provider probe")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument(
        "--config-file",
        type=Path,
        default=Path.home() / ".codex" / "config.toml",
    )
    parser.add_argument("--timeout-seconds", type=float, default=25)
    args = parser.parse_args()
    result = run_live_provider_probe(args.env_file, args.config_file, args.timeout_seconds)
    print(json.dumps(asdict(result), sort_keys=True))
    raise SystemExit(0 if result.success else 2)
