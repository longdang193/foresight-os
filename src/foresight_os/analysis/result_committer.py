"""Typed stage-result normalization and canonical persistence boundary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import json
import math
from typing import Any, Mapping

from foresight_os.domain.models import (
    AnalyticalRecord,
    Artifact,
    Assessment,
    Basis,
    CalculationRecord,
    CalculationVerificationStatus,
    Evidence,
    Lifecycle,
    MeasurementKey,
    AnalysisState,
    Revision,
    RevisionStatus,
    Relationship,
    SourceLocator,
)
from foresight_os.domain.relationships import RELATIONSHIP_RULES, RecordKind, relationship_rule
from foresight_os.domain.validation import ValidationError
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash, deterministic_id


ANALYSIS_STAGE_RESULT_CONTRACT = "analysis-stage-result/v1"
_RECOGNIZED_FIELDS = frozenset(
    {
        "contract",
        "stage_id",
        "evidence",
        "calculations",
        "claims",
        "implications",
        "recommendations",
        "artifacts",
        "relationships",
        "assumptions",
        "uncertainty",
        "monitoring_indicators",
    }
)
_MEASUREMENT_KEY_FIELDS = frozenset({"region", "measure", "period", "units", "scenario", "version"})
_SOURCE_LOCATOR_FIELDS = frozenset({"file_version", "sheet", "range", "units", "transformation", "calculation"})
_EVIDENCE_FIELDS = frozenset({"id", "source_locator", "version", "date", "excerpt", "limitations", "measurement_key"})
_CALCULATION_FIELDS = frozenset({"id", "key", "input_ids", "formula", "output", "units", "source_locators", "verification_status"})
_ANALYTICAL_RECORD_FIELDS = frozenset(
    {
        "id",
        "statement",
        "basis",
        "assessment",
        "lifecycle",
        "evidence_ids",
        "relationship_ids",
        "assumptions",
        "uncertainty",
        "confidence_rationale",
        "disconfirmation_conditions",
        "monitoring_indicators",
    }
)
_ARTIFACT_FIELDS = frozenset({"id", "kind", "path", "lifecycle", "relationship_ids"})
_RELATIONSHIP_FIELDS = frozenset({"id", "from_id", "to_id", "relation_type"})


def decode_stage_output(output: object) -> object:
    """Unwrap provider response containers and decode one JSON text boundary."""

    nested_response = getattr(output, "agent_response", None)
    if nested_response is not None and nested_response is not output:
        return decode_stage_output(nested_response)
    try:
        value = getattr(output, "value", None)
    except (TypeError, ValueError, json.JSONDecodeError):
        value = None
    if value is not None:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
    try:
        text = getattr(output, "text", None)
    except (TypeError, ValueError, json.JSONDecodeError):
        text = None
    if text is None:
        return output
    if isinstance(text, str):
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def analysis_stage_result_schema() -> dict[str, Any]:
    """Return the provider-facing JSON schema for the versioned contract."""

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "analysis_stage_result_v1",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "contract",
                    "stage_id",
                    "evidence",
                    "calculations",
                    "claims",
                    "implications",
                    "recommendations",
                    "relationships",
                    "artifacts",
                    "assumptions",
                    "uncertainty",
                    "monitoring_indicators",
                ],
                "properties": {
                    "contract": {"type": "string", "const": ANALYSIS_STAGE_RESULT_CONTRACT},
                    "stage_id": {"type": "string", "minLength": 1},
                    "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
                    "calculations": {"type": "array", "items": {"$ref": "#/$defs/calculation"}},
                    "claims": {"type": "array", "items": {"$ref": "#/$defs/analytical_record"}},
                    "implications": {"type": "array", "items": {"$ref": "#/$defs/analytical_record"}},
                    "recommendations": {"type": "array", "items": {"$ref": "#/$defs/analytical_record"}},
                    "relationships": {"type": "array", "items": {"$ref": "#/$defs/relationship"}},
                    "artifacts": {"type": "array", "items": {"$ref": "#/$defs/artifact"}},
                    "assumptions": {"type": "array", "items": {"type": "string"}},
                    "uncertainty": {"type": "array", "items": {"type": "string"}},
                    "monitoring_indicators": {"type": "array", "items": {"type": "string"}},
                },
                "$defs": {
                    "measurement_key": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["region", "measure", "period", "units", "scenario", "version"],
                        "properties": {
                            "region": {"type": "string", "minLength": 1},
                            "measure": {"type": "string", "minLength": 1},
                            "period": {"type": "string", "minLength": 1},
                            "units": {"type": "string", "minLength": 1},
                            "scenario": {"type": "string", "minLength": 1},
                            "version": {"type": "string", "minLength": 1},
                        },
                    },
                    "source_locator": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["file_version", "sheet", "range", "units", "transformation", "calculation"],
                        "properties": {
                            field: {"type": "string", "minLength": 1}
                            for field in ("file_version", "sheet", "range", "units", "transformation", "calculation")
                        },
                    },
                    "evidence": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "source_locator", "version", "date", "excerpt", "limitations", "measurement_key"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "source_locator": {"$ref": "#/$defs/source_locator"},
                            "version": {"type": "string", "minLength": 1},
                            "date": {"type": "string", "minLength": 1},
                            "excerpt": {"type": "string", "minLength": 1},
                            "limitations": {"type": "array", "items": {"type": "string"}},
                            "measurement_key": {
                                "anyOf": [
                                    {"$ref": "#/$defs/measurement_key"},
                                    {"type": "null"},
                                ]
                            },
                        },
                    },
                    "calculation": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "key", "formula", "input_ids", "output", "units", "source_locators"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "key": {"$ref": "#/$defs/measurement_key"},
                            "formula": {"type": "string", "minLength": 1},
                            "input_ids": {"type": "array", "items": {"type": "string", "minLength": 1}},
                            "output": {"type": "number"},
                            "units": {"type": "string", "minLength": 1},
                            "source_locators": {"type": "array", "items": {"type": "string", "minLength": 1}},
                        },
                    },
                    "analytical_record": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "id",
                            "statement",
                            "basis",
                            "assessment",
                            "lifecycle",
                            "evidence_ids",
                            "relationship_ids",
                            "assumptions",
                            "uncertainty",
                            "confidence_rationale",
                            "disconfirmation_conditions",
                            "monitoring_indicators",
                        ],
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "statement": {"type": "string", "minLength": 1},
                            "basis": {"enum": ["OBSERVED", "DERIVED", "ASSUMED"]},
                            "assessment": {"enum": ["UNASSESSED", "SUPPORTED", "UNCERTAIN", "CONTESTED", "REFUTED"]},
                            "lifecycle": {"enum": ["CURRENT", "SUPERSEDED"]},
                            "evidence_ids": {"type": "array", "items": {"type": "string", "minLength": 1}},
                            "relationship_ids": {"type": "array", "items": {"type": "string", "minLength": 1}},
                            "assumptions": {"type": "array", "items": {"type": "string"}},
                            "uncertainty": {"type": "array", "items": {"type": "string"}},
                            "confidence_rationale": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "null"},
                                ]
                            },
                            "disconfirmation_conditions": {"type": "array", "items": {"type": "string"}},
                            "monitoring_indicators": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "artifact": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "kind", "path", "lifecycle", "relationship_ids"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "kind": {"type": "string", "minLength": 1},
                            "path": {"type": "string", "minLength": 1},
                            "lifecycle": {"enum": ["CURRENT", "SUPERSEDED"]},
                            "relationship_ids": {"type": "array", "items": {"type": "string", "minLength": 1}},
                        },
                    },
                    "relationship": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "from_id", "to_id", "relation_type"],
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "from_id": {"type": "string", "minLength": 1},
                            "to_id": {"type": "string", "minLength": 1},
                            "relation_type": {"type": "string", "enum": sorted(RELATIONSHIP_RULES)},
                        },
                    },
                },
            },
        },
    }


@dataclass(frozen=True)
class StageAnalyticalResult:
    """Normalized, typed stage output before it is merged into durable state."""

    stage_id: str
    contract: str
    evidence: tuple[Evidence, ...] = ()
    calculations: tuple[CalculationRecord, ...] = ()
    claims: tuple[AnalyticalRecord, ...] = ()
    implications: tuple[AnalyticalRecord, ...] = ()
    recommendations: tuple[AnalyticalRecord, ...] = ()
    artifacts: tuple[Artifact, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    assumptions: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    monitoring_indicators: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), default=lambda value: value.value if hasattr(value, "value") else str(value)))

    def to_contract_payload(self) -> dict[str, Any]:
        payload = self.to_payload()
        field_sets = {
            "evidence": _EVIDENCE_FIELDS,
            "calculations": _CALCULATION_FIELDS,
            "claims": _ANALYTICAL_RECORD_FIELDS,
            "implications": _ANALYTICAL_RECORD_FIELDS,
            "recommendations": _ANALYTICAL_RECORD_FIELDS,
            "artifacts": _ARTIFACT_FIELDS,
            "relationships": _RELATIONSHIP_FIELDS,
        }
        for collection, fields in field_sets.items():
            payload[collection] = [
                {key: value for key, value in item.items() if key in fields}
                for item in payload[collection]
            ]
        return payload

    def canonical_records(self) -> dict[str, object]:
        payload = self.to_payload()
        records: dict[str, object] = {}
        for key in ("evidence", "calculations", "claims", "implications", "recommendations", "artifacts", "relationships"):
            records.update({item["id"]: item for item in payload[key]})
        return records


@dataclass(frozen=True)
class CanonicalStageResult:
    """Verified canonical output eligible for the workflow receipt writer."""

    result_references: tuple[str, ...]
    result_hashes: tuple[str, ...]
    output: object
    canonical_records: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.result_references or len(self.result_references) != len(self.result_hashes):
            raise ValueError("canonical stage results require matching non-empty references and hashes")
        if len(self.result_references) == 1 and self.result_hashes[0] != canonical_json_hash(self.output):
            raise ValueError("canonical stage result hash does not match its output")


def _merge_record_collection(current: list[Any], incoming: tuple[Any, ...] | list[Any], label: str) -> list[Any]:
    result = list(current)
    positions = {item.id: index for index, item in enumerate(result)}
    for item in incoming:
        existing_index = positions.get(item.id)
        if existing_index is None:
            positions[item.id] = len(result)
            result.append(item)
            continue
        if canonical_json_hash(asdict(result[existing_index])) != canonical_json_hash(asdict(item)):
            raise ValidationError(f"same-ID/different-content conflict for {label} {item.id}", code="MATERIAL_CONFLICT")
    return result


def _initial_analysis_state(investigation_id: str) -> AnalysisState:
    return AnalysisState(
        investigation_id,
        1,
        revisions=[Revision("revision-1", 1, "initial state", [])],
    )


class CanonicalResultCommitter:
    """Normalize stage output, persist provisional state, and verify its reload."""

    def __init__(self, store: AnalysisStore, investigation_id: str):
        self.store = store
        self.investigation_id = investigation_id

    def __call__(self, stage: Any, output: object, context: Mapping[str, Any]) -> CanonicalStageResult:
        stage_id = str(getattr(stage, "stage_id", "stage"))
        contract = str(getattr(stage, "result_contract", ANALYSIS_STAGE_RESULT_CONTRACT))
        if self.store.pending_analysis_path.exists() or self.store.analysis_path.exists():
            current = self.store.load_pending()
        else:
            current = _initial_analysis_state(self.investigation_id)
        if current.investigation_id != self.investigation_id:
            raise ValueError("canonical result investigation does not match the analysis store")
        existing_records = context.get("dependency_records")
        if existing_records is None:
            existing_records = current.canonical_records()
        existing_record_kinds = {
            record.id: kind
            for collection, kind in (
                (current.evidence, RecordKind.EVIDENCE),
                (current.claims, RecordKind.CLAIM),
                (current.implications, RecordKind.IMPLICATION),
                (current.recommendations, RecordKind.RECOMMENDATION),
                (current.artifacts, RecordKind.ARTIFACT),
            )
            for record in collection
        }
        normalized = output if isinstance(output, StageAnalyticalResult) else normalize_stage_result(
            output,
            expected_stage_id=stage_id,
            expected_contract=contract,
            existing_records=existing_records,
            existing_record_kinds=existing_record_kinds,
        )
        if normalized.stage_id != stage_id or normalized.contract != contract:
            raise ValidationError("canonical result does not match the recipe stage contract")

        merged = replace(
            current,
            evidence=_merge_record_collection(current.evidence, normalized.evidence, "evidence"),
            calculations=_merge_record_collection(current.calculations, normalized.calculations, "calculation"),
            claims=_merge_record_collection(current.claims, normalized.claims, "claim"),
            implications=_merge_record_collection(current.implications, normalized.implications, "implication"),
            recommendations=_merge_record_collection(current.recommendations, normalized.recommendations, "recommendation"),
            artifacts=_merge_record_collection(current.artifacts, normalized.artifacts, "artifact"),
            relationships=_merge_record_collection(current.relationships, normalized.relationships, "relationship"),
            revision_status=RevisionStatus.PENDING_REVIEW,
            pending_token=None,
        )

        if self.store.pending_analysis_path.exists() and self.store.analysis_path.exists():
            accepted = self.store.load_accepted()
            merged = replace(merged, revision=accepted.revision, revisions=list(accepted.revisions))
        persisted = self.store.save_pending(merged)
        reloaded = self.store.load_pending()
        persisted_records = reloaded.canonical_records()
        normalized_records = normalized.canonical_records()
        for reference, record in normalized_records.items():
            if reference not in persisted_records:
                raise ValueError(f"persisted canonical record missing after reload: {reference}")
            if canonical_json_hash(persisted_records[reference]) != canonical_json_hash(record):
                raise ValueError(f"persisted canonical record hash mismatch after reload: {reference}")

        references = tuple(normalized_records)
        hashes = tuple(canonical_json_hash(normalized_records[reference]) for reference in references)
        payload = normalized.to_payload()
        output = normalized_records[references[0]] if len(references) == 1 else payload
        return CanonicalStageResult(references, hashes, output, normalized_records)


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError(f"{label} must be an object, not prose", code="MALFORMED_OUTPUT")
    return dict(value)


def _list(value: object, label: str) -> list[object]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list", code="MALFORMED_OUTPUT")
    return value


def _required_text(value: Mapping[str, Any], key: str, label: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise ValidationError(f"{label}.{key} must be non-empty text", code="MALFORMED_OUTPUT")
    return result


def _optional_text(value: Mapping[str, Any], key: str, label: str, default: str = "") -> str:
    result = value.get(key, default)
    if result is None:
        return default
    if not isinstance(result, str):
        raise ValidationError(f"{label}.{key} must be text", code="MALFORMED_OUTPUT")
    return result


def _validate_fields(value: Mapping[str, Any], allowed: frozenset[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValidationError(f"{label} contains unsupported fields: {', '.join(sorted(unknown))}", code="MALFORMED_OUTPUT")


def _text_list(value: object, label: str) -> list[str]:
    entries = _list(value, label)
    result: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, str) or not entry.strip():
            raise ValidationError(f"{label}[{index}] must be non-empty text", code="MALFORMED_OUTPUT")
        result.append(entry)
    return result


def _reference_list(value: object, label: str) -> list[str]:
    return _text_list(value, label)


def _register_alias(
    supplied_id: object,
    canonical_id: str,
    aliases: dict[str, str],
    supplied_ids: set[str],
    canonical_ids: set[str],
    label: str,
) -> None:
    if canonical_id in canonical_ids:
        raise ValidationError(f"duplicate canonical identifier: {canonical_id}", code="AMBIGUOUS_ALIAS")
    canonical_ids.add(canonical_id)
    if supplied_id is None:
        return
    if not isinstance(supplied_id, str) or not supplied_id.strip():
        raise ValidationError(f"{label}.id must be non-empty text", code="MALFORMED_OUTPUT")
    if supplied_id in supplied_ids:
        raise ValidationError(f"duplicate identifier: {supplied_id}", code="AMBIGUOUS_ALIAS")
    supplied_ids.add(supplied_id)
    aliases[supplied_id] = canonical_id


def _enum_value(enum_type: type, value: object, label: str) -> Any:
    try:
        return enum_type(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} has unsupported value: {value}", code="MALFORMED_OUTPUT") from exc


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label}.output must be a finite number", code="MALFORMED_OUTPUT")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationError(f"{label}.output must be a finite number", code="MALFORMED_OUTPUT")
    return result


def _measurement_key(value: object, label: str) -> MeasurementKey:
    item = _mapping(value, label)
    _validate_fields(item, _MEASUREMENT_KEY_FIELDS, label)
    return MeasurementKey(
        region=_required_text(item, "region", label),
        measure=_required_text(item, "measure", label),
        period=_required_text(item, "period", label),
        units=_required_text(item, "units", label),
        scenario=str(item.get("scenario", "default")),
        version=str(item.get("version", "v1")),
    )


def _unknown_reference_error(
    value: object,
    aliases: Mapping[str, str],
    label: str,
    *,
    code: str,
) -> ValidationError:
    available = sorted(set(aliases.values()))
    hint = ", ".join(available[:20])
    if len(available) > 20:
        hint += f", ... ({len(available) - 20} more)"
    suffix = f"; valid canonical IDs: {hint}" if hint else ""
    return ValidationError(f"unknown reference: {label} -> {value}{suffix}", code=code)


def _resolve(value: object, aliases: Mapping[str, str], label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must reference a non-empty ID", code="UNRESOLVED_REFERENCE")
    if value not in aliases:
        raise _unknown_reference_error(value, aliases, label, code="UNRESOLVED_REFERENCE")
    return aliases[value]


def _canonical_record_id(record_id: object, record: object) -> str:
    if isinstance(record, Mapping):
        value = record.get("id")
    else:
        value = getattr(record, "id", None)
    return str(value if value is not None else record_id)


def _source_locator(value: object, label: str) -> SourceLocator:
    item = _mapping(value, label)
    _validate_fields(item, _SOURCE_LOCATOR_FIELDS, label)
    return SourceLocator(
        file_version=_required_text(item, "file_version", label),
        sheet=_required_text(item, "sheet", label),
        range=_required_text(item, "range", label),
        units=_required_text(item, "units", label),
        transformation=_required_text(item, "transformation", label),
        calculation=_required_text(item, "calculation", label),
    )


def normalize_stage_result(
    payload: Mapping[str, Any],
    *,
    expected_stage_id: str | None = None,
    expected_contract: str = ANALYSIS_STAGE_RESULT_CONTRACT,
    existing_records: Mapping[str, object] | None = None,
    existing_record_kinds: Mapping[str, RecordKind] | None = None,
    prefer_current_aliases: bool = False,
    trusted_existing_records: Mapping[str, object] | None = None,
    return_aliases: bool = False,
) -> StageAnalyticalResult | tuple[StageAnalyticalResult, dict[str, str], dict[str, RecordKind]]:
    """Normalize provider output and assign system-owned canonical identities."""

    value = _mapping(payload, "stage result")
    unknown = set(value) - _RECOGNIZED_FIELDS
    if unknown:
        raise ValidationError(f"stage result contains unsupported fields: {', '.join(sorted(unknown))}", code="MALFORMED_OUTPUT")
    if value.get("contract") != expected_contract:
        raise ValidationError(f"stage result contract must be {expected_contract}", code="MALFORMED_OUTPUT")
    stage_id = _required_text(value, "stage_id", "stage result")
    if expected_stage_id and stage_id != expected_stage_id:
        raise ValidationError(f"stage result stage_id must be {expected_stage_id}", code="MALFORMED_OUTPUT")
    if not any(value.get(key) for key in ("evidence", "calculations", "claims", "implications", "recommendations", "artifacts", "relationships")):
        raise ValidationError("stage result must contain at least one typed analytical collection", code="MALFORMED_OUTPUT")

    aliases: dict[str, str] = {}
    supplied_ids: set[str] = set()
    canonical_ids: set[str] = set()
    def has_field(record: object, field_name: str) -> bool:
        return isinstance(record, Mapping) and field_name in record

    known_evidence_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in dict(existing_records or {}).items()
        if isinstance(record, Evidence) or has_field(record, "source_locator")
    }
    known_calculation_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in dict(existing_records or {}).items()
        if isinstance(record, CalculationRecord) or has_field(record, "formula")
    }
    known_record_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in dict(existing_records or {}).items()
        if isinstance(record, (AnalyticalRecord, Artifact)) or has_field(record, "statement") or has_field(record, "path")
    }
    known_relationship_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in dict(existing_records or {}).items()
        if isinstance(record, Relationship) or has_field(record, "relation_type")
    }
    trusted_records = dict(existing_records or {}) if trusted_existing_records is None else dict(trusted_existing_records)
    trusted_evidence_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in trusted_records.items()
        if isinstance(record, Evidence) or has_field(record, "source_locator")
    }
    trusted_calculation_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in trusted_records.items()
        if isinstance(record, CalculationRecord) or has_field(record, "formula")
    }
    trusted_record_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in trusted_records.items()
        if isinstance(record, (AnalyticalRecord, Artifact)) or has_field(record, "statement") or has_field(record, "path")
    }
    trusted_relationship_aliases = {
        record_id: _canonical_record_id(record_id, record)
        for record_id, record in trusted_records.items()
        if isinstance(record, Relationship) or has_field(record, "relation_type")
    }
    evidence_aliases: dict[str, str] = {}
    calculation_aliases: dict[str, str] = {}
    record_aliases: dict[str, str] = {}
    record_kinds: dict[str, RecordKind] = dict(existing_record_kinds or {})
    for record_id, record in dict(existing_records or {}).items():
        canonical_id = _canonical_record_id(record_id, record)
        if isinstance(record, Evidence) or has_field(record, "source_locator"):
            kind = RecordKind.EVIDENCE
        elif isinstance(record, (AnalyticalRecord, Artifact)) or has_field(record, "statement") or has_field(record, "path"):
            kind = RecordKind.CLAIM if has_field(record, "statement") else RecordKind.ARTIFACT
        else:
            continue
        record_kinds.setdefault(str(record_id), kind)
        record_kinds.setdefault(canonical_id, kind)
    evidence: list[Evidence] = []
    for index, raw in enumerate(_list(value.get("evidence"), "evidence")):
        item = _mapping(raw, f"evidence[{index}]")
        _validate_fields(item, _EVIDENCE_FIELDS, f"evidence[{index}]")
        locator = _source_locator(item.get("source_locator"), f"evidence[{index}].source_locator")
        measurement = item.get("measurement_key")
        version = _required_text(item, "version", f"evidence[{index}]")
        date = _required_text(item, "date", f"evidence[{index}]")
        excerpt = _required_text(item, "excerpt", f"evidence[{index}]")
        limitations = _text_list(item.get("limitations", ()), f"evidence[{index}].limitations")
        evidence_item = Evidence(
            id=deterministic_id("evidence", {"stage_id": stage_id, "source_locator": asdict(locator), "version": version, "date": date, "excerpt": excerpt}),
            source_locator=locator,
            version=version,
            date=date,
            excerpt=excerpt,
            limitations=limitations,
            measurement_key=_measurement_key(measurement, f"evidence[{index}].measurement_key") if measurement is not None else None,
        )
        _register_alias(item.get("id"), evidence_item.id, aliases, supplied_ids, canonical_ids, f"evidence[{index}]")
        if item.get("id") is not None:
            evidence_aliases[str(item["id"])] = evidence_item.id
        evidence_aliases[evidence_item.id] = evidence_item.id
        record_aliases.update(evidence_aliases)
        record_kinds[evidence_item.id] = RecordKind.EVIDENCE
        evidence.append(evidence_item)

    calculations: list[CalculationRecord] = []
    for index, raw in enumerate(_list(value.get("calculations"), "calculations")):
        item = _mapping(raw, f"calculations[{index}]")
        _validate_fields(item, _CALCULATION_FIELDS, f"calculations[{index}]")
        key = _measurement_key(item.get("key"), f"calculations[{index}].key")
        input_ids = [
            _resolve(
                entry,
                ({**known_evidence_aliases, **known_calculation_aliases,
                  **evidence_aliases, **calculation_aliases,
                  **trusted_evidence_aliases, **trusted_calculation_aliases}
                 if prefer_current_aliases else
                 {**evidence_aliases, **calculation_aliases, **known_evidence_aliases, **known_calculation_aliases,
                  **trusted_evidence_aliases, **trusted_calculation_aliases}),
                f"calculations[{index}].input_ids",
            )
            for entry in _reference_list(item.get("input_ids"), f"calculations[{index}].input_ids")
        ]
        if not input_ids:
            raise ValidationError(f"calculations[{index}].input_ids must not be empty", code="MISSING_INPUT")
        formula = _required_text(item, "formula", f"calculations[{index}]")
        units = _required_text(item, "units", f"calculations[{index}]")
        source_locators = _text_list(item.get("source_locators", ()), f"calculations[{index}].source_locators")
        output = _finite_number(item.get("output"), f"calculations[{index}]")
        calculation = CalculationRecord(
            id=deterministic_id("calculation", {"stage_id": stage_id, "key": asdict(key), "formula": formula, "input_ids": input_ids, "output": output, "units": units, "source_locators": source_locators, "verification_status": CalculationVerificationStatus.NOT_VERIFIED.value}),
            key=key,
            formula=formula,
            input_ids=input_ids,
            output=output,
            units=units,
            source_locators=source_locators,
            verification_status=CalculationVerificationStatus.NOT_VERIFIED,
        )
        _register_alias(item.get("id"), calculation.id, aliases, supplied_ids, canonical_ids, f"calculations[{index}]")
        if item.get("id") is not None:
            calculation_aliases[str(item["id"])] = calculation.id
        calculation_aliases[calculation.id] = calculation.id
        calculations.append(calculation)

    record_inputs: dict[str, dict[str, Any]] = {}
    records: dict[str, list[AnalyticalRecord]] = {}
    for collection in ("claims", "implications", "recommendations"):
        parsed: list[AnalyticalRecord] = []
        for index, raw in enumerate(_list(value.get(collection), collection)):
            item = _mapping(raw, f"{collection}[{index}]")
            _validate_fields(item, _ANALYTICAL_RECORD_FIELDS, f"{collection}[{index}]")
            statement = _required_text(item, "statement", f"{collection}[{index}]")
            basis = _enum_value(Basis, item.get("basis", "DERIVED"), f"{collection}[{index}].basis")
            _enum_value(Assessment, item.get("assessment", "UNASSESSED"), f"{collection}[{index}].assessment")
            _enum_value(Lifecycle, item.get("lifecycle", "CURRENT"), f"{collection}[{index}].lifecycle")
            evidence_ids = [
                _resolve(
                    entry,
                    ({**known_evidence_aliases, **evidence_aliases, **trusted_evidence_aliases}
                     if prefer_current_aliases else
                     {**evidence_aliases, **known_evidence_aliases, **trusted_evidence_aliases}),
                    f"{collection}[{index}].evidence_ids",
                )
                for entry in _reference_list(item.get("evidence_ids", ()), f"{collection}[{index}].evidence_ids")
            ]
            relationship_ids = _reference_list(item.get("relationship_ids", ()), f"{collection}[{index}].relationship_ids")
            assumptions = _text_list(item.get("assumptions", value.get("assumptions", [])), f"{collection}[{index}].assumptions")
            uncertainty = _text_list(item.get("uncertainty", value.get("uncertainty", [])), f"{collection}[{index}].uncertainty")
            disconfirmation_conditions = _text_list(item.get("disconfirmation_conditions", []), f"{collection}[{index}].disconfirmation_conditions")
            monitoring_indicators = _text_list(item.get("monitoring_indicators", value.get("monitoring_indicators", [])), f"{collection}[{index}].monitoring_indicators")
            record = AnalyticalRecord(
                id=deterministic_id(collection[:-1], {"stage_id": stage_id, "statement": statement, "basis": basis.value, "assessment": Assessment.UNASSESSED.value, "evidence_ids": evidence_ids}),
                statement=statement,
                basis=basis,
                assessment=Assessment.UNASSESSED,
                lifecycle=Lifecycle.CURRENT,
                evidence_ids=evidence_ids,
                relationship_ids=[],
                assumptions=tuple(assumptions),
                uncertainty=tuple(uncertainty),
                confidence_rationale=_optional_text(item, "confidence_rationale", f"{collection}[{index}]"),
                disconfirmation_conditions=tuple(disconfirmation_conditions),
                monitoring_indicators=tuple(monitoring_indicators),
            )
            _register_alias(item.get("id"), record.id, aliases, supplied_ids, canonical_ids, f"{collection}[{index}]")
            if item.get("id") is not None:
                record_aliases[str(item["id"])] = record.id
            record_aliases[record.id] = record.id
            record_kinds[record.id] = {
                "claims": RecordKind.CLAIM,
                "implications": RecordKind.IMPLICATION,
                "recommendations": RecordKind.RECOMMENDATION,
            }[collection]
            record_inputs[record.id] = {"collection": collection, "relationship_ids": relationship_ids}
            parsed.append(record)
        records[collection] = parsed

    artifacts: list[Artifact] = []
    for index, raw in enumerate(_list(value.get("artifacts"), "artifacts")):
        item = _mapping(raw, f"artifacts[{index}]")
        _validate_fields(item, _ARTIFACT_FIELDS, f"artifacts[{index}]")
        kind = _required_text(item, "kind", f"artifacts[{index}]")
        path = _required_text(item, "path", f"artifacts[{index}]")
        lifecycle = _enum_value(Lifecycle, item.get("lifecycle", "CURRENT"), f"artifacts[{index}].lifecycle")
        relationship_ids = _reference_list(item.get("relationship_ids", ()), f"artifacts[{index}].relationship_ids")
        artifact = Artifact(
            id=deterministic_id("artifact", {"stage_id": stage_id, "kind": kind, "path": path}),
            kind=kind,
            path=path,
            lifecycle=lifecycle,
            relationship_ids=[],
        )
        _register_alias(item.get("id"), artifact.id, aliases, supplied_ids, canonical_ids, f"artifacts[{index}]")
        if item.get("id") is not None:
            record_aliases[str(item["id"])] = artifact.id
        record_aliases[artifact.id] = artifact.id
        record_kinds[artifact.id] = RecordKind.ARTIFACT
        record_inputs[artifact.id] = {"collection": "artifacts", "relationship_ids": relationship_ids}
        artifacts.append(artifact)

    relationships: list[Relationship] = []
    relationship_aliases: dict[str, str] = {}
    for index, raw in enumerate(_list(value.get("relationships"), "relationships")):
        item = _mapping(raw, f"relationships[{index}]")
        _validate_fields(item, _RELATIONSHIP_FIELDS, f"relationships[{index}]")
        try:
            from_id = _resolve(
                item.get("from_id"),
                ({**known_evidence_aliases, **known_record_aliases, **record_aliases, **trusted_evidence_aliases, **trusted_record_aliases}
                 if not prefer_current_aliases else
                 {**known_evidence_aliases, **known_record_aliases, **record_aliases, **trusted_evidence_aliases, **trusted_record_aliases}),
                f"relationships[{index}].from_id",
            )
            to_id = _resolve(
                item.get("to_id"),
                {**known_evidence_aliases, **known_record_aliases, **record_aliases, **trusted_evidence_aliases, **trusted_record_aliases},
                f"relationships[{index}].to_id",
            )
        except ValidationError as error:
            raise ValidationError(str(error), code="INVALID_RELATIONSHIP") from error
        relation_type = _required_text(item, "relation_type", f"relationships[{index}]")
        try:
            rule = relationship_rule(relation_type)
        except ValueError as exc:
            raise ValidationError(str(exc), code="INVALID_RELATIONSHIP") from exc
        from_kind = record_kinds.get(from_id)
        to_kind = record_kinds.get(to_id)
        if from_kind is None or to_kind is None:
            raise ValidationError(
                f"relationship endpoints must have known record kinds: {from_id} -> {to_id}",
                code="INVALID_RELATIONSHIP",
            )
        if from_kind not in rule.sources or to_kind not in rule.targets:
            raise ValidationError(
                f"invalid endpoints for relationship {relation_type}: "
                f"{from_kind.value} -> {to_kind.value}",
                code="INVALID_RELATIONSHIP",
            )
        relationship_id = deterministic_id("relationship", {"stage_id": stage_id, "from_id": from_id, "to_id": to_id, "relation_type": relation_type})
        if relationship_id in relationship_aliases:
            continue
        relationship = Relationship(
            id=relationship_id,
            from_id=from_id,
            to_id=to_id,
            relation_type=relation_type,
        )
        _register_alias(item.get("id"), relationship.id, relationship_aliases, supplied_ids, canonical_ids, f"relationships[{index}]")
        relationship_aliases[relationship.id] = relationship.id
        relationships.append(relationship)

    def resolve_relationships(record_id: str, label: str) -> list[str]:
        resolved: list[str] = []
        for reference in record_inputs[record_id]["relationship_ids"]:
            relationship_id = (
                trusted_relationship_aliases.get(reference)
                or relationship_aliases.get(reference)
                or known_relationship_aliases.get(reference)
            )
            if relationship_id is None:
                raise _unknown_reference_error(
                    reference,
                    {**trusted_relationship_aliases, **relationship_aliases, **known_relationship_aliases},
                    label,
                    code="INVALID_RELATIONSHIP",
                )
            resolved.append(relationship_id)
        return resolved

    def attach_relationships(collection: str) -> tuple[AnalyticalRecord, ...]:
        result: list[AnalyticalRecord] = []
        for record in records[collection]:
            result.append(AnalyticalRecord(**{**asdict(record), "relationship_ids": resolve_relationships(record.id, f"{collection}.relationship_ids")}))
        return tuple(result)

    attached_artifacts = tuple(
        Artifact(artifact.id, artifact.kind, artifact.path, artifact.lifecycle, resolve_relationships(artifact.id, "artifacts.relationship_ids"))
        for artifact in artifacts
    )

    result = StageAnalyticalResult(
        stage_id=stage_id,
        contract=expected_contract,
        evidence=tuple(evidence),
        calculations=tuple(calculations),
        claims=attach_relationships("claims"),
        implications=attach_relationships("implications"),
        recommendations=attach_relationships("recommendations"),
        artifacts=attached_artifacts,
        relationships=tuple(relationships),
        assumptions=tuple(_text_list(value.get("assumptions", ()), "stage result.assumptions")),
        uncertainty=tuple(_text_list(value.get("uncertainty", ()), "stage result.uncertainty")),
        monitoring_indicators=tuple(_text_list(value.get("monitoring_indicators", ()), "stage result.monitoring_indicators")),
    )
    if return_aliases:
        alias_map = dict(aliases)
        alias_map.update(relationship_aliases)
        for record_id in result.canonical_records():
            alias_map.setdefault(record_id, record_id)
        return result, alias_map, record_kinds
    return result
