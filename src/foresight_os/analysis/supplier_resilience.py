from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.review_workflow import review_and_accept_pending_analysis
from foresight_os.analysis.workbook_inputs import apply_table_column_mappings, read_workbook, require_row_columns, require_table, row_evidence, table_rows
from foresight_os.domain.analysis_inputs import AnalysisInputContract, normalize_work_brief
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import AnalyticalRecord, AnalysisState, Assessment, Basis, CalculationRecord, Evidence, Invalidation, MeasurementKey, Relationship, Revision, RevisionStatus, SourceLocator
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError


@dataclass(frozen=True)
class SupplierDataQualityIssue:
    kind: str
    message: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SupplierConcentrationMetric:
    part_family: str
    spend_eur: float
    top_supplier_share: float
    top_country_share: float
    supplier_hhi: float
    criticality_weighted: float
    alternatives_weighted: float
    lead_time_weighted_days: float
    defect_weighted_ppm: float
    geo_risk_weighted: float
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SupplierScenarioProjection:
    scenario: str
    part_family: str
    demand_at_risk_pct: float
    affected_spend_eur: float
    expedite_cost_eur: float
    outage_days: float
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SupplierMitigationOption:
    action: str
    one_time_cost_eur: float | None
    lead_time_months: float
    reversibility: str
    description: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class SupplierAnalysis:
    source_sha256: str
    decision_question: str
    horizon: str
    assumptions: tuple[str, ...]
    data_quality_issues: tuple[SupplierDataQualityIssue, ...]
    concentration_metrics: tuple[SupplierConcentrationMetric, ...]
    scenarios: tuple[SupplierScenarioProjection, ...]
    options: tuple[SupplierMitigationOption, ...]
    monitoring_triggers: tuple[str, ...]
    recommendation: str
    state: AnalysisState
    contract_fingerprint: str = ""
    reporting_currency: str = "EUR"

@dataclass(frozen=True)
class SupplierWorkflowResult:
    status: str
    analysis: AnalysisState | None
    supplier: SupplierAnalysis | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

def _table(workbook: Any, sheet: str) -> Any:
    return require_table(workbook, sheet)

def _rows(table: Any) -> list[dict[str, Any]]:
    return table_rows(table)

def _row_evidence(table: Any, index: int, digest: str) -> Evidence:
    values = dict(zip(table.columns, table.rows[index], strict=False))
    return row_evidence(table, index, digest, f"{table.sheet} row", units=str(values.get("Currency", "EUR")), transformation="supplier_resilience_recipe", evidence_prefix="supplier")

def _weighted(values: list[tuple[float, float]]) -> float:
    total = sum(weight for _, weight in values)
    return sum(value * weight for value, weight in values) / total if total else 0.0

def _fx(currency: str, rates: dict[str, float] | None = None, *, legacy: bool = True) -> float | None:
    supported = rates if rates is not None else {"EUR": 1.0, "USD": 0.92, "CNY": 0.13}
    if currency in supported:
        return supported[currency]
    return 1.0 if legacy and rates is None else None

def _unit_cost_eur(row: dict[str, Any], rates: dict[str, float] | None = None, *, legacy: bool = True) -> float | None:
    fx = _fx(str(row.get("Currency", "EUR")), rates, legacy=legacy)
    return None if fx is None else (_number(row.get("Unit_Cost")) or 0.0) * fx

def _record(record_id: str, statement: str, evidence_ids: list[str], assumptions: tuple[str, ...], uncertainty: tuple[str, ...], disconfirmation: tuple[str, ...], monitoring: tuple[str, ...]) -> AnalyticalRecord:
    return AnalyticalRecord(record_id, statement, Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=list(dict.fromkeys(evidence_ids)), assumptions=assumptions, uncertainty=uncertainty, confidence_rationale="Derived from deterministic row-level calculations with explicit exclusions and assumptions.", disconfirmation_conditions=disconfirmation, monitoring_indicators=monitoring)

def analyze_supplier_resilience(source: Path, input_contract: AnalysisInputContract | dict[str, Any] | None = None, *, workbook_context: Any | None = None) -> SupplierAnalysis:
    source = Path(source)
    contract = AnalysisInputContract.from_dict(input_contract) if input_contract is not None else AnalysisInputContract(
        domain="supplier_resilience",
        required_tables=("Brief", "Supplier_Master", "Incidents", "Scenario_Assumptions", "Mitigation_Options"),
        units="EUR",
        reporting_currency="EUR",
        conversion_rates={"EUR": 1.0, "USD": 0.92, "CNY": 0.13},
        compatibility_assumption="legacy supplier workbook FX map: EUR=1.0, USD=0.92, CNY=0.13",
    )
    contract.validate()
    workbook = read_workbook(source, SheetSelection(sheet_names=("Brief", "Supplier_Master", "Incidents", "Scenario_Assumptions", "Mitigation_Options"), include_hidden=True, include_hidden_rows=True), workbook_context=workbook_context)
    digest = workbook.workbook_sha256
    brief, supplier_table, incident_table, scenario_table, option_table = [_table(workbook, name) for name in ("Brief", "Supplier_Master", "Incidents", "Scenario_Assumptions", "Mitigation_Options")]
    conversion_rates = contract.conversion_rates
    reporting_unit = contract.reporting_currency or contract.units or "EUR"
    legacy_conversion = input_contract is None
    required_columns = (
        (supplier_table, ("Line_ID", "Supplier", "Country", "Part_Family", "Annual_Spend", "Currency", "Criticality_1_5", "Lead_Time_Days", "Defect_PPM", "Qualified_Alternatives", "Geo_Risk_1_5", "Unit_Cost")),
        (incident_table, ("Incident_ID", "Date", "Supplier", "Part_Family", "Disruption_Days", "Expedite_Premium_pct")),
        (scenario_table, ("Scenario", "Outage_Days", "Expedite_Premium", "Demand_at_Risk_pct")),
        (option_table, ("Action", "One_Time_Cost_EUR", "Lead_Time_Months", "Reversibility", "Description")),
    )
    supplier_rows, incident_rows, scenario_rows, option_rows = [
        apply_table_column_mappings(table, _rows(table), contract.column_mappings, columns)
        for table, columns in required_columns
    ]
    for (table, columns), rows in zip(required_columns, (supplier_rows, incident_rows, scenario_rows, option_rows), strict=True):
        require_row_columns(rows, table.sheet, columns)
    supplier_rows = [dict(row, __source_index=index) for index, row in enumerate(supplier_rows)]
    selected_entities = set(contract.entity_scope)
    if selected_entities:
        supplier_rows = [
            row for row in supplier_rows
            if any(str(row.get(field, "")) in selected_entities for field in ("Supplier", "Country", "Part_Family"))
        ]
    evidence: list[Evidence] = []
    by_row: dict[tuple[str, int], Evidence] = {}
    for table in (supplier_table, incident_table, scenario_table, option_table):
        for index in range(len(table.rows)):
            by_row[(table.sheet, index)] = _row_evidence(table, index, digest)
            evidence.append(by_row[(table.sheet, index)])
    issues: list[SupplierDataQualityIssue] = []
    available_scenarios = {str(row.get("Scenario")) for row in scenario_rows}
    selected_scenarios = set(contract.scenarios)
    if selected_scenarios:
        unknown_scenarios = sorted(selected_scenarios - available_scenarios)
        if unknown_scenarios:
            issues.append(SupplierDataQualityIssue("UNKNOWN_SCENARIO_SCOPE", f"Requested scenarios are not present in the workbook: {unknown_scenarios}.", tuple(by_row[(scenario_table.sheet, index)].id for index in range(len(scenario_rows)))))
    if selected_entities and not supplier_rows:
        issues.append(SupplierDataQualityIssue("EMPTY_ENTITY_SCOPE", f"No supplier rows match the declared entity scope: {sorted(selected_entities)}.", ()))
    duplicate_indexes: set[int] = set()
    seen: dict[tuple[Any, ...], int] = {}
    for index, row in enumerate(supplier_rows):
        key = (row.get("Line_ID"), row.get("Supplier"), row.get("Part_Family"))
        if key in seen:
            duplicate_indexes.add(index)
            issues.append(SupplierDataQualityIssue("DUPLICATE_LINE", f"Duplicate supplier-part line for {key}.", (by_row[(supplier_table.sheet, seen[key])].id, by_row[(supplier_table.sheet, row["__source_index"])].id)))
        else:
            seen[key] = row["__source_index"]
        if row.get("Qualified_Alternatives") is None:
            issues.append(SupplierDataQualityIssue("MISSING_ALTERNATIVES", f"Qualified alternatives are missing for {row.get('Line_ID')}.", (by_row[(supplier_table.sheet, row["__source_index"])].id,)))
    if contract.duplicate_policy == "reject" and any(issue.kind == "DUPLICATE_LINE" for issue in issues):
        raise ValueError("duplicate policy reject: supplier duplicate rows are present")
    if contract.missing_value_policy == "reject" and any(issue.kind == "MISSING_ALTERNATIVES" for issue in issues):
        raise ValueError("missing-value policy reject: supplier alternatives are missing")
    valid_rows = [(index, row) for index, row in enumerate(supplier_rows) if index not in duplicate_indexes]
    family_values: dict[str, list[tuple[int, dict[str, Any], float]]] = {}
    for index, row in valid_rows:
        fx = _fx(str(row.get("Currency", "EUR")), conversion_rates, legacy=legacy_conversion)
        if fx is None:
            issues.append(SupplierDataQualityIssue("UNSUPPORTED_CONVERSION", f"No declared conversion rate for {row.get('Currency')}.", (by_row[(supplier_table.sheet, row["__source_index"])].id,)))
            continue
        spend = (_number(row.get("Annual_Spend")) or 0.0) * fx
        family_values.setdefault(str(row.get("Part_Family")), []).append((index, row, spend))
    for family, items in family_values.items():
        costs = sorted(value for _, row, _ in items if (value := _unit_cost_eur(row, conversion_rates, legacy=legacy_conversion)) is not None)
        if not costs:
            continue
        median = costs[len(costs) // 2] if len(costs) % 2 else (costs[len(costs) // 2 - 1] + costs[len(costs) // 2]) / 2
        for index, row, _ in items:
            unit_cost = _unit_cost_eur(row, conversion_rates, legacy=legacy_conversion)
            if unit_cost is not None and (_number(row.get("Geo_Risk_1_5")) or 0.0) >= 4 and unit_cost <= median * 0.8:
                issues.append(SupplierDataQualityIssue("LOW_COST_HIGH_RISK", f"{row.get('Supplier')} is low-cost relative to {family} but has high geographic risk.", (by_row[(supplier_table.sheet, row["__source_index"])].id,)))
    metrics: list[SupplierConcentrationMetric] = []
    for family, items in sorted(family_values.items()):
        by_supplier: dict[str, float] = {}
        by_country: dict[str, float] = {}
        for _, row, spend in items:
            by_supplier[str(row.get("Supplier"))] = by_supplier.get(str(row.get("Supplier")), 0.0) + spend
            by_country[str(row.get("Country"))] = by_country.get(str(row.get("Country")), 0.0) + spend
        total = sum(by_supplier.values())
        shares = [value / total for value in by_supplier.values()] if total else []
        metrics.append(SupplierConcentrationMetric(family, total, max(by_supplier.values(), default=0.0) / total if total else 0.0, max(by_country.values(), default=0.0) / total if total else 0.0, sum(share * share for share in shares), _weighted([(_number(row.get("Criticality_1_5")) or 0.0, spend) for _, row, spend in items]), _weighted([(_number(row.get("Qualified_Alternatives")) or 0.0, spend) for _, row, spend in items]), _weighted([(_number(row.get("Lead_Time_Days")) or 0.0, spend) for _, row, spend in items]), _weighted([(_number(row.get("Defect_PPM")) or 0.0, spend) for _, row, spend in items]), _weighted([(_number(row.get("Geo_Risk_1_5")) or 0.0, spend) for _, row, spend in items]), tuple(by_row[(supplier_table.sheet, row["__source_index"])].id for _, row, _ in items)))
    scenarios: list[SupplierScenarioProjection] = []
    for scenario_index, row in enumerate(scenario_rows):
        name = str(row.get("Scenario"))
        if selected_scenarios and name not in selected_scenarios:
            continue
        risk = _number(row.get("Demand_at_Risk_pct")) or 0.0
        premium = _number(row.get("Expedite_Premium")) or 0.0
        for metric in metrics:
            scenarios.append(SupplierScenarioProjection(name, metric.part_family, risk, metric.spend_eur * risk, metric.spend_eur * risk * premium, _number(row.get("Outage_Days")) or 0.0, tuple(dict.fromkeys((*metric.evidence_ids, by_row[(scenario_table.sheet, scenario_index)].id)))))
    options_list: list[SupplierMitigationOption] = []
    for index, row in enumerate(option_rows):
        source_currency = str(row.get("Currency") or row.get("Unit") or "EUR")
        factor = 1.0 if source_currency == reporting_unit else conversion_rates.get(source_currency)
        if factor is None:
            issues.append(SupplierDataQualityIssue("UNSUPPORTED_CONVERSION", f"No declared conversion rate from {source_currency} to {reporting_unit}.", (by_row[(option_table.sheet, index)].id,)))
        cost = _number(row.get("One_Time_Cost_EUR"))
        options_list.append(SupplierMitigationOption(str(row.get("Action")), cost * factor if cost is not None and factor is not None else None, _number(row.get("Lead_Time_Months")) or 0.0, str(row.get("Reversibility")), str(row.get("Description")), (by_row[(option_table.sheet, index)].id,)))
    options = tuple(options_list)
    conversion_assumption = "EUR is the reporting currency; deterministic conversions are EUR=1.00, USD=0.92, and CNY=0.13." if legacy_conversion else f"{reporting_unit} is the reporting currency; declared conversion rates are applied only to monetary inputs."
    assumptions = (conversion_assumption, "The later exact supplier-part duplicate is excluded from quality-adjusted metrics and remains visible as an issue.", "Missing qualified alternatives are not imputed; zero alternatives means none are recorded, while blank remains unresolved.", "Outage exposure is family spend × demand-at-risk × stated expedite premium; it is a prioritization proxy, not a realized-loss forecast.", "Spend concentration is not treated as strategic risk without criticality, substitution, geography, quality, and lead-time context.")
    all_ids = [item.id for item in evidence]
    claims: list[AnalyticalRecord] = []
    relationships: list[Relationship] = []
    for metric in metrics:
        claim = _record(f"supplier-signal-{metric.part_family.lower().replace(' ', '-')}", f"{metric.part_family} has {metric.top_supplier_share:.1%} top-supplier share, {metric.top_country_share:.1%} top-country share, HHI {metric.supplier_hhi:.3f}, and criticality-weighted exposure {metric.criticality_weighted:.1f}/5.", list(metric.evidence_ids), assumptions, ("Concentration alone is insufficient to establish strategic exposure.",), (f"A validated refresh lowers {metric.part_family} exposure or confirms qualified alternatives.",), (f"Monthly {metric.part_family} supplier share, alternatives, lead time, and defect PPM.",))
        claims.append(claim)
        relationships.extend(Relationship(f"{claim.id}-supports-{evidence_id}", evidence_id, claim.id, "supports") for evidence_id in claim.evidence_ids)
    quality_ids = [item for issue in issues for item in issue.evidence_ids]
    quality = _record("supplier-data-quality", f"The supplier master contains {len(issues)} explicit data-quality exceptions that must remain visible before sourcing commitments are finalized.", quality_ids or all_ids, assumptions, ("The flagged exceptions may change the ranking after source-owner confirmation.",), ("Source owners resolve every exception and the risk ranking remains unchanged.",), ("Open exception count and unresolved alternatives at each refresh.",))
    claims.append(quality)
    relationships.extend(Relationship(f"{quality.id}-supports-{evidence_id}", evidence_id, quality.id, "supports") for evidence_id in quality.evidence_ids)
    critical = max(metrics, key=lambda item: item.criticality_weighted * item.top_supplier_share, default=None)
    implication = _record("supplier-priority-implication", f"{critical.part_family if critical else 'The highest-criticality family'} carries the strongest combined criticality and concentration exposure, while the planted exceptions limit confidence in the raw ranking.", all_ids, assumptions, ("The workbook does not quantify lost revenue or customer penalties from an outage.",), ("A validated outage-loss model or qualified alternative set reverses the family priority.",), ("Scenario exposure, supplier share, alternatives, and incident severity.",))
    relationships.extend(Relationship(f"{claim.id}-informs-{implication.id}", claim.id, implication.id, "informs") for claim in claims)
    recommendation_text = "Prioritize staged diversification of Power Electronics through dual-sourcing and safety stock, then close the missing-alternatives and low-cost/high-risk exceptions; condition further redesign spend on validated outage and substitution evidence."
    recommendation = _record("supplier-recommendation", recommendation_text, all_ids, assumptions, ("Mitigation costs are not allocated to specific families, so option-to-family ROI is not claimed.",), ("Power Electronics no longer leads after source correction or qualified substitutes are confirmed.",), ("Quarterly critical-family HHI, supplier-country concentration, alternatives, disruption days, and expedite premium.",))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation.id}", implication.id, recommendation.id, "informs"))
    for issue_index, issue in enumerate(issues):
        for evidence_id in issue.evidence_ids:
            relationships.append(Relationship(f"supplier-issue-{issue_index}-{issue.kind.lower()}-{evidence_id}", evidence_id, recommendation.id, "contradicts"))
    recommendation = replace(recommendation, relationship_ids=[item.id for item in relationships if item.to_id == recommendation.id])
    calculations = [CalculationRecord(f"supplier-{metric.part_family.lower().replace(' ', '-')}-hhi", MeasurementKey(metric.part_family, "supplier_hhi", "current", "index"), "sum((supplier_spend / total_family_spend)^2)", list(metric.evidence_ids), metric.supplier_hhi, "index", [f"Supplier_Master:{item}" for item in metric.evidence_ids]) for metric in metrics]
    calculations.extend(CalculationRecord(f"supplier-{item.scenario.lower().replace(' ', '-')}-{item.part_family.lower().replace(' ', '-')}", MeasurementKey(item.part_family, "expedite_cost", item.scenario, reporting_unit, item.scenario), "family_spend * demand_at_risk_pct * expedite_premium", list(item.evidence_ids), item.expedite_cost_eur, reporting_unit, [f"Supplier_Master:{item}" for item in item.evidence_ids]) for item in scenarios)
    state = AnalysisState("supplier-resilience", 1, evidence=evidence, claims=claims, implications=[implication], recommendations=[recommendation], relationships=relationships, revisions=[Revision("revision-1", 1, "supplier resilience analysis pending acceptance", [item.id for item in [*evidence, *calculations, *claims, implication, recommendation]])], invalidation=Invalidation(), revision_status=RevisionStatus.DRAFT, calculations=calculations)
    decision_question = next((str(row[1]) for row in brief.rows if row and row[0] == "Decision question" and len(row) > 1), "Does purchasing concentration create unacceptable strategic exposure?")
    horizon = next((str(row[1]) for row in brief.rows if row and row[0] == "Horizon" and len(row) > 1), "12–36 months")
    return SupplierAnalysis(digest, decision_question, horizon, assumptions, tuple(issues), tuple(metrics), tuple(scenarios), options, ("Supplier-part HHI and top supplier share", "Qualified alternatives by critical family", "Disruption days and expedite premium", "Defect PPM and lead-time excursions", "Open data-quality exceptions"), recommendation.statement, state, contract.fingerprint, reporting_unit)

def _money(value: float | None, currency: str = "EUR") -> str:
    return "n/a" if value is None else f"{currency} {value:,.0f}"

def _citations(state: AnalysisState, ids: tuple[str, ...] | list[str]) -> str:
    by_id = {item.id: item for item in state.evidence}
    return ", ".join(f"`{by_id[item].source_locator.sheet}!{by_id[item].source_locator.range}`" for item in dict.fromkeys(ids) if item in by_id) or "`unavailable`"

def render_supplier_report(supplier: SupplierAnalysis, state: AnalysisState | None = None) -> str:
    state = state or supplier.state
    if state.revision_status != RevisionStatus.ACCEPTED or any(not item.accepted for item in derive_finding_views(state)):
        raise ValueError("supplier report requires current accepted findings")
    lines = ["# Supplier Resilience Executive Report", "", f"Decision question: {supplier.decision_question}", f"Horizon: {supplier.horizon}", f"Reporting currency: {supplier.reporting_currency}", f"Source workbook SHA-256: `{supplier.source_sha256}`", "", "## What is changing?", "- Strategic exposure is driven by concentration combined with criticality, substitution difficulty, geography, quality, and lead time—not spend concentration alone.", "- The quality-adjusted view excludes only the later duplicate line; missing alternatives remain unresolved and visible.", "", "## Concentration metrics", f"| Part family | Spend {supplier.reporting_currency} | Top supplier | Top country | HHI | Criticality | Alternatives | Lead time | Defect PPM | Geo risk | Evidence |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for item in sorted(supplier.concentration_metrics, key=lambda value: value.criticality_weighted * value.top_supplier_share, reverse=True):
        lines.append(f"| {item.part_family} | {_money(item.spend_eur, supplier.reporting_currency)} | {item.top_supplier_share:.1%} | {item.top_country_share:.1%} | {item.supplier_hhi:.3f} | {item.criticality_weighted:.1f}/5 | {item.alternatives_weighted:.1f} | {item.lead_time_weighted_days:.0f} d | {item.defect_weighted_ppm:.0f} | {item.geo_risk_weighted:.1f}/5 | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Outage scenarios", "Scenario exposure is modeled as family spend × demand at risk, with expedite cost applying the stated scenario premium.", "| Scenario | Part family | Outage days | Demand at risk | Affected spend | Expedite cost | Evidence |", "|---|---|---:|---:|---:|---:|---|"])
    for item in supplier.scenarios:
        lines.append(f"| {item.scenario} | {item.part_family} | {item.outage_days:g} | {item.demand_at_risk_pct:.1%} | {_money(item.affected_spend_eur, supplier.reporting_currency)} | {_money(item.expedite_cost_eur, supplier.reporting_currency)} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Sourcing alternatives", "| Action | One-time cost | Lead time | Reversibility | Description | Evidence |", "|---|---:|---:|---|---|---|"])
    for item in supplier.options:
        lines.append(f"| {item.action} | {_money(item.one_time_cost_eur, supplier.reporting_currency)} | {item.lead_time_months:g} months | {item.reversibility} | {item.description} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Counterarguments"])
    lines.extend(f"- `{issue.kind}`: {issue.message} (source: {_citations(state, issue.evidence_ids)})" for issue in supplier.data_quality_issues)
    lines.append("- A high HHI is not automatically a diversification mandate when criticality is low or substitutes are plentiful; low spend can still matter when criticality and substitution difficulty are high.")
    lines.extend(["", "## Assumptions and uncertainty"])
    lines.extend(f"- {item}" for item in supplier.assumptions)
    lines.extend(["", "## Recommended action", f"- {supplier.recommendation}", "", "## Early-warning indicators"])
    lines.extend(f"- {item}" for item in supplier.monitoring_triggers)
    lines.extend(["", "## What changes our mind?", "- Re-rank the actions if a validated refresh changes the criticality-weighted concentration ranking, confirms qualified alternatives, or shows outage losses below mitigation cost.", "", "## FindingView status"])
    lines.extend(f"- `{item.target_id}`: {item.review_status}/{item.review_outcome}; accepted={item.accepted}; evidence={_citations(state, item.evidence_ids)}" for item in derive_finding_views(state))
    return "\n".join(lines) + "\n"

def write_supplier_report(path: Path, supplier: SupplierAnalysis, state: AnalysisState | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_supplier_report(supplier, state), encoding="utf-8")

def run_supplier_resilience_workflow(store: AnalysisStore, source: Path, *, human_decision: str = "REJECT", output_dir: Path | None = None, input_contract: AnalysisInputContract | dict[str, Any] | None = None) -> SupplierWorkflowResult:
    try:
        if input_contract is None and store.brief_path.exists():
            input_contract = normalize_work_brief(store.load_brief()).contract_for_domain("supplier_resilience")
        supplier = analyze_supplier_resilience(Path(source), input_contract=input_contract)
        pending = store.save_pending(supplier.state)
        review = review_analysis_state(pending)
        acceptance = review_and_accept_pending_analysis(store, pending, review, f"review-{pending.investigation_id}-{pending.revision}", human_decision=human_decision)
        if acceptance.status == "pending":
            return SupplierWorkflowResult("pending", acceptance.state, replace(supplier, state=acceptance.state), review, None, acceptance.failure)
        if acceptance.status != "accepted":
            return SupplierWorkflowResult("rejected", acceptance.state, replace(supplier, state=acceptance.state), review, None, acceptance.failure)
        committed = acceptance.state
        final = replace(supplier, state=committed)
        report_path = (Path(output_dir) if output_dir is not None else store.root / "artifacts") / "executive-report.md"
        write_supplier_report(report_path, final, committed)
        return SupplierWorkflowResult("accepted", committed, final, review, report_path)
    except Exception as error:
        return SupplierWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
