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


class RevisionStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ResearchNeedKind(StrEnum):
    EXTERNAL_FACT = "EXTERNAL_FACT"
    SOURCE_DETAIL = "SOURCE_DETAIL"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    STRUCTURED_DATA = "STRUCTURED_DATA"
    QUANTITATIVE_ANALYSIS = "QUANTITATIVE_ANALYSIS"
    EXISTING_EVIDENCE = "EXISTING_EVIDENCE"
    INTERNAL_KNOWLEDGE = "INTERNAL_KNOWLEDGE"
    VALIDATION = "VALIDATION"
    ARTIFACT_OUTPUT = "ARTIFACT_OUTPUT"
    UNRESOLVED_CAPABILITY = "UNRESOLVED_CAPABILITY"


@dataclass(frozen=True)
class ResearchNeed:
    kind: ResearchNeedKind | str
    query: str
    source_hint: str | None = None


@dataclass(frozen=True)
class MeasurementKey:
    region: str
    measure: str
    period: str
    units: str
    scenario: str = "default"
    version: str = "v1"


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
    measurement_key: MeasurementKey | None = None


@dataclass(frozen=True)
class EvidenceCandidate:
    candidate_id: str
    capability_id: str
    source: str
    request: str
    excerpt: str
    provenance: dict[str, str] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    acquisition_kind: str = "unknown"
    retrieved_at: str = ""
    query: str = ""
    context: str = ""
    raw_result: Any = None
    retrieval_proof: Any = None


@dataclass(frozen=True)
class CalculationRecord:
    id: str
    key: MeasurementKey
    formula: str
    input_ids: list[str]
    output: float
    units: str
    source_locators: list[str]


@dataclass(frozen=True)
class AnalyticalRecord:
    id: str
    statement: str
    basis: Basis
    assessment: Assessment
    lifecycle: Lifecycle = Lifecycle.CURRENT
    evidence_ids: list[str] = field(default_factory=list)
    relationship_ids: list[str] = field(default_factory=list)
    assumptions: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    confidence_rationale: str = ""
    disconfirmation_conditions: tuple[str, ...] = ()


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
    schema_version: int = 1
    revision_status: RevisionStatus = RevisionStatus.ACCEPTED
    calculations: list[CalculationRecord] = field(default_factory=list)
    pending_token: str | None = None
    review_records: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkStage:
    stage_id: str
    objective: str
    participants: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    expected_result: str = ""
    research_needs: list[ResearchNeed | str] = field(default_factory=list)
    skill_ids: list[str] = field(default_factory=list)
    execution_pattern_override: str | list[str] | None = None
    limits: dict[str, int | str] = field(default_factory=dict)


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
    execution_pattern_override: str | list[str] | None = None
    stages: list[WorkStage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
