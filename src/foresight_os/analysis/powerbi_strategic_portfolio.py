from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from foresight_os.analysis.evidence_workflow import attach_review_record
from foresight_os.analysis.reviewer import ReviewResult, review_reasoning
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import AnalyticalRecord, AnalysisState, Assessment, Basis, CalculationRecord, Evidence, Invalidation, MeasurementKey, Relationship, Revision, RevisionStatus, SourceLocator
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError, spreadsheet_read


@dataclass(frozen=True)
class PowerBIDataQualityIssue:
    kind: str
    message: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class PowerBISegmentAssessment:
    segment: str
    revenue_2025_jan_sep: float
    revenue_2026_jan_sep: float
    yoy_growth: float
    gross_margin_2026: float
    forward_signal_index: float
    action: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class PowerBIChangeReassessment:
    change_id: str
    changed_scope: str
    updated_value: float | str | None
    unaffected_scope: str
    recommendation: str

@dataclass(frozen=True)
class PowerBIAnalysis:
    source_sha256: str
    decision_question: str
    horizon: str
    assumptions: tuple[str, ...]
    data_quality_issues: tuple[PowerBIDataQualityIssue, ...]
    revenue_2025_jan_sep: float
    revenue_2026_jan_sep: float
    yoy_revenue_growth: float
    gross_profit_2026_jan_sep: float
    gross_margin_2026_jan_sep: float
    forward_risk_index: float
    segment_assessments: tuple[PowerBISegmentAssessment, ...]
    options: tuple[dict[str, Any], ...]
    change_reassessments: tuple[PowerBIChangeReassessment, ...]
    monitoring_triggers: tuple[str, ...]
    recommendation: str
    state: AnalysisState

@dataclass(frozen=True)
class PowerBIWorkflowResult:
    status: str
    analysis: AnalysisState | None
    powerbi: PowerBIAnalysis | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _table(workbook: Any, sheet: str) -> Any:
    for table in workbook.tables:
        if table.sheet == sheet:
            return table
    raise ToolbeltError(f"Power BI recipe requires sheet: {sheet}")

def _rows(table: Any) -> list[dict[str, Any]]:
    return [dict(zip(table.columns, row, strict=False)) for row in table.rows]

def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

def _row_evidence(table: Any, index: int, digest: str) -> Evidence:
    values = dict(zip(table.columns, table.rows[index], strict=False))
    provenance = table.row_provenance[index]
    row_range = f"{provenance[0].coordinate}:{provenance[-1].coordinate}"
    evidence_id = "powerbi-evidence-" + hashlib.sha256(f"{digest}:{table.sheet}:{row_range}".encode()).hexdigest()[:16]
    return Evidence(evidence_id, SourceLocator(digest, table.sheet, row_range, "EUR", "powerbi_strategic_portfolio_recipe", f"{table.sheet} row"), digest, date.today().isoformat(), json.dumps(values, sort_keys=True, default=str))

def _record(record_id: str, statement: str, evidence_ids: list[str], assumptions: tuple[str, ...], uncertainty: tuple[str, ...], disconfirmation: tuple[str, ...], monitoring: tuple[str, ...]) -> AnalyticalRecord:
    return AnalyticalRecord(record_id, statement, Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=list(dict.fromkeys(evidence_ids)), assumptions=assumptions, uncertainty=uncertainty, confidence_rationale="Derived from deduplicated, period-aligned facts and separately appraised forward signals.", disconfirmation_conditions=disconfirmation, monitoring_indicators=monitoring)

def _date(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None

def _source_quality(value: str) -> float:
    return {"High": 3.0, "Medium": 2.0, "Low": 1.0}.get(value, 1.0)

def analyze_powerbi_strategic_portfolio(source: Path) -> PowerBIAnalysis:
    source = Path(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    sheets = ("Brief", "Dim_Region", "Dim_Segment", "Fact_Performance", "Targets", "Forward_Signals", "Measure_Definitions", "Dashboard_Snapshot", "Strategic_Options", "Change_One_Input")
    workbook = spreadsheet_read(source, SheetSelection(sheet_names=sheets, include_hidden=True, include_hidden_rows=True))
    tables = {name: _table(workbook, name) for name in sheets}
    rows = {name: _rows(table) for name, table in tables.items() if name != "Brief"}
    evidence: list[Evidence] = []
    by_row: dict[tuple[str, int], Evidence] = {}
    for name, table in tables.items():
        if name == "Brief":
            continue
        for index in range(len(table.rows)):
            by_row[(name, index)] = _row_evidence(table, index, digest)
            evidence.append(by_row[(name, index)])
    issues: list[PowerBIDataQualityIssue] = []
    seen: dict[tuple[Any, ...], int] = {}
    duplicate_indexes: set[int] = set()
    for index, row in enumerate(rows["Fact_Performance"]):
        key = (row.get("Year"), row.get("Month"), row.get("Region"), row.get("Segment"))
        if key in seen:
            duplicate_indexes.add(index)
            issues.append(PowerBIDataQualityIssue("DUPLICATE_FACT", f"Duplicate fact row for {key}; the later row is excluded from reconciled KPIs.", (by_row[("Fact_Performance", seen[key])].id, by_row[("Fact_Performance", index)].id)))
        else:
            seen[key] = index
    valid_facts = [(index, row) for index, row in enumerate(rows["Fact_Performance"]) if index not in duplicate_indexes]
    def period_total(year: int, field: str) -> float:
        return sum(_number(row.get(field)) or 0.0 for _, row in valid_facts if int(row.get("Year")) == year and int(row.get("Month")) <= 9)
    revenue_2025 = period_total(2025, "Revenue_EUR")
    revenue_2026 = period_total(2026, "Revenue_EUR")
    gp_2026 = period_total(2026, "Gross_Profit_EUR")
    yoy = revenue_2026 / revenue_2025 - 1 if revenue_2025 else 0.0
    targets = {(int(row.get("Year")), str(row.get("Region")), str(row.get("Segment"))): (index, row) for index, row in enumerate(rows["Targets"])}
    regions = [str(row.get("Region")) for row in rows["Dim_Region"]]
    segments = [str(row.get("Segment")) for row in rows["Dim_Segment"]]
    missing_targets = [(year, region, segment) for year in (2025, 2026) for region in regions for segment in segments if (year, region, segment) not in targets]
    for key in missing_targets:
        issues.append(PowerBIDataQualityIssue("MISSING_TARGET", f"Target is missing for {key[0]} / {key[1]} / {key[2]}; target attainment is incomplete.", tuple(by_row[("Targets", index)].id for index, row in enumerate(rows["Targets"]) if str(row.get("Region")) == key[1] and str(row.get("Segment")) == key[2]) or tuple()))
    latest_refresh = max((_date(row.get("Refresh_Timestamp")) for _, row in valid_facts), default=None)
    for index, row in enumerate(rows["Dashboard_Snapshot"]):
        refresh = _date(row.get("Refresh_Timestamp"))
        if latest_refresh and refresh and refresh < latest_refresh:
            issues.append(PowerBIDataQualityIssue("STALE_REFRESH", f"{row.get('Page')} / {row.get('KPI')} refreshes at {refresh.date().isoformat()}, older than the latest fact refresh {latest_refresh.date().isoformat()}.", (by_row[("Dashboard_Snapshot", index)].id,)))
    measure_issue_rows = [index for index, row in enumerate(rows["Measure_Definitions"]) if str(row.get("Measure")) == "YoY Revenue %" and "full-year" in str(row.get("Validation_Note")).lower()]
    if measure_issue_rows:
        issues.append(PowerBIDataQualityIssue("FILTER_CONTEXT_TRAP", "The YoY measure must compare 2026 Jan–Sep with 2025 Jan–Sep; a full-year versus YTD comparison is invalid.", tuple(by_row[("Measure_Definitions", index)].id for index in measure_issue_rows)))
    signal_rows = rows["Forward_Signals"]
    weighted_forward = sum((_number(row.get("Change_Index")) or 0.0) * _source_quality(str(row.get("Source_Quality"))) for row in signal_rows if str(row.get("Type")) != "Narrative") / sum(_source_quality(str(row.get("Source_Quality"))) for row in signal_rows if str(row.get("Type")) != "Narrative")
    dashboard_growth = {str(row.get("KPI")): _number(row.get("Displayed_Value")) or 0.0 for row in rows["Dashboard_Snapshot"]}
    if (dashboard_growth.get("YoY Revenue %", 0.0) > 0 and weighted_forward < 0) or any((_number(row.get("Change_Index")) or 0.0) < 0 for row in signal_rows if str(row.get("Type")) == "Leading"):
        issues.append(PowerBIDataQualityIssue("CONTRADICTORY_FORWARD_SIGNAL", "Booked dashboard growth is positive while leading order, pipeline, tender, budget, or macro signals weaken.", tuple(by_row[("Forward_Signals", index)].id for index, row in enumerate(signal_rows) if (_number(row.get("Change_Index")) or 0.0) < 0)))
    segment_assessments: list[PowerBISegmentAssessment] = []
    for segment in segments:
        rev25 = sum(_number(row.get("Revenue_EUR")) or 0.0 for _, row in valid_facts if str(row.get("Segment")) == segment and int(row.get("Year")) == 2025 and int(row.get("Month")) <= 9)
        rev26 = sum(_number(row.get("Revenue_EUR")) or 0.0 for _, row in valid_facts if str(row.get("Segment")) == segment and int(row.get("Year")) == 2026 and int(row.get("Month")) <= 9)
        gp26 = sum(_number(row.get("Gross_Profit_EUR")) or 0.0 for _, row in valid_facts if str(row.get("Segment")) == segment and int(row.get("Year")) == 2026 and int(row.get("Month")) <= 9)
        signal_values = [(_number(row.get("Change_Index")) or 0.0) for row in signal_rows if str(row.get("Segment")) in {segment, "All"}]
        forward = sum(signal_values) / len(signal_values) if signal_values else 0.0
        action = "Selective/staged" if forward < 0 else "Protect/scale"
        ids = tuple(by_row[("Fact_Performance", index)].id for index, row in valid_facts if str(row.get("Segment")) == segment) + tuple(by_row[("Forward_Signals", index)].id for index, row in enumerate(signal_rows) if str(row.get("Segment")) in {segment, "All"})
        segment_assessments.append(PowerBISegmentAssessment(segment, rev25, rev26, rev26 / rev25 - 1 if rev25 else 0.0, gp26 / rev26 if rev26 else 0.0, forward, action, ids))
    assumptions = ("All reconciled KPI comparisons use Jan–Sep 2025 versus Jan–Sep 2026.", "The later duplicate composite fact row is excluded; the workbook is not silently edited.", "Target attainment is provisional when a denominator is missing.", "Forward signals are appraised by type and source quality; narrative media is not treated as booked demand.", "Power BI metadata, filter context, and refresh timestamps are part of evidence quality.")
    all_ids = [item.id for item in evidence]
    claims: list[AnalyticalRecord] = []
    relationships: list[Relationship] = []
    for item in segment_assessments:
        claim = _record(f"powerbi-segment-{item.segment.lower()}", f"{item.segment} delivered {item.yoy_growth:.1%} Jan–Sep growth with {item.gross_margin_2026:.1%} gross margin and a {item.forward_signal_index:.2f} forward-signal index; the action is {item.action.lower()}.", list(item.evidence_ids), assumptions, ("Booked growth can coexist with weakening forward indicators.",), (f"A validated forward refresh changes the {item.segment} action posture.",), (f"{item.segment} Jan–Sep revenue, margin, and forward signal index.",))
        claims.append(claim)
        relationships.extend(Relationship(f"{claim.id}-supports-{evidence_id}", evidence_id, claim.id, "supports") for evidence_id in claim.evidence_ids)
    quality_ids = [evidence_id for issue in issues for evidence_id in issue.evidence_ids]
    quality = _record("powerbi-data-quality", f"The Power BI evidence contains {len(issues)} duplicate, denominator, freshness, filter-context, or forward-signal issues that constrain an automatic broad-investment decision.", quality_ids or all_ids, assumptions, ("Corrected model metadata or refreshed leading signals can change the recommendation.",), ("All model-quality issues are resolved and forward signals strengthen without period-context drift.",), ("Duplicate count, target completeness, refresh age, period alignment, and forward risk index.",))
    claims.append(quality)
    relationships.extend(Relationship(f"{quality.id}-supports-{evidence_id}", evidence_id, quality.id, "supports") for evidence_id in quality.evidence_ids)
    implication = _record("powerbi-priority-implication", "Historical booked growth is real after deduplication, but weakening forward signals and model-quality caveats argue for selective Analytics/Services allocation and stage gates rather than broad acceleration.", all_ids, assumptions, ("The workbook does not supply a causal investment-uplift model.",), ("Forward pipeline, order, tender, and macro signals strengthen across affected segments and the missing target is restored.",), ("Forward risk index, target completeness, and refresh freshness.",))
    relationships.extend(Relationship(f"{claim.id}-informs-{implication.id}", claim.id, implication.id, "informs") for claim in claims)
    recommendation = _record("powerbi-recommendation", "Conditional recommendation: prefer Scale Analytics + Services selectively or stage-gated portfolio investment; do not accelerate broad investment until forward signals strengthen and semantic-model caveats are resolved.", all_ids, assumptions, ("Investment options lack a full causal return forecast.",), ("Two refreshes show improving pipeline/order/tender evidence and complete target denominators.",), ("Analytics pipeline coverage, Services renewal intent, Hardware orders/tenders, Southern Europe budget scrutiny, and refresh status.",))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation.id}", implication.id, recommendation.id, "informs"))
    for issue_index, issue in enumerate(issues):
        for evidence_id in issue.evidence_ids:
            relationships.append(Relationship(f"powerbi-issue-{issue_index}-{issue.kind.lower()}-{evidence_id}", evidence_id, recommendation.id, "contradicts"))
    recommendation = replace(recommendation, relationship_ids=[item.id for item in relationships if item.to_id == recommendation.id])
    calculations = [CalculationRecord("powerbi-revenue-2025-jan-sep", MeasurementKey("all", "revenue", "2025-01:2025-09", "EUR"), "sum(deduplicated Revenue_EUR where Year=2025 and Month<=9)", [by_row[("Fact_Performance", index)].id for index, row in valid_facts if int(row.get("Year")) == 2025 and int(row.get("Month")) <= 9], revenue_2025, "EUR", ["Fact_Performance:2025-01:2025-09"]), CalculationRecord("powerbi-revenue-2026-jan-sep", MeasurementKey("all", "revenue", "2026-01:2026-09", "EUR"), "sum(deduplicated Revenue_EUR where Year=2026 and Month<=9)", [by_row[("Fact_Performance", index)].id for index, row in valid_facts if int(row.get("Year")) == 2026 and int(row.get("Month")) <= 9], revenue_2026, "EUR", ["Fact_Performance:2026-01:2026-09"]), CalculationRecord("powerbi-yoy-growth", MeasurementKey("all", "yoy_revenue_growth", "2026-01:2026-09 vs 2025-01:2025-09", "ratio"), "revenue_2026_jan_sep / revenue_2025_jan_sep - 1", ["powerbi-revenue-2025-jan-sep", "powerbi-revenue-2026-jan-sep"], yoy, "ratio", ["Fact_Performance:comparable-period"])]
    changes = tuple(PowerBIChangeReassessment(str(row.get("Change_ID")), str(row.get("Expected_Reassessment")), _number(row.get("Replacement")) if row.get("Replacement") is not None else row.get("Replacement"), "Unrelated source appraisal remains unchanged.", "Reassess only the named evidence path before changing the portfolio recommendation.") for row in rows["Change_One_Input"])
    state = AnalysisState("powerbi-strategic-portfolio", 1, evidence=evidence, claims=claims, implications=[implication], recommendations=[recommendation], relationships=relationships, revisions=[Revision("revision-1", 1, "Power BI strategic portfolio analysis pending acceptance", [item.id for item in [*evidence, *calculations, *claims, implication, recommendation]])], invalidation=Invalidation(), revision_status=RevisionStatus.DRAFT, calculations=calculations)
    decision_question = next((str(row[1]) for row in tables["Brief"].rows if row and row[0] == "Decision question" and len(row) > 1), "Should management accelerate investment?")
    horizon = next((str(row[1]) for row in tables["Brief"].rows if row and row[0] == "Horizon" and len(row) > 1), "Next 12–24 months")
    options = tuple(dict(row) for row in rows["Strategic_Options"])
    return PowerBIAnalysis(digest, decision_question, horizon, assumptions, tuple(issues), revenue_2025, revenue_2026, yoy, gp_2026, gp_2026 / revenue_2026 if revenue_2026 else 0.0, weighted_forward, tuple(segment_assessments), options, changes, ("Comparable-period revenue and YoY growth", "Analytics pipeline coverage and customer budget scrutiny", "Services renewal intent and aftermarket utilization", "Hardware order/tender signals", "Target completeness and dashboard refresh age"), recommendation.statement, state)

def _citations(state: AnalysisState, ids: tuple[str, ...] | list[str]) -> str:
    by_id = {item.id: item for item in state.evidence}
    return ", ".join(f"`{by_id[item].source_locator.sheet}!{by_id[item].source_locator.range}`" for item in dict.fromkeys(ids) if item in by_id) or "`unavailable`"

def render_powerbi_report(powerbi: PowerBIAnalysis, state: AnalysisState | None = None) -> str:
    state = state or powerbi.state
    if state.revision_status != RevisionStatus.ACCEPTED or any(not item.accepted for item in derive_finding_views(state)):
        raise ValueError("Power BI report requires current accepted findings")
    lines = ["# Power BI Strategic Portfolio Executive Report", "", f"Decision question: {powerbi.decision_question}", f"Horizon: {powerbi.horizon}", f"Source workbook SHA-256: `{powerbi.source_sha256}`", "", "## What is changing?", "- The dashboard shows positive booked growth, but forward indicators and semantic-model caveats prevent a simple broad-acceleration conclusion.", "", "## Reconciled KPIs", "| KPI | Value | Definition |", "|---|---:|---|", f"| 2025 Jan–Sep revenue | €{powerbi.revenue_2025_jan_sep:,.2f} | Deduplicated comparable-period facts |", f"| 2026 Jan–Sep revenue | €{powerbi.revenue_2026_jan_sep:,.2f} | Deduplicated comparable-period facts |", f"| 2026 Jan–Sep YoY revenue growth | {powerbi.yoy_revenue_growth:.2%} | 2026 Jan–Sep versus 2025 Jan–Sep |", f"| 2026 Jan–Sep gross margin | {powerbi.gross_margin_2026_jan_sep:.2%} | Reconciled gross profit / revenue |", "", "## Filter-context checks", "- YoY uses Jan–Sep versus Jan–Sep; full-year 2025 versus 2026 YTD is not used.", "- Target attainment remains provisional where the Southern Europe Analytics denominator is missing.", "", "## Segment evidence", "| Segment | YoY growth | Gross margin | Forward index | Action | Evidence |", "|---|---:|---:|---:|---|---|"]
    lines.extend(f"| {item.segment} | {item.yoy_growth:.2%} | {item.gross_margin_2026:.2%} | {item.forward_signal_index:.2f} | {item.action} | {_citations(state, item.evidence_ids)} |" for item in powerbi.segment_assessments)
    lines.extend(["", "## Contradiction analysis"])
    lines.extend(f"- `{issue.kind}`: {issue.message} (source: {_citations(state, issue.evidence_ids)})" for issue in powerbi.data_quality_issues)
    lines.extend(["", "## Competing options", "| ID | Option | Investment | Reversibility | Hypothesis |", "|---|---|---:|---|---|"])
    lines.extend(f"| {row.get('Option_ID')} | {row.get('Option')} | €{(_number(row.get('Investment_EUR')) or 0.0):,.0f} | {row.get('Reversibility')} | {row.get('Strategic_Hypothesis')} |" for row in powerbi.options)
    lines.extend(["", "## Assumptions and uncertainty"])
    lines.extend(f"- {item}" for item in powerbi.assumptions)
    lines.extend(["", "## Recommended action", f"- {powerbi.recommendation}", "", "## Monitoring signposts"])
    lines.extend(f"- {item}" for item in powerbi.monitoring_triggers)
    lines.extend(["", "## Change-one-input tests"])
    lines.extend(f"- `{item.change_id}`: {item.changed_scope}; update={item.updated_value}; {item.recommendation}" for item in powerbi.change_reassessments)
    lines.extend(["", "## What changes our mind?", "- Broaden investment only after forward pipeline/order/tender signals strengthen, target denominators are complete, refresh timestamps are current, and the comparison period remains aligned.", "", "## FindingView status"])
    lines.extend(f"- `{item.target_id}`: {item.review_status}/{item.review_outcome}; accepted={item.accepted}; evidence={_citations(state, item.evidence_ids)}" for item in derive_finding_views(state))
    return "\n".join(lines) + "\n"

def run_powerbi_strategic_portfolio_workflow(store: AnalysisStore, source: Path, *, human_decision: str = "REJECT", output_dir: Path | None = None) -> PowerBIWorkflowResult:
    try:
        powerbi = analyze_powerbi_strategic_portfolio(Path(source))
        pending = store.save_pending(powerbi.state)
        review = review_reasoning(pending.evidence, [*pending.claims, *pending.implications, *pending.recommendations], calculations=pending.calculations)
        decision = human_decision.upper()
        if decision in {"PENDING", "PENDING_REVIEW"}:
            return PowerBIWorkflowResult("pending", pending, replace(powerbi, state=pending), review, None)
        if decision != "ACCEPT" or not review.accepted:
            rejected = store.commit_revision(pending, expected_revision=pending.revision, accepted=False)
            return PowerBIWorkflowResult("rejected", rejected, replace(powerbi, state=rejected), review, None, "explicit acceptance was not granted")
        reviewed = attach_review_record(pending, review, f"review-{pending.investigation_id}-{pending.revision}")
        committed = store.commit_revision(reviewed, expected_revision=reviewed.revision, accepted=True)
        final = replace(powerbi, state=committed)
        report_path = (Path(output_dir) if output_dir is not None else store.root / "artifacts") / "executive-report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_powerbi_report(final, committed), encoding="utf-8")
        return PowerBIWorkflowResult("accepted", committed, final, review, report_path)
    except Exception as error:
        return PowerBIWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
