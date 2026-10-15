from typing import Any

from foresight_os.domain.models import WorkBrief


_UNKNOWN = "not specified"
_NONE_DECLARED = "none declared"


def deliverable_status(requested: str, state: Any) -> str:
    """Evaluate one supported deliverable using explicit state predicates."""

    normalized = str(requested).strip().lower()
    records = state.canonical_records()
    artifacts = tuple(getattr(state, "artifacts", ()))
    accepted_revision = getattr(state.revision_status, "value", state.revision_status) == "ACCEPTED"
    stale_artifact_ids = set(getattr(state.invalidation, "stale_artifact_ids", ()))

    def current_receipt(item: Any, destination: str) -> bool:
        receipt = getattr(item, "delivery_receipt", None)
        if not accepted_revision or item.id in stale_artifact_ids or item.lifecycle.value != "CURRENT" or not isinstance(receipt, dict):
            return False
        return (
            receipt.get("destination") == destination
            and receipt.get("source_revision") == state.revision
            and receipt.get("confirmed_state") in {"CONFIRMED", "SUCCEEDED"}
            and bool(receipt.get("presentation_spec_hash"))
            and item.id.endswith(str(receipt["presentation_spec_hash"])[:16])
        )
    if normalized in {"analysis", "analytical records"}:
        return "PERSISTED" if bool(records) else "NOT_STARTED"
    if normalized in {"calculation", "verified calculation", "verified calculations"}:
        return "PERSISTED" if any(getattr(item.verification_status, "value", item.verification_status) == "VERIFIED" for item in state.calculations) else "NOT_STARTED"
    if normalized in {"report", "executive report"}:
        return "PERSISTED" if any(str(item.kind).lower() == "report" and item.lifecycle.value == "CURRENT" for item in artifacts) else "NOT_STARTED"
    if normalized in {"presentation outline", "presentation-spec", "presentation spec"}:
        return "PERSISTED" if any(str(item.kind).lower() in {"presentation-outline", "presentation_spec"} and item.lifecycle.value == "CURRENT" for item in artifacts) else "NOT_STARTED"
    if normalized in {"pptx", "verified pptx"}:
        return "PERSISTED" if any(current_receipt(item, "pptx") for item in artifacts) else "NOT_STARTED"
    if normalized in {"canva", "canva design", "canva receipt"}:
        return "PERSISTED" if any(current_receipt(item, "canva") for item in artifacts) else "NOT_STARTED"
    return "NOT_VERIFIED"


def _inline(value: Any, fallback: str = _UNKNOWN) -> str:
    if value is None:
        return fallback
    text = str(value).replace("\\", "\\\\").replace("\r\n", " ").replace("\n", " ").strip()
    if not text:
        return fallback
    if text[:1] in {"#", ">", "-", "*", "+"}:
        return "\\" + text
    return text


def _items(value: Any, empty_label: str = _UNKNOWN) -> list[str]:
    if value is None:
        return [empty_label]
    if isinstance(value, (str, bytes)):
        values = [value] if str(value).strip() else []
    else:
        values = list(value)
    return [_inline(item) for item in values] or [empty_label]


def _append_bullets(lines: list[str], values: Any, empty_label: str = _UNKNOWN) -> None:
    lines.extend(f"- {item}" for item in _items(values, empty_label))


def _render_intent(lines: list[str], intent: dict[str, Any] | None) -> None:
    if not intent:
        lines.append(f"- {_UNKNOWN}")
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
        values = intent.get(key, ())
        if values:
            lines.append(f"- {label}: {', '.join(_inline(item) for item in values)}")
            rendered = True
    reasoning = intent.get("preferred_reasoning_controls") or {}
    if reasoning:
        controls = ", ".join(f"{_inline(key)}={_inline(value)}" for key, value in sorted(reasoning.items()))
        lines.append(f"- Preferred reasoning controls: {controls}")
        rendered = True
    if intent.get("source"):
        lines.append(f"- Intent source: {_inline(intent['source'])}")
        rendered = True
    if not rendered:
        lines.append(f"- {_UNKNOWN}")


def render_work_brief_markdown(brief: WorkBrief | dict[str, Any]) -> str:
    value = brief.to_dict() if isinstance(brief, WorkBrief) else dict(brief)
    lines = [
        "# Work Brief",
        "",
        "> Generated from the canonical WorkBrief fields.",
        "> Revise the structured WorkBrief rather than editing this generated body.",
        "",
        "## Decision",
        "",
        _inline(value.get("decision_question")),
        "",
        "## Context",
        "",
        f"- Investigation: {_inline(value.get('investigation_id'))}",
        f"- Horizon: {_inline(value.get('horizon'))}",
        f"- Consequence level: {_inline(value.get('consequence_level'))}",
        "",
        "## Scope",
        "",
    ]
    _append_bullets(lines, value.get("scope"))
    lines.extend(["", "## Evidence and research needs", ""])
    needs_found = False
    for stage in value.get("stages") or ():
        for need in stage.get("research_needs") or ():
            kind = _inline(need.get("kind"))
            query = _inline(need.get("query"))
            source_hint = need.get("source_hint")
            suffix = f" (source: {_inline(source_hint)})" if source_hint else ""
            lines.append(f"- [{kind}] {query}{suffix}")
            needs_found = True
    if not needs_found:
        lines.append(f"- {_UNKNOWN}")
    lines.extend(["", "## Assumptions", ""])
    _append_bullets(lines, value.get("assumptions"), _NONE_DECLARED)
    lines.extend(["", "## Open dependencies", ""])
    _append_bullets(lines, value.get("open_dependencies"), _NONE_DECLARED)
    lines.extend(["", "## Execution intent", ""])
    _render_intent(lines, value.get("execution_intent"))
    lines.extend(["", "## Proposed investigation", ""])
    stages = value.get("stages") or ()
    if not stages:
        lines.append(f"- {_UNKNOWN}")
    for stage in stages:
        lines.extend([
            f"### {_inline(stage.get('stage_id'))}",
            "",
            f"- Objective: {_inline(stage.get('objective'))}",
            f"- Participants: {', '.join(_items(stage.get('participants')))}",
            f"- Subtasks: {', '.join(_items(stage.get('subtasks')))}",
            f"- Dependencies: {', '.join(_items(stage.get('dependencies')))}",
            f"- Expected result: {_inline(stage.get('expected_result'))}",
            f"- Skills: {', '.join(_items(stage.get('skill_ids')))}",
            "- Execution intent:",
        ])
        _render_intent(lines, stage.get("execution_intent"))
        if stage.get("limits"):
            limits = ", ".join(f"{_inline(key)}={_inline(value)}" for key, value in sorted(stage["limits"].items()))
            lines.append(f"- Limits: {limits}")
        lines.append("")
    lines.extend(["## Deliverables", ""])
    _append_bullets(lines, value.get("desired_deliverables"))
    lines.extend([
        "",
        "## Current direction",
        "",
        _inline(value.get("current_direction")),
        "",
        "## Next step",
        "",
        _inline(value.get("next_useful_step")),
    ])
    producer = value.get("producer")
    if producer:
        lines.extend([
            "",
            "## Method provenance",
            "",
            f"- Producer: {_inline(producer.get('id'))}",
            f"- Source: {_inline(producer.get('source'))}",
            f"- Contract version: {_inline(producer.get('contract_version'))}",
        ])
        if producer.get("content_sha256"):
            lines.append(f"- Content SHA-256: {_inline(producer['content_sha256'])}")
    return "\n".join(lines).rstrip() + "\n"
