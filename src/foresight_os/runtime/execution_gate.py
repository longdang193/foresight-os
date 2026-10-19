from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Any, Mapping

from filelock import FileLock

from foresight_os.domain.approval import AdaptationEnvelope, ApprovalProjection, ApprovalStatus, approval_projection
from foresight_os.controller.recipes import ExecutionRecipe
from foresight_os.analysis.result_committer import ANALYSIS_STAGE_RESULT_CONTRACT, CanonicalResultCommitter, analysis_stage_result_schema
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.domain.analysis_inputs import AnalysisInputContract, GLOBAL_SCOPE, NormalizedIntent, normalize_work_brief
from foresight_os.analysis.workbook_inputs import resolve_workbook_contract, workbook_analyzer_fingerprint
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.runtime.capabilities import CapabilityUnavailableError, admit_capability_context
from foresight_os.runtime.local_toolbelt import SourceSnapshot, ToolbeltError, ToolbeltLimits
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


def _local_capability_context(store: AnalysisStore, run_context: dict[str, Any] | None) -> dict[str, Any]:
    context = dict(run_context or {})
    context.setdefault("local_workspace", store.root)
    context.setdefault("document_roots", (store.root, Path.cwd()))
    return context


def _assert_store_writable(store: AnalysisStore) -> None:
    try:
        store.root.mkdir(parents=True, exist_ok=True)
        fd, path = tempfile.mkstemp(prefix=".execution-preflight-", dir=store.root)
        os.close(fd)
        Path(path).unlink(missing_ok=True)
    except OSError as exc:
        raise ExecutionAdmissionError(f"RESULT_PERSISTENCE_UNAVAILABLE: analysis store is not writable: {exc}") from exc


def _preflight_recipe(
    store: AnalysisStore,
    recipe: ExecutionRecipe,
    run_context: dict[str, Any],
    workbook_source: Path | None = None,
) -> SourceSnapshot | None:
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
            admit_capability_context(
                required,
                run_context,
                human_approved=True,
            )
        except (CapabilityUnavailableError, RuntimeError, ValueError) as exc:
            raise ExecutionAdmissionError(f"capability preflight failed: {exc}") from exc
    if not isinstance(analysis_stage_result_schema(), dict):
        raise ExecutionAdmissionError("structured output schema is unavailable")
    if any(str(getattr(stage, "executor_kind", "agent")) == "deterministic_local" for stage in recipe.stages):
        if workbook_source is None:
            raise ExecutionAdmissionError("BLOCKED_INPUT: deterministic execution requires --workbook")
        if workbook_source.suffix.lower() not in {".xlsx", ".xlsm"} or not workbook_source.is_file():
            raise ExecutionAdmissionError(f"BLOCKED_INPUT: invalid workbook source: {workbook_source}")
        try:
            return SourceSnapshot.capture(workbook_source, max_bytes=ToolbeltLimits().max_bytes)
        except (OSError, ToolbeltError) as exc:
            raise ExecutionAdmissionError(f"BLOCKED_INPUT: cannot capture workbook source: {exc}") from exc
    return ""


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
    brief: Any
    normalized_intent: NormalizedIntent
    approval_projection: ApprovalProjection
    brief_fingerprint: str
    persisted_recipe_fingerprint: str
    effective_contracts: Mapping[str, AnalysisInputContract]
    workbook_source: Path | None = None
    workbook_source_sha256: str = ""
    workbook_snapshot: SourceSnapshot | None = None


def _effective_contract_resolver(
    contracts: Mapping[str, AnalysisInputContract],
):
    def resolve(domain: str, stage_id: str) -> AnalysisInputContract:
        contract = contracts.get(f"{stage_id}:{domain}") or contracts.get(f"{GLOBAL_SCOPE}:{domain}") or contracts.get(domain)
        if contract is None:
            raise ValueError(f"missing effective analysis input contract: {stage_id}:{domain}")
        return contract

    return resolve


class ExecutionGate:
    def __init__(self, store: AnalysisStore):
        self.store = store

    @staticmethod
    def _effective_contracts(
        recipe: ExecutionRecipe,
        normalized_intent: NormalizedIntent,
    ) -> Mapping[str, AnalysisInputContract]:
        effective: dict[str, AnalysisInputContract] = {}
        for declared in normalized_intent.declarations:
            if declared.stage_id is None:
                resolved = normalized_intent.effective_contract_for_domain(declared.domain)
                effective[f"{GLOBAL_SCOPE}:{declared.domain}"] = resolved
                effective.setdefault(declared.domain, resolved)
        for stage in recipe.stages:
            if str(getattr(stage, "executor_kind", "agent")) != "deterministic_local":
                continue
            stage_id = str(getattr(stage, "stage_id", "stage"))
            for domain in getattr(stage, "analysis_domains", ()):
                try:
                    effective[f"{stage_id}:{domain}"] = normalized_intent.effective_contract_for_domain(str(domain), stage_id)
                except ValueError as error:
                    raise ExecutionAdmissionError(str(error)) from error
        return MappingProxyType(effective)

    def admit(
        self,
        *,
        prompt: str,
        run_id: str | None = None,
        run_context: dict[str, Any] | None = None,
        workbook_source: str | Path | None = None,
    ) -> ApprovedExecution:
        with FileLock(str(self.store.lock_path)):
            if not self.store.brief_path.exists():
                raise ExecutionAdmissionError("execution requires a persisted WorkBrief")
            if not self.store.execution_recipe_path.exists():
                raise ExecutionAdmissionError("execution requires a persisted ExecutionRecipe")
            brief = self.store.load_brief()
            loaded_recipe = self.store.load_recipe_bundle()
            recipe = loaded_recipe.recipe
            approval = self.store.load_execution_approval()
            if approval is None:
                raise ExecutionAdmissionError("execution requires an approved ApprovalRecord")
            if approval.status != ApprovalStatus.APPROVED:
                raise ExecutionAdmissionError(f"execution approval is {approval.status.value.lower()}")
            envelope = AdaptationEnvelope.from_dict(approval.projection.adaptation_envelope)
            current = approval_projection(brief, recipe, envelope)
            recipe_fingerprint = canonical_json_hash(recipe.to_dict())
            persisted_recipe_fingerprint = loaded_recipe.persisted_fingerprint
            if current.fingerprint != approval.projection_fingerprint:
                current_compatibility_fingerprint = ApprovalProjection.compatibility_fingerprint_for_dict(current.to_dict())
                approved_compatibility_fingerprint = ApprovalProjection.compatibility_fingerprint_for_dict(approval.projection.to_dict())
                if current_compatibility_fingerprint != approved_compatibility_fingerprint:
                    raise ExecutionAdmissionError("persisted brief or recipe no longer matches the approved projection")
            if approval.displayed_fingerprint != approval.projection_fingerprint:
                raise ExecutionAdmissionError("approval displayed fingerprint is stale")
            if approval.recipe_snapshot_fingerprint not in {recipe_fingerprint, persisted_recipe_fingerprint}:
                raise ExecutionAdmissionError("persisted recipe no longer matches the approved snapshot")
            if approval.investigation_id != brief.investigation_id:
                raise ExecutionAdmissionError("approval investigation does not match the WorkBrief")
            source_path = Path(workbook_source).resolve() if workbook_source is not None else None
            normalized_intent = normalize_work_brief(brief)
            effective_contracts = self._effective_contracts(recipe, normalized_intent)
            brief_fingerprint = canonical_json_hash(brief.to_dict())
        source_snapshot = _preflight_recipe(
            self.store,
            recipe,
            _local_capability_context(self.store, run_context),
            source_path,
        )
        with FileLock(str(self.store.lock_path)):
            current_brief = self.store.load_brief()
            current_recipe_bundle = self.store.load_recipe_bundle()
            current_approval = self.store.load_execution_approval()
            if canonical_json_hash(current_brief.to_dict()) != brief_fingerprint:
                raise ExecutionAdmissionError("persisted WorkBrief changed during workbook capture")
            if current_recipe_bundle.persisted_fingerprint != persisted_recipe_fingerprint or canonical_json_hash(current_recipe_bundle.recipe.to_dict()) != recipe_fingerprint:
                raise ExecutionAdmissionError("persisted ExecutionRecipe changed during workbook capture")
            if (
                current_approval is None
                or current_approval.status != ApprovalStatus.APPROVED
                or current_approval.projection_fingerprint != approval.projection_fingerprint
                or current_approval.displayed_fingerprint != approval.displayed_fingerprint
            ):
                raise ExecutionAdmissionError("approval changed during workbook capture")
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
            brief=brief,
            normalized_intent=normalized_intent,
            approval_projection=approval.projection,
            brief_fingerprint=brief_fingerprint,
            persisted_recipe_fingerprint=persisted_recipe_fingerprint,
            effective_contracts=effective_contracts,
            workbook_source=source_path,
            workbook_source_sha256=source_snapshot.sha256 if source_snapshot else "",
            workbook_snapshot=source_snapshot,
        )

    async def execute(
        self,
        *,
        prompt: str,
        client: Any | None = None,
        run_id: str | None = None,
        run_context: dict[str, Any] | None = None,
        workbook_source: str | Path | None = None,
    ):
        admission = self.admit(
            prompt=prompt,
            run_id=run_id,
            run_context=run_context,
            workbook_source=workbook_source,
        )
        with FileLock(str(self.store.lock_path)):
            current_approval = self.store.load_execution_approval()
            if current_approval is None or current_approval.status != ApprovalStatus.APPROVED or current_approval.projection_fingerprint != admission.approval_fingerprint:
                raise ExecutionAdmissionError("approval was superseded before dispatch")
        has_external_stage = any(
            str(getattr(stage, "executor_kind", "agent")) != "deterministic_local"
            for stage in admission.recipe.stages or ()
        )
        if client is None and has_external_stage:
            raise ExecutionAdmissionError("approved execution requires a configured client")
        normalized_intent = admission.normalized_intent
        context = _local_capability_context(self.store, run_context)
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
            "canonical_result_committer": CanonicalResultCommitter(self.store, admission.brief.investigation_id),
            "normalized_intent": normalized_intent,
            "workbook_source": admission.workbook_source,
            "workbook_source_sha256": admission.workbook_source_sha256,
            "workbook_snapshot": admission.workbook_snapshot,
            "source_revision": admission.workbook_source_sha256,
            "analysis_contracts": {key: contract.to_dict() for key, contract in admission.effective_contracts.items()},
            "analysis_contract_resolver": _effective_contract_resolver(admission.effective_contracts),
            "analysis_contract_fingerprints": {
                key: contract.fingerprint for key, contract in admission.effective_contracts.items()
            },
            "analysis_analyzer_fingerprints": {
                key: workbook_analyzer_fingerprint(contract.domain)
                for key, contract in admission.effective_contracts.items()
            },
        })
        return await run_recipe_async(admission.recipe, prompt, client, admission.run_id, context)


async def execute_approved_investigation(
    work_dir: Path,
    prompt: str,
    client: Any | None = None,
    run_id: str | None = None,
    run_context: dict[str, Any] | None = None,
    workbook_source: str | Path | None = None,
):
    return await ExecutionGate(AnalysisStore(work_dir)).execute(
        prompt=prompt,
        client=client,
        run_id=run_id,
        run_context=run_context,
        workbook_source=workbook_source,
    )
