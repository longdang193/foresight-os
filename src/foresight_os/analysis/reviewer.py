from __future__ import annotations

from dataclasses import asdict, replace
import json
from collections.abc import Mapping
from typing import Any, TYPE_CHECKING

from foresight_os.analysis.review_core import ReviewResult, review_analysis_state, review_reasoning, parse_review_objections
from foresight_os.controller.skills import SkillRegistry
from foresight_os.domain.challenge import ChallengeObjection, ObjectionDisposition, ReviewOutcome
from foresight_os.domain.models import AnalyticalRecord, CalculationRecord, Evidence

if TYPE_CHECKING:
    from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
    from foresight_os.runtime.executors import ReviewerExecutor


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
    from foresight_os.runtime.executors import ReviewerExecutor as RuntimeReviewerExecutor
    from foresight_os.runtime.participants import ParticipantConfig

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
    reviewer = executor or RuntimeReviewerExecutor(client, factory, participant, context)
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


async def review_analysis_state_with_skills(
    state: object,
    *,
    client: Any | None = None,
    executor: ReviewerExecutor | None = None,
    factory: AgentFactory | None = None,
    run_context: Mapping[str, Any] | None = None,
) -> ReviewResult:
    calculations = list(getattr(state, "calculations", ()))
    from foresight_os.controller.policy import ReviewPolicyResolver

    policy = ReviewPolicyResolver().resolve(target_kind="QUANTITATIVE_ANALYSIS" if calculations else "CLAIM")
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
