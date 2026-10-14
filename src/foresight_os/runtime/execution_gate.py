from dataclasses import dataclass
from pathlib import Path
from typing import Any

from filelock import FileLock

from foresight_os.domain.approval import AdaptationEnvelope, ApprovalStatus, approval_projection
from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.workflow import run_recipe_async


class ExecutionAdmissionError(ValueError):
    pass


def classify_material_changes(before: dict[str, Any], after: dict[str, Any], envelope: AdaptationEnvelope) -> tuple[dict[str, Any], ...]:
    changes: list[dict[str, Any]] = []
    keys = sorted(set(before) | set(after))
    for key in keys:
        if before.get(key) == after.get(key):
            continue
        allowed = key in {"retry", "concurrency", "topology"} and (
            (key == "retry" and "bounded_retry" in envelope.allowed_operations)
            or (key == "concurrency" and "reduced_concurrency" in envelope.allowed_operations)
            or (key == "topology" and envelope.dependency_safe_topology_reduction)
        )
        changes.append({"field": key, "before": before.get(key), "after": after.get(key), "requires_reapproval": not allowed})
    return tuple(changes)


@dataclass(frozen=True)
class ApprovedExecution:
    work_dir: Path
    prompt: str
    run_id: str
    recipe_fingerprint: str
    approval_fingerprint: str
    run_decisions: dict[str, Any]
    recipe: ExecutionRecipe


class ExecutionGate:
    def __init__(self, store: AnalysisStore):
        self.store = store

    def admit(self, *, prompt: str, run_id: str | None = None) -> ApprovedExecution:
        with FileLock(str(self.store.lock_path)):
            if not self.store.brief_path.exists():
                raise ExecutionAdmissionError("execution requires a persisted WorkBrief")
            if not self.store.execution_recipe_path.exists():
                raise ExecutionAdmissionError("execution requires a persisted ExecutionRecipe")
            brief = self.store.load_brief()
            recipe = self.store.load_recipe()
            approval = self.store.load_execution_approval()
            if approval is None:
                raise ExecutionAdmissionError("execution requires an approved ApprovalRecord")
            if approval.status != ApprovalStatus.APPROVED:
                raise ExecutionAdmissionError(f"execution approval is {approval.status.value.lower()}")
            envelope = AdaptationEnvelope.from_dict(approval.projection.adaptation_envelope)
            current = approval_projection(brief, recipe, envelope)
            recipe_fingerprint = canonical_json_hash(recipe.to_dict())
            if current.fingerprint != approval.projection_fingerprint:
                raise ExecutionAdmissionError("persisted brief or recipe no longer matches the approved projection")
            if approval.displayed_fingerprint != approval.projection_fingerprint:
                raise ExecutionAdmissionError("approval displayed fingerprint is stale")
            if approval.recipe_snapshot_fingerprint != recipe_fingerprint:
                raise ExecutionAdmissionError("persisted recipe no longer matches the approved snapshot")
            if approval.investigation_id != brief.investigation_id:
                raise ExecutionAdmissionError("approval investigation does not match the WorkBrief")
            return ApprovedExecution(
                work_dir=self.store.root,
                prompt=prompt,
                run_id=run_id or f"run-{brief.investigation_id}",
                recipe_fingerprint=recipe_fingerprint,
                approval_fingerprint=approval.projection_fingerprint,
                run_decisions={
                    **dict(approval.run_decisions),
                    "fallback_on_stale_reuse": envelope.fallback_on_stale_reuse,
                },
                recipe=recipe,
            )

    async def execute(
        self,
        *,
        prompt: str,
        client: Any | None = None,
        run_id: str | None = None,
        run_context: dict[str, Any] | None = None,
    ):
        admission = self.admit(prompt=prompt, run_id=run_id)
        with FileLock(str(self.store.lock_path)):
            current_approval = self.store.load_execution_approval()
            if current_approval is None or current_approval.status != ApprovalStatus.APPROVED or current_approval.projection_fingerprint != admission.approval_fingerprint:
                raise ExecutionAdmissionError("approval was superseded before dispatch")
        context = dict(run_context or {})
        context.update({
            "execution_admitted": True,
            "approved_recipe_fingerprint": admission.recipe_fingerprint,
            "approval_projection_fingerprint": admission.approval_fingerprint,
            "run_fresh_stages": tuple(admission.run_decisions.get("run_fresh_stages", ())),
            "fallback_on_stale_reuse": admission.run_decisions.get("fallback_on_stale_reuse", "run_fresh"),
            "analysis_store": self.store,
        })
        return await run_recipe_async(admission.recipe, prompt, client, admission.run_id, context)


async def execute_approved_investigation(
    work_dir: Path,
    prompt: str,
    client: Any | None = None,
    run_id: str | None = None,
    run_context: dict[str, Any] | None = None,
):
    return await ExecutionGate(AnalysisStore(work_dir)).execute(
        prompt=prompt,
        client=client,
        run_id=run_id,
        run_context=run_context,
    )
