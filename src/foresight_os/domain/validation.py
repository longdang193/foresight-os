import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from .models import AnalysisState, EvidenceCandidate, ResearchNeed, ResearchNeedKind, WorkBrief
from .relationships import RecordKind, relationship_rule


class ValidationError(ValueError):
    """Raised when a durable Foresight OS record violates its trust boundary."""


CURRENT_SCHEMA_VERSION = 1


def migrate_analysis_dict(value: dict[str, Any]) -> dict[str, Any]:
    migrated = dict(value)
    version = migrated.get("schema_version", 0)
    if version > CURRENT_SCHEMA_VERSION:
        raise ValidationError(f"unsupported future analysis schema version: {version}")
    if version == 0:
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
    _validate_schema(value, "work_brief.schema.json")
    return value


def _normalize_work_brief(value: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(value)
    stages = []
    for stage in value.get("stages", []):
        current = dict(stage)
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
        current.setdefault("execution_pattern_override", None)
        current.setdefault("limits", {})
        stages.append(current)
    normalized["stages"] = stages
    normalized.setdefault("horizon", "unspecified")
    normalized.setdefault("consequence_level", "standard")
    return normalized


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
