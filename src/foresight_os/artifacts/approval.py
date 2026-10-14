import json
from dataclasses import dataclass
from typing import Any

from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalProjection, approval_projection
from foresight_os.domain.models import WorkBrief


@dataclass(frozen=True)
class ApprovalPackage:
    investigation_id: str
    projection: ApprovalProjection
    reuse_candidates: tuple[dict[str, Any], ...] = ()

    @property
    def fingerprint(self) -> str:
        return self.projection.fingerprint

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "fingerprint": self.fingerprint,
            "projection": self.projection.to_dict(),
            "reuse_candidates": [dict(item) for item in self.reuse_candidates],
        }


def build_approval_package(
    brief: WorkBrief | dict[str, Any],
    recipe: ExecutionRecipe | dict[str, Any],
    adaptation_envelope: AdaptationEnvelope | dict[str, Any] | None = None,
    reuse_candidates: tuple[dict[str, Any], ...] = (),
) -> ApprovalPackage:
    projection = approval_projection(brief, recipe, adaptation_envelope or AdaptationEnvelope())
    investigation_id = brief.investigation_id if isinstance(brief, WorkBrief) else str(brief["investigation_id"])
    return ApprovalPackage(investigation_id, projection, tuple(dict(item) for item in reuse_candidates))


def render_approval_json(package: ApprovalPackage) -> str:
    return json.dumps(package.to_dict(), indent=2, sort_keys=True, default=str) + "\n"


def _approval_inline(value: Any, fallback: str = "not specified") -> str:
    if value is None:
        return fallback
    text = str(value).replace("\\", "\\\\").replace("\r\n", " ").replace("\n", " ").strip()
    if not text:
        return fallback
    if text[:1] in {"#", ">", "-", "*", "+"}:
        return "\\" + text
    return text


def _approval_list(value: Any, fallback: str = "not specified") -> str:
    if not value:
        return fallback
    return ", ".join(_approval_inline(item) for item in value)


def _approval_json(value: Any, fallback: str = "not specified") -> str:
    return json.dumps(value, sort_keys=True) if value else fallback


def _render_intent_lines(lines: list[str], intent: dict[str, Any] | None) -> None:
    if not intent:
        lines.append("- User execution intent: not specified")
        return
    rendered = False
    for label, key in (
        ("Required patterns", "required_patterns"),
        ("Preferred patterns", "preferred_patterns"),
        ("Required participants", "required_participants"),
        ("Preferred participants", "preferred_participants"),
        ("Required capabilities", "required_capabilities"),
        ("Preferred capabilities", "preferred_capabilities"),
    ):
        if intent.get(key):
            lines.append(f"- {label}: {_approval_list(intent[key])}")
            rendered = True
    if intent.get("preferred_reasoning_controls"):
        lines.append(f"- Preferred reasoning controls: {_approval_json(intent['preferred_reasoning_controls'])}")
        rendered = True
    if intent.get("source"):
        lines.append(f"- Intent source: {_approval_inline(intent['source'])}")
        rendered = True
    if not rendered:
        lines.append("- User execution intent: not specified")


def render_approval_markdown(package: ApprovalPackage, *, detailed: bool = False) -> str:
    projection = package.projection.to_dict()
    brief = projection["brief"]
    recipe = projection["recipe"]
    envelope = projection["adaptation_envelope"]
    lines = [
        "# Execution Approval Package",
        "",
        f"Investigation: `{package.investigation_id}`",
        f"Fingerprint: `{package.fingerprint}`",
        "",
        "## Decision",
        f"- Question: {_approval_inline(brief.get('decision_question'))}",
        f"- Scope: {_approval_list(brief.get('scope'))}",
        f"- Deliverables: {_approval_list(brief.get('desired_deliverables'))}",
        f"- Horizon: {_approval_inline(brief.get('horizon'))}",
        "",
        "## Decision Context",
        f"- Assumptions: {_approval_list(brief.get('assumptions'), 'none declared')}",
        f"- Open dependencies: {_approval_list(brief.get('open_dependencies'), 'none declared')}",
    ]
    producer = brief.get("producer")
    if producer:
        lines.extend([
            f"- Producer: `{_approval_inline(producer.get('id'))}`",
            f"- Producer source: {_approval_inline(producer.get('source'))}",
            f"- Producer contract version: {_approval_inline(producer.get('contract_version'))}",
        ])
        if producer.get("content_sha256"):
            lines.append(f"- Producer content SHA-256: `{_approval_inline(producer['content_sha256'])}`")
    _render_intent_lines(lines, brief.get("execution_intent"))
    lines.extend([
        "",
        "## Execution Summary",
        f"- Pattern: `{_approval_inline(recipe.get('pattern'))}`",
        f"- Rationale: {_approval_inline(recipe.get('rationale'))}",
        f"- Completion: {_approval_inline(recipe.get('completion'))}",
        f"- Partial result: {_approval_inline(recipe.get('partial_result'))}",
        f"- Escalation: {_approval_inline(recipe.get('escalation'))}",
        f"- Reuse: {_approval_inline(recipe.get('reuse_policy'))}",
        f"- Maximum agent steps: {_approval_inline(recipe.get('max_agent_steps'))}",
        f"- Maximum correction rounds: {_approval_inline(recipe.get('max_correction_rounds'))}",
        f"- Maximum total agent calls: {_approval_inline(recipe.get('max_total_agent_calls'))}",
        f"- Review policy: {_approval_inline(recipe.get('review_policy'))}",
        f"- Adaptation policy: {_approval_list(recipe.get('adaptation_policy'))}",
        "",
        "## Stages",
    ])
    for stage in recipe.get("stages", []):
        participants = []
        for participant in stage.get("participants", []):
            if isinstance(participant, dict):
                participants.append(_approval_inline(participant.get("id", "not specified")))
            else:
                participants.append(_approval_inline(participant))
        responsibilities = []
        for responsibility in stage.get("participant_responsibilities", []):
            if isinstance(responsibility, dict):
                responsibilities.append(_approval_json(responsibility))
            else:
                responsibilities.append(_approval_inline(responsibility))
        lines.extend([
            f"### {_approval_inline(stage.get('stage_id'))}: {_approval_inline(stage.get('objective'))}",
            f"- Pattern: `{_approval_inline(stage.get('pattern'))}`",
            f"- Dependencies: {_approval_list(stage.get('dependencies'), 'none declared')}",
            f"- Expected result: {_approval_inline(stage.get('expected_result'))}",
            f"- Input type: {_approval_inline(stage.get('input_type'))}",
            f"- Output type: {_approval_inline(stage.get('output_type'))}",
            f"- Participants: {', '.join(participants) or 'not specified'}",
            f"- Responsibilities: {', '.join(responsibilities) or 'not specified'}",
            f"- Skills: {_approval_list(stage.get('skill_ids'), 'none declared')}",
            f"- Limits: {_approval_json(stage.get('limits'))}",
            f"- Provider: `{_approval_inline(stage.get('provider'))}`",
            f"- Model: `{_approval_inline(stage.get('model'), 'unavailable')}`",
            f"- Reasoning controls: {_approval_json(stage.get('reasoning_controls'))}",
        ])
        if detailed:
            lines.extend([
                f"- Rationale: {_approval_inline(stage.get('rationale'))}",
                f"- Capabilities: {_approval_list(stage.get('capabilities'), 'none declared')}",
                f"- Access scope: {_approval_list(stage.get('access_scope'), 'none declared')}",
                f"- Review checks: {_approval_list(stage.get('review_checks'), 'none declared')}",
                f"- Completion rule: {_approval_inline(stage.get('completion_rule'))}",
                f"- Escalation rule: {_approval_inline(stage.get('escalation_rule'))}",
                f"- Partial result rule: {_approval_inline(stage.get('partial_result_rule'))}",
                f"- Adaptation policy: {_approval_list(stage.get('adaptation_policy'), 'none declared')}",
            ])
        lines.append("")
    lines.extend([
        "## Approved Adaptation Envelope",
        f"- Allowed operations: {_approval_list(envelope.get('allowed_operations'), 'none declared')}",
        f"- Maximum retries: {_approval_inline(envelope.get('max_retries'))}",
        f"- Maximum concurrency reduction: {_approval_inline(envelope.get('max_concurrency_reduction'))}",
        f"- Compatible participant substitution: {_approval_inline(envelope.get('compatible_participant_substitution'))}",
        f"- Dependency-safe topology reduction: {_approval_inline(envelope.get('dependency_safe_topology_reduction'))}",
        f"- Evidence reuse: {_approval_inline(envelope.get('evidence_reuse'))}",
        f"- Stale reuse fallback: `{_approval_inline(envelope.get('fallback_on_stale_reuse'))}`",
        "",
        "## Reuse Decisions",
    ])
    for candidate in package.reuse_candidates:
        lines.append(
            f"- `{candidate.get('stage_id', '')}`: `{candidate.get('status', '')}` — {candidate.get('reason', '')}"
            + (f" (source revision: {candidate.get('source_revision')})" if candidate.get("source_revision") else "")
        )
    lines.extend([
        "",
        "Review the exact recipe and fingerprint before approving.",
        "",
    ])
    return "\n".join(lines)
