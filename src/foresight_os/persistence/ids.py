import hashlib
import json
from typing import Any


def deterministic_id(kind: str, value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(f"{kind}:{payload}".encode("utf-8")).hexdigest()[:16]
    return f"{kind.lower()}-{digest}"


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
