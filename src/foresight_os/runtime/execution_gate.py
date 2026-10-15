from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import Any

from filelock import FileLock

from foresight_os.domain.approval import AdaptationEnvelope, ApprovalStatus, approval_projection
from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.analysis.result_committer import ANALYSIS_STAGE_RESULT_CONTRACT, CanonicalResultCommitter, analysis_stage_result_schema
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.capabilities import CapabilityUnavailableError, prepare_capability_context
from foresight_os.runtime.workflow import run_recipe_async


class ExecutionAdmissionError(ValueError):
    pass


def _required_capability_ids(recipe: ExecutionRecipe) -> tuple[str, ...]:
    values: list[str] = []
    for stage in recipe.stages:
        values.extend(str(item) for item in getattr(stage, "capabilities", ()))
        for participant in getattr(stage, "participants", ()):
            if isinstance(participant, dict):
                values.extend(str(item) for item in participant.get("capability_ids", participant.get("capabilities", ())))
    if not recipe.stages:
        for participant in recipe.roles:
            values.extend(str(item) for item in participant.get("capability_ids", participant.get("capabilities", ())))
    return tuple(dict.fromkeys(item for item in values if item))


def _assert_store_writable(store: AnalysisStore) -> None:
    try:
        store.root.mkdir(parents=True, exist_ok=True)
        fd, path = tempfile.mkstemp(prefix=".execution-preflight-", dir=store.root)
        os.close(fd)
        Path(path).unlink(missing_ok=True)
    except OSError as exc:
        raise ExecutionAdmissionError(f"RESULT_PERSISTENCE_UNAVAILABLE: analysis store is not writable: {exc}") from exc


def _preflight_recipe(store: AnalysisStore, recipe: ExecutionRecipe, run_context: dict[str, Any]) -> None:
    _assert_store_writable(store)
    for stage in recipe.stages:
        contract = str(getattr(stage, "result_contract", ""))
        if contract != ANALYSIS_STAGE_RESULT_CONTRACT:
            raise ExecutionAdmissionError(f"unsupported result contract for stage {stage.stage_id}: {contract or 'missing'}")
        if str(getattr(stage, "output_type", "")) != "typed-result":
            raise ExecutionAdmissionError(f"stage {stage.stage_id} requires unsupported output type")
        if getattr(stage, "pattern", None) is None:
            raise ExecutionAdmissionError(f"stage {stage.stage_id} has no execution pattern")
        pattern = getattr(getattr(stage, "pattern", None), "value", getattr(stage, "pattern", ""))
        output_count = len(getattr(stage, "participants", ()))
        if str(pattern) in {"concurrent", "handoff", "group_chat"} or output_count > 1:
            if str(getattr(stage, "synthesis_policy", "")) != "aggregate-typed-results":
                raise ExecutionAdmissionError(f"stage {stage.stage_id} requires an explicit synthesis policy")
    required = _required_capability_ids(recipe)
    if required:
        try:
            prepare_capability_context(
                required,
                run_context,
                human_approved=True,
            )
        except (CapabilityUnavailableError, RuntimeError, ValueError) as exc:
            raise ExecutionAdmissionError(f"capability preflight failed: {exc}") from exc
    if not isinstance(analysis_stage_result_schema(), dict):
        raise ExecutionAdmissionError("structured output schema is unavailable")


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

    def admit(self, *, prompt: str, run_id: str | None = None, run_context: dict[str, Any] | None = None) -> ApprovedExecution:
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
            _preflight_recipe(self.store, recipe, dict(run_context or {}))
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
        admission = self.admit(prompt=prompt, run_id=run_id, run_context=run_context)
        with FileLock(str(self.store.lock_path)):
            current_approval = self.store.load_execution_approval()
            if current_approval is None or current_approval.status != ApprovalStatus.APPROVED or current_approval.projection_fingerprint != admission.approval_fingerprint:
                raise ExecutionAdmissionError("approval was superseded before dispatch")
        if client is None:
            raise ExecutionAdmissionError("approved execution requires a configured client")
        context = dict(run_context or {})
        context.update({
            "execution_admitted": True,
            "approved_recipe_fingerprint": admission.recipe_fingerprint,
            "approval_projection_fingerprint": admission.approval_fingerprint,
            "run_fresh_stages": tuple(admission.run_decisions.get("run_fresh_stages", ())),
            "fallback_on_stale_reuse": admission.run_decisions.get("fallback_on_stale_reuse", "run_fresh"),
            "human_approved": True,
            "analysis_store": self.store,
            "require_structured_output": True,
            "structured_output_schema": analysis_stage_result_schema(),
            "canonical_result_committer": CanonicalResultCommitter(self.store, self.store.load_brief().investigation_id),
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
