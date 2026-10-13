from __future__ import annotations

import hashlib
import json
import asyncio

from evaluation.probes.compare_optimization_receipts import compare
from foresight_os.analysis.ev_capacity_investment import _capacity_dependency_ids
from foresight_os.analysis.powerbi_strategic_portfolio import _forward_signal_index
from foresight_os.analysis.reviewer import review_analysis_state, review_reasoning
from foresight_os.analysis.technology_radar import _action
from foresight_os.domain.challenge import ReviewValidity, review_validity
from foresight_os.domain.models import AnalysisState, AnalyticalRecord, Assessment, Basis, CalculationRecord, Evidence, Invalidation, MeasurementKey, Revision, SourceLocator
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.analysis_store import StageReceipt
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.runtime.workflow import _canonical_provenance_matches, _canonical_result_hash, _committed_cache_output, _stage_cache_key, run_recipe_async


def _state(record: AnalyticalRecord, *, evidence: list[Evidence] | None = None, calculations: list[CalculationRecord] | None = None) -> AnalysisState:
    return AnalysisState("hardening", 1, evidence=evidence or [], claims=[record], revisions=[Revision("r1", 1, "test", [record.id])], invalidation=Invalidation(), calculations=calculations or [])


def test_merge_states_replaces_same_id_with_incoming_revision(tmp_path):
    evidence = Evidence("e1", SourceLocator("v1", "Sheet", "A1", "units", "none", "source"), "v1", "2026", "old")
    old = _state(AnalyticalRecord("claim", "old", Basis.OBSERVED, Assessment.SUPPORTED, evidence_ids=["e1"]), evidence=[evidence])
    new_evidence = Evidence("e1", evidence.source_locator, "v2", "2026", "new")
    new = _state(AnalyticalRecord("claim", "new", Basis.OBSERVED, Assessment.SUPPORTED, evidence_ids=["e1"]), evidence=[new_evidence])
    merged = AnalysisStore._merge_states(old, new)
    assert merged.claims[0].statement == "new"
    assert merged.evidence[0].excerpt == "new"


def test_receipt_reuse_requires_existing_untampered_canonical_records():
    record = {"id": "claim-1", "value": 42}
    expected = _canonical_result_hash(record)
    assert _canonical_provenance_matches(("claim-1",), (expected,), {"claim-1": record})
    assert not _canonical_provenance_matches(("missing",), (expected,), {"claim-1": record})
    assert not _canonical_provenance_matches(("claim-1",), (expected,), {"claim-1": {"id": "claim-1", "value": 43}})
    valid, output = _committed_cache_output(
        {"status": "committed", "provenance_complete": True, "result_references": ["claim-1"], "result_hashes": [expected], "output": {"tampered": True}},
        {"claim-1": record},
    )
    assert valid and output == record
    assert not _committed_cache_output(
        {"status": "committed", "provenance_complete": True, "result_references": ["missing"], "result_hashes": ["bogus"], "output": {"tampered": True}},
        None,
    )[0]


def test_rejected_receipt_cannot_fall_back_to_legacy_cache_entry():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds, base.max_total_agent_calls, base.completion, base.escalation, base.partial_result, stages=(stage,))
    output = {"stage": "old-scope"}
    record_hash = _canonical_result_hash(output)
    receipt = StageReceipt("first", _stage_cache_key(stage, "start", ()), authorization_scope_fingerprint="old-scope", result_references=("claim-1",), result_hashes=(record_hash,), status="committed", committed=True, provenance_complete=True)
    result = asyncio.run(run_recipe_async(recipe, "start", run_context={
        "stage_receipts": {"first": receipt},
        "canonical_outputs": {"first": {"tampered": True}},
        "canonical_records": {"claim-1": output},
        "stage_cache": {_stage_cache_key(stage, "start", ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-1"], "result_hashes": [record_hash], "output": output}},
        "authorization_scope_fingerprint": "new-scope",
    }))
    assert result.metrics.cache_hits == 0
    assert result.metrics.reassessed_stages == 1


def test_review_policy_is_resolved_and_blocks_calculation_error():
    evidence = Evidence("e1", SourceLocator("v1", "Sheet", "A1", "units", "none", "source"), "v1", "2026", "fact")
    record = AnalyticalRecord("claim-1", "formula is unsupported", Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=["e1"])
    review = review_reasoning([evidence], [record], policy=type("Policy", (), {"policy_id": "p", "version": "1", "required_skill_ids": ("skill",), "acceptable_outcomes": ("ACCEPTED",), "blocking_objection_kinds": ("CALCULATION_ERROR",), "unresolved_classification_issue": None})())
    assert not review.accepted
    assert review.policy_id == "p"
    reviewed = review_analysis_state(
        _state(
            record,
            evidence=[evidence],
            calculations=[CalculationRecord("c1", MeasurementKey("x", "y", "2026", "units"), "x", ["e1"], 1, "units", ["A1"])],
        )
    )
    assert reviewed.policy_id
    assert reviewed.skill_ids


def test_policy_bearing_review_fingerprint_is_current_after_attachment():
    evidence = Evidence("e1", SourceLocator("v1", "Sheet", "A1", "units", "none", "source"), "v1", "2026", "fact")
    record = AnalyticalRecord("claim-1", "A sourced claim", Basis.OBSERVED, Assessment.SUPPORTED, evidence_ids=["e1"])
    state = _state(record, evidence=[evidence])
    review = review_analysis_state(state)
    from foresight_os.analysis.evidence_workflow import attach_review_record
    attached = attach_review_record(state, review, "review-1")
    assert review_validity(attached, attached.review_records[0]) == ReviewValidity.CURRENT


def test_technology_action_changes_when_evidence_weakens():
    assert _action(4.8, 3, 5, 5, 4) == "Invest"
    assert _action(2.0, 3, 5, 5, 4) != "Invest"


def test_narrative_signal_does_not_change_segment_decision_index():
    rows = [
        {"Type": "Leading", "Segment": "A", "Change_Index": -0.2},
        {"Type": "Narrative", "Segment": "A", "Change_Index": 10.0},
    ]
    assert _forward_signal_index(rows, "A") == -0.2
    rows[1]["Change_Index"] = -10.0
    assert _forward_signal_index(rows, "A") == -0.2


def test_capacity_gap_dependencies_include_capacity_rows():
    rows = [(0, {"Year": 2030}), (1, {"Year": 2031})]
    evidence = {("Capacity", 0): Evidence("cap-2030", SourceLocator("v", "Capacity", "A1", "units", "none", "source"), "v", "2026", "capacity")}
    assert _capacity_dependency_ids(rows, evidence, 2030) == ("cap-2030",)


def _receipt(findings: int = 1, *, healthy: bool = True) -> dict:
    return {
        "schema_version": 1,
        "workload": {"fixture": "x", "fixture_sha256": "x"},
        "accepted_finding_count": findings,
        "stage_metrics": [{"failure_class": None if healthy else "provider"}],
        "resource": {"rss_bytes": 1},
        "maf_patterns": {"direct": {"cleanup_complete": healthy}},
        "xlsx": {"deterministic_key": "k", "p95_ms": 1, "peak_allocation_bytes": 1},
        "native_mcp": {"status": "VERIFIED" if healthy else "FAILED"},
        "soak": {"runs": 100 if healthy else 0, "resource_counts": {"owned_after_cleanup": 0 if healthy else 1}, "monotonic_growth": not healthy},
        "acceptance": {"soak_runs": 100},
    }


def test_optimization_comparison_rejects_zero_output_or_unhealthy_release():
    baseline = _receipt()
    assert not compare(baseline, _receipt(findings=0))["accepted"]
    assert not compare(baseline, _receipt(healthy=False))["accepted"]
    rss_regression = _receipt()
    rss_regression["resource"]["rss_bytes"] = 10**12
    assert not compare(baseline, rss_regression)["accepted"]
