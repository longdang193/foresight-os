import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import AnalysisState, WorkBrief


ROOT = Path(__file__).parents[3]


class ValidationError(ValueError):
    """Raised when a durable Foresight OS record violates its trust boundary."""


def _validate_schema(value: dict[str, Any], schema_name: str) -> None:
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
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
    for relationship in value["relationships"]:
        if relationship["from_id"] not in record_ids or relationship["to_id"] not in record_ids:
            raise ValidationError("relationship endpoints must reference existing records")

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
