import argparse
import asyncio
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parents[2]
if "--installed" not in sys.argv:
    sys.path.insert(0, str(ROOT / "src"))

from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope
from foresight_os.runtime.crawl4ai import Crawl4AICapability, bind_crawl4ai
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


URL = "https://www.iea.org/reports/global-ev-outlook-2024"


async def main(output_root: Path | None) -> dict:
    captured: dict = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return type("Agent", (), {"id": kwargs["id"]})()

    started = time.perf_counter()
    scope = CapabilityScope()
    factory = AgentFactory(Client())
    factory.create(
        ParticipantConfig("analyst", "analyst", "crawl public reports", capability_ids=("web_crawl",), data_scope=("public",)),
        {
            "scope": scope,
            "capability_resolver": CapabilityResolver(),
            "adapters": {"web_crawl": bind_crawl4ai(Crawl4AICapability())},
        },
    )
    result = await captured["tools"][0](URL, "electric vehicle outlook")
    await scope.close()
    excerpt = result["excerpt"]
    receipt = {
        "mode": "live-crawl4ai-maf-agent-boundary",
        "status": "VERIFIED",
        "provider": "crawl4ai",
        "capability_id": result["capability_id"],
        "maf_agent_tool_injected": bool(captured.get("tools")),
        "tool_capability_id": getattr(captured["tools"][0], "capability_id", None),
        "url_host": urlsplit(URL).netloc,
        "url_path": urlsplit(URL).path,
        "content_hash": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "excerpt_chars": len(excerpt),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "raw_payload_retained": "raw_result" in result,
        "cleanup": "scope-closed",
    }
    if output_root is not None:
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / "crawl4ai-maf-agent-probe.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return receipt


def cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed", action="store_true")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.output_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
