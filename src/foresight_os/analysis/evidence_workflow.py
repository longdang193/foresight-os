from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state, review_analysis_state_with_skills, review_reasoning
from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.domain.challenge import ReviewOutcome, ReviewRecord, build_material_fingerprint
from foresight_os.domain.models import (
    AnalysisState,
    AnalyticalRecord,
    Assessment,
    Basis,
    Evidence,
    Invalidation,
    Relationship,
    Revision,
    RevisionStatus,
    CalculationRecord,
    MeasurementKey,
    SourceLocator,
)
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.page_retrieval import PageRetrievalCapability
from foresight_os.runtime.executors import ReviewerExecutor
from foresight_os.runtime.web_search import WebSearchCapability, WebSearchProvider
from foresight_os.runtime.local_toolbelt import (
    AnalysisOperation,
    FormulaStatus,
    SheetSelection,
    ToolbeltError,
    data_analysis,
    spreadsheet_read,
)


def attach_review_record(
    state: AnalysisState,
    review: ReviewResult,
    review_id: str,
    *,
    target_ids: tuple[str, ...] | list[str] | None = None,
    check_id: str | None = None,
    reviewer_id: str | None = None,
    execution_id: str | None = None,
    attempt_id: str | None = None,
    method: str | None = None,
    source_fingerprints: tuple[str, ...] | list[str] = (),
    dependency_fingerprints: tuple[tuple[str, str], ...] | list[tuple[str, str]] = (),
    slot_key: str | None = None,
    supersedes_review_id: str | None = None,
) -> AnalysisState:
    legacy_scope = target_ids is None
    if legacy_scope:
        if any((check_id, reviewer_id, execution_id, attempt_id, method)) or review.check_id:
            raise ValueError("typed review attachment requires explicit target_ids")
        target_ids = tuple(item.id for collection in (state.claims, state.implications, state.recommendations) for item in collection)
    target_ids = tuple(dict.fromkeys(str(item) for item in target_ids or ()))
    if not target_ids:
        raise ValueError("review attachment requires at least one target_id")
    known_ids = {
        item.id
        for collection in (state.evidence, state.claims, state.implications, state.recommendations, state.calculations)
        for item in collection
    }
    if not set(target_ids).issubset(known_ids):
        raise ValueError("review attachment references unknown target_ids")
    resolved_check_id = str(check_id or review.check_id or "")
    resolved_reviewer_id = str(reviewer_id or "")
    resolved_execution_id = str(execution_id or "")
    resolved_attempt_id = str(attempt_id or "")
    resolved_method = str(method or review.method or "")
    source_fingerprints = tuple(source_fingerprints or review.source_fingerprints)
    dependency_fingerprints = tuple(dependency_fingerprints or review.dependency_fingerprints)
    typed_metadata = any((resolved_check_id, resolved_reviewer_id, resolved_execution_id, resolved_attempt_id, resolved_method))
    if typed_metadata and not all((resolved_check_id, resolved_reviewer_id, resolved_execution_id, resolved_attempt_id, resolved_method)):
        raise ValueError("typed review attachment requires check, reviewer, execution, attempt, and method identity")
    record = ReviewRecord(
        review_id=review_id,
        target_ids=target_ids,
        reviewed_state_revision=state.revision,
        input_fingerprint=build_material_fingerprint(
            state,
            target_ids,
            review.skill_ids,
            review.skill_versions,
            review.skill_hashes,
            (review.policy_id, review.policy_version) if review.policy_id and review.policy_version else None,
            source_fingerprints,
            dependency_fingerprints,
        ),
        skill_ids=review.skill_ids,
        skill_versions=review.skill_versions,
        objections=review.objections,
        outcome=review.outcome,
        unresolved_issues=tuple(review.issues),
        policy_id=review.policy_id,
        policy_version=review.policy_version,
        skill_hashes=review.skill_hashes,
        check_id=resolved_check_id,
        reviewer_id=resolved_reviewer_id,
        execution_id=resolved_execution_id,
        attempt_id=resolved_attempt_id,
        method=resolved_method,
        source_fingerprints=tuple(source_fingerprints),
        dependency_fingerprints=tuple(tuple(item) for item in dependency_fingerprints),
        slot_key=str(slot_key or ""),
        supersedes_review_id=supersedes_review_id,
        check_results=review.check_results,
        legacy=legacy_scope or not typed_metadata,
    )
    for existing in state.review_records:
        if existing.review_id == review_id:
            if existing == record:
                return state
            raise ValueError(f"review_id already exists with different content: {review_id}")
    active_slot = record.effective_slot_key if typed_metadata else ""
    updated_records = list(state.review_records)
    if active_slot:
        same_slot = [
            existing
            for existing in updated_records
            if existing.effective_slot_key == active_slot and existing.superseded_by_review_id is None
        ]
        for existing in same_slot:
            existing_index = updated_records.index(existing)
            if supersedes_review_id == existing.review_id or (
                existing.reviewer_id == record.reviewer_id
                and existing.method == record.method
            ):
                updated_records[existing_index] = replace(existing, superseded_by_review_id=review_id)
            else:
                conflict_ids = tuple(dict.fromkeys((*existing.conflict_review_ids, review_id)))
                updated_records[existing_index] = replace(existing, conflict_review_ids=conflict_ids)
                record = replace(record, conflict_review_ids=tuple(dict.fromkeys((*record.conflict_review_ids, existing.review_id))))
    updated_records.append(record)
    return replace(state, review_records=updated_records)

@dataclass(frozen=True)
class EvidenceWorkflowResult:
    status: str
    candidates: tuple[dict[str, Any], ...]
    selected_source: str | None
    evidence: Evidence | None
    claim: AnalyticalRecord | None
    review: ReviewResult | None
    analysis: AnalysisState | None
    tool_calls: tuple[str, ...]
    failure: str | None = None


async def run_evidence_workflow(
    store: AnalysisStore,
    query: str,
    provider: WebSearchProvider,
    *,
    retrieval: PageRetrievalCapability | None = None,
    investigation_id: str = "evidence-workflow",
    human_decision: str = "REJECT",
    source_trust_accepted: bool = True,
    review_client: Any | None = None,
    reviewer_executor: ReviewerExecutor | None = None,
) -> EvidenceWorkflowResult:
    tools = ["web_search"]
    try:
        candidates = tuple(await WebSearchCapability(provider)(query))
        if not candidates:
            return EvidenceWorkflowResult("failed", candidates, None, None, None, None, tuple(tools), "no search candidates")
        selected = candidates[0]
        retrieval = retrieval or PageRetrievalCapability()
        page = await retrieval({"url": selected["provenance"]["url"]}, query)
        tools.append("page_retrieval")
        evidence = normalize_evidence_candidate(page)
        claim = AnalyticalRecord(
            id=f"claim-{evidence.id}",
            statement="The retrieved source reports a forecast fact.",
            basis=Basis.OBSERVED,
            assessment=Assessment.SUPPORTED if source_trust_accepted else Assessment.UNCERTAIN,
            evidence_ids=[evidence.id],
        )
        relationship = Relationship(f"relationship-{evidence.id}", evidence.id, claim.id, "supports")
        claim = AnalyticalRecord(
            claim.id,
            claim.statement,
            claim.basis,
            claim.assessment,
            evidence_ids=claim.evidence_ids,
            relationship_ids=[relationship.id],
        )
        review_state = AnalysisState(investigation_id, 1, evidence=[evidence], claims=[claim])
        if review_client is not None or reviewer_executor is not None:
            review = await review_analysis_state_with_skills(
                review_state,
                client=review_client,
                executor=reviewer_executor,
            )
        else:
            review = review_analysis_state(review_state)
        if not source_trust_accepted:
            review = ReviewResult(False, ["human source-trust decision rejected the retrieved source"])
        state = AnalysisState(
            investigation_id,
            1,
            evidence=[evidence],
            claims=[claim],
            relationships=[relationship],
            revisions=[Revision("revision-1", 1, "retrieved evidence pending acceptance", [evidence.id, claim.id, relationship.id])],
            invalidation=Invalidation(),
            revision_status=RevisionStatus.DRAFT,
        )
        pending = store.save_pending(state)
        if human_decision.upper() in {"PENDING", "PENDING_REVIEW"}:
            return EvidenceWorkflowResult("pending", candidates, evidence.source_locator.file_version, evidence, claim, review, pending, tuple(tools))
        if not review.accepted or human_decision.upper() != "ACCEPT":
            rejected = store.commit_revision(pending, expected_revision=pending.revision, accepted=False)
            return EvidenceWorkflowResult("rejected", candidates, evidence.source_locator.file_version, evidence, claim, review, rejected, tuple(tools), "explicit acceptance was not granted")
        reviewed = attach_review_record(pending, review, f"review-{pending.investigation_id}-{pending.revision}")
        committed = store.commit_revision(reviewed, expected_revision=reviewed.revision, accepted=True)
        return EvidenceWorkflowResult("accepted", candidates, evidence.source_locator.file_version, evidence, claim, review, committed, tuple(tools))
    except Exception as error:
        return EvidenceWorkflowResult("failed", tuple(), None, None, None, None, None, tuple(tools), type(error).__name__)


def accept_pending_evidence(store: AnalysisStore, *, human_decision: str, source_trust_accepted: bool = True) -> EvidenceWorkflowResult:
    state = store.load_pending()
    if state.revision_status != RevisionStatus.PENDING_REVIEW:
        raise ValueError("analysis does not contain a pending evidence review")
    review = review_analysis_state(state)
    if not source_trust_accepted:
        review = ReviewResult(False, ["human source-trust decision rejected the retrieved source"])
    if human_decision != "ACCEPT" or not review.accepted:
        committed = store.commit_revision(state, expected_revision=state.revision, accepted=False)
        return EvidenceWorkflowResult("rejected", tuple(), None, state.evidence[0] if state.evidence else None, state.claims[0] if state.claims else None, review, committed, tuple(), "explicit acceptance was not granted")
    reviewed = attach_review_record(state, review, f"review-{state.investigation_id}-{state.revision}")
    committed = store.commit_revision(reviewed, expected_revision=reviewed.revision, accepted=True)
    return EvidenceWorkflowResult("accepted", tuple(), None, state.evidence[0] if state.evidence else None, state.claims[0] if state.claims else None, review, committed, tuple())


def run_xlsx_finding_workflow(
    store: AnalysisStore,
    source: Path,
    operation: AnalysisOperation,
    *,
    selection: SheetSelection | None = None,
    investigation_id: str = "xlsx-evidence-workflow",
    human_decision: str = "REJECT",
) -> EvidenceWorkflowResult:
    """Promote a deterministic workbook analysis into reviewable domain state."""
    try:
        before = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        workbook = spreadsheet_read(Path(source), selection)
        if before != hashlib.sha256(Path(source).read_bytes()).hexdigest():
            raise ToolbeltError("source workbook changed during read")
        if not workbook.tables:
            raise ToolbeltError("workbook selection produced no table")
        table = workbook.tables[0]
        if selection is not None and selection.tables:
            requested = set(selection.tables)
            table = next((candidate for candidate in workbook.tables if (candidate.sheet, candidate.name) in requested), None)
            if table is None:
                raise ToolbeltError("selected table was not found in workbook")
        elif selection is not None and selection.ranges:
            requested = set(selection.ranges)
            table = next((candidate for candidate in workbook.tables if (candidate.sheet, candidate.source_range) in requested), None)
            if table is None:
                raise ToolbeltError("selected range was not found in workbook")
        result = data_analysis(table, operation)
        measurements = {(item.provenance.sheet, item.provenance.coordinate): item for item in workbook.measurements}
        evidence: list[Evidence] = []
        selected_columns = {table.columns.index(operation.value_column)} if operation.value_column in table.columns else set(range(len(table.columns)))
        for row in table.row_provenance:
            for index, locator in enumerate(row):
                if index not in selected_columns:
                    continue
                measurement = measurements.get((locator.sheet, locator.coordinate))
                if measurement is None or measurement.value is None or isinstance(measurement.value, str) and measurement.value.startswith("#"):
                    continue
                if measurement.formula_status in {FormulaStatus.FORMULA_WITHOUT_CACHE, FormulaStatus.FORMULA_STALE_OR_UNKNOWN, FormulaStatus.ERROR}:
                    raise ToolbeltError("BLOCKED_RECALCULATION: formula input is not trustworthy")
                evidence_id = "xlsx-evidence-" + hashlib.sha256(f"{locator.workbook_sha256}:{locator.sheet}:{locator.coordinate}".encode()).hexdigest()[:16]
                evidence.append(
                    Evidence(
                        evidence_id,
                        SourceLocator(locator.workbook_sha256, locator.sheet, locator.coordinate, "unknown", f"data_analysis:{operation.kind}", operation.kind),
                        locator.workbook_sha256,
                        date.today().isoformat(),
                        str(measurement.value),
                        ["read-only workbook inspection", *([f"cross-sheet:{name}" for name in measurement.cross_sheet_references])],
                    )
                )
        if not evidence:
            raise ToolbeltError("analysis has no promotable evidence")
        output = None
        if result.rows and isinstance(result.rows[0], dict):
            output = result.rows[0].get("sum")
            if output is None:
                output = result.rows[0].get("value")
        if output is None:
            raise ToolbeltError("analysis result has no deterministic numeric output")
        calculation = CalculationRecord(
            "xlsx-calculation-" + result.deterministic_key[:16],
            MeasurementKey(table.sheet, operation.kind, "current", "unknown"),
            f"data_analysis({operation.kind})",
            [item.id for item in evidence],
            float(output),
            "unknown",
            sorted({item.source_locator.range for item in evidence}),
        )
        claim_id = "xlsx-claim-" + result.deterministic_key[:16]
        claim = AnalyticalRecord(claim_id, f"Workbook analysis {operation.kind} produced {output}.", Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=[item.id for item in evidence])
        relationship = Relationship("xlsx-relationship-" + result.deterministic_key[:16], evidence[0].id, claim.id, "supports")
        claim = AnalyticalRecord(claim.id, claim.statement, claim.basis, claim.assessment, evidence_ids=claim.evidence_ids, relationship_ids=[relationship.id])
        state = AnalysisState(
            investigation_id,
            1,
            evidence=evidence,
            claims=[claim],
            relationships=[relationship],
            revisions=[Revision("revision-1", 1, "deterministic workbook analysis pending acceptance", [item.id for item in evidence] + [calculation.id, claim.id, relationship.id])],
            invalidation=Invalidation(),
            revision_status=RevisionStatus.DRAFT,
            calculations=[calculation],
        )
        pending = store.save_pending(state)
        review = review_analysis_state(pending)
        if human_decision.upper() in {"PENDING", "PENDING_REVIEW"}:
            return EvidenceWorkflowResult("pending", tuple(), table.sheet, evidence[0], claim, review, pending, ("spreadsheet_read", "data_analysis"))
        if human_decision.upper() != "ACCEPT" or not review.accepted:
            rejected = store.commit_revision(pending, expected_revision=pending.revision, accepted=False)
            return EvidenceWorkflowResult("rejected", tuple(), table.sheet, evidence[0], claim, review, rejected, ("spreadsheet_read", "data_analysis"), "explicit acceptance was not granted")
        reviewed = attach_review_record(pending, review, f"review-{pending.investigation_id}-{pending.revision}")
        committed = store.commit_revision(reviewed, expected_revision=reviewed.revision, accepted=True)
        return EvidenceWorkflowResult("accepted", tuple(), table.sheet, evidence[0], claim, review, committed, ("spreadsheet_read", "data_analysis"))
    except Exception as error:
        return EvidenceWorkflowResult("failed", tuple(), None, None, None, None, None, ("spreadsheet_read", "data_analysis"), type(error).__name__)
