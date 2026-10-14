from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.domain.models import WorkBrief
from foresight_os.persistence.ids import canonical_json_hash


class ApprovalStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class AdaptationEnvelope:
    allowed_operations: tuple[str, ...] = ()
    max_retries: int = 0
    max_concurrency_reduction: int | None = None
    compatible_participant_substitution: bool = False
    dependency_safe_topology_reduction: bool = False
    evidence_reuse: bool = True
    fallback_on_stale_reuse: str = "stop"

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_operations": list(self.allowed_operations),
            "max_retries": self.max_retries,
            "max_concurrency_reduction": self.max_concurrency_reduction,
            "compatible_participant_substitution": self.compatible_participant_substitution,
            "dependency_safe_topology_reduction": self.dependency_safe_topology_reduction,
            "evidence_reuse": self.evidence_reuse,
            "fallback_on_stale_reuse": self.fallback_on_stale_reuse,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AdaptationEnvelope":
        return cls(
            allowed_operations=tuple(value.get("allowed_operations", ())),
            max_retries=int(value.get("max_retries", 0)),
            max_concurrency_reduction=value.get("max_concurrency_reduction"),
            compatible_participant_substitution=bool(value.get("compatible_participant_substitution", False)),
            dependency_safe_topology_reduction=bool(value.get("dependency_safe_topology_reduction", False)),
            evidence_reuse=bool(value.get("evidence_reuse", True)),
            fallback_on_stale_reuse=str(value.get("fallback_on_stale_reuse", "stop")),
        )

    def validate(self) -> None:
        if self.max_retries < 0:
            raise ValueError("adaptation max_retries must be non-negative")
        if self.max_concurrency_reduction is not None and self.max_concurrency_reduction < 0:
            raise ValueError("adaptation max_concurrency_reduction must be non-negative")
        if self.fallback_on_stale_reuse not in {"stop", "run_fresh"}:
            raise ValueError("stale reuse fallback must be stop or run_fresh")


@dataclass(frozen=True)
class ApprovalProjection:
    brief: dict[str, Any]
    recipe: dict[str, Any]
    adaptation_envelope: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "brief": self.brief,
            "recipe": self.recipe,
            "adaptation_envelope": self.adaptation_envelope,
        }

    @property
    def fingerprint(self) -> str:
        return canonical_json_hash(self.to_dict())

    @classmethod
    def from_values(
        cls,
        brief: WorkBrief | dict[str, Any],
        recipe: ExecutionRecipe | dict[str, Any],
        adaptation_envelope: AdaptationEnvelope | dict[str, Any],
    ) -> "ApprovalProjection":
        brief_value = brief.to_dict() if isinstance(brief, WorkBrief) else dict(brief)
        recipe_value = recipe.to_dict() if isinstance(recipe, ExecutionRecipe) else dict(recipe)
        envelope_value = adaptation_envelope.to_dict() if isinstance(adaptation_envelope, AdaptationEnvelope) else AdaptationEnvelope.from_dict(dict(adaptation_envelope)).to_dict()
        return cls(
            _sanitize_projection(brief_value),
            _sanitize_projection(recipe_value),
            _sanitize_projection(envelope_value),
        )


@dataclass(frozen=True)
class ApprovalRecord:
    investigation_id: str
    status: ApprovalStatus
    projection: ApprovalProjection
    projection_fingerprint: str
    displayed_fingerprint: str
    recipe_snapshot_fingerprint: str
    approval_source: str
    approved_at: str
    approver_label: str | None = None
    supersedes_fingerprint: str | None = None
    run_decisions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in set(ApprovalStatus):
            raise ValueError(f"unsupported approval status: {self.status}")
        if self.approval_source != "local_cli":
            raise ValueError("approval_source must identify the local CLI human boundary")
        if self.projection_fingerprint != self.projection.fingerprint:
            raise ValueError("approval projection fingerprint does not match projection")
        if self.displayed_fingerprint != self.projection_fingerprint:
            raise ValueError("displayed fingerprint must match the approved projection")

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "status": self.status.value,
            "projection": self.projection.to_dict(),
            "projection_fingerprint": self.projection_fingerprint,
            "displayed_fingerprint": self.displayed_fingerprint,
            "recipe_snapshot_fingerprint": self.recipe_snapshot_fingerprint,
            "approval_source": self.approval_source,
            "approved_at": self.approved_at,
            "approver_label": self.approver_label,
            "supersedes_fingerprint": self.supersedes_fingerprint,
            "run_decisions": dict(self.run_decisions),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ApprovalRecord":
        projection_value = value["projection"]
        projection = ApprovalProjection(
            dict(projection_value["brief"]),
            dict(projection_value["recipe"]),
            dict(projection_value["adaptation_envelope"]),
        )
        return cls(
            investigation_id=str(value["investigation_id"]),
            status=ApprovalStatus(value["status"]),
            projection=projection,
            projection_fingerprint=str(value["projection_fingerprint"]),
            displayed_fingerprint=str(value.get("displayed_fingerprint", value["projection_fingerprint"])),
            recipe_snapshot_fingerprint=str(value["recipe_snapshot_fingerprint"]),
            approval_source=str(value.get("approval_source", "")),
            approved_at=str(value["approved_at"]),
            approver_label=value.get("approver_label"),
            supersedes_fingerprint=value.get("supersedes_fingerprint"),
            run_decisions=dict(value.get("run_decisions", {})),
        )

    def superseded(self) -> "ApprovalRecord":
        return ApprovalRecord(
            investigation_id=self.investigation_id,
            status=ApprovalStatus.SUPERSEDED,
            projection=self.projection,
            projection_fingerprint=self.projection_fingerprint,
            displayed_fingerprint=self.displayed_fingerprint,
            recipe_snapshot_fingerprint=self.recipe_snapshot_fingerprint,
            approval_source=self.approval_source,
            approved_at=self.approved_at,
            approver_label=self.approver_label,
            supersedes_fingerprint=self.supersedes_fingerprint,
            run_decisions=dict(self.run_decisions),
        )


@dataclass(frozen=True)
class MaterialChange:
    field: str
    before: Any
    after: Any
    requires_reapproval: bool
    reason: str


@dataclass(frozen=True)
class ReuseCandidate:
    stage_id: str
    status: str
    reason: str
    source_revision: str = ""
    age: str = ""


def approval_projection(
    brief: WorkBrief | dict[str, Any],
    recipe: ExecutionRecipe | dict[str, Any],
    adaptation_envelope: AdaptationEnvelope | dict[str, Any],
) -> ApprovalProjection:
    envelope = adaptation_envelope if isinstance(adaptation_envelope, AdaptationEnvelope) else AdaptationEnvelope.from_dict(adaptation_envelope)
    envelope.validate()
    return ApprovalProjection.from_values(brief, recipe, envelope)


def _sanitize_projection(value: Any, key: str = "") -> Any:
    lowered = key.lower()
    if any(marker in lowered for marker in ("secret", "token", "password", "credential", "authorization", "raw_payload", "raw_result", "header")):
        return "[excluded]"
    if isinstance(value, dict):
        return {str(item_key): _sanitize_projection(item_value, str(item_key)) for item_key, item_value in sorted(value.items()) if item_key not in {"raw_provider_payload", "credentials"}}
    if isinstance(value, (list, tuple)):
        return [_sanitize_projection(item, key) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
