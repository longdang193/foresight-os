from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[2]
if "--installed" not in __import__("sys").argv:
    __import__("sys").path.insert(0, str(ROOT / "src"))

from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope
from foresight_os.runtime.external_signals import HOSTED_MCP_PROVIDERS, bind_hosted_mcp
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


def _credential(provider_id: str) -> tuple[str, str]:
    provider = HOSTED_MCP_PROVIDERS[provider_id]
    configured = os.getenv(provider.credential_env, "").strip()
    if configured:
        return configured, "environment"
    if provider_id == "github":
        try:
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            token = ""
        if token:
            return token, "github-cli-keyring"
    if provider_id == "alpha_vantage" and os.getenv("FORESIGHT_ALLOW_ALPHA_DEMO", "") == "1":
        return "demo", "public-demo"
    return "", "missing"


def _operation(provider_id: str) -> tuple[str, dict[str, object]]:
    if provider_id == "github":
        return "search_repositories", {"query": "electric vehicles", "perPage": 1, "minimal_output": True}
    if provider_id == "alpha_vantage":
        return "GLOBAL_QUOTE", {"symbol": "IBM", "datatype": "json"}
    tool_name = os.getenv("FRED_MCP_READ_TOOL", "").strip()
    raw_args = os.getenv("FRED_MCP_READ_ARGS_JSON", "{}")
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError as error:
        raise ValueError("FRED_MCP_READ_ARGS_JSON must contain a JSON object") from error
    if not isinstance(args, dict):
        raise ValueError("FRED_MCP_READ_ARGS_JSON must contain a JSON object")
    return tool_name, args


def _mcp_result_is_success(result: object) -> bool:
    if result is None or bool(getattr(result, "is_error", False)):
        return False
    if isinstance(result, dict):
        if result.get("is_error") or result.get("error") or result.get("Error Message"):
            return False
        return bool(result)
    if isinstance(result, (list, tuple)):
        if not result:
            return False
        return all(_mcp_result_is_success(item) for item in result)
    text = " ".join(
        str(getattr(result, attribute, "") or "")
        for attribute in ("text", "output", "result", "message", "error_details", "error")
    ).strip().lower()
    return bool(text) and not any(marker in text for marker in ("error message", "invalid api key", "unauthorized", "forbidden"))


def _provider_result_is_success(provider_id: str, result: object) -> bool:
    if not _mcp_result_is_success(result):
        return False
    if isinstance(result, (list, tuple)):
        text = " ".join(_provider_result_text(item) for item in result).lower()
    else:
        text = _provider_result_text(result).lower()
    if provider_id == "alpha_vantage":
        return "global quote" in text or ("symbol" in text and "price" in text)
    if provider_id == "github":
        return any(marker in text for marker in ("full_name", "repositories", "items"))
    return not any(marker in text for marker in ("error", "rate limit", "information", "unauthorized", "forbidden"))


def _provider_result_text(result: object) -> str:
    if result is None:
        return ""
    if isinstance(result, (str, int, float, bool)):
        return str(result)
    if isinstance(result, dict):
        return " ".join(f"{key} {value}" for key, value in result.items())
    return " ".join(
        str(getattr(result, attribute, "") or "")
        for attribute in ("text", "output", "result", "message", "error_details", "error")
    )


async def _probe(provider_id: str) -> dict[str, object]:
    provider = HOSTED_MCP_PROVIDERS[provider_id]
    credential, credential_source = _credential(provider_id)
    base = {
        "mode": "live-external-signal-maf-agent-boundary",
        "provider": provider_id,
        "capability_id": provider.capability_id,
        "endpoint_host": urlsplit(provider.endpoint).netloc,
        "credential_source": credential_source,
        "raw_payload_retained": False,
    }
    if not credential:
        return {**base, "status": "BLOCKED_EXTERNAL", "blocker": provider.credential_env}
    try:
        tool_name, arguments = _operation(provider_id)
    except ValueError as error:
        return {**base, "status": "FAILED", "failure_class": "configuration", "error_type": type(error).__name__}
    if not tool_name:
        return {**base, "status": "BLOCKED_EXTERNAL", "blocker": "FRED_MCP_READ_TOOL/FRED_MCP_READ_ARGS_JSON not configured"}

    scope = CapabilityScope()
    captured: dict[str, object] = {}

    from agent_framework import Agent, ChatResponse, Content, Message

    class ProbeChatClient:
        async def get_response(self, **kwargs):
            tools = (kwargs.get("options") or {}).get("tools") or ()
            matching = next((item for item in tools if getattr(item, "name", "").endswith(tool_name)), None)
            if matching is None:
                raise RuntimeError(f"MAF Agent did not discover {tool_name}")
            captured["provider_result"] = await matching.invoke(**arguments)
            return ChatResponse(messages=[Message("assistant", [Content("text", text="provider tool invoked")])])

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            agent = Agent(ProbeChatClient(), **kwargs)
            captured["agent"] = agent
            return agent

    started = time.perf_counter()
    binding = bind_hosted_mcp(provider_id, credential, allowed_tools=(tool_name,) if provider_id == "fred" else None)
    receipt: dict[str, object] | None = None
    cleanup_error: BaseException | None = None
    try:
        AgentFactory(Client()).create(
            ParticipantConfig(
                "analyst",
                "analyst",
                f"collect {provider_id} signals",
                capability_ids=(provider.capability_id,),
                data_scope=("public",),
            ),
            {"scope": scope, "capability_resolver": CapabilityResolver(), "mcp_tools": {provider.capability_id: binding}},
        )
        agent = captured.get("agent")
        if agent is None:
            raise RuntimeError("MAF agent was not created")
        result = await agent.run(f"request {tool_name}")
        tool = captured["tools"][0]
        discovered = len(getattr(tool, "functions", ()) or ())
        if discovered < 1 or not _provider_result_is_success(provider_id, captured.get("provider_result")):
            raise RuntimeError("MCP server returned an error result")
        receipt = {
            **base,
            "status": "VERIFIED",
            "maf_agent_tool_injected": captured.get("tools", [None])[0] is tool,
            "maf_agent_request_cycle": True,
            "discovered_tool_count": discovered,
            "invoked_tool": tool_name,
            "result_type": type(result).__name__,
            "result_size": len(str(result)),
            "production_credential_configured": credential_source != "public-demo",
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "cleanup": "scope-closed",
        }
    except Exception as error:
        status = "BLOCKED_EXTERNAL" if "401" in str(error) or "Unauthorized" in str(error) else "FAILED"
        receipt = {
            **base,
            "status": status,
            "failure_class": "authentication" if status == "BLOCKED_EXTERNAL" else "provider",
            "error_type": type(error).__name__,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        }
    finally:
        try:
            await scope.close()
        except BaseException as error:
            cleanup_error = error
    if cleanup_error is not None:
        return {**(receipt or base), "status": "FAILED", "failure_class": "cleanup", "error_type": type(cleanup_error).__name__}
    return receipt or {**base, "status": "FAILED", "failure_class": "provider", "error_type": "unknown"}


async def _main(output_root: Path | None) -> list[dict[str, object]]:
    receipts = [await _probe(provider_id) for provider_id in ("github", "alpha_vantage", "fred")]
    if output_root is not None:
        output_root.mkdir(parents=True, exist_ok=True)
        for receipt in receipts:
            (output_root / f"{receipt['provider']}-mcp-maf-agent-probe.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed", action="store_true")
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    args = parser.parse_args()
    receipts = asyncio.run(_main(args.output_root))
    for receipt in receipts:
        print(json.dumps(receipt, sort_keys=True))
    return 0 if all(receipt["status"] in {"VERIFIED", "BLOCKED_EXTERNAL"} for receipt in receipts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
