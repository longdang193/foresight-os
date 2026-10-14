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
        f"- Question: {brief.get('decision_question', '')}",
        f"- Scope: {', '.join(brief.get('scope', [])) or 'not specified'}",
        f"- Deliverables: {', '.join(brief.get('desired_deliverables', [])) or 'not specified'}",
        f"- Horizon: {brief.get('horizon', 'unspecified')}",
        "",
        "## Execution Summary",
        f"- Pattern: `{recipe.get('pattern', '')}`",
        f"- Rationale: {recipe.get('rationale', '')}",
        f"- Completion: {recipe.get('completion', '')}",
        f"- Escalation: {recipe.get('escalation', '')}",
        f"- Reuse: {recipe.get('reuse_policy', '')}",
        "",
        "## Stages",
    ]
    for stage in recipe.get("stages", []):
        lines.extend([
            f"### {stage.get('stage_id', '')}: {stage.get('objective', '')}",
            f"- Pattern: `{stage.get('pattern', '')}`",
            f"- Dependencies: {', '.join(stage.get('dependencies', [])) or 'none'}",
            f"- Expected result: {stage.get('expected_result', '')}",
            f"- Participants: {', '.join(str(item.get('id', item)) if isinstance(item, dict) else str(item) for item in stage.get('participants', [])) or 'controller default'}",
            f"- Limits: {json.dumps(stage.get('limits', {}), sort_keys=True)}",
        ])
        if detailed:
            lines.extend([
                f"- Rationale: {stage.get('rationale', '')}",
                f"- Capabilities: {', '.join(stage.get('capabilities', [])) or 'none'}",
                f"- Access scope: {', '.join(stage.get('access_scope', [])) or 'none'}",
                f"- Review checks: {', '.join(stage.get('review_checks', [])) or 'none'}",
                f"- Completion rule: {stage.get('completion_rule', '')}",
                f"- Escalation rule: {stage.get('escalation_rule', '')}",
                f"- Partial result rule: {stage.get('partial_result_rule', '')}",
                f"- Adaptation policy: {', '.join(stage.get('adaptation_policy', [])) or 'none'}",
            ])
        lines.append("")
    lines.extend([
        "## Approved Adaptation Envelope",
        f"- Allowed operations: {', '.join(envelope.get('allowed_operations', [])) or 'none'}",
        f"- Maximum retries: {envelope.get('max_retries', 0)}",
        f"- Stale reuse fallback: `{envelope.get('fallback_on_stale_reuse', 'stop')}`",
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
