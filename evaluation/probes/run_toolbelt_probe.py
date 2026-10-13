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
    local = bind_local_toolbelt()
    unavailable = ("document_read", "internal_knowledge", "artifact_generation")
    semantic_ids = tuple(sorted(set(local) | set(unavailable)))
    resolved = CapabilityResolver().resolve(semantic_ids, {"local_capabilities": local, "participant_data_scope": ("local", "public")})
    unknown_local = sorted(set(local) - set(resolved))
    receipt = {
        "mode": "toolbelt",
        "status": "verified" if not unknown_local and all(resolved[name].available for name in local) and all(not resolved[name].available for name in unavailable) else "failed",
        "available": sorted(name for name, item in resolved.items() if item.available),
        "unavailable": sorted(name for name, item in resolved.items() if not item.available),
        "unknown_local": unknown_local,
        "resolution_side_effect_free": True,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "toolbelt-probe.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
