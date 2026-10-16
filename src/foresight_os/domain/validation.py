import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from .analysis_inputs import AnalysisInputContract
from .models import AnalysisState, EvidenceCandidate, ExecutionIntent, MethodProvenance, ResearchNeed, ResearchNeedKind, WorkBrief
from foresight_os.controller.recipes import (
    INDEPENDENT_VALIDATION_POLICY,
    ExecutionRecipe,
    TYPED_REVIEW_CHECK_IDS,
    minimum_agent_call_budget,
    minimum_stage_agent_calls,
)
from foresight_os.domain.approval import ApprovalProjection, ApprovalRecord, AdaptationEnvelope
from .relationships import RecordKind, relationship_rule


class ValidationError(ValueError):
    """Raised when a durable Foresight OS record violates its trust boundary."""


CURRENT_SCHEMA_VERSION = 2


def migrate_analysis_dict(value: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(value)
    version = migrated.get("schema_version", 0)
    if version > CURRENT_SCHEMA_VERSION:
        raise ValidationError(f"unsupported future analysis schema version: {version}")
    if version in {0, 1}:
        migrated["schema_version"] = CURRENT_SCHEMA_VERSION
        migrated.setdefault("revision_status", "ACCEPTED")
        migrated.setdefault("calculations", [])
        migrated.setdefault("pending_token", None)
        migrated.setdefault("review_records", [])
    elif version == CURRENT_SCHEMA_VERSION:
        migrated.setdefault("revision_status", "ACCEPTED")
        migrated.setdefault("calculations", [])
        migrated.setdefault("pending_token", None)
        migrated.setdefault("review_records", [])
    for calculation in migrated.get("calculations", ()):
        calculation.setdefault("verification_status", "NOT_VERIFIED")
    for artifact in migrated.get("artifacts", ()):
        artifact.setdefault("delivery_receipt", None)
    for review in migrated.get("review_records", ()):
        review.setdefault("check_id", "")
        review.setdefault("reviewer_id", "")
        review.setdefault("execution_id", "")
        review.setdefault("attempt_id", "")
        review.setdefault("method", "")
        review.setdefault("source_fingerprints", [])
        review.setdefault("dependency_fingerprints", [])
        review.setdefault("slot_key", "")
        review.setdefault("supersedes_review_id", None)
        review.setdefault("superseded_by_review_id", None)
        review.setdefault("conflict_review_ids", [])
        review.setdefault("check_results", [])
        review.setdefault("legacy", True)
    return migrated


@lru_cache(maxsize=8)
def _compiled_schema_validator(schema_name: str, schema_text: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads(schema_text))


def _validate_schema(value: dict[str, Any], schema_name: str) -> None:
    schema_text = files("foresight_os.schemas").joinpath(schema_name).read_text(encoding="utf-8")
    errors = sorted(_compiled_schema_validator(schema_name, schema_text).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        raise ValidationError("; ".join(error.message for error in errors))


def validate_work_brief(brief: WorkBrief | dict[str, Any]) -> dict[str, Any]:
    value = brief.to_dict() if isinstance(brief, WorkBrief) else dict(brief)
    value = _normalize_work_brief(value)
    for contract_value in value.get("analysis_inputs", ()):
        try:
            AnalysisInputContract.from_dict(contract_value).validate()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
    _validate_schema(value, "work_brief.schema.json")
    return value


def validate_execution_recipe(recipe: ExecutionRecipe | dict[str, Any]) -> dict[str, Any]:
    value = recipe.to_dict() if isinstance(recipe, ExecutionRecipe) else dict(recipe)
    _validate_schema(value, "execution_recipe.schema.json")
    if value.get("review_policy") == INDEPENDENT_VALIDATION_POLICY:
        typed_checks = [
            check
            for stage in value.get("stages", ())
            for check in stage.get("review_checks", ())
        ]
        unknown_checks = sorted(set(typed_checks) - set(TYPED_REVIEW_CHECK_IDS))
        if unknown_checks:
            raise ValidationError(
                "independent-validation/v1 does not support review check(s): "
                + ", ".join(unknown_checks)
            )
        if not typed_checks:
            raise ValidationError("independent-validation/v1 requires at least one typed review check")
    stage_ids = [stage["stage_id"] for stage in value.get("stages", [])]
    if len(stage_ids) != len(set(stage_ids)):
        raise ValidationError("recipe stage IDs must be unique")
    if value.get("stages") and value.get("max_total_agent_calls", 0) < len(value["stages"]):
        raise ValidationError("global agent-call budget must cover the recipe stage count")
    recipe_object = recipe if isinstance(recipe, ExecutionRecipe) else ExecutionRecipe.from_dict(value)
    stage_count = len(value.get("stages", ()))
    if stage_count and int(value.get("max_agent_steps", 0)) < stage_count:
        raise ValidationError("global agent-step budget must cover the recipe stage count")
    for stage_value, stage_object in zip(value.get("stages", ()), recipe_object.stages, strict=True):
        configured_step_limit = int(stage_value.get("limits", {}).get("max_agent_steps", 0))
        if configured_step_limit < 0:
            raise ValidationError(f"stage {stage_object.stage_id} has a negative limit")
        if stage_count and configured_step_limit < stage_count:
            raise ValidationError(
                f"stage {stage_object.stage_id} effective agent-step budget {configured_step_limit} "
                f"is below required minimum {stage_count}"
            )
        configured_limit = int(stage_value.get("limits", {}).get("max_total_agent_calls", 0))
        required_limit = minimum_stage_agent_calls(
            stage_object,
            recipe_object.max_correction_rounds,
            tuple(recipe_object.roles),
        )
        if configured_limit < required_limit:
            raise ValidationError(
                f"stage {stage_object.stage_id} effective agent-call budget {configured_limit} "
                f"is below required minimum {required_limit}"
            )
    required_global = minimum_agent_call_budget(recipe_object)
    if int(value.get("max_total_agent_calls", 0)) < required_global:
        raise ValidationError(
            f"global effective agent-call budget {value.get('max_total_agent_calls', 0)} "
            f"is below required minimum {required_global}"
        )
    seen: set[str] = set()
    for stage in value.get("stages", []):
        if any(dependency not in seen for dependency in stage.get("dependencies", [])):
            raise ValidationError(f"stage {stage['stage_id']} depends on missing or later stage")
        if any(isinstance(limit, int) and limit < 0 for limit in stage.get("limits", {}).values()):
            raise ValidationError(f"stage {stage['stage_id']} has a negative limit")
        seen.add(stage["stage_id"])
    return value


def validate_approval_record(record: ApprovalRecord | dict[str, Any]) -> dict[str, Any]:
    value = record.to_dict() if isinstance(record, ApprovalRecord) else dict(record)
    _validate_schema(value, "approval_record.schema.json")
    projection = value.get("projection", {})
    if value.get("projection_fingerprint") != _canonical_projection_fingerprint(projection):
        raise ValidationError("approval projection fingerprint does not match projection")
    if value.get("displayed_fingerprint") != value.get("projection_fingerprint"):
        raise ValidationError("displayed fingerprint must match the projection fingerprint")
    if value.get("status") not in {"APPROVED", "REJECTED", "SUPERSEDED"}:
        raise ValidationError("invalid approval status")
    return value


def _normalize_work_brief(value: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(value)
    producer = normalized.get("producer")
    if isinstance(producer, MethodProvenance):
        normalized["producer"] = producer.to_dict()
    legacy_override = normalized.pop("execution_pattern_override", None)
    if legacy_override is not None and "execution_intent" not in normalized:
        patterns = (legacy_override,) if isinstance(legacy_override, str) else tuple(legacy_override)
        normalized["execution_intent"] = ExecutionIntent(
            required_patterns=tuple(str(pattern) for pattern in patterns),
            source="legacy_execution_pattern_override",
        ).to_dict()
    if "execution_intent" in normalized:
        normalized["execution_intent"] = _normalize_execution_intent(normalized["execution_intent"])
    stages = []
    for stage in value.get("stages", []):
        current = dict(stage)
        legacy_stage_override = current.pop("execution_pattern_override", None)
        if legacy_stage_override is not None and "execution_intent" not in current:
            patterns = (legacy_stage_override,) if isinstance(legacy_stage_override, str) else tuple(legacy_stage_override)
            current["execution_intent"] = ExecutionIntent(
                required_patterns=tuple(str(pattern) for pattern in patterns),
                source="legacy_execution_pattern_override",
            ).to_dict()
        if "execution_intent" in current:
            current["execution_intent"] = _normalize_execution_intent(current["execution_intent"])
        needs = []
        for need in current.get("research_needs", []):
            if isinstance(need, str):
                needs.append({
                    "kind": ResearchNeedKind.UNRESOLVED_CAPABILITY.value,
                    "query": need,
                })
            elif isinstance(need, ResearchNeed):
                needs.append({
                    "kind": need.kind.value if isinstance(need.kind, ResearchNeedKind) else str(need.kind),
                    "query": need.query,
                    **({"source_hint": need.source_hint} if need.source_hint else {}),
                })
            else:
                normalized_need = dict(need)
                kind = normalized_need.get("kind")
                if isinstance(kind, ResearchNeedKind):
                    normalized_need["kind"] = kind.value
                elif kind is not None:
                    normalized_need["kind"] = str(kind)
                needs.append(normalized_need)
        current["research_needs"] = needs
        current.setdefault("skill_ids", [])
        current.setdefault("limits", {})
        stages.append(current)
    normalized["stages"] = stages
    if "analysis_inputs" in normalized:
        contracts = normalized["analysis_inputs"]
        if isinstance(contracts, dict):
            contracts = [
                {**dict(contract), "domain": str(domain)} if isinstance(contract, dict) else {"domain": str(domain)}
                for domain, contract in contracts.items()
            ]
        normalized_contracts = []
        for contract in contracts:
            try:
                normalized_contracts.append(AnalysisInputContract.from_dict(contract).to_dict())
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
        normalized["analysis_inputs"] = normalized_contracts
    normalized.setdefault("horizon", "unspecified")
    normalized.setdefault("consequence_level", "standard")
    return normalized


def _normalize_execution_intent(value: ExecutionIntent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, ExecutionIntent):
        normalized = value.to_dict()
    else:
        normalized = dict(value)
    for key in (
        "required_patterns",
        "preferred_patterns",
        "required_participants",
        "preferred_participants",
        "required_capabilities",
        "preferred_capabilities",
    ):
        normalized[key] = [str(item) for item in normalized.get(key, ())]
    normalized["preferred_reasoning_controls"] = dict(normalized.get("preferred_reasoning_controls", {}))
    normalized["source"] = str(normalized.get("source", "user"))
    required = set(normalized["required_patterns"])
    preferred = set(normalized["preferred_patterns"])
    if required & preferred:
        raise ValidationError("execution intent cannot require and prefer the same pattern")
    return normalized


def _canonical_projection_fingerprint(value: dict[str, Any]) -> str:
    return ApprovalProjection.fingerprint_for_dict(value)


def validate_evidence_candidate(candidate: EvidenceCandidate | dict[str, Any]) -> EvidenceCandidate:
    value = candidate if isinstance(candidate, EvidenceCandidate) else EvidenceCandidate(**candidate)
    if not all((value.candidate_id, value.capability_id, value.source, value.request, value.excerpt)):
        raise ValidationError("evidence candidates require identity, capability, source, request, and excerpt")
    if not value.provenance:
        raise ValidationError("evidence candidates require provenance")
    unsafe_markers = ("ignore previous instructions", "change capabilities", "change permissions", "grant authority", "increase budget")
    content = " ".join((value.source, value.request, value.excerpt, value.context)).lower()
    if any(marker in content for marker in unsafe_markers):
        raise ValidationError("evidence candidate content cannot modify runtime authority")
    return value


def validate_analysis(state: AnalysisState | dict[str, Any]) -> dict[str, Any]:
    value = _json_shape(state.to_dict() if isinstance(state, AnalysisState) else state)
    _validate_schema(value, "analysis.schema.json")

    collections = (
        value["evidence"],
        value["claims"],
        value["implications"],
        value["recommendations"],
        value["artifacts"],
        value["relationships"],
        value["revisions"],
    )
    ids = [record["id"] for collection in collections for record in collection]
    calculation_ids = [record["id"] for record in value.get("calculations", [])]
    ids.extend(calculation_ids)
    if len(ids) != len(set(ids)):
        raise ValidationError("record IDs must be unique")

    record_ids = set(ids)
    evidence_ids = {item["id"] for item in value["evidence"]}
    for calculation in value.get("calculations", []):
        if not set(calculation["input_ids"]).issubset(evidence_ids | set(calculation_ids)):
            raise ValidationError("calculations must reference existing evidence or calculations")
    relationship_ids = {relationship["id"] for relationship in value["relationships"]}
    kinds = {
        **{item["id"]: RecordKind.EVIDENCE for item in value["evidence"]},
        **{item["id"]: RecordKind.CLAIM for item in value["claims"]},
        **{item["id"]: RecordKind.IMPLICATION for item in value["implications"]},
        **{item["id"]: RecordKind.RECOMMENDATION for item in value["recommendations"]},
        **{item["id"]: RecordKind.ARTIFACT for item in value["artifacts"]},
    }
    for relationship in value["relationships"]:
        if relationship["from_id"] not in record_ids or relationship["to_id"] not in record_ids:
            raise ValidationError("relationship endpoints must reference existing records")
        try:
            rule = relationship_rule(relationship["relation_type"])
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if kinds[relationship["from_id"]] not in rule.sources or kinds[relationship["to_id"]] not in rule.targets:
            raise ValidationError(
                f"invalid endpoints for relationship {relationship['relation_type']}: "
                f"{kinds[relationship['from_id']]} -> {kinds[relationship['to_id']]}"
            )

    for record in (*value["claims"], *value["implications"], *value["recommendations"]):
        if not set(record["evidence_ids"]).issubset({item["id"] for item in value["evidence"]}):
            raise ValidationError("analytical records must reference existing evidence")
        if not set(record["relationship_ids"]).issubset(relationship_ids):
            raise ValidationError("analytical records must reference existing relationships")

    for record in (*value["claims"], *value["implications"], *value["recommendations"]):
        direct_support_ids = {
            relationship["from_id"]
            for relationship in value["relationships"]
            if relationship["id"] in record["relationship_ids"]
            and relationship["to_id"] == record["id"]
            and relationship["relation_type"].lower() == "supports"
            and relationship["from_id"] in evidence_ids
        }
        if not direct_support_ids.issubset(set(record["evidence_ids"])):
            raise ValidationError("direct evidence support must agree with analytical evidence_ids")

    for artifact in value["artifacts"]:
        if not set(artifact["relationship_ids"]).issubset(relationship_ids):
            raise ValidationError("artifacts must reference existing relationships")

    for review in value.get("review_records", []):
        if not set(review["target_ids"]).issubset(record_ids):
            raise ValidationError("reviews must reference existing target records")
        if review.get("check_id") and review.get("check_id") not in {
            "source_fidelity",
            "scope_reconciliation",
            "calculation_reconciliation",
            "decision_challenge",
        }:
            raise ValidationError(f"unsupported review check: {review['check_id']}")

    revision_numbers = [revision["number"] for revision in value["revisions"]]
    if revision_numbers != list(range(1, len(revision_numbers) + 1)):
        raise ValidationError("revision numbers must be contiguous and start at 1")
    if value["revision"] != len(revision_numbers):
        raise ValidationError("current revision must match revision history")
    if not all(set(revision["record_ids"]).issubset(record_ids) for revision in value["revisions"]):
        raise ValidationError("revisions must reference existing records")
    return value


def _json_shape(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_shape(item) for item in value]
    if isinstance(value, list):
        return [_json_shape(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_shape(item) for key, item in value.items()}
    return value
