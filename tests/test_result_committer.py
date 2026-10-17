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
    _unknown_reference_error,
)
from foresight_os.domain.validation import ValidationError
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeStage, RecipeName, StageInput, make_recipe
from foresight_os.domain.models import AnalysisState, Revision, SourceLocator, Evidence
from foresight_os.runtime.metrics import BudgetExceededError
import foresight_os.runtime.workflow as workflow_module
from foresight_os.runtime.workflow import CanonicalStageResult, _stage_cache_key, _synthesize_stage_outputs, run_recipe_async


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


def test_unknown_reference_error_lists_available_canonical_ids():
    existing = normalize_stage_result(_payload()).canonical_records()
    invalid = _payload(claims=[{**_payload()["claims"][0], "evidence_ids": ["missing"]}])

    with pytest.raises(ValidationError) as error:
        normalize_stage_result(invalid, existing_records=existing)

    assert next(iter(existing)) in str(error.value)
    assert error.value.code == "UNRESOLVED_REFERENCE"


def test_unknown_reference_error_bounds_and_deduplicates_canonical_ids():
    aliases = {"provider-duplicate": "canonical-00"}
    aliases.update({f"provider-{index:02d}": f"canonical-{index:02d}" for index in range(21)})

    error = _unknown_reference_error("missing", aliases, "claims.evidence_ids", code="UNRESOLVED_REFERENCE")
    message = str(error)

    assert "valid canonical IDs:" in message
    assert "... (1 more)" in message
    assert "canonical-20" not in message
    assert error.code == "UNRESOLVED_REFERENCE"


def test_dependency_only_relationship_reference_is_rejected():
    prior = normalize_stage_result(_payload())
    dependency_claim = prior.claims[0]
    payload = _payload(
        relationships=[],
        claims=[{
            **_payload()["claims"][0],
            "relationship_ids": [prior.relationships[0].id],
        }],
    )

    with pytest.raises(ValidationError, match="unknown reference: claims.relationship_ids"):
        normalize_stage_result(
            payload,
            existing_records={dependency_claim.id: dependency_claim},
        )


def test_duplicate_provider_aliases_are_rejected():
    duplicate = _payload()
    duplicate["evidence"].append({**duplicate["evidence"][0], "excerpt": "second"})

    with pytest.raises(ValidationError, match="duplicate identifier"):
        normalize_stage_result(duplicate)


def test_duplicate_relationship_edges_are_canonicalized_once():
    duplicate = _payload()
    duplicate["relationships"].append(dict(duplicate["relationships"][0]))

    result = normalize_stage_result(duplicate)

    assert len(result.relationships) == 1


def test_invalid_relationship_endpoint_types_are_rejected_during_normalization():
    payload = _payload(
        claims=[],
        implications=[
            {
                "id": "provider-implication",
                "statement": "The observed share informs a planning implication.",
                "basis": "DERIVED",
                "assessment": "UNASSESSED",
                "evidence_ids": [],
                "relationship_ids": ["provider-invalid-edge"],
            }
        ],
        recommendations=[
            {
                "id": "provider-recommendation",
                "statement": "Use the implication to shape the next decision.",
                "basis": "ASSUMED",
                "assessment": "UNASSESSED",
                "evidence_ids": [],
                "relationship_ids": [],
            }
        ],
        relationships=[
            {
                "id": "provider-invalid-edge",
                "from_id": "provider-implication",
                "to_id": "provider-recommendation",
                "relation_type": "produces",
            }
        ],
    )

    with pytest.raises(ValidationError, match="invalid endpoints for relationship produces") as caught:
        normalize_stage_result(payload)

    assert caught.value.code == "INVALID_RELATIONSHIP"


def test_unknown_record_reference_has_a_typed_validation_code():
    payload = _payload(
        claims=[{**_payload()["claims"][0], "evidence_ids": ["missing-evidence"]}],
        relationships=[],
    )

    with pytest.raises(ValidationError, match="unknown reference") as caught:
        normalize_stage_result(payload)

    assert caught.value.code == "UNRESOLVED_REFERENCE"


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


def test_synthesized_artifact_payload_remains_provider_compatible(tmp_path):
    stage = RecipeStage("stage-1", ExecutionPattern.CONCURRENT, ({"id": "one"}, {"id": "two"}), "prompt", "typed-result", {})
    artifact = {"id": "provider-artifact", "kind": "report", "path": "work/report.md", "relationship_ids": []}
    payload = _payload(evidence=[], claims=[], relationships=[], artifacts=[artifact])
    synthesized = _synthesize_stage_outputs(stage, [payload, payload])

    committer = CanonicalResultCommitter(AnalysisStore(tmp_path / "case"), "case")
    result = committer(stage, synthesized, {})

    assert result.result_references


def test_multi_participant_validation_uses_correction_budget(monkeypatch):
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("stage-1", ExecutionPattern.CONCURRENT, ({"id": "one"}, {"id": "two"}), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        4,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    synthesis_calls = 0
    native_calls = 0
    prompts = []

    async def fake_native(*args, **kwargs):
        nonlocal native_calls
        native_calls += 1
        prompts.append(args[1])
        return [{"status": "raw"}, {"status": "raw"}]

    def fake_synthesis(*args, **kwargs):
        nonlocal synthesis_calls
        synthesis_calls += 1
        if synthesis_calls == 1:
            raise ValidationError("invalid endpoints for relationship informs: claim -> claim")
        return {"status": "ready"}

    monkeypatch.setattr(workflow_module, "_run_native_stage", fake_native)
    monkeypatch.setattr(workflow_module, "_synthesize_stage_outputs", fake_synthesis)

    def committer(stage, output, context):
        return CanonicalStageResult(("result",), (canonical_json_hash(output),), output)

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=object(),
            run_id="aggregate-correction",
            run_context={"canonical_result_committer": committer},
        )
    )

    assert result.metrics.correction_rounds == 1
    assert native_calls == 2
    assert "correct only the exact invalid edge" in prompts[1]
    assert "never silently drop" in prompts[1]


def test_tool_enabled_multi_participant_correction_can_dispatch_again(monkeypatch):
    base = make_recipe(RecipeName.DIRECT)
    participants = (
        {"id": "analyst", "purpose": "analyze", "capability_ids": ("spreadsheet_read",)},
        {"id": "reviewer", "purpose": "review", "capability_ids": ("domain_validation",)},
    )
    stage = RecipeStage("stage-1", ExecutionPattern.SEQUENTIAL, participants, "prompt", "typed-result", {"max_total_agent_calls": 12})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        12,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )
    synthesis_calls = 0

    async def fake_native(*args, **kwargs):
        reserve_call = args[5]["reserve_agent_call"]
        record_call = args[5]["record_agent_call"]
        for _ in range(6):
            assert reserve_call()
            record_call()
        return [{"status": "raw"}, {"status": "raw"}]

    def fake_synthesis(*args, **kwargs):
        nonlocal synthesis_calls
        synthesis_calls += 1
        if synthesis_calls == 1:
            raise ValidationError("canonical validation requires a correction")
        return {"status": "ready"}

    monkeypatch.setattr(workflow_module, "_run_native_stage", fake_native)
    monkeypatch.setattr(workflow_module, "_synthesize_stage_outputs", fake_synthesis)

    def committer(stage, output, context):
        return CanonicalStageResult(("result",), (canonical_json_hash(output),), output)

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=object(),
            run_id="tool-enabled-correction-budget",
            run_context={"canonical_result_committer": committer},
        )
    )

    assert result.metrics.correction_rounds == 1
    assert result.metrics.model_calls == 12


def test_schema_is_strict_and_binds_contract():
    schema = analysis_stage_result_schema()["json_schema"]["schema"]

    assert schema["additionalProperties"] is False
    assert schema["properties"]["contract"] == {
        "type": "string",
        "const": ANALYSIS_STAGE_RESULT_CONTRACT,
    }
    assert schema["$defs"]["relationship"]["properties"]["relation_type"]["enum"] == sorted(
        ["supports", "contradicts", "derived_from", "depends_on", "informs", "produces", "supersedes"]
    )


def test_strict_schema_requires_every_declared_property():
    schema = analysis_stage_result_schema()["json_schema"]["schema"]
    object_schemas = [schema, *schema["$defs"].values()]

    for object_schema in object_schemas:
        assert set(object_schema["required"]) == set(object_schema["properties"])


def test_nullable_confidence_rationale_normalizes_to_empty_text():
    payload = _payload(
        claims=[{**_payload()["claims"][0], "confidence_rationale": None}],
    )

    result = normalize_stage_result(payload)

    assert result.claims[0].confidence_rationale == ""


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


def test_committer_resolves_references_to_prior_stage_records(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    first_stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    first = committer(first_stage, _payload(), {})
    prior_evidence_id = next(item for item in first.result_references if item.startswith("evidence-"))
    second_payload = _payload(
        stage_id="stage-2",
        evidence=[],
        claims=[{**_payload()["claims"][0], "evidence_ids": [prior_evidence_id], "relationship_ids": []}],
        relationships=[],
    )

    second_stage = type("Stage", (), {"stage_id": "stage-2", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    second = committer(second_stage, second_payload, {})

    assert second.output["evidence_ids"] == [prior_evidence_id]
    assert store.load_pending().claims[-1].evidence_ids == [prior_evidence_id]


def test_current_provider_alias_cannot_redirect_existing_canonical_reference(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    first_stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    first = committer(first_stage, _payload(), {})
    prior_evidence_id = next(item for item in first.result_references if item.startswith("evidence-"))
    second_payload = _payload(
        stage_id="stage-2",
        evidence=[{**_payload()["evidence"][0], "id": prior_evidence_id, "excerpt": "different evidence"}],
        claims=[{**_payload()["claims"][0], "evidence_ids": [prior_evidence_id], "relationship_ids": []}],
        relationships=[],
    )

    second_stage = type("Stage", (), {"stage_id": "stage-2", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    second = committer(second_stage, second_payload, {})

    assert second.output["claims"][0]["evidence_ids"] == [prior_evidence_id]
    assert len(store.load_pending().evidence) == 2


def test_committer_resolves_only_declared_dependency_records(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    first_stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    first = committer(first_stage, _payload(), {})
    evidence_id = next(item for item in first.result_references if item.startswith("evidence-"))
    second_stage = type("Stage", (), {"stage_id": "stage-2", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    second_payload = _payload(
        stage_id="stage-2",
        evidence=[],
        claims=[{**_payload()["claims"][0], "evidence_ids": [evidence_id], "relationship_ids": []}],
        relationships=[],
    )

    committer(second_stage, second_payload, {"dependency_records": {evidence_id: first.canonical_records[evidence_id]}})

    with pytest.raises(ValidationError, match="unknown reference"):
        committer(second_stage, second_payload, {"dependency_records": {}})


def test_participant_cannot_assign_assessment_or_supersede_lifecycle():
    result = normalize_stage_result(_payload())

    assert result.claims[0].assessment.value == "UNASSESSED"
    assert result.claims[0].lifecycle.value == "CURRENT"


def test_current_relationship_alias_cannot_redirect_existing_relationship_reference(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    first_stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    first = committer(first_stage, _payload(), {})
    prior_evidence_id = next(item for item in first.result_references if item.startswith("evidence-"))
    prior_claim_id = next(item for item in first.result_references if item.startswith("claim-"))
    prior_relationship_id = next(item for item in first.result_references if item.startswith("relationship-"))
    second_payload = _payload(
        stage_id="stage-2",
        evidence=[],
        claims=[{**_payload()["claims"][0], "evidence_ids": [prior_evidence_id], "relationship_ids": [prior_relationship_id]}],
        relationships=[
            {
                "id": prior_relationship_id,
                "from_id": prior_evidence_id,
                "to_id": prior_claim_id,
                "relation_type": "supports",
            }
        ],
    )

    second_stage = type("Stage", (), {"stage_id": "stage-2", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    second = committer(second_stage, second_payload, {})

    assert second.output["claims"][0]["relationship_ids"] == [prior_relationship_id]


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


def test_normalizer_rejects_invalid_relationships():
    payload = _payload(
        relationships=[
            {
                "id": "provider-support",
                "from_id": "provider-claim",
                "to_id": "provider-claim",
                "relation_type": "informs",
            }
        ]
    )

    with pytest.raises(ValidationError):
        normalize_stage_result(payload)


def test_normalizer_rejects_unknown_relationship_endpoints():
    payload = _payload(
        relationships=[
            {
                "id": "provider-support",
                "from_id": "missing-evidence",
                "to_id": "provider-claim",
                "relation_type": "supports",
            }
        ]
    )

    with pytest.raises(ValidationError):
        normalize_stage_result(payload)


def test_normalizer_rejects_unresolved_relationship_references():
    payload = _payload(
        relationships=[],
        claims=[{**_payload()["claims"][0], "relationship_ids": ["missing-relationship"]}],
    )

    with pytest.raises(ValidationError):
        normalize_stage_result(payload)


def test_workflow_retries_and_drops_unknown_record_relationship_reference(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.DIRECT,
        ({"id": "analyst", "purpose": "analyze"},),
        "prompt",
        "typed-result",
        {},
    )
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
    invalid = _payload(
        claims=[],
        implications=[{
            "id": "provider-implication",
            "statement": "The observed share informs a planning implication.",
            "basis": "DERIVED",
            "assessment": "UNASSESSED",
            "evidence_ids": [],
            "relationship_ids": ["missing-relationship"],
        }],
        relationships=[],
    )

    class Agent:
        async def run(self, prompt, **kwargs):
            return SimpleNamespace(value=invalid, text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    with pytest.raises(ValidationError):
        asyncio.run(
            run_recipe_async(
                recipe,
                "question",
                client=Client(),
                run_id="relationship-reference-correction",
                run_context={"canonical_result_committer": CanonicalResultCommitter(store, "case")},
            )
        )


def test_synthesis_rejects_invalid_relationships():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "prompt",
        "typed-result",
        {},
    )
    payload = _payload(
        relationships=[
            {
                "id": "invalid-edge",
                "from_id": "provider-claim",
                "to_id": "provider-claim",
                "relation_type": "informs",
            }
        ]
    )

    with pytest.raises(ValidationError):
        _synthesize_stage_outputs(stage, [payload, payload])


def test_synthesis_rejects_conflicting_records():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "prompt",
        "typed-result",
        {},
    )
    outputs = [
        {"evidence": [{"id": "e1", "statement": "first"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
        {"evidence": [{"id": "e1", "statement": "second"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []},
    ]

    with pytest.raises(ValidationError, match="conflicting canonical record"):
        _synthesize_stage_outputs(stage, outputs)


def test_synthesis_preserves_trusted_existing_evidence_when_peer_reuses_its_alias():
    prior = normalize_stage_result(_payload())
    prior_evidence = prior.evidence[0]
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "prompt",
        "typed-result",
        {},
    )
    conflicting = _payload(
        evidence=[{**_payload()["evidence"][0], "id": prior_evidence.id, "excerpt": "different evidence"}],
        claims=[{**_payload()["claims"][0], "evidence_ids": [prior_evidence.id], "relationship_ids": []}],
        relationships=[],
    )

    synthesized = _synthesize_stage_outputs(
        stage,
        [conflicting, conflicting],
        existing_records={prior_evidence.id: prior_evidence},
    )

    assert synthesized["claims"][0]["evidence_ids"] == [prior_evidence.id]


def test_synthesis_resolves_calculation_aliases_across_three_participant_hops():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}, {"id": "three"}),
        "prompt",
        "typed-result",
        {},
    )
    evidence = _payload()["evidence"][0]
    outputs = [
        _payload(
            calculations=[{
                "id": "calculation-one",
                "key": {"region": "Vietnam", "measure": "share", "period": "2026", "units": "percent"},
                "formula": "42",
                "input_ids": ["provider-evidence"],
                "output": 42,
                "units": "percent",
                "source_locators": ["Summary!B2"],
            }],
        ),
        _payload(
            evidence=[],
            claims=[],
            relationships=[],
            calculations=[{
                "id": "calculation-two",
                "key": {"region": "Vietnam", "measure": "share-adjusted", "period": "2026", "units": "percent"},
                "formula": "calculation-one + 1",
                "input_ids": ["calculation-one"],
                "output": 43,
                "units": "percent",
                "source_locators": ["derived"],
            }],
        ),
        _payload(
            evidence=[],
            claims=[],
            relationships=[],
            calculations=[{
                "id": "calculation-three",
                "key": {"region": "Vietnam", "measure": "share-final", "period": "2026", "units": "percent"},
                "formula": "calculation-two + 1",
                "input_ids": ["calculation-two"],
                "output": 44,
                "units": "percent",
                "source_locators": ["derived"],
            }],
        ),
    ]
    outputs[0]["evidence"] = [evidence]

    synthesized = _synthesize_stage_outputs(stage, outputs)

    calculations = {item["formula"]: item for item in synthesized["calculations"]}
    assert calculations["calculation-one + 1"]["input_ids"] == [calculations["42"]["id"]]
    assert calculations["calculation-two + 1"]["input_ids"] == [calculations["calculation-one + 1"]["id"]]


def test_synthesis_keeps_valid_relationship_alias_after_an_invalid_relationship_is_filtered():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "one"}, {"id": "two"}),
        "prompt",
        "typed-result",
        {},
    )
    output = _payload(
        claims=[{**_payload()["claims"][0], "relationship_ids": ["valid-support"]}],
        relationships=[
            {
                "id": "invalid-support",
                "from_id": "missing-evidence",
                "to_id": "provider-claim",
                "relation_type": "supports",
            },
            {
                "id": "valid-support",
                "from_id": "provider-evidence",
                "to_id": "provider-claim",
                "relation_type": "supports",
            },
        ],
    )
    peer_output = _payload(
        evidence=[],
        claims=[{
            "id": "peer-claim",
            "statement": "The valid edge remains usable.",
            "basis": "DERIVED",
            "assessment": "UNASSESSED",
            "evidence_ids": [],
            "relationship_ids": ["valid-support"],
        }],
        relationships=[],
    )

    with pytest.raises(ValidationError):
        _synthesize_stage_outputs(stage, [output, peer_output])


def test_synthesis_reports_material_conflict_by_stable_participant_id():
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.CONCURRENT,
        ({"id": "alpha"}, {"id": "beta"}),
        "prompt",
        "typed-result",
        {},
        synthesis_policy="aggregate-typed-results",
    )
    first = {"evidence": [{"id": "e1", "statement": "first"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []}
    second = {"evidence": [{"id": "e1", "statement": "second"}], "claims": [], "calculations": [], "implications": [], "recommendations": [], "artifacts": [], "relationships": [], "assumptions": [], "uncertainty": [], "monitoring_indicators": []}

    with pytest.raises(ValidationError) as caught:
        _synthesize_stage_outputs(stage, [first, second], participant_ids=("alpha", "beta"))

    assert caught.value.code == "MATERIAL_CONFLICT"
    assert caught.value.participant_id == "beta"

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
        async def run(self, prompt, **kwargs):
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


def test_workflow_uses_one_correction_round_for_canonical_validation_feedback():
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
    prompts = []

    class Agent:
        async def run(self, prompt, **kwargs):
            prompts.append(prompt)
            return SimpleNamespace(value={"status": "invalid" if len(prompts) == 1 else "ready"}, text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    def committer(stage, output, context):
        if len(prompts) == 1:
            raise ValidationError("relationship endpoint is missing", code="INVALID_RELATIONSHIP", participant_index=0)
        return CanonicalStageResult(("result",), (canonical_json_hash(output),), output)

    result = asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=Client(),
            run_id="canonical-correction",
            run_context={"canonical_result_committer": committer},
        )
    )

    assert result.outputs[-1]["status"] == "ready"
    assert result.metrics.correction_rounds == 1
    assert len(prompts) == 2
    assert "canonical validation" in prompts[1]


def test_workflow_explains_dependency_record_redeclaration_on_unknown_reference():
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
    prompts = []

    class Agent:
        async def run(self, prompt, **kwargs):
            prompts.append(prompt)
            return SimpleNamespace(value={"status": "invalid" if len(prompts) == 1 else "ready"}, text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    def committer(stage, output, context):
        if len(prompts) == 1:
            raise ValidationError("dependency record is unresolved", code="UNRESOLVED_REFERENCE", participant_index=0)
        return CanonicalStageResult(("result",), (canonical_json_hash(output),), output)

    asyncio.run(
        run_recipe_async(
            recipe,
            "question",
            client=Client(),
            run_id="dependency-reference-correction",
            run_context={"canonical_result_committer": committer},
        )
    )

    assert "reference an existing canonical dependency ID" in prompts[1]
    assert "every from_id and to_id must refer to a record declared" in prompts[1]
    assert '"dependency_outputs"' in prompts[1]
    assert "audit every evidence_ids" in prompts[1]
    assert "validate its hash and invalidation state" in prompts[1]
    assert "Every text-list item" in prompts[1]


def test_workflow_retries_same_id_conflict_as_canonical_validation(tmp_path):
    store = AnalysisStore(tmp_path / "case")
    committer = CanonicalResultCommitter(store, "case")
    stage = type("Stage", (), {"stage_id": "stage-1", "result_contract": ANALYSIS_STAGE_RESULT_CONTRACT})()
    committer(stage, _payload(), {})
    persisted = json.loads(store.pending_analysis_path.read_text(encoding="utf-8"))
    persisted["evidence"][0]["limitations"] = ["tampered persisted content"]
    store.pending_analysis_path.write_text(json.dumps(persisted), encoding="utf-8")

    base = make_recipe(RecipeName.DIRECT)
    recipe_stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst", "purpose": "analyze"},), "prompt", "typed-result", {})
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
        stages=(recipe_stage,),
    )
    prompts = []

    class Agent:
        async def run(self, prompt, **kwargs):
            prompts.append(prompt)
            value = _payload() if len(prompts) == 1 else _payload(evidence=[{**_payload()["evidence"][0], "limitations": ["tampered persisted content"]}])
            return SimpleNamespace(value=value, text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    with pytest.raises(ValidationError, match="same-ID/different-content") as caught:
        asyncio.run(
            run_recipe_async(
                recipe,
                "question",
                client=Client(),
                run_id="same-id-correction",
                run_context={
                    "analysis_store": store,
                    "canonical_result_committer": committer,
                    "require_structured_output": True,
                    "structured_output_schema": analysis_stage_result_schema(),
                },
            )
        )

    assert caught.value.code == "MATERIAL_CONFLICT"
    assert len(prompts) == 1


def test_canonical_correction_retry_reserves_agent_call_budget():
    base = make_recipe(RecipeName.DIRECT)
    stage = RecipeStage("stage-1", ExecutionPattern.DIRECT, ({"id": "analyst", "purpose": "analyze"},), "prompt", "typed-result", {})
    recipe = ExecutionRecipe(
        base.name,
        base.pattern,
        base.roles,
        base.max_agent_steps,
        base.max_correction_rounds,
        1,
        base.completion,
        base.escalation,
        base.partial_result,
        stages=(stage,),
    )

    class Agent:
        async def run(self, prompt, **kwargs):
            return SimpleNamespace(value={"status": "invalid"}, text="")

    class Client:
        def as_agent(self, **kwargs):
            return Agent()

    def committer(stage, output, context):
        raise ValidationError("canonical rejection")

    with pytest.raises(BudgetExceededError, match="agent calls"):
        asyncio.run(
            run_recipe_async(
                recipe,
                "question",
                client=Client(),
                run_id="canonical-correction-budget",
                run_context={"canonical_result_committer": committer},
            )
        )
