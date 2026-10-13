import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.runtime.capabilities import CapabilityResolver
from foresight_os.runtime.local_toolbelt import bind_local_toolbelt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    args = parser.parse_args()
    semantic_ids = ("web_search", "page_retrieval", "web_crawl", "technology_signals", "market_signals", "macro_signals", "spreadsheet_read", "data_analysis", "calculation", "graph_context", "domain_validation", "document_read", "internal_knowledge", "artifact_generation")
    local = bind_local_toolbelt()
    resolved = CapabilityResolver().resolve(semantic_ids, {"local_capabilities": local, "participant_data_scope": ("local", "public")})
    receipt = {
        "mode": "toolbelt",
        "status": "verified" if all(resolved[name].available for name in local) and all(not resolved[name].available for name in ("document_read", "internal_knowledge", "artifact_generation")) else "failed",
        "available": sorted(name for name, item in resolved.items() if item.available),
        "unavailable": sorted(name for name, item in resolved.items() if not item.available),
        "resolution_side_effect_free": True,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "toolbelt-probe.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
