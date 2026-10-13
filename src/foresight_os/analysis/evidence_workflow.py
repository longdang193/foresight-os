from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_reasoning
from foresight_os.domain.evidence import normalize_evidence_candidate
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
from foresight_os.runtime.web_search import WebSearchCapability, WebSearchProvider
from foresight_os.runtime.local_toolbelt import (
    AnalysisOperation,
    FormulaStatus,
    SheetSelection,
    ToolbeltError,
    data_analysis,
    spreadsheet_read,
)


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
        review = review_reasoning([evidence], [claim])
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
        committed = store.commit_revision(pending, expected_revision=pending.revision, accepted=True)
        return EvidenceWorkflowResult("accepted", candidates, evidence.source_locator.file_version, evidence, claim, review, committed, tuple(tools))
    except Exception as error:
        return EvidenceWorkflowResult("failed", tuple(), None, None, None, None, None, tuple(tools), type(error).__name__)


def accept_pending_evidence(store: AnalysisStore, *, human_decision: str, source_trust_accepted: bool = True) -> EvidenceWorkflowResult:
    state = store.load_analysis()
    if state.revision_status != RevisionStatus.PENDING_REVIEW:
        raise ValueError("analysis does not contain a pending evidence review")
    review = review_reasoning(state.evidence, state.claims)
    if not source_trust_accepted:
        review = ReviewResult(False, ["human source-trust decision rejected the retrieved source"])
    if human_decision != "ACCEPT" or not review.accepted:
        committed = store.commit_revision(state, expected_revision=state.revision, accepted=False)
        return EvidenceWorkflowResult("rejected", tuple(), None, state.evidence[0] if state.evidence else None, state.claims[0] if state.claims else None, review, committed, tuple(), "explicit acceptance was not granted")
    committed = store.commit_revision(state, expected_revision=state.revision, accepted=True)
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
        result = data_analysis(table, operation)
        measurements = {item.provenance.coordinate: item for item in workbook.measurements}
        evidence: list[Evidence] = []
        selected_columns = {table.columns.index(operation.value_column)} if operation.value_column in table.columns else set(range(len(table.columns)))
        for row in table.row_provenance:
            for index, locator in enumerate(row):
                if index not in selected_columns:
                    continue
                measurement = measurements.get(locator.coordinate)
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
        review = review_reasoning(pending.evidence, pending.claims)
        if human_decision.upper() in {"PENDING", "PENDING_REVIEW"}:
            return EvidenceWorkflowResult("pending", tuple(), table.sheet, evidence[0], claim, review, pending, ("spreadsheet_read", "data_analysis"))
        if human_decision.upper() != "ACCEPT" or not review.accepted:
            rejected = store.commit_revision(pending, expected_revision=pending.revision, accepted=False)
            return EvidenceWorkflowResult("rejected", tuple(), table.sheet, evidence[0], claim, review, rejected, ("spreadsheet_read", "data_analysis"), "explicit acceptance was not granted")
        committed = store.commit_revision(pending, expected_revision=pending.revision, accepted=True)
        return EvidenceWorkflowResult("accepted", tuple(), table.sheet, evidence[0], claim, review, committed, ("spreadsheet_read", "data_analysis"))
    except Exception as error:
        return EvidenceWorkflowResult("failed", tuple(), None, None, None, None, None, ("spreadsheet_read", "data_analysis"), type(error).__name__)
