import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from .models import AnalysisState, WorkBrief
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
    elif version == CURRENT_SCHEMA_VERSION:
        migrated.setdefault("revision_status", "ACCEPTED")
    return migrated


def _validate_schema(value: dict[str, Any], schema_name: str) -> None:
    schema = json.loads(files("foresight_os.schemas").joinpath(schema_name).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        raise ValidationError("; ".join(error.message for error in errors))


def validate_work_brief(brief: WorkBrief | dict[str, Any]) -> dict[str, Any]:
    value = brief.to_dict() if isinstance(brief, WorkBrief) else brief
    _validate_schema(value, "work_brief.schema.json")
    return value


def validate_analysis(state: AnalysisState | dict[str, Any]) -> dict[str, Any]:
    value = state.to_dict() if isinstance(state, AnalysisState) else state
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
    if len(ids) != len(set(ids)):
        raise ValidationError("record IDs must be unique")

    record_ids = set(ids)
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

    for artifact in value["artifacts"]:
        if not set(artifact["relationship_ids"]).issubset(relationship_ids):
            raise ValidationError("artifacts must reference existing relationships")

    revision_numbers = [revision["number"] for revision in value["revisions"]]
    if revision_numbers != list(range(1, len(revision_numbers) + 1)):
        raise ValidationError("revision numbers must be contiguous and start at 1")
    if value["revision"] != len(revision_numbers):
        raise ValidationError("current revision must match revision history")
    if not all(set(revision["record_ids"]).issubset(record_ids) for revision in value["revisions"]):
        raise ValidationError("revisions must reference existing records")
    return value
