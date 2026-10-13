import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[2]
if "--installed" not in sys.argv:
    sys.path.insert(0, str(ROOT / "src"))

from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.runtime.capabilities import (
    CapabilityDefinition,
    CapabilityScope,
    instrument_tool,
)
from foresight_os.runtime.metrics import RunMetrics


def _host(url: str) -> str:
    return urlsplit(url).netloc or "configured-endpoint"


async def _disposable() -> dict:
    metrics = RunMetrics("mcp-disposable", "MCP", "mcp")
    scope = CapabilityScope()
    result: dict[str, object] = {"mode": "disposable", "status": "failed", "cleanup": "not-attempted"}
    try:
        from agent_framework import MCPStdioTool

        agent_tool = MCPStdioTool(
            "disposable",
            sys.executable,
            args=[str(Path(__file__).with_name("disposable_mcp_server.py"))],
            load_prompts=False,
            allowed_tools=("read_evidence",),
        )
        scope.register(agent_tool)
        await agent_tool.connect()
        names = {function.name for function in agent_tool.functions}
        if "read_evidence" not in names or "mutate_fixture" in names:
            raise RuntimeError("read-only MCP boundary exposed the wrong tool set")
        read_function = next(function for function in agent_tool.functions if function.name == "read_evidence")

        async def read(query: str):
            return await read_function.invoke(arguments={"query": query})

        call = instrument_tool(
            read,
            CapabilityDefinition("mcp_read", "external_read"),
            {"scope": scope, "metrics": metrics},
        )
        result_content = await call(query="capacity")
        payload = result_content[0].text if result_content else ""
        candidate = normalize_evidence_candidate(
            {
                "candidate_id": "disposable-mcp-capacity",
                "capability_id": "mcp_read",
                "source": "disposable-mcp",
                "request": "capacity",
                "excerpt": "Capacity remains uncertain.",
                "retrieved_at": "2030-01-01T00:00:00Z",
                "provenance": {"source_version": "fixture-v1", "date": "2030-01-01"},
                "raw_result": payload,
            }
        )
        result = {
            "mode": "disposable",
            "status": "verified",
            "source": "disposable-mcp",
            "discovered_read_tool": "read_evidence" in names,
            "mutation_tool_refused": "mutate_fixture" not in names,
            "candidate_id": candidate.id,
            "tool_calls": metrics.tool_calls,
            "cleanup": "scope-owned-session",
            "raw_payload_retained": False,
        }
    except asyncio.TimeoutError:
        result = {"mode": "disposable", "status": "failed", "failure_class": "timeout", "cleanup": "attempted"}
    except (ConnectionError, BrokenPipeError) as error:
        result = {"mode": "disposable", "status": "failed", "failure_class": "connection_loss", "error_type": type(error).__name__}
    except BaseException as error:
        result = {"mode": "disposable", "status": "failed", "failure_class": "probe", "error_type": type(error).__name__}
    finally:
        try:
            await scope.close()
            result["cleanup"] = "scope-owned-session"
        except BaseException as error:
            result = {**result, "status": "failed", "failure_class": "cleanup", "cleanup": "failed", "error_type": type(error).__name__}
    return result


async def _real_mcp() -> dict:
    url = os.getenv("FORESIGHT_REAL_MCP_URL")
    token = os.getenv("FORESIGHT_REAL_MCP_TOKEN")
    query = os.getenv("FORESIGHT_REAL_MCP_QUERY")
    if not all((url, token, query)):
        return {"mode": "real-mcp", "status": "BLOCKED_EXTERNAL", "blocker": "FORESIGHT_REAL_MCP_URL/TOKEN/QUERY not fully configured"}
    return {
        "mode": "real-mcp",
        "status": "BLOCKED_EXTERNAL",
        "blocker": "real MCP adapter is environment-approved only; configure the provider adapter before invocation",
        "endpoint_host": _host(url),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("disposable", "real-mcp"), required=True)
    parser.add_argument("--installed", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    result = asyncio.run(_disposable() if args.mode == "disposable" else _real_mcp())
    if args.output_root is not None:
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / f"mcp-{args.mode}-probe.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"verified", "BLOCKED_EXTERNAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
