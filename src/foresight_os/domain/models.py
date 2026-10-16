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


class CalculationVerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"


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
class MethodProvenance:
    id: str
    source: str
    contract_version: str = "1"
    content_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = {
            "id": self.id,
            "source": self.source,
            "contract_version": self.contract_version,
        }
        if self.content_sha256:
            value["content_sha256"] = self.content_sha256
        return value


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
    verification_status: CalculationVerificationStatus = CalculationVerificationStatus.NOT_VERIFIED


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
    monitoring_indicators: tuple[str, ...] = ()


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    path: str
    lifecycle: Lifecycle = Lifecycle.CURRENT
    relationship_ids: list[str] = field(default_factory=list)
    delivery_receipt: dict[str, Any] | None = None


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
    schema_version: int = 2
    revision_status: RevisionStatus = RevisionStatus.ACCEPTED
    calculations: list[CalculationRecord] = field(default_factory=list)
    pending_token: str | None = None
    review_records: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_records(self) -> dict[str, dict[str, Any]]:
        value = self.to_dict()
        records: dict[str, dict[str, Any]] = {}
        for collection in ("evidence", "calculations", "claims", "implications", "recommendations", "artifacts", "relationships"):
            records.update({item["id"]: item for item in value[collection]})
        return records


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
    execution_intent: "ExecutionIntent | None" = None


@dataclass(frozen=True)
class ExecutionIntent:
    required_patterns: tuple[str, ...] = ()
    preferred_patterns: tuple[str, ...] = ()
    required_participants: tuple[str, ...] = ()
    preferred_participants: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    preferred_capabilities: tuple[str, ...] = ()
    preferred_reasoning_controls: dict[str, str | int | float | bool] = field(default_factory=dict)
    source: str = "user"

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_patterns": list(self.required_patterns),
            "preferred_patterns": list(self.preferred_patterns),
            "required_participants": list(self.required_participants),
            "preferred_participants": list(self.preferred_participants),
            "required_capabilities": list(self.required_capabilities),
            "preferred_capabilities": list(self.preferred_capabilities),
            "preferred_reasoning_controls": dict(self.preferred_reasoning_controls),
            "source": self.source,
        }


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
    horizon: str = "unspecified"
    consequence_level: str = "standard"
    user_preferences: dict[str, Any] = field(default_factory=dict)
    analysis_inputs: Any = field(default_factory=dict)
    execution_intent: ExecutionIntent | None = None
    producer: MethodProvenance | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("execution_pattern_override", None)
        if self.producer is None:
            value.pop("producer", None)
        else:
            value["producer"] = self.producer.to_dict()
        if not self.analysis_inputs:
            value.pop("analysis_inputs", None)
        elif isinstance(self.analysis_inputs, dict):
            value["analysis_inputs"] = [
                {**dict(contract), "domain": str(domain)} if isinstance(contract, dict) else {"domain": str(domain)}
                for domain, contract in self.analysis_inputs.items()
            ]
        if self.execution_intent is None:
            if self.execution_pattern_override is None:
                value.pop("execution_intent", None)
            else:
                patterns = (self.execution_pattern_override,) if isinstance(self.execution_pattern_override, str) else tuple(self.execution_pattern_override)
                value["execution_intent"] = ExecutionIntent(required_patterns=tuple(str(item) for item in patterns)).to_dict()
        else:
            value["execution_intent"] = self.execution_intent.to_dict()
        for stage_value, stage in zip(value.get("stages", ()), self.stages):
            stage_value.pop("execution_pattern_override", None)
            if stage.execution_intent is None:
                if stage.execution_pattern_override is None:
                    stage_value.pop("execution_intent", None)
                else:
                    patterns = (stage.execution_pattern_override,) if isinstance(stage.execution_pattern_override, str) else tuple(stage.execution_pattern_override)
                    stage_value["execution_intent"] = ExecutionIntent(required_patterns=tuple(str(item) for item in patterns)).to_dict()
            else:
                stage_value["execution_intent"] = stage.execution_intent.to_dict()
        return value
