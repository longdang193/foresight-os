import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope, instrument_tool
from foresight_os.runtime.metrics import RunMetrics
from foresight_os.runtime.web_search import (
    WebSearchError,
    bind_web_search,
    load_configured_web_search_provider,
)


async def run(query: str) -> dict:
    provider = load_configured_web_search_provider()
    scope = CapabilityScope()
    metrics = RunMetrics("web-search-probe", "WEB_SEARCH", "web_search")
    try:
        resolved = await CapabilityResolver().resolve_async(
            ("web_search",),
            {
                "scope": scope,
                "adapters": {"web_search": bind_web_search(provider)},
                "metrics": metrics,
                "participant_data_scope": ("public",),
            },
        )
        capability = resolved["web_search"]
        if not capability.available or capability.tool is None:
            return {"mode": "web-search", "status": "BLOCKED_EXTERNAL", "blocker": capability.reason}
        results = await instrument_tool(capability.tool, capability.definition, {"scope": scope, "metrics": metrics})(query)
        return {
            "mode": "web-search",
            "status": "verified" if results else "failed",
            "provider": provider.name,
            "candidate_count": len(results),
            "candidate_ids": [item["candidate_id"] for item in results],
            "tool_calls": metrics.tool_calls,
            "cleanup": "scope-owned",
            "raw_payload_retained": any("raw_result" in item for item in results),
        }
    except WebSearchError as error:
        return {"mode": "web-search", "status": "failed", "failure_type": type(error).__name__}
    finally:
        try:
            await scope.close()
        except BaseException:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default=os.getenv("FORESIGHT_WEB_SEARCH_QUERY", ""))
    args = parser.parse_args()
    if not args.query:
        print(json.dumps({
            "mode": "web-search",
            "status": "BLOCKED_EXTERNAL",
            "blocker": "FORESIGHT_WEB_SEARCH_QUERY is not configured",
        }, sort_keys=True))
        return 0
    try:
        result = asyncio.run(run(args.query))
    except WebSearchError as error:
        result = {"mode": "web-search", "status": "BLOCKED_EXTERNAL", "blocker": str(error)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"verified", "BLOCKED_EXTERNAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
