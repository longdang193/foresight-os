from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.review_workflow import review_and_accept_pending_analysis
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import AnalyticalRecord, AnalysisState, Assessment, Basis, CalculationRecord, Evidence, Invalidation, MeasurementKey, Relationship, Revision, RevisionStatus, SourceLocator
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError, spreadsheet_read


@dataclass(frozen=True)
class EVDataQualityIssue:
    kind: str
    message: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class EVDemandHistory:
    year: int
    region: str
    demand_units: float
    basis: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class EVScenarioProjection:
    scenario: str
    year: int
    demand_units: float
    practical_capacity: float
    capacity_gap: float
    basis: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class EVOptionAssessment:
    option: str
    investment_eur: float | None
    lead_time_months: float
    added_capacity: float
    operating_cost_premium: float
    reversibility: str
    cost_per_added_capacity: float | None
    notes: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class EVAnalysis:
    source_sha256: str
    decision_question: str
    horizon: str
    assumptions: tuple[str, ...]
    data_quality_issues: tuple[EVDataQualityIssue, ...]
    demand_history: tuple[EVDemandHistory, ...]
    scenarios: tuple[EVScenarioProjection, ...]
    options: tuple[EVOptionAssessment, ...]
    monitoring_triggers: tuple[str, ...]
    recommendation: str
    state: AnalysisState

@dataclass(frozen=True)
class EVWorkflowResult:
    status: str
    analysis: AnalysisState | None
    ev: EVAnalysis | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

def _table(workbook: Any, sheet: str) -> Any:
    for table in workbook.tables:
        if table.sheet == sheet:
            return table
    raise ToolbeltError(f"EV recipe requires sheet: {sheet}")

def _rows(table: Any) -> list[dict[str, Any]]:
    return [dict(zip(table.columns, row, strict=False)) for row in table.rows]

def _row_evidence(table: Any, index: int, digest: str) -> Evidence:
    values = dict(zip(table.columns, table.rows[index], strict=False))
    provenance = table.row_provenance[index]
    row_range = f"{provenance[0].coordinate}:{provenance[-1].coordinate}"
    evidence_id = "ev-evidence-" + hashlib.sha256(f"{digest}:{table.sheet}:{row_range}".encode()).hexdigest()[:16]
    return Evidence(evidence_id, SourceLocator(digest, table.sheet, row_range, "units", "ev_capacity_investment_recipe", f"{table.sheet} row"), digest, date.today().isoformat(), json.dumps(values, sort_keys=True, default=str))

def _record(record_id: str, statement: str, evidence_ids: list[str], assumptions: tuple[str, ...], uncertainty: tuple[str, ...], disconfirmation: tuple[str, ...], monitoring: tuple[str, ...]) -> AnalyticalRecord:
    return AnalyticalRecord(record_id, statement, Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=list(dict.fromkeys(evidence_ids)), assumptions=assumptions, uncertainty=uncertainty, confidence_rationale="Derived from deterministic workbook rows while preserving observed/projected basis and unresolved inputs.", disconfirmation_conditions=disconfirmation, monitoring_indicators=monitoring)


def _capacity_dependency_ids(capacity_rows: list[tuple[int, dict[str, Any]]], by_row: dict[tuple[str, int], Evidence], year: int) -> tuple[str, ...]:
    return tuple(by_row[("Capacity", index)].id for index, row in capacity_rows if int(row.get("Year")) == year)

def analyze_ev_capacity_investment(source: Path) -> EVAnalysis:
    source = Path(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    sheets = ("Brief", "Demand_History", "Demand_Scenarios", "Capacity", "Infrastructure", "Policy_Signals", "Strategic_Options", "Reported_KPIs")
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
    history = tuple(EVDemandHistory(int(row.get("Year")), str(row.get("Region")), _number(row.get("Service_Demand_Units")) or 0.0, str(row.get("Basis", "Observed")), (by_row[("Demand_History", index)].id,)) for index, row in enumerate(rows["Demand_History"]))
    capacity_by_year: dict[int, float] = {}
    for index, row in enumerate(rows["Capacity"]):
        year = int(row.get("Year"))
        capacity_by_year[year] = capacity_by_year.get(year, 0.0) + (_number(row.get("Nominal_Capacity")) or 0.0) * (_number(row.get("Practical_Availability")) or 0.0)
    scenario_groups: dict[tuple[str, int], list[tuple[int, dict[str, Any]]]] = {}
    for index, row in enumerate(rows["Demand_Scenarios"]):
        scenario_groups.setdefault((str(row.get("Scenario")), int(row.get("Year"))), []).append((index, row))
    capacity_evidence_by_year = {
        year: _capacity_dependency_ids(list(enumerate(rows["Capacity"])), by_row, year)
        for year in capacity_by_year
    }
    scenarios: list[EVScenarioProjection] = []
    for (scenario, year), items in sorted(scenario_groups.items()):
        demand = sum(_number(row.get("Demand_Units")) or 0.0 for _, row in items)
        scenarios.append(EVScenarioProjection(scenario, year, demand, capacity_by_year.get(year, 0.0), demand - capacity_by_year.get(year, 0.0), "Projected", tuple(dict.fromkeys([*(by_row[("Demand_Scenarios", index)].id for index, _ in items), *capacity_evidence_by_year.get(year, ())]))))
    issues: list[EVDataQualityIssue] = []
    kpi_rows = rows["Reported_KPIs"]
    for index, row in enumerate(kpi_rows):
        kpi = str(row.get("KPI"))
        reported = _number(row.get("Reported_Value"))
        if reported is None:
            continue
        if "Base Demand" in kpi or "High Demand" in kpi:
            scenario = "Base" if "Base" in kpi else "High"
            year = int(str(row.get("Scenario_Year")).split("/")[-1].strip())
            expected = next((item for item in scenarios if item.scenario == scenario and item.year == year), None)
            if expected and not math.isclose(reported, expected.demand_units, rel_tol=0.001, abs_tol=1.0):
                issues.append(EVDataQualityIssue("KPI_MISMATCH", f"{kpi} reports {reported:,.0f}, but Demand_Scenarios sum to {expected.demand_units:,.0f}.", (by_row[("Reported_KPIs", index)].id, *expected.evidence_ids)))
        elif "Existing Practical Capacity" in kpi:
            year = int(str(row.get("Scenario_Year", "2030")).split("/")[-1].strip())
            expected = capacity_by_year.get(year)
            if expected is not None and not math.isclose(reported, expected, rel_tol=0.01, abs_tol=1.0):
                issues.append(EVDataQualityIssue("KPI_MISMATCH", f"{kpi} reports {reported:,.0f}, but nominal capacity × practical availability is {expected:,.0f}.", (by_row[("Reported_KPIs", index)].id, *[by_row[("Capacity", i)].id for i, item in enumerate(rows["Capacity"]) if int(item.get("Year")) == year])))
    for index, row in enumerate(rows["Strategic_Options"]):
        if row.get("Investment_EUR") is None:
            issues.append(EVDataQualityIssue("MISSING_EXPANSION_COST", f"Investment cost is missing for {row.get('Option')}.", (by_row[("Strategic_Options", index)].id,)))
    for policy_index, policy in enumerate(rows["Policy_Signals"]):
        direction = str(policy.get("Direction", ""))
        if direction not in {"Step-down", "Uncertain renewal"}:
            continue
        region = str(policy.get("Region"))
        end_year = int(policy.get("Current_End_Year"))
        conflicting = [index for index, row in enumerate(rows["Demand_Scenarios"]) if str(row.get("Region")) == region and int(row.get("Year")) > end_year and str(row.get("Basis")) == "Projected" and (_number(row.get("Annual_Growth")) or 0.0) > 0.0]
        if conflicting:
            issues.append(EVDataQualityIssue("POLICY_CONFLICT", f"{region} has {direction} policy support ending in {end_year}, while projected demand growth continues beyond the policy horizon.", (by_row[("Policy_Signals", policy_index)].id, *[by_row[("Demand_Scenarios", i)].id for i in conflicting])))
    options = tuple(EVOptionAssessment(str(row.get("Option")), _number(row.get("Investment_EUR")), _number(row.get("Lead_Time_Months")) or 0.0, _number(row.get("Added_Capacity")) or 0.0, _number(row.get("Operating_Cost_Premium")) or 0.0, str(row.get("Reversibility")), ((_number(row.get("Investment_EUR")) or 0.0) / (_number(row.get("Added_Capacity")) or 1.0)) if row.get("Investment_EUR") is not None and (_number(row.get("Added_Capacity")) or 0.0) > 0 else None, str(row.get("Notes")), (by_row[("Strategic_Options", index)].id,)) for index, row in enumerate(rows["Strategic_Options"]))
    assumptions = ("Demand_History rows are observed and Demand_Scenarios rows are projected assumptions; forecasts are not treated as facts.", "Existing practical capacity is nominal capacity multiplied by practical availability and is rounded only for display.", "Missing South regional expansion cost is not substituted or estimated.", "Infrastructure readiness and policy signals are treated as constraints and counterevidence to demand realization, not as automatic demand reductions.", "Option economics report investment per added capacity where the workbook supplies both inputs; no causal revenue uplift is claimed.")
    all_ids = [item.id for item in evidence]
    claims: list[AnalyticalRecord] = []
    relationships: list[Relationship] = []
    for item in scenarios:
        claim = _record(f"ev-signal-{item.scenario.lower()}-{item.year}", f"The {item.scenario} forecast for {item.year} is {item.demand_units:,.0f} projected units against {item.practical_capacity:,.0f} existing practical capacity, leaving a capacity gap of {item.capacity_gap:,.0f} units.", list(item.evidence_ids), assumptions, ("Forecast realization depends on infrastructure readiness and policy continuity.",), (f"Observed demand realization or policy changes reduce the {item.scenario} gap materially.",), (f"Annual {item.scenario} demand realization versus practical capacity in {item.year}.",))
        claims.append(claim)
        relationships.extend(Relationship(f"{claim.id}-supports-{evidence_id}", evidence_id, claim.id, "supports") for evidence_id in claim.evidence_ids)
    issue_ids = [item for issue in issues for item in issue.evidence_ids]
    quality = _record("ev-data-quality", f"The EV workbook contains {len(issues)} explicit reconciliation, missing-input, or policy-consistency issues that limit confidence in an irreversible build decision.", issue_ids or all_ids, assumptions, ("Corrected source data or policy updates may change the option ranking.",), ("All reported KPIs reconcile, expansion cost is supplied, and policy signals align with the forecast narrative.",), ("Open KPI deltas, missing costs, infrastructure readiness, and policy status.",))
    claims.append(quality)
    relationships.extend(Relationship(f"{quality.id}-supports-{evidence_id}", evidence_id, quality.id, "supports") for evidence_id in quality.evidence_ids)
    implication = _record("ev-capacity-implication", "The projected capacity gap supports staged capacity protection, but infrastructure and policy constraints make the high forecast an insufficient standalone case for a full irreversible expansion.", all_ids, assumptions, ("The workbook lacks utilization, margin, and customer-level adoption evidence.",), ("Observed demand, infrastructure readiness, and policy support all confirm the high forecast before the full-expansion lead time expires.",), ("Demand realization, policy renewal, grid readiness, and service-network readiness.",))
    relationships.extend(Relationship(f"{claim.id}-informs-{implication.id}", claim.id, implication.id, "informs") for claim in claims)
    recommendation = _record("ev-recommendation", "Conditional recommendation: start with the modular pilot and reversible outsource overflow, preserve the option to expand, and approve full expansion only when demand realization and policy/infrastructure triggers confirm the capacity gap.", all_ids, assumptions, ("Option costs are not netted against a demand-linked contribution model because the workbook does not provide one.",), ("Two consecutive refreshes confirm the high-case gap, DACH grid readiness improves, Southern Europe policy support is renewed, and the missing expansion cost is validated.",), ("Quarterly demand realization, policy renewal, grid queue resolution, service readiness, and capacity utilization.",))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation.id}", implication.id, recommendation.id, "informs"))
    for issue_index, issue in enumerate(issues):
        for evidence_id in issue.evidence_ids:
            relationships.append(Relationship(f"ev-issue-{issue_index}-{issue.kind.lower()}-{evidence_id}", evidence_id, recommendation.id, "contradicts"))
    recommendation = replace(recommendation, relationship_ids=[item.id for item in relationships if item.to_id == recommendation.id])
    capacity_calculations = [CalculationRecord(f"ev-capacity-{year}", MeasurementKey("all regions", "practical_capacity", str(year), "units"), "sum(nominal_capacity * practical_availability)", list(capacity_evidence_by_year[year]), value, "units", [f"Capacity:{year}"]) for year, value in sorted(capacity_by_year.items())]
    capacity_calculation_ids = {item.key.period: item.id for item in capacity_calculations}
    calculations = [CalculationRecord(f"ev-{item.scenario.lower()}-{item.year}-gap", MeasurementKey(item.scenario, "capacity_gap", str(item.year), "units", item.scenario), "projected_demand - existing_practical_capacity", [*item.evidence_ids, capacity_calculation_ids.get(str(item.year), "")], item.capacity_gap, "units", [f"Demand_Scenarios:{item.year}", f"Capacity:{item.year}"]) for item in scenarios]
    calculations.extend(capacity_calculations)
    state = AnalysisState("ev-capacity-investment", 1, evidence=evidence, claims=claims, implications=[implication], recommendations=[recommendation], relationships=relationships, revisions=[Revision("revision-1", 1, "EV capacity analysis pending acceptance", [item.id for item in [*evidence, *calculations, *claims, implication, recommendation]])], invalidation=Invalidation(), revision_status=RevisionStatus.DRAFT, calculations=calculations)
    decision_question = next((str(row[1]) for row in tables["Brief"].rows if row and row[0] == "Decision question" and len(row) > 1), "Should the company expand, pilot, outsource, or defer EV service capacity?")
    horizon = next((str(row[1]) for row in tables["Brief"].rows if row and row[0] == "Horizon" and len(row) > 1), "2026–2030")
    return EVAnalysis(digest, decision_question, horizon, assumptions, tuple(issues), history, tuple(scenarios), options, ("Annual demand realization by scenario", "Capacity utilization and practical availability", "Policy renewal and step-down dates", "Regional grid, charging, and service readiness", "Open KPI and expansion-cost exceptions"), recommendation.statement, state)

def _money(value: float | None) -> str:
    return "n/a" if value is None else f"€{value:,.0f}"

def _citations(state: AnalysisState, ids: tuple[str, ...] | list[str]) -> str:
    by_id = {item.id: item for item in state.evidence}
    return ", ".join(f"`{by_id[item].source_locator.sheet}!{by_id[item].source_locator.range}`" for item in dict.fromkeys(ids) if item in by_id) or "`unavailable`"

def render_ev_report(ev: EVAnalysis, state: AnalysisState | None = None) -> str:
    state = state or ev.state
    if state.revision_status != RevisionStatus.ACCEPTED or any(not item.accepted for item in derive_finding_views(state)):
        raise ValueError("EV report requires current accepted findings")
    lines = ["# EV Capacity Investment Executive Report", "", f"Decision question: {ev.decision_question}", f"Horizon: {ev.horizon}", f"Source workbook SHA-256: `{ev.source_sha256}`", "", "## What is changing?", "- Observed history is separated from projected scenarios; the forecast is a decision input, not an observed fact.", "- Practical capacity is calculated deterministically as nominal capacity × practical availability, while policy and infrastructure remain explicit constraints.", "", "## Observed demand", "| Year | Region | Demand units | Basis | Evidence |", "|---:|---|---:|---|---|"]
    for item in ev.demand_history:
        lines.append(f"| {item.year} | {item.region} | {item.demand_units:,.0f} | {item.basis} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Alternative futures", "| Scenario | Year | Projected demand | Existing practical capacity | Capacity gap | Basis | Evidence |", "|---|---:|---:|---:|---:|---|---|"])
    for item in ev.scenarios:
        lines.append(f"| {item.scenario} | {item.year} | {item.demand_units:,.0f} | {item.practical_capacity:,.0f} | {item.capacity_gap:,.0f} | {item.basis} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Capacity gap", "The gap is a scenario signal. It does not by itself prove that demand will materialize or that full expansion is the best response.", "", "## Option economics", "| Option | Investment | Lead time | Added capacity | Cost per capacity | Operating premium | Reversibility | Notes | Evidence |", "|---|---:|---:|---:|---:|---:|---|---|---|"])
    for item in ev.options:
        lines.append(f"| {item.option} | {_money(item.investment_eur)} | {item.lead_time_months:g} months | {item.added_capacity:,.0f} | {_money(item.cost_per_added_capacity)} | {item.operating_cost_premium:.1%} | {item.reversibility} | {item.notes} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Counterarguments"])
    lines.extend(f"- `{issue.kind}`: {issue.message} (source: {_citations(state, issue.evidence_ids)})" for issue in ev.data_quality_issues)
    lines.append("- Nordics readiness and stable policy support the demand case, while DACH grid queues and Southern Europe readiness/policy uncertainty argue against treating the high scenario as certain.")
    lines.extend(["", "## Assumptions and uncertainty"])
    lines.extend(f"- {item}" for item in ev.assumptions)
    lines.extend(["", "## Recommended action", f"- {ev.recommendation}", "", "## Decision triggers"])
    lines.extend(f"- {item}" for item in ev.monitoring_triggers)
    lines.extend(["", "## What changes our mind?", "- Move to full expansion only after repeated demand realization and confirmed policy/infrastructure signposts; otherwise keep reversible capacity options active.", "", "## FindingView status"])
    lines.extend(f"- `{item.target_id}`: {item.review_status}/{item.review_outcome}; accepted={item.accepted}; evidence={_citations(state, item.evidence_ids)}" for item in derive_finding_views(state))
    return "\n".join(lines) + "\n"

def write_ev_report(path: Path, ev: EVAnalysis, state: AnalysisState | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_ev_report(ev, state), encoding="utf-8")

def run_ev_capacity_investment_workflow(store: AnalysisStore, source: Path, *, human_decision: str = "REJECT", output_dir: Path | None = None) -> EVWorkflowResult:
    try:
        ev = analyze_ev_capacity_investment(Path(source))
        pending = store.save_pending(ev.state)
        review = review_analysis_state(pending)
        acceptance = review_and_accept_pending_analysis(store, pending, review, f"review-{pending.investigation_id}-{pending.revision}", human_decision=human_decision)
        if acceptance.status == "pending":
            return EVWorkflowResult("pending", acceptance.state, replace(ev, state=acceptance.state), review, None, acceptance.failure)
        if acceptance.status != "accepted":
            return EVWorkflowResult("rejected", acceptance.state, replace(ev, state=acceptance.state), review, None, acceptance.failure)
        committed = acceptance.state
        final = replace(ev, state=committed)
        report_path = (Path(output_dir) if output_dir is not None else store.root / "artifacts") / "executive-report.md"
        write_ev_report(report_path, final, committed)
        return EVWorkflowResult("accepted", committed, final, review, report_path)
    except Exception as error:
        return EVWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
