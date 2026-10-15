from dataclasses import dataclass, field
from enum import StrEnum
import json
from typing import Any

from foresight_os.controller.profiles import Profile
from foresight_os.runtime.maf_probe import vertical_slice_guardrail


class RecipeName(StrEnum):
    DIRECT = "DIRECT"
    ANALYZE = "ANALYZE"
    ANALYZE_REVIEW = "ANALYZE_REVIEW"
    CONCURRENT = "CONCURRENT"
    HANDOFF = "HANDOFF"
    CHALLENGE_RECOMMENDATION = "CHALLENGE_RECOMMENDATION"


class ExecutionPattern(StrEnum):
    DIRECT = "direct"
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    HANDOFF = "handoff"
    GROUP_CHAT = "group_chat"


class ReviewCheckKind(StrEnum):
    SOURCE_FIDELITY = "source_fidelity"
    SCOPE_RECONCILIATION = "scope_reconciliation"
    CALCULATION_RECONCILIATION = "calculation_reconciliation"
    DECISION_CHALLENGE = "decision_challenge"


INDEPENDENT_VALIDATION_POLICY = "independent-validation/v1"
TYPED_REVIEW_CHECK_IDS = tuple(item.value for item in ReviewCheckKind)
DEFAULT_REVIEW_CHECK_IDS = (
    ReviewCheckKind.SOURCE_FIDELITY.value,
    ReviewCheckKind.SCOPE_RECONCILIATION.value,
    ReviewCheckKind.DECISION_CHALLENGE.value,
)
DEFAULT_REVIEWER_CAPABILITY_IDS = DEFAULT_REVIEW_CHECK_IDS
DEFAULT_REVIEWER_SKILL_IDS = (
    "source-appraisal",
    "key-assumptions-check",
    "red-team-claim",
)


def _normalize_role(value: object) -> object:
    if not isinstance(value, dict):
        return value
    normalized = dict(value)
    for key in (
        "capability_ids",
        "handoff_targets",
        "review_check_ids",
        "reviewer_capability_ids",
        "skill_ids",
        "unresolved_capabilities",
    ):
        if key in normalized:
            normalized[key] = tuple(normalized[key])
    return normalized


@dataclass(frozen=True)
class StageInput:
    decision_question: str
    horizon: str
    objective: str
    expected_result: str
    relevant_constraints: tuple[str, ...] = ()
    dependency_outputs: tuple[tuple[str, object], ...] = ()
    research_needs: tuple[object, ...] = ()
    analysis_contract_fingerprints: tuple[tuple[str, str], ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "decision_question": self.decision_question,
            "horizon": self.horizon,
            "objective": self.objective,
            "expected_result": self.expected_result,
            "relevant_constraints": self.relevant_constraints,
            "dependency_outputs": {stage_id: output for stage_id, output in self.dependency_outputs},
            "research_needs": self.research_needs,
            "analysis_contract_fingerprints": dict(self.analysis_contract_fingerprints),
        }

    def __str__(self) -> str:
        return json.dumps(self.to_payload(), sort_keys=True, default=str, separators=(",", ":"))


@dataclass(frozen=True)
class RecipeStage:
    stage_id: str
    pattern: ExecutionPattern
    participants: tuple[object, ...]
    input_type: str
    output_type: str
    limits: dict[str, int | str]
    skill_ids: tuple[str, ...] = ()
    objective: str = ""
    dependencies: tuple[str, ...] = ()
    expected_result: str = ""
    research_needs: tuple[object, ...] = ()
    decision_question: str = ""
    horizon: str = "unspecified"
    relevant_constraints: tuple[str, ...] = ()
    rationale: str = ""
    capabilities: tuple[str, ...] = ()
    access_scope: tuple[str, ...] = ()
    participant_responsibilities: tuple[dict[str, str], ...] = ()
    provider: str = "local"
    model: str = "unspecified"
    reasoning_controls: dict[str, str | int | float | bool] = field(default_factory=dict)
    review_checks: tuple[str, ...] = ()
    completion_rule: str = ""
    escalation_rule: str = ""
    partial_result_rule: str = ""
    reuse_policy: str = "reuse only committed, provenance-complete matching receipts"
    adaptation_policy: tuple[str, ...] = ()
    result_contract: str = "analysis-stage-result/v1"
    synthesis_policy: str = "aggregate-typed-results"

    @property
    def typed_review_checks(self) -> tuple[str, ...]:
        return tuple(item for item in self.review_checks if item in TYPED_REVIEW_CHECK_IDS)

    def to_dict(self) -> dict[str, Any]:
        value = {
            "stage_id": self.stage_id,
            "pattern": self.pattern.value,
            "participants": list(self.participants),
            "input_type": self.input_type,
            "output_type": self.output_type,
            "limits": dict(self.limits),
            "skill_ids": list(self.skill_ids),
            "objective": self.objective,
            "dependencies": list(self.dependencies),
            "expected_result": self.expected_result,
            "research_needs": list(self.research_needs),
            "decision_question": self.decision_question,
            "horizon": self.horizon,
            "relevant_constraints": list(self.relevant_constraints),
            "rationale": self.rationale,
            "capabilities": list(self.capabilities),
            "access_scope": list(self.access_scope),
            "participant_responsibilities": [dict(item) for item in self.participant_responsibilities],
            "provider": self.provider,
            "model": self.model,
            "reasoning_controls": dict(self.reasoning_controls),
            "review_checks": list(self.review_checks),
            "completion_rule": self.completion_rule,
            "escalation_rule": self.escalation_rule,
            "partial_result_rule": self.partial_result_rule,
            "reuse_policy": self.reuse_policy,
            "adaptation_policy": list(self.adaptation_policy),
            "result_contract": self.result_contract,
            "synthesis_policy": self.synthesis_policy,
        }
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RecipeStage":
        return cls(
            stage_id=str(value["stage_id"]),
            pattern=ExecutionPattern(value["pattern"]),
            participants=tuple(_normalize_role(item) for item in value.get("participants", ())),
            input_type=str(value.get("input_type", "prompt")),
            output_type=str(value.get("output_type", "typed-result")),
            limits=dict(value.get("limits", {})),
            skill_ids=tuple(value.get("skill_ids", ())),
            objective=str(value.get("objective", "")),
            dependencies=tuple(value.get("dependencies", ())),
            expected_result=str(value.get("expected_result", "")),
            research_needs=tuple(value.get("research_needs", ())),
            decision_question=str(value.get("decision_question", "")),
            horizon=str(value.get("horizon", "unspecified")),
            relevant_constraints=tuple(value.get("relevant_constraints", ())),
            rationale=str(value.get("rationale", "")),
            capabilities=tuple(value.get("capabilities", ())),
            access_scope=tuple(value.get("access_scope", ())),
            participant_responsibilities=tuple(dict(item) for item in value.get("participant_responsibilities", ())),
            provider=str(value.get("provider", "local")),
            model=str(value.get("model", "unspecified")),
            reasoning_controls=dict(value.get("reasoning_controls", {})),
            review_checks=tuple(value.get("review_checks", ())),
            completion_rule=str(value.get("completion_rule", "")),
            escalation_rule=str(value.get("escalation_rule", "")),
            partial_result_rule=str(value.get("partial_result_rule", "")),
            reuse_policy=str(value.get("reuse_policy", "reuse only committed, provenance-complete matching receipts")),
            adaptation_policy=tuple(value.get("adaptation_policy", ())),
            result_contract=str(value.get("result_contract", "analysis-stage-result/v1")),
            synthesis_policy=str(value.get("synthesis_policy", "aggregate-typed-results")),
        )


@dataclass(frozen=True)
class ExecutionRecipe:
    name: RecipeName
    pattern: str
    roles: list[dict[str, str]]
    max_agent_steps: int
    max_correction_rounds: int
    max_total_agent_calls: int
    completion: str
    escalation: str
    partial_result: str
    metadata: dict[str, str] = field(default_factory=dict)
    purpose: str = "execute"
    stages: tuple[RecipeStage, ...] = ()
    rationale: str = ""
    review_policy: str = ""
    reuse_policy: str = ""
    adaptation_policy: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name.value,
            "pattern": self.pattern,
            "roles": [dict(role) for role in self.roles],
            "max_agent_steps": self.max_agent_steps,
            "max_correction_rounds": self.max_correction_rounds,
            "max_total_agent_calls": self.max_total_agent_calls,
            "completion": self.completion,
            "escalation": self.escalation,
            "partial_result": self.partial_result,
            "metadata": dict(self.metadata),
            "purpose": self.purpose,
            "stages": [stage.to_dict() for stage in self.stages],
            "rationale": self.rationale,
            "review_policy": self.review_policy,
            "reuse_policy": self.reuse_policy,
            "adaptation_policy": list(self.adaptation_policy),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExecutionRecipe":
        return cls(
            name=RecipeName(value["name"]),
            pattern=str(value["pattern"]),
            roles=[_normalize_role(role) for role in value.get("roles", ())],
            max_agent_steps=int(value.get("max_agent_steps", 0)),
            max_correction_rounds=int(value.get("max_correction_rounds", 0)),
            max_total_agent_calls=int(value.get("max_total_agent_calls", 0)),
            completion=str(value.get("completion", "")),
            escalation=str(value.get("escalation", "")),
            partial_result=str(value.get("partial_result", "")),
            metadata=dict(value.get("metadata", {})),
            purpose=str(value.get("purpose", "execute")),
            stages=tuple(RecipeStage.from_dict(stage) for stage in value.get("stages", ())),
            rationale=str(value.get("rationale", "")),
            review_policy=str(value.get("review_policy", "")),
            reuse_policy=str(value.get("reuse_policy", "")),
            adaptation_policy=tuple(value.get("adaptation_policy", ())),
        )


def make_recipe(name: RecipeName) -> ExecutionRecipe:
    guardrail = vertical_slice_guardrail()
    roles = [{"purpose": "execute", "profile": Profile.NORMAL.value}]
    pattern = "direct"
    if name == RecipeName.ANALYZE:
        pattern = "sequential"
    if name == RecipeName.ANALYZE_REVIEW:
        pattern = "sequential"
        roles = [
            {"purpose": "execute", "profile": Profile.NORMAL.value},
            {
                "purpose": "review",
                "profile": Profile.NORMAL.value,
                "capability_ids": (),
                "reviewer_capability_ids": DEFAULT_REVIEWER_CAPABILITY_IDS,
                "review_check_ids": DEFAULT_REVIEW_CHECK_IDS,
                "skill_ids": DEFAULT_REVIEWER_SKILL_IDS,
            },
        ]
    if name == RecipeName.CONCURRENT:
        pattern = "concurrent"
        roles = [
            {"purpose": "scan-a", "profile": Profile.NORMAL.value},
            {"purpose": "scan-b", "profile": Profile.NORMAL.value},
        ]
    if name == RecipeName.HANDOFF:
        pattern = "handoff"
        roles = [
            {"purpose": "analyst", "profile": Profile.NORMAL.value, "handoff_targets": ("participant-2",)},
            {"purpose": "reviewer", "profile": Profile.NORMAL.value, "handoff_targets": ()},
        ]
    if name == RecipeName.CHALLENGE_RECOMMENDATION:
        pattern = "group_chat"
        roles = [
            {"purpose": "analyst", "profile": Profile.NORMAL.value},
            {"purpose": "skeptic", "profile": Profile.NORMAL.value},
        ]
    stage = RecipeStage(
        "stage-1",
        ExecutionPattern(pattern),
        tuple(
            {
                **role,
                "id": role.get("id", f"participant-{index}"),
            }
            for index, role in enumerate(roles, 1)
        ),
        "prompt",
        "typed-result",
        {"max_agent_steps": guardrail.max_agent_steps, "max_total_agent_calls": guardrail.max_total_agent_calls},
        review_checks=(DEFAULT_REVIEW_CHECK_IDS if name == RecipeName.ANALYZE_REVIEW else ()),
    )
    return ExecutionRecipe(
        name,
        pattern,
        roles,
        guardrail.max_agent_steps,
        guardrail.max_correction_rounds,
        guardrail.max_total_agent_calls,
        "accepted recommendation after required evidence and review",
        "route to human decision/review boundary",
        "no accepted recommendation; preserve partial state",
        purpose=name.value,
        stages=(stage,),
        review_policy=INDEPENDENT_VALIDATION_POLICY if name == RecipeName.ANALYZE_REVIEW else "",
    )
