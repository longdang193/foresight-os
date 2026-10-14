from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from foresight_os.controller.policy import select_recipe
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeStage
from foresight_os.controller.task_shape import TaskShape
from foresight_os.domain.models import WorkBrief
from foresight_os.domain.validation import ValidationError, validate_execution_recipe
from foresight_os.persistence.analysis_store import StageReceipt


@dataclass(frozen=True)
class OverrideDiagnostic:
    path: str
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ProposalResult:
    recipe: ExecutionRecipe | None
    diagnostics: tuple[OverrideDiagnostic, ...] = ()
    status: str = "READY_FOR_REVIEW"

    @property
    def accepted(self) -> bool:
        return self.recipe is not None and not any(item.severity == "error" for item in self.diagnostics)


def build_execution_recipe(brief: WorkBrief, task_shape: TaskShape | None = None) -> ProposalResult:
    try:
        recipe = select_recipe(brief, task_shape)
        validate_execution_recipe(recipe)
    except (ValueError, ValidationError) as exc:
        return ProposalResult(None, (OverrideDiagnostic("recipe", "invalid_recipe", str(exc)),), "DRAFT")
    return ProposalResult(recipe, (), "READY_FOR_REVIEW")


def validate_execution_recipe_contract(recipe: ExecutionRecipe) -> tuple[OverrideDiagnostic, ...]:
    try:
        validate_execution_recipe(recipe)
    except (ValueError, ValidationError) as exc:
        return (OverrideDiagnostic("recipe", "invalid_recipe", str(exc)),)
    return ()


def classify_reuse(receipt: StageReceipt | None, *, reusable: bool, reason: str = "") -> dict[str, str]:
    if receipt is None:
        return {"status": "fresh", "reason": reason or "no committed receipt exists"}
    if not receipt.reusable():
        return {"status": "blocked", "reason": reason or "receipt is incomplete or provenance-incomplete"}
    if not reusable:
        return {"status": "fresh", "reason": reason or "fingerprints do not match"}
    return {
        "status": "reusable",
        "reason": reason or "committed receipt matches current inputs and policy",
        "source_revision": receipt.source_revision,
        "created_at": receipt.created_at,
        "age": _receipt_age(receipt.created_at),
    }


def _receipt_age(created_at: str) -> str:
    if not created_at:
        return "unknown"
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        seconds = max(0, int((datetime.now(timezone.utc) - created).total_seconds()))
        return f"{seconds}s"
    except ValueError:
        return "unknown"


def apply_execution_overrides(recipe: ExecutionRecipe, overrides: dict[str, Any]) -> ProposalResult:
    diagnostics: list[OverrideDiagnostic] = []
    allowed = {"pattern", "max_agent_steps", "max_correction_rounds", "max_total_agent_calls", "stages", "review_policy", "reuse_policy", "adaptation_policy"}
    for key in overrides:
        if key not in allowed:
            diagnostics.append(OverrideDiagnostic(key, "unsupported_override", f"override '{key}' is not supported"))
    updated = recipe
    if not diagnostics:
        try:
            if "pattern" in overrides:
                updated = replace(updated, pattern=ExecutionPattern(str(overrides["pattern"])).value)
            for field_name in ("max_agent_steps", "max_correction_rounds", "max_total_agent_calls"):
                if field_name in overrides:
                    value = int(overrides[field_name])
                    if value < 0:
                        raise ValueError(f"{field_name} must be non-negative")
                    updated = replace(updated, **{field_name: value})
            if "review_policy" in overrides:
                updated = replace(updated, review_policy=str(overrides["review_policy"]))
            if "reuse_policy" in overrides:
                updated = replace(updated, reuse_policy=str(overrides["reuse_policy"]))
            if "adaptation_policy" in overrides:
                updated = replace(updated, adaptation_policy=tuple(str(item) for item in overrides["adaptation_policy"]))
            if "stages" in overrides:
                updated = replace(updated, stages=_apply_stage_overrides(updated.stages, overrides["stages"], diagnostics))
        except (TypeError, ValueError) as exc:
            diagnostics.append(OverrideDiagnostic("recipe", "invalid_override", str(exc)))
    if not diagnostics:
        diagnostics.extend(validate_execution_recipe_contract(updated))
    if diagnostics:
        return ProposalResult(None, tuple(diagnostics), "DRAFT")
    return ProposalResult(updated, (), "READY_FOR_REVIEW")


def _apply_stage_overrides(stages: tuple[RecipeStage, ...], requested: Any, diagnostics: list[OverrideDiagnostic]) -> tuple[RecipeStage, ...]:
    if not isinstance(requested, (list, tuple)):
        diagnostics.append(OverrideDiagnostic("stages", "invalid_override", "stages override must be a list"))
        return stages
    by_id = {stage.stage_id: stage for stage in stages}
    for item in requested:
        if not isinstance(item, dict) or "stage_id" not in item:
            diagnostics.append(OverrideDiagnostic("stages", "invalid_override", "each stage override needs stage_id"))
            continue
        stage_id = str(item["stage_id"])
        if stage_id not in by_id:
            diagnostics.append(OverrideDiagnostic(f"stages.{stage_id}", "unknown_stage", "stage does not exist"))
            continue
        stage = by_id[stage_id]
        allowed = {"stage_id", "pattern", "participants", "skill_ids", "capabilities", "access_scope", "limits", "provider", "model", "reasoning_controls", "review_checks", "completion_rule", "escalation_rule", "partial_result_rule", "reuse_policy", "adaptation_policy"}
        unknown = set(item) - allowed
        for key in sorted(unknown):
            diagnostics.append(OverrideDiagnostic(f"stages.{stage_id}.{key}", "unsupported_override", "stage override is not supported"))
        if unknown:
            continue
        try:
            if "pattern" in item:
                stage = replace(stage, pattern=ExecutionPattern(str(item["pattern"])))
            for field_name in ("participants", "skill_ids", "capabilities", "access_scope", "review_checks", "adaptation_policy"):
                if field_name in item:
                    setattr_value = tuple(item[field_name])
                    stage = replace(stage, **{field_name: setattr_value})
            for field_name in ("limits", "reasoning_controls"):
                if field_name in item:
                    stage = replace(stage, **{field_name: dict(item[field_name])})
            for field_name in ("provider", "model", "completion_rule", "escalation_rule", "partial_result_rule", "reuse_policy"):
                if field_name in item:
                    stage = replace(stage, **{field_name: str(item[field_name])})
            if stage.pattern == ExecutionPattern.GROUP_CHAT and len(stage.participants) < 2:
                diagnostics.append(OverrideDiagnostic(f"stages.{stage_id}.participants", "insufficient_participants", "group chat requires at least two participants"))
            by_id[stage_id] = stage
        except (TypeError, ValueError) as exc:
            diagnostics.append(OverrideDiagnostic(f"stages.{stage_id}", "invalid_override", str(exc)))
    return tuple(by_id[stage.stage_id] for stage in stages)
