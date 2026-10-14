from dataclasses import asdict, dataclass, replace
import json
from collections.abc import Mapping, Sequence
from typing import Any

from foresight_os.controller.policy import ReviewPolicyResolver
from foresight_os.controller.skills import SkillRegistry
from foresight_os.domain.challenge import ChallengeObjection, ObjectionDisposition, ReviewOutcome
from foresight_os.domain.models import AnalyticalRecord, CalculationRecord, Evidence
from foresight_os.runtime.executors import ReviewerExecutor
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


@dataclass(frozen=True)
class ReviewResult:
    accepted: bool
    issues: list[str]
    corrected: bool = False
    objections: tuple[ChallengeObjection, ...] = ()
    outcome: ReviewOutcome = ReviewOutcome.PROVISIONAL
    policy_id: str = ""
    policy_version: str = ""
    skill_ids: tuple[str, ...] = ()
    skill_versions: tuple[str, ...] = ()
    skill_hashes: tuple[str, ...] = ()


def _review_objection(value: Any, default_target_id: str) -> ChallengeObjection:
    if isinstance(value, ChallengeObjection):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("reviewer output must contain structured objection mappings")
    disposition = value.get("disposition", ObjectionDisposition.UNRESOLVED)
    return ChallengeObjection(
        kind=str(value.get("kind", "")),
        target_id=str(value.get("target_id", default_target_id)),
        statement=str(value.get("statement", "")),
        evidence_ids=tuple(str(item) for item in value.get("evidence_ids", ())),
        disposition=ObjectionDisposition(str(disposition)),
    )


def parse_review_objections(output: Any, default_target_id: str = "review") -> tuple[ChallengeObjection, ...]:
    """Convert the existing reviewer runtime's structured output into domain objections."""
    if output is None or output == "":
        return ()
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except json.JSONDecodeError as error:
            raise ValueError("reviewer output must be JSON or a structured mapping") from error
    if isinstance(output, Mapping):
        output = output.get("objections", output.get("challenge_objections", ()))
    if not isinstance(output, Sequence) or isinstance(output, (bytes, bytearray)):
        raise ValueError("reviewer output objections must be a sequence")
    return tuple(_review_objection(item, default_target_id) for item in output)


def _review_prompt(evidence: list[Evidence], records: list[AnalyticalRecord], calculations: list[CalculationRecord]) -> str:
    payload = {
        "task": "Return only typed challenge objections for the supplied analytical records.",
        "contract": "ChallengeObjection",
        "objection_schema": {
            "kind": "string",
            "target_id": "string",
            "statement": "string",
            "evidence_ids": ["string"],
            "disposition": [item.value for item in ObjectionDisposition],
        },
        "evidence": [asdict(item) for item in evidence],
        "records": [asdict(item) for item in records],
        "calculations": [asdict(item) for item in calculations],
    }
    return json.dumps(payload, sort_keys=True, default=str)


async def execute_review_skills(
    evidence: list[Evidence],
    records: list[AnalyticalRecord],
    *,
    calculations: list[CalculationRecord] | None = None,
    policy: object | None = None,
    client: Any | None = None,
    executor: ReviewerExecutor | None = None,
    factory: AgentFactory | None = None,
    run_context: Mapping[str, Any] | None = None,
) -> tuple[ChallengeObjection, ...]:
    """Run selected review skills through the canonical ReviewerExecutor seam."""
    skill_ids = tuple(str(item) for item in getattr(policy, "required_skill_ids", ()))
    context = dict(run_context or {})
    if "skill_registry" not in context:
        context["skill_registry"] = SkillRegistry()
    registry = context["skill_registry"]
    skills = registry.resolve(skill_ids)
    participant = ParticipantConfig(
        "reviewer",
        "reviewer",
        "adversarial review",
        skill_ids=skill_ids,
        structured_output={"type": "json", "items": "ChallengeObjection"},
    )
    context.update({"selected_skills": skills})
    reviewer = executor or ReviewerExecutor(client, factory, participant, context)
    output = await reviewer.execute(_review_prompt(evidence, records, list(calculations or ())))
    objections = parse_review_objections(output, records[-1].id if records else "review")
    known_evidence_ids = {item.id for item in evidence}
    known_calculation_ids = {item.id for item in calculations or ()}
    for objection in objections:
        objection.validate(known_evidence_ids, known_calculation_ids)
    return objections


async def review_reasoning_with_skills(
    evidence: list[Evidence],
    records: list[AnalyticalRecord],
    *,
    calculations: list[CalculationRecord] | None = None,
    policy: object | None = None,
    client: Any | None = None,
    executor: ReviewerExecutor | None = None,
    factory: AgentFactory | None = None,
    run_context: Mapping[str, Any] | None = None,
) -> ReviewResult:
    context = dict(run_context or {})
    if "skill_registry" not in context:
        context["skill_registry"] = SkillRegistry()
    deterministic = review_reasoning(evidence, records, calculations=calculations, policy=policy, run_context=context)
    skill_objections = await execute_review_skills(
        evidence,
        records,
        calculations=calculations,
        policy=policy,
        client=client,
        executor=executor,
        factory=factory,
        run_context=context,
    )
    if not skill_objections:
        return deterministic
    objections = (*deterministic.objections, *skill_objections)
    blocking_kinds = {str(item) for item in getattr(policy, "blocking_objection_kinds", ())}
    blocking = [item for item in skill_objections if item.kind in blocking_kinds and item.disposition != ObjectionDisposition.REJECTED]
    issues = [*deterministic.issues, *(f"{item.target_id}: {item.statement}" for item in blocking)]
    accepted = not issues
    return replace(
        deterministic,
        accepted=accepted,
        issues=issues,
        objections=objections,
        outcome=ReviewOutcome.ACCEPTED if accepted else ReviewOutcome.REJECTED,
    )


def review_reasoning(
    evidence: list[Evidence],
    records: list[AnalyticalRecord],
    *,
    calculations: list[CalculationRecord] | None = None,
    policy: object | None = None,
    run_context: Mapping[str, Any] | None = None,
) -> ReviewResult:
    evidence_ids = {item.id for item in evidence}
    issues = []
    objections: list[ChallengeObjection] = []
    for record in records:
        if not record.evidence_ids:
            message = f"{record.id}: missing evidence"
            issues.append(message)
            objections.append(ChallengeObjection("INSUFFICIENT_EVIDENCE", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
        elif not set(record.evidence_ids).issubset(evidence_ids):
            message = f"{record.id}: unknown evidence reference"
            issues.append(message)
            objections.append(ChallengeObjection("SOURCE_CONTRADICTION", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
        if record.basis == "DERIVED" and "forecast" not in record.statement.lower() and "capacity" not in record.statement.lower() and record.id.startswith("claim-"):
            message = f"{record.id}: derived claim needs period and unit context"
            issues.append(message)
            objections.append(ChallengeObjection("UNSUPPORTED_ASSUMPTION", record.id, message, disposition=ObjectionDisposition.UNRESOLVED))
    if any("capacity" in record.statement.lower() for record in records) and not any("conditional" in record.statement.lower() for record in records):
        message = "recommendation must address the capacity contradiction"
        issues.append(message)
        objections.append(ChallengeObjection("ALTERNATIVE_HYPOTHESIS", records[-1].id if records else "review", message, disposition=ObjectionDisposition.UNRESOLVED))
    if calculations is not None and any("formula" in item.statement.lower() for item in records) and not calculations:
        message = "calculation evidence is unavailable"
        issues.append(message)
        objections.append(ChallengeObjection("CALCULATION_ERROR", records[-1].id if records else "review", message, disposition=ObjectionDisposition.UNRESOLVED))
    policy_id = str(getattr(policy, "policy_id", ""))
    policy_version = str(getattr(policy, "version", ""))
    skill_ids = tuple(getattr(policy, "required_skill_ids", ()))
    skill_versions: tuple[str, ...] = ()
    skill_hashes: tuple[str, ...] = ()
    if skill_ids:
        try:
            registry = (run_context or {}).get("skill_registry") if run_context is not None else None
            if registry is None:
                registry = SkillRegistry()
            resolved_skills = registry.resolve(skill_ids)
        except (ValueError, RuntimeError) as error:
            issues.append(f"required review skills unavailable: {error}")
        else:
            skill_versions = tuple(skill.version for skill in resolved_skills)
            skill_hashes = tuple(skill.content_sha256 for skill in resolved_skills)
    unresolved_classification = getattr(policy, "unresolved_classification_issue", None)
    if unresolved_classification:
        issues.append(unresolved_classification)
        objections.append(ChallengeObjection("INSUFFICIENT_EVIDENCE", records[-1].id if records else "review", unresolved_classification, disposition=ObjectionDisposition.UNRESOLVED))
    outcome = ReviewOutcome.ACCEPTED if not issues else ReviewOutcome.REJECTED
    acceptable_outcomes = tuple(str(item) for item in getattr(policy, "acceptable_outcomes", (ReviewOutcome.ACCEPTED.value,)))
    if outcome.value not in acceptable_outcomes:
        issues.append(f"review outcome {outcome.value} is not acceptable under the selected policy")
    blocking_kinds = {str(item) for item in getattr(policy, "blocking_objection_kinds", ())}
    if blocking_kinds:
        for objection in objections:
            if objection.kind in blocking_kinds and objection.disposition != ObjectionDisposition.REJECTED:
                issues.append(f"{objection.target_id}: blocking objection {objection.kind}")
    accepted = not issues
    if not accepted:
        outcome = ReviewOutcome.REJECTED
    return ReviewResult(accepted, issues, objections=tuple(objections), outcome=outcome, policy_id=policy_id, policy_version=policy_version, skill_ids=skill_ids, skill_versions=skill_versions, skill_hashes=skill_hashes)


def review_analysis_state(state: object) -> ReviewResult:
    calculations = list(getattr(state, "calculations", ()))
    policy = ReviewPolicyResolver().resolve(
        target_kind="QUANTITATIVE_ANALYSIS" if calculations else "CLAIM",
    )
    return review_reasoning(
        list(getattr(state, "evidence", ())),
        [*getattr(state, "claims", ()), *getattr(state, "implications", ()), *getattr(state, "recommendations", ())],
        calculations=calculations,
        policy=policy,
    )


async def review_analysis_state_with_skills(
    state: object,
    *,
    client: Any | None = None,
    executor: ReviewerExecutor | None = None,
    factory: AgentFactory | None = None,
    run_context: Mapping[str, Any] | None = None,
) -> ReviewResult:
    calculations = list(getattr(state, "calculations", ()))
    policy = ReviewPolicyResolver().resolve(
        target_kind="QUANTITATIVE_ANALYSIS" if calculations else "CLAIM",
    )
    return await review_reasoning_with_skills(
        list(getattr(state, "evidence", ())),
        [*getattr(state, "claims", ()), *getattr(state, "implications", ()), *getattr(state, "recommendations", ())],
        calculations=calculations,
        policy=policy,
        client=client,
        executor=executor,
        factory=factory,
        run_context=run_context,
    )
