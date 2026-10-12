from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Basis(StrEnum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"


class Assessment(StrEnum):
    UNASSESSED = "UNASSESSED"
    SUPPORTED = "SUPPORTED"
    UNCERTAIN = "UNCERTAIN"
    CONTESTED = "CONTESTED"
    REFUTED = "REFUTED"


class Lifecycle(StrEnum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class SourceLocator:
    file_version: str
    sheet: str
    range: str
    units: str
    transformation: str
    calculation: str


@dataclass(frozen=True)
class Evidence:
    id: str
    source_locator: SourceLocator
    version: str
    date: str
    excerpt: str
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalyticalRecord:
    id: str
    statement: str
    basis: Basis
    assessment: Assessment
    lifecycle: Lifecycle = Lifecycle.CURRENT
    evidence_ids: list[str] = field(default_factory=list)
    relationship_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    path: str
    lifecycle: Lifecycle = Lifecycle.CURRENT
    relationship_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Relationship:
    id: str
    from_id: str
    to_id: str
    relation_type: str


@dataclass(frozen=True)
class Revision:
    id: str
    number: int
    change_reason: str
    record_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Invalidation:
    stale_artifact_ids: list[str] = field(default_factory=list)
    reassessment_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisState:
    investigation_id: str
    revision: int
    evidence: list[Evidence] = field(default_factory=list)
    claims: list[AnalyticalRecord] = field(default_factory=list)
    implications: list[AnalyticalRecord] = field(default_factory=list)
    recommendations: list[AnalyticalRecord] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    revisions: list[Revision] = field(default_factory=list)
    invalidation: Invalidation = field(default_factory=Invalidation)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkBrief:
    investigation_id: str
    decision_question: str
    scope: list[str]
    desired_deliverables: list[str]
    assumptions: list[str]
    open_dependencies: list[str]
    current_direction: str
    next_useful_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
