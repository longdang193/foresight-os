import json
from dataclasses import asdict
import asyncio
from types import SimpleNamespace

import pytest

from foresight_os.analysis.result_committer import (
    ANALYSIS_STAGE_RESULT_CONTRACT,
    CanonicalResultCommitter,
    analysis_stage_result_schema,
    normalize_stage_result,
)
from foresight_os.domain.validation import ValidationError
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeStage, RecipeName, StageInput, make_recipe
from foresight_os.domain.models import AnalysisState, Revision, SourceLocator, Evidence
from foresight_os.runtime.workflow import _stage_cache_key, run_recipe_async


def _payload(**overrides):
    evidence = {
        "id": "provider-evidence",
        "source_locator": {
            "file_version": "workbook-v1",
            "sheet": "Summary",
            "range": "B2",
            "units": "percent",
            "transformation": "none",
            "calculation": "source value",
        },
        "version": "v1",
        "date": "2026-10-15",
        "excerpt": "Observed share is 42%.",
        "limitations": ["single period"],
    }
    payload = {
        "contract": ANALYSIS_STAGE_RESULT_CONTRACT,
        "stage_id": "stage-1",
        "evidence": [evidence],
        "calculations": [],
        "claims": [
            {
                "id": "provider-claim",
                "statement": "The observed share is material.",
                "basis": "OBSERVED",
                "assessment": "SUPPORTED",
                "evidence_ids": ["provider-evidence"],
                "relationship_ids": ["provider-support"],
            }
        ],
        "implications": [],
        "recommendations": [],
        "artifacts": [],
        "relationships": [
            {
                "id": "provider-support",
                "from_id": "provider-evidence",
                "to_id": "provider-claim",
                "relation_type": "supports",
            }
        ],
        "assumptions": [],
        "uncertainty": [],
        "monitoring_indicators": [],
    }
    payload.update(overrides)
    return payload


def test_valid_result_normalizes_with_system_owned_ids_and_round_trips_deterministically():
    first = normalize_stage_result(_payload())
    second = normalize_stage_result(_payload())

    assert first == second
    assert first.evidence[0].id != "provider-evidence"
    assert first.claims[0].id != "provider-claim"
    assert first.relationships[0].id != "provider-support"
    assert first.claims[0].evidence_ids == [first.evidence[0].id]
    assert first.claims[0].relationship_ids == [first.relationships[0].id]
    assert set(first.canonical_records()) == {
        first.evidence[0].id,
        first.claims[0].id,
        first.relationships[0].id,
    }


def test_provider_ids_do_not_change_canonical_identity():
    renamed = _payload()
    renamed["evidence"][0]["id"] = "another-provider-id"
    renamed["claims"][0]["id"] = "another-claim-id"
    renamed["relationships"][0]["id"] = "another-relationship-id"
    renamed["claims"][0]["evidence_ids"] = ["another-provider-id"]
    renamed["claims"][0]["relationship_ids"] = ["another-relationship-id"]
    renamed["relationships"][0]["from_id"] = "another-provider-id"
    renamed["relationships"][0]["to_id"] = "another-claim-id"

    assert normalize_stage_result(_payload()).canonical_records() == normalize_stage_result(renamed).canonical_records()


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"contract": "wrong", "stage_id": "stage-1"}, "contract"),
        ("model prose", "not prose"),
        (_payload(extra="unsupported"), "unsupported fields"),
        (_payload(evidence=[{**_payload()["evidence"][0], "unexpected": True}]), "unsupported fields"),
        (_payload(claims=[{**_payload()["claims"][0], "evidence_ids": ["missing"]}]), "unknown reference"),
        (_payload(relationships=[{**_payload()["relationships"][0], "from_id": "missing"}]), "unknown reference"),
    ],
)
def test_invalid_contract_provenance_and_references_are_rejected(payload, message):
    with pytest.raises(ValidationError, match=message):
        normalize_stage_result(payload)


def test_duplicate_provider_aliases_are_rejected():
    duplicate = _payload()
    duplicate["evidence"].append({**duplicate["evidence"][0], "excerpt": "second"})

    with pytest.raises(ValidationError, match="duplicate identifier"):
        normalize_stage_result(duplicate)


@pytest.mark.parametrize("output", [True, float("nan"), float("inf"), "not-a-number"])
def test_invalid_calculation_output_is_rejected(output):
    payload = _payload(
        calculations=[
            {
                "id": "provider-calculation",
                "key": {
                    "region": "Vietnam",
                    "measure": "share",
                    "period": "2026",
                    "units": "percent",
                },
                "formula": "42 / 100",
                "input_ids": ["provider-evidence"],
                "output": output,
                "units": "percent",
                "source_locators": ["Summary!B2"],
            }
        ]
    )

    with pytest.raises(ValidationError, match="output"):
        normalize_stage_result(payload)


def test_artifact_relationship_aliases_are_resolved():
    payload = _payload(
        claims=[{**_payload()["claims"][0], "relationship_ids": []}],
        artifacts=[
            {
                "id": "provider-artifact",
                "kind": "report",
                "path": "work/report.md",
                "relationship_ids": ["provider-produces"],
            }
        ],
        relationships=[
            {
                "id": "provider-produces",
                "from_id": "provider-claim",
                "to_id": "provider-artifact",
                "relation_type": "produces",
            }
        ],
    )

    result = normalize_stage_result(payload)

    assert result.artifacts[0].relationship_ids == [result.relationships[0].id]


def test_schema_is_strict_and_binds_contract():
    schema = analysis_stage_result_schema()["json_schema"]["schema"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["contract"] == {"const": ANALYSIS_STAGE_RESULT_CONTRACT}


def test_committer_persists_provisional_state_and_never_writes_receipts(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()

    result = committer(stage, _payload(), {})
    loaded = store.load_pending()

    assert result.result_references
    assert loaded.revision_status.value == "PENDING_REVIEW"
    assert loaded.canonical_records()
    assert store.load_stage_receipts() == {}
    assert all(result.result_hashes[index] for index in range(len(result.result_references)))


def test_committer_repeated_same_content_is_idempotent(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()

    first = committer(stage, _payload(), {})
    second = committer(stage, _payload(), {})
    loaded = store.load_pending()

    assert first.result_references == second.result_references
    assert first.result_hashes == second.result_hashes
    assert len(loaded.evidence) == len(loaded.claims) == len(loaded.relationships) == 1
    assert [revision.number for revision in loaded.revisions] == [1]


def test_committer_rejects_same_id_with_different_persisted_content(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    committer(stage, _payload(), {})

    value = json.loads(store.pending_analysis_path.read_text(encoding="utf-8"))
    value["evidence"][0]["excerpt"] = "tampered persisted content"
    store.pending_analysis_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="same-ID/different-content conflict"):
        committer(stage, _payload(), {})


def test_workflow_hydrates_canonical_records_from_persisted_state_for_cache_reuse(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    evidence = Evidence(
        "evidence-1",
        SourceLocator("v1", "Summary", "B2", "percent", "none", "source"),
        "v1",
        "2026-10-15",
        "Observed share is 42%.",
    )
    store.save_analysis(AnalysisState("case", 1, evidence=[evidence], revisions=[Revision("revision-1", 1, "initial", [evidence.id])]))
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, (), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    stage_input = StageInput("question", "unspecified", "execute declared stage", "")
    cache_key = _stage_cache_key(stage, stage_input, (), {})

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=None,
            run_id="fresh-process-hydration",
            run_context={
                "analysis_store": store,
                "stage_cache": {
                    cache_key: {
                        "status": "committed",
                        "provenance_complete": True,
                        "result_references": (evidence.id,),
                        "result_hashes": (canonical_json_hash(asdict(evidence)),),
                        "output": asdict(evidence),
                    }
                },
            },
        )
    )

    assert result.outputs[0]["id"] == evidence.id
    assert result.metrics.cache_hits == 1


def test_workflow_writes_receipt_only_after_committer_returns_verified_state(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst", "purpose": "analyze"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        base.max_total_agent_calls,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )

    class Agent:
        async def run(self, prompt):
            return SimpleNamespace(value=_payload(), text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=Client(),
            run_id="receipt-after-persistence",
            run_context={
                "analysis_store": store,
                "canonical_result_committer": committer,
                "require_structured_output": True,
            },
        )
    )

    receipts = store.load_stage_receipts()
    assert receipts["stage-1"].reusable()
    assert store.load_pending().revision_status.value == "PENDING_REVIEW"
    assert result.metrics.runtime_status == "SETTLED"
    assert result.metrics.persistence_status == "PERSISTED"
    assert result.metrics.analysis_status == "PENDING_REVIEW"
