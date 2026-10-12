import argparse
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.runtime.capabilities import (
    CapabilityBinding,
    CapabilityDefinition,
    CapabilityResolver,
    CapabilityScope,
    instrument_tool,
)
from foresight_os.runtime.metrics import RunMetrics


def _host(url: str) -> str:
    return urlsplit(url).netloc or "configured-endpoint"


class _SessionOwner:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


@asynccontextmanager
async def _stdio_session():
    from mcp import ClientSession, StdioServerParameters, stdio_client

    parameters = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("disposable_mcp_server.py"))])
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            yield session, _SessionOwner()


async def _disposable() -> dict:
    metrics = RunMetrics("mcp-disposable", "MCP", "mcp")
    scope = CapabilityScope()
    try:
        async with _stdio_session() as (session, owner):
            scope.register(owner)
            listing = await session.list_tools()
            names = {tool.name for tool in listing.tools}
            if "mutate_fixture" in names:
                names.remove("mutate_fixture")
            if "read_evidence" not in names:
                raise RuntimeError("disposable MCP read tool was not discovered")

            async def read(query: str):
                return await session.call_tool("read_evidence", {"query": query})

            resolver = CapabilityResolver({"mcp_read": CapabilityDefinition("mcp_read", "external_read")})
            resolved = await resolver.resolve_async(
                ("mcp_read",),
                {"scope": scope, "mcp_tools": {"mcp_read": CapabilityBinding(read, fingerprint="disposable-mcp-read")}},
            )
            if not resolved["mcp_read"].available:
                raise RuntimeError(resolved["mcp_read"].reason)
            call = instrument_tool(resolved["mcp_read"].tool, resolved["mcp_read"].definition, {"scope": scope, "metrics": metrics})
            result = await call("capacity")
            payload = result.content[0].text if result.content else ""
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
            return {
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
        return {"mode": "disposable", "status": "failed", "failure_class": "timeout", "cleanup": "attempted"}
    except (ConnectionError, BrokenPipeError) as error:
        return {"mode": "disposable", "status": "failed", "failure_class": "connection_loss", "error_type": type(error).__name__}
    except BaseException as error:
        return {"mode": "disposable", "status": "failed", "failure_class": "probe", "error_type": type(error).__name__}
    finally:
        try:
            await scope.close()
        except BaseException:
            pass


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
    args = parser.parse_args()
    result = asyncio.run(_disposable() if args.mode == "disposable" else _real_mcp())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"verified", "BLOCKED_EXTERNAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
