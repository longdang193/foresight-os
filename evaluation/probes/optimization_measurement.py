from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from foresight_os.analysis.evidence_workflow import run_xlsx_finding_workflow
from foresight_os.domain.challenge import ReviewOutcome, ReviewRecord, build_material_fingerprint, derive_finding_views
from foresight_os.domain.models import AnalysisState
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection


SCHEMA_VERSION = 1


def process_rss_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.Process(os.getpid()).memory_info().rss)
    except Exception:
        return None


def observed_finding_views(state: AnalysisState | None) -> tuple[object, ...]:
    return derive_finding_views(state) if state is not None else ()


def accepted_finding_count(state: AnalysisState | None) -> int:
    return sum(1 for finding in observed_finding_views(state) if finding.accepted)


def observed_xlsx_state(fixture: Path, root: Path) -> AnalysisState | None:
    store = AnalysisStore(root / "finding-state")
    result = run_xlsx_finding_workflow(
        store,
        fixture,
        AnalysisOperation("aggregate", value_column="Value"),
        selection=SheetSelection(include_hidden=True, include_hidden_rows=True),
        human_decision="ACCEPT",
    )
    state = result.analysis
    if state is None:
        return None
    target_ids = tuple(item.id for item in [*state.claims, *state.implications, *state.recommendations])
    review = ReviewRecord(
        review_id="optimization-observed-review",
        target_ids=target_ids,
        reviewed_state_revision=state.revision,
        input_fingerprint=build_material_fingerprint(state, target_ids),
        outcome=ReviewOutcome.ACCEPTED,
    )
    return replace(state, review_records=[review])


def stage_metric(stage_id: str, pattern: str, result: Any, elapsed_ms: float) -> dict[str, Any]:
    metrics = getattr(result, "metrics", result)
    return {
        "stage_id": stage_id,
        "pattern": pattern,
        "wall_time_ms": round(elapsed_ms, 3),
        "model_calls": int(getattr(metrics, "model_calls", 0)),
        "tool_calls": int(getattr(metrics, "tool_calls", 0)),
        "cache_hits": int(getattr(metrics, "cache_hits", 0)),
        "reused_stages": int(getattr(metrics, "reused_stages", 0)),
        "reassessed_stages": int(getattr(metrics, "reassessed_stages", 0)),
        "failure_class": getattr(metrics, "failure_class", None),
    }


def build_receipt(
    *,
    mode: str,
    fixture: Path,
    workbook: dict[str, Any],
    patterns: dict[str, Any],
    soak: dict[str, Any],
    external_fixture: dict[str, Any],
    native_mcp: dict[str, Any],
    state: AnalysisState | None,
    stage_metrics: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "status": "VERIFIED" if native_mcp.get("status") == "VERIFIED" else "FAILED",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "workload": {"fixture": str(fixture), "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(), "warmups": 2, "measured_runs": 10},
        "acceptance": thresholds,
        "accepted_finding_count": accepted_finding_count(state),
        "xlsx": workbook,
        "maf_patterns": patterns,
        "stage_metrics": stage_metrics,
        "soak": soak,
        "external_fixture": external_fixture,
        "native_mcp": native_mcp,
        "resource": {"rss_bytes": process_rss_bytes()},
    }
