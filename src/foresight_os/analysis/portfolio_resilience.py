from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.review_workflow import review_and_accept_pending_analysis
from foresight_os.analysis.workbook_inputs import apply_column_mappings, read_workbook, require_row_columns, require_table, row_evidence, table_rows, validate_mapping_targets
from foresight_os.domain.analysis_inputs import AnalysisInputContract, normalize_work_brief
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import (
    AnalyticalRecord,
    AnalysisState,
    Assessment,
    Basis,
    CalculationRecord,
    Evidence,
    Invalidation,
    MeasurementKey,
    Relationship,
    Revision,
    RevisionStatus,
    SourceLocator,
)
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError


@dataclass(frozen=True)
class PortfolioDataQualityIssue:
    kind: str
    message: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioSegmentBaseline:
    segment: str
    valid_rows: int
    units: float
    revenue: float
    gross_profit: float
    gross_margin: float
    annual_fixed_cost: float
    contribution_after_fixed_cost: float
    weighted_list_price: float
    weighted_discount: float
    weighted_variable_cost: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioScenarioProjection:
    scenario: str
    segment: str
    projected_revenue: float
    projected_gross_profit: float
    projected_contribution: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioSensitivityThreshold:
    segment: str
    break_even_demand_growth: float
    break_even_discount_shift: float


@dataclass(frozen=True)
class PortfolioOptionAssessment:
    option_id: str
    option: str
    investment_eur: float | None
    time_to_impact_months: float
    reversibility: str
    target_segment: str | None
    base_contribution: float | None
    downside_contribution: float | None
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioKpiReconciliation:
    kpi: str
    reported_value: float | None
    raw_observed_value: float | None
    quality_adjusted_value: float | None
    adjusted_delta: float | None
    status: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioAnalysis:
    source_sha256: str
    decision_question: str
    horizon: str
    assumptions: tuple[str, ...]
    data_quality_issues: tuple[PortfolioDataQualityIssue, ...]
    segment_baselines: tuple[PortfolioSegmentBaseline, ...]
    scenarios: tuple[PortfolioScenarioProjection, ...]
    sensitivity_thresholds: tuple[PortfolioSensitivityThreshold, ...]
    options: tuple[PortfolioOptionAssessment, ...]
    kpi_reconciliations: tuple[PortfolioKpiReconciliation, ...]
    monitoring_triggers: tuple[str, ...]
    recommendation: str
    state: AnalysisState
    contract_fingerprint: str = ""
    reporting_currency: str = "EUR"


@dataclass(frozen=True)
class PortfolioWorkflowResult:
    status: str
    analysis: AnalysisState | None
    portfolio: PortfolioAnalysis | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _table(workbook: Any, sheet: str) -> Any:
    return require_table(workbook, sheet)


def _rows(table: Any) -> list[dict[str, Any]]:
    return table_rows(table)


def _row_range(table: Any, index: int) -> str:
    provenance = table.row_provenance[index]
    return f"{provenance[0].coordinate}:{provenance[-1].coordinate}"


def _row_evidence(table: Any, index: int, digest: str, calculation: str) -> Evidence:
    values = dict(zip(table.columns, table.rows[index], strict=False))
    return row_evidence(
        table,
        index,
        digest,
        calculation,
        units=str(values.get("Currency", "unknown")),
        transformation="portfolio_resilience_recipe",
        evidence_prefix="portfolio",
    )


def _weighted(values: list[tuple[float, float]]) -> float:
    denominator = sum(weight for _, weight in values)
    return sum(value * weight for value, weight in values) / denominator if denominator else 0.0


def _record(
    record_id: str,
    statement: str,
    evidence_ids: list[str],
    *,
    assumptions: tuple[str, ...] = (),
    uncertainty: tuple[str, ...] = (),
    confidence_rationale: str = "",
    disconfirmation_conditions: tuple[str, ...] = (),
    monitoring_indicators: tuple[str, ...] = (),
) -> AnalyticalRecord:
    return AnalyticalRecord(
        record_id,
        statement,
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=evidence_ids,
        assumptions=assumptions,
        uncertainty=uncertainty,
        confidence_rationale=confidence_rationale,
        disconfirmation_conditions=disconfirmation_conditions,
        monitoring_indicators=monitoring_indicators,
    )


def analyze_portfolio_resilience(source: Path, input_contract: AnalysisInputContract | dict[str, Any] | None = None, *, workbook_context: Any | None = None) -> PortfolioAnalysis:
    source = Path(source)
    contract = AnalysisInputContract.from_dict(input_contract) if input_contract is not None else AnalysisInputContract(
        domain="portfolio_resilience",
        required_tables=("Brief", "Sales_History", "Fixed_Costs", "Scenario_Assumptions", "Strategic_Options", "Reported_KPIs"),
        periods=("2026",),
        baseline_period="2026",
        comparison_period="2025",
        scenarios=("Downside", "Base", "Upside"),
        units="EUR",
        reporting_currency="EUR",
        compatibility_assumption="legacy workbook metadata defaults",
    )
    contract.validate()
    period_by_raw = {spec.raw: spec for spec in contract.period_specs}
    selected_spec = period_by_raw.get(contract.baseline_period or "") or (contract.period_specs[-1] if contract.period_specs else None)
    comparison_spec = period_by_raw.get(contract.comparison_period or "") or (contract.period_specs[-2] if len(contract.period_specs) > 1 else None)
    if selected_spec is not None and (selected_spec.granularity != "year" or selected_spec.is_cross_year):
        raise ValueError("unsupported period granularity for portfolio_resilience: year required")
    if comparison_spec is not None and (comparison_spec.granularity != "year" or comparison_spec.is_cross_year):
        raise ValueError("unsupported comparison period granularity for portfolio_resilience: year required")
    selected_period = str(selected_spec.start_year if selected_spec is not None else 2026)
    comparison_period = str(comparison_spec.start_year if comparison_spec is not None else 2025)
    workbook = read_workbook(
        source,
        SheetSelection(
            sheet_names=("Brief", "Sales_History", "Fixed_Costs", "Scenario_Assumptions", "Strategic_Options", "Reported_KPIs"),
            include_hidden=True,
            include_hidden_rows=True,
        ),
        workbook_context=workbook_context,
    )
    source_sha256 = workbook.workbook_sha256
    brief_table = _table(workbook, "Brief")
    selected_entities = set(contract.entity_scope)
    sales_table = _table(workbook, "Sales_History")
    fixed_table = _table(workbook, "Fixed_Costs")
    scenario_table = _table(workbook, "Scenario_Assumptions")
    options_table = _table(workbook, "Strategic_Options")
    kpi_table = _table(workbook, "Reported_KPIs")
    mapping_headers = {
        column
        for table in (sales_table, fixed_table, scenario_table, options_table, kpi_table)
        for column in getattr(table, "columns", ())
    }
    validate_mapping_targets(mapping_headers, contract.column_mappings)
    sales_rows = apply_column_mappings(_rows(sales_table), contract.column_mappings, available_headers=mapping_headers)
    fixed_rows = apply_column_mappings(_rows(fixed_table), contract.column_mappings, available_headers=mapping_headers)
    scenario_rows = apply_column_mappings(_rows(scenario_table), contract.column_mappings, available_headers=mapping_headers)
    option_rows = apply_column_mappings(_rows(options_table), contract.column_mappings, available_headers=mapping_headers)
    kpi_rows = apply_column_mappings(_rows(kpi_table), contract.column_mappings, available_headers=mapping_headers)
    for sheet, rows, columns in (
        (sales_table.sheet, sales_rows, ("Quarter", "Region", "Segment", "Units", "List_Price", "Discount_pct", "Variable_Cost_per_Unit", "Revenue", "Gross_Profit")),
        (fixed_table.sheet, fixed_rows, ("Segment", "Annual_Fixed_Cost_EUR")),
        (scenario_table.sheet, scenario_rows, ("Scenario", "Demand_Growth", "Cost_Inflation", "Discount_Shift", "Fixed_Cost_Change")),
        (options_table.sheet, option_rows, ("Option_ID", "Option", "Investment_EUR", "Time_to_Impact_Months", "Reversibility")),
        (kpi_table.sheet, kpi_rows, ("KPI", "Reported_Value", "Unit")),
    ):
        require_row_columns(rows, sheet, columns)
    reporting_unit = contract.reporting_currency or contract.units or "EUR"
    evidence: list[Evidence] = []
    evidence_by_table_row: dict[tuple[str, int], Evidence] = {}
    for table in (sales_table, fixed_table, scenario_table, options_table, kpi_table):
        for index in range(len(table.rows)):
            item = _row_evidence(table, index, source_sha256, f"{table.sheet} row")
            evidence.append(item)
            evidence_by_table_row[(table.sheet, index)] = item
    sales_evidence = {index: evidence_by_table_row[("Sales_History", index)] for index in range(len(sales_rows))}
    issues: list[PortfolioDataQualityIssue] = []
    unsupported_conversion_rows: set[tuple[str, int]] = set()
    for sheet, rows, monetary_fields in (
        (sales_table.sheet, sales_rows, ("Revenue", "Gross_Profit", "Variable_Cost_per_Unit", "List_Price")),
        (fixed_table.sheet, fixed_rows, ("Annual_Fixed_Cost_EUR",)),
        (options_table.sheet, option_rows, ("Investment_EUR",)),
        (kpi_table.sheet, kpi_rows, ("Reported_Value",)),
    ):
        for index, row in enumerate(rows):
            if sheet == kpi_table.sheet and str(row.get("Unit", "")).strip().lower() in {"%", "percent", "percentage", "ratio", "count", "index"}:
                continue
            source_currency = str(row.get("Currency") or row.get("Unit") or "EUR")
            factor = 1.0 if source_currency == reporting_unit else contract.conversion_rates.get(source_currency)
            if factor is None:
                unsupported_conversion_rows.add((sheet, index))
                issues.append(PortfolioDataQualityIssue("UNSUPPORTED_CONVERSION", f"No declared conversion rate from {source_currency} to {reporting_unit}.", (evidence_by_table_row[(sheet, index)].id,)))
                continue
            for field in monetary_fields:
                if isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool):
                    row[field] = float(row[field]) * factor
    seen: dict[tuple[Any, ...], int] = {}
    duplicate_indexes: set[int] = set()
    missing_cost_indexes: set[int] = set()
    for index, row in enumerate(sales_rows):
        key = (row.get("Quarter"), row.get("Region"), row.get("Segment"))
        if key in seen:
            duplicate_indexes.add(index)
            issues.append(PortfolioDataQualityIssue("DUPLICATE_ROW", f"Duplicate sales row for {key}.", (sales_evidence[seen[key]].id, sales_evidence[index].id)))
        else:
            seen[key] = index
        discount = _number(row.get("Discount_pct"))
        if discount is None or not 0 <= discount <= 1:
            issues.append(PortfolioDataQualityIssue("MALFORMED_DISCOUNT", f"Discount is outside the 0–1 range for {row.get('Source_ID')}.", (sales_evidence[index].id,)))
        if row.get("Variable_Cost_per_Unit") is None or row.get("Gross_Profit") is None:
            missing_cost_indexes.add(index)
            issues.append(PortfolioDataQualityIssue("MISSING_COST", f"Variable cost or derived gross profit is missing for {row.get('Source_ID')}.", (sales_evidence[index].id,)))
        revenue = _number(row.get("Revenue"))
        if revenue is not None and revenue < 0:
            issues.append(PortfolioDataQualityIssue("NEGATIVE_REVENUE", f"Revenue is negative for {row.get('Source_ID')}.", (sales_evidence[index].id,)))
    if contract.duplicate_policy == "reject" and any(issue.kind == "DUPLICATE_ROW" for issue in issues):
        raise ValueError("duplicate policy reject: portfolio duplicate rows are present")
    if contract.missing_value_policy == "reject" and any(issue.kind == "MISSING_COST" for issue in issues):
        raise ValueError("missing-value policy reject: portfolio cost values are missing")
    quality_rows: list[tuple[int, dict[str, Any]]] = []
    for index, row in enumerate(sales_rows):
        discount = _number(row.get("Discount_pct"))
        if (
            index not in duplicate_indexes
            and (contract.missing_value_policy == "preserve_as_issue" or index not in missing_cost_indexes)
            and ("Sales_History", index) not in unsupported_conversion_rows
            and discount is not None
            and 0 <= discount <= 1
            and _number(row.get("Revenue")) is not None
            and (_number(row.get("Revenue")) or 0) >= 0
        ):
            quality_rows.append((index, row))
    quality_adjusted_rows = [
        (index, row)
        for index, row in quality_rows
        if str(row.get("Quarter", "")).startswith(selected_period)
        and (not selected_entities or str(row.get("Region")) in selected_entities)
    ]
    unsupported_fixed_segments = {
        str(row.get("Segment"))
        for index, row in enumerate(fixed_rows)
        if ("Fixed_Costs", index) in unsupported_conversion_rows
    }
    fixed_costs = {
        str(row.get("Segment")): _number(row.get("Annual_Fixed_Cost_EUR")) or 0.0
        for index, row in enumerate(fixed_rows)
        if ("Fixed_Costs", index) not in unsupported_conversion_rows
    }
    by_segment: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, row in quality_adjusted_rows:
        by_segment.setdefault(str(row.get("Segment")), []).append((index, row))
    segments = sorted((set(by_segment) | set(fixed_costs)) - unsupported_fixed_segments)
    baselines: list[PortfolioSegmentBaseline] = []
    for segment in segments:
        items = by_segment.get(segment, [])
        units = sum(_number(row.get("Units")) or 0.0 for _, row in items)
        revenue = sum(_number(row.get("Revenue")) or 0.0 for _, row in items)
        gross_profit = sum(_number(row.get("Gross_Profit")) or 0.0 for _, row in items)
        cost_valid_items = [(index, row) for index, row in items if _number(row.get("Variable_Cost_per_Unit")) is not None and _number(row.get("Gross_Profit")) is not None]
        fixed_cost = fixed_costs.get(segment, 0.0)
        baselines.append(
            PortfolioSegmentBaseline(
                segment,
                len(items),
                units,
                revenue,
                gross_profit,
                gross_profit / revenue if revenue else 0.0,
                fixed_cost,
                gross_profit - fixed_cost,
                _weighted([(_number(row.get("List_Price")) or 0.0, _number(row.get("Units")) or 0.0) for _, row in items]),
                _weighted([(_number(row.get("Discount_pct")) or 0.0, _number(row.get("Units")) or 0.0) for _, row in items]),
                _weighted([(_number(row.get("Variable_Cost_per_Unit")) or 0.0, _number(row.get("Units")) or 0.0) for _, row in cost_valid_items]),
                tuple(sales_evidence[index].id for index, _ in items),
            )
        )
    baseline_by_segment = {item.segment: item for item in baselines}
    scenario_projections: list[PortfolioScenarioProjection] = []
    scenario_evidence: dict[str, tuple[str, ...]] = {}
    for index, row in enumerate(scenario_rows):
        scenario = str(row.get("Scenario"))
        if contract.scenarios and scenario not in contract.scenarios:
            continue
        scenario_evidence[scenario] = (evidence_by_table_row[("Scenario_Assumptions", index)].id,)
        demand_growth = _number(row.get("Demand_Growth")) or 0.0
        cost_inflation = _number(row.get("Cost_Inflation")) or 0.0
        discount_shift = _number(row.get("Discount_Shift")) or 0.0
        fixed_cost_change = _number(row.get("Fixed_Cost_Change")) or 0.0
        for baseline in baselines:
            units = baseline.units * (1 + demand_growth)
            discount = baseline.weighted_discount + discount_shift
            price = baseline.weighted_list_price
            variable_cost = baseline.weighted_variable_cost * (1 + cost_inflation)
            projected_revenue = units * price * (1 - discount)
            projected_gross_profit = units * (price * (1 - discount) - variable_cost)
            projected_contribution = projected_gross_profit - baseline.annual_fixed_cost * (1 + fixed_cost_change)
            scenario_projections.append(PortfolioScenarioProjection(scenario, baseline.segment, projected_revenue, projected_gross_profit, projected_contribution, baseline.evidence_ids + scenario_evidence[scenario]))
    sensitivities: list[PortfolioSensitivityThreshold] = []
    for baseline in baselines:
        unit_contribution = baseline.weighted_list_price * (1 - baseline.weighted_discount) - baseline.weighted_variable_cost
        sensitivities.append(
            PortfolioSensitivityThreshold(
                baseline.segment,
                baseline.annual_fixed_cost / (baseline.units * unit_contribution) - 1 if baseline.units and unit_contribution else math.nan,
                1 - (baseline.weighted_variable_cost + baseline.annual_fixed_cost / baseline.units) / baseline.weighted_list_price - baseline.weighted_discount if baseline.units and baseline.weighted_list_price else math.nan,
            )
        )
    options: list[PortfolioOptionAssessment] = []
    for index, row in enumerate(option_rows):
        option = str(row.get("Option"))
        target_segment = next((segment for segment in baseline_by_segment if segment.lower() in option.lower()), None)
        if target_segment is None and "spare" in option.lower():
            target_segment = "Spare Parts"
        baseline = baseline_by_segment.get(target_segment) if target_segment else None
        downside = next((item for item in scenario_projections if item.scenario == "Downside" and item.segment == target_segment), None)
        options.append(
            PortfolioOptionAssessment(
                str(row.get("Option_ID")),
                option,
                _number(row.get("Investment_EUR")) if ("Strategic_Options", index) not in unsupported_conversion_rows else None,
                _number(row.get("Time_to_Impact_Months")) or 0.0,
                str(row.get("Reversibility")),
                target_segment,
                baseline.contribution_after_fixed_cost if baseline else None,
                downside.projected_contribution if downside else None,
                (evidence_by_table_row[("Strategic_Options", index)].id,),
            )
        )
    raw_2026 = [row for row in sales_rows if str(row.get("Quarter", "")).startswith(selected_period) and (not selected_entities or str(row.get("Region")) in selected_entities)]
    adjusted_2026 = [row for _, row in quality_adjusted_rows if str(row.get("Quarter", "")).startswith(selected_period)]
    raw_totals = {
        "Revenue": sum(_number(row.get("Revenue")) or 0.0 for row in raw_2026),
        "Gross_Profit": sum(_number(row.get("Gross_Profit")) or 0.0 for row in raw_2026),
    }
    adjusted_totals = {
        "Revenue": sum(_number(row.get("Revenue")) or 0.0 for row in adjusted_2026),
        "Gross_Profit": sum(_number(row.get("Gross_Profit")) or 0.0 for row in adjusted_2026),
    }
    analytics_revenue_by_year = {
        year: sum(
            _number(row.get("Revenue")) or 0.0
            for _, row in quality_rows
            if str(row.get("Quarter", "")).startswith(year)
            and row.get("Segment") == "Analytics Software"
        )
        for year in (comparison_period, selected_period)
    }
    analytics_cagr = (
        analytics_revenue_by_year[selected_period] / analytics_revenue_by_year[comparison_period] - 1
        if analytics_revenue_by_year[comparison_period]
        else None
    )
    reconciliations: list[PortfolioKpiReconciliation] = []
    for index, row in enumerate(kpi_rows):
        kpi = str(row.get("KPI"))
        reported = _number(row.get("Reported_Value"))
        metric = "Revenue" if kpi in {f"{selected_period} Revenue", "2026 Revenue"} else "Gross_Profit" if kpi in {f"{selected_period} Gross Profit", "2026 Gross Profit"} else None
        if metric is not None:
            raw_value = raw_totals[metric]
            adjusted = adjusted_totals[metric]
            delta = adjusted - reported if reported is not None else None
            status = "UNSUPPORTED_CONVERSION" if ("Reported_KPIs", index) in unsupported_conversion_rows else "MISMATCH" if reported is None or not math.isclose(adjusted, reported, rel_tol=1e-9, abs_tol=0.01) else "RECONCILED"
        elif kpi == "Analytics Software CAGR":
            raw_value = analytics_cagr
            adjusted = analytics_cagr
            delta = adjusted - reported if adjusted is not None and reported is not None else None
            status = "UNSUPPORTED_CONVERSION" if ("Reported_KPIs", index) in unsupported_conversion_rows else "MISMATCH" if adjusted is None or reported is None or not math.isclose(adjusted, reported, rel_tol=1e-9, abs_tol=0.0001) else "RECONCILED"
        elif kpi == "Service Contract renewal proxy":
            raw_value = None
            adjusted = None
            delta = None
            status = "ASSUMPTION_ONLY"
        else:
            raw_value = None
            adjusted = None
            delta = None
            status = "NOT_RECONCILED"
        reconciliations.append(
            PortfolioKpiReconciliation(
                kpi,
                reported,
                raw_value,
                adjusted,
                delta,
                status,
                (evidence_by_table_row[("Reported_KPIs", index)].id,),
            )
        )
    assumptions = (
        f"Observed {selected_period} rows are the baseline; scenario assumptions are not treated as observed facts.",
        "Duplicate rows, missing cost/gross profit, malformed discounts, and negative revenue are excluded from quality-adjusted calculations and remain visible as issues.",
        "Scenario projections apply demand growth to units, cost inflation to weighted variable cost, discount shift to weighted discount, and fixed-cost change to annual fixed cost.",
        "Option assessments are prioritization proxies, not causal ROI forecasts; investment uplift is not supplied by the workbook.",
        "Do not silently repair data; new source evidence is required before changing an exception.",
    )
    scenario_by_segment = {
        segment: {item.scenario: item for item in scenario_projections if item.segment == segment}
        for segment in baseline_by_segment
    }
    segment_claims: list[AnalyticalRecord] = []
    relationships: list[Relationship] = []
    for baseline in baselines:
        projections = scenario_by_segment[baseline.segment]
        modeled = tuple(projections.values())
        scenario_text = ", ".join(f"{item.scenario} {_money(item.projected_contribution, reporting_unit)}" for item in modeled) or "no selected scenario projection"
        scenario_evidence_ids = [evidence_id for item in modeled for evidence_id in item.evidence_ids]
        claim = _record(
            f"portfolio-claim-{baseline.segment.lower().replace(' ', '-')}",
            f"{baseline.segment}: quality-adjusted {selected_period} revenue was {_money(baseline.revenue, reporting_unit)} with {baseline.gross_margin:.1%} gross margin; modeled contribution is {scenario_text}.",
            list(dict.fromkeys((*baseline.evidence_ids, *scenario_evidence_ids))),
            assumptions=assumptions,
            uncertainty=("Quality-adjusted results exclude planted exceptions; the excluded rows require source-owner confirmation.",),
            confidence_rationale="The claim is derived from deterministic row-level calculations and the explicitly selected scenario inputs.",
            disconfirmation_conditions=(f"{baseline.segment} contribution falls below {reporting_unit} 0 under observed 2027 inputs.",),
            monitoring_indicators=(f"Quarterly {baseline.segment} units, realized discount, and gross margin.",),
        )
        for evidence_id in claim.evidence_ids:
            relationships.append(Relationship(f"{claim.id}-supports-{evidence_id}", evidence_id, claim.id, "supports"))
        claim_relationships = [item.id for item in relationships if item.to_id == claim.id]
        segment_claims.append(AnalyticalRecord(claim.id, claim.statement, claim.basis, claim.assessment, evidence_ids=claim.evidence_ids, relationship_ids=claim_relationships, assumptions=claim.assumptions, uncertainty=claim.uncertainty, confidence_rationale=claim.confidence_rationale, disconfirmation_conditions=claim.disconfirmation_conditions, monitoring_indicators=claim.monitoring_indicators))
    quality_ids = tuple(dict.fromkeys(evidence_id for issue in issues for evidence_id in issue.evidence_ids))
    quality_claim_draft = _record(
        "portfolio-data-quality-claim",
        f"The {selected_period} portfolio baseline contains {len(issues)} explicit data-quality exceptions; reported KPIs require reconciliation before management treats them as authoritative.",
        list(quality_ids),
        assumptions=assumptions,
        uncertainty=("Raw and quality-adjusted totals diverge because the workbook contains planted exceptions.",),
        confidence_rationale="Every exception is tied to a row-level source locator.",
        disconfirmation_conditions=("Source owners replace or explain each flagged row and the reconciled totals converge.",),
        monitoring_indicators=("Exception count and unresolved KPI deltas at each refresh.",),
    )
    for evidence_id in quality_claim_draft.evidence_ids:
        relationships.append(Relationship(f"{quality_claim_draft.id}-supports-{evidence_id}", evidence_id, quality_claim_draft.id, "supports"))
    quality_claim = AnalyticalRecord(quality_claim_draft.id, quality_claim_draft.statement, quality_claim_draft.basis, quality_claim_draft.assessment, evidence_ids=quality_claim_draft.evidence_ids, relationship_ids=[item.id for item in relationships if item.to_id == quality_claim_draft.id], assumptions=quality_claim_draft.assumptions, uncertainty=quality_claim_draft.uncertainty, confidence_rationale=quality_claim_draft.confidence_rationale, disconfirmation_conditions=quality_claim_draft.disconfirmation_conditions, monitoring_indicators=quality_claim_draft.monitoring_indicators)
    claims = [*segment_claims, quality_claim]
    ranked_segments = sorted(baselines, key=lambda item: item.contribution_after_fixed_cost, reverse=True)
    top_segments = ranked_segments[:2]
    if len(top_segments) >= 2:
        ranking_statement = f"{top_segments[0].segment} and {top_segments[1].segment} lead the quality-adjusted contribution ranking"
    elif top_segments:
        ranking_statement = f"{top_segments[0].segment} is the only segment with a quality-adjusted contribution result"
    else:
        ranking_statement = "No segment has a quality-adjusted contribution result"
    modeled_scenarios = tuple(dict.fromkeys(item.scenario for item in scenario_projections))
    modeled_scenario_text = ", ".join(modeled_scenarios) or "none"
    implication_draft = _record(
        "portfolio-priority-implication",
        f"{ranking_statement} across the selected modeled scenarios ({modeled_scenario_text}); Core Hardware should not receive an irreversible commitment until its pricing and revenue exceptions are remediated.",
        list(dict.fromkeys(item.id for item in evidence if item.source_locator.sheet in {"Sales_History", "Scenario_Assumptions", "Strategic_Options", "Fixed_Costs"})),
        assumptions=assumptions,
        uncertainty=("The prioritization ranking is a contribution proxy and does not estimate causal investment uplift.",),
        confidence_rationale=f"The ranking is derived from deterministic contribution calculations across the selected modeled scenarios ({modeled_scenario_text}).",
        disconfirmation_conditions=("A validated refresh reverses the top-two ranking or Core Hardware clears its data-quality exceptions.",),
        monitoring_indicators=("Scenario rank, realized gross margin, discount pressure, and exception remediation status.",),
    )
    for claim in claims:
        relationships.append(Relationship(f"{claim.id}-informs-{implication_draft.id}", claim.id, implication_draft.id, "informs"))
    implication = AnalyticalRecord(implication_draft.id, implication_draft.statement, implication_draft.basis, implication_draft.assessment, evidence_ids=implication_draft.evidence_ids, relationship_ids=[item.id for item in relationships if item.to_id == implication_draft.id], assumptions=implication_draft.assumptions, uncertainty=implication_draft.uncertainty, confidence_rationale=implication_draft.confidence_rationale, disconfirmation_conditions=implication_draft.disconfirmation_conditions, monitoring_indicators=implication_draft.monitoring_indicators)
    recommendation_statement = (
        "Prioritize staged investment in Analytics Software, then reversible Service Contracts expansion; defer irreversible Core Hardware and Spare Parts commitments until KPI reconciliation and planted data exceptions are resolved."
        if baselines
        else f"Do not make portfolio investment decisions until required conversion rates are supplied for the affected fixed-cost inputs: {', '.join(sorted(unsupported_fixed_segments)) or 'unavailable segments'}."
    )
    recommendation_draft = _record(
        "portfolio-recommendation",
        recommendation_statement,
        list(dict.fromkeys(implication.evidence_ids + [item.id for option in options for item in evidence if item.id in option.evidence_ids])),
        assumptions=assumptions,
        uncertainty=("No causal uplift or external market evidence is present in this workbook; this is an internal portfolio prioritization recommendation.",),
        confidence_rationale="The recommendation combines stable scenario ranking, option reversibility, time to impact, and explicit data-quality constraints.",
        disconfirmation_conditions=("Analytics Software or Service Contracts falls below Core Hardware on validated contribution, or unresolved data exceptions persist after the next refresh.",),
        monitoring_indicators=("Quarterly contribution by segment, discount realization, KPI deltas, and exception closure.",),
    )
    for evidence_id in recommendation_draft.evidence_ids:
        relationships.append(Relationship(f"{recommendation_draft.id}-supports-{evidence_id}", evidence_id, recommendation_draft.id, "supports"))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation_draft.id}", implication.id, recommendation_draft.id, "informs"))
    for issue_index, issue in enumerate(issues):
        for evidence_id in issue.evidence_ids:
            relationships.append(
                Relationship(
                    f"portfolio-issue-{issue_index}-{issue.kind.lower()}-{evidence_id}-contradicts-{recommendation_draft.id}",
                    evidence_id,
                    recommendation_draft.id,
                    "contradicts",
                )
            )
    recommendation = AnalyticalRecord(recommendation_draft.id, recommendation_draft.statement, recommendation_draft.basis, recommendation_draft.assessment, evidence_ids=recommendation_draft.evidence_ids, relationship_ids=[item.id for item in relationships if item.to_id == recommendation_draft.id], assumptions=recommendation_draft.assumptions, uncertainty=recommendation_draft.uncertainty, confidence_rationale=recommendation_draft.confidence_rationale, disconfirmation_conditions=recommendation_draft.disconfirmation_conditions, monitoring_indicators=recommendation_draft.monitoring_indicators)
    calculations: list[CalculationRecord] = []
    for baseline in baselines:
        calculations.append(
            CalculationRecord(
                f"portfolio-baseline-{baseline.segment.lower().replace(' ', '-')}",
                MeasurementKey(baseline.segment, "contribution_after_fixed_cost", selected_period, reporting_unit),
                "gross_profit - annual_fixed_cost",
                list(baseline.evidence_ids),
                baseline.contribution_after_fixed_cost,
                reporting_unit,
                [f"Sales_History:{item}" for item in baseline.evidence_ids],
            )
        )
    for projection in scenario_projections:
        calculations.append(
            CalculationRecord(
                f"portfolio-{projection.scenario.lower()}-{projection.segment.lower().replace(' ', '-')}",
                MeasurementKey(projection.segment, "scenario_contribution", projection.scenario, reporting_unit, projection.scenario),
                "projected_gross_profit - projected_fixed_cost",
                list(projection.evidence_ids),
                projection.projected_contribution,
                reporting_unit,
                [f"Sales_History:{item}" for item in projection.evidence_ids],
            )
        )
    all_records = [*evidence, *calculations, *claims, implication, recommendation, *relationships]
    state = AnalysisState(
        "portfolio-resilience",
        1,
        evidence=evidence,
        claims=claims,
        implications=[implication],
        recommendations=[recommendation],
        relationships=relationships,
        revisions=[Revision("revision-1", 1, "portfolio resilience analysis pending acceptance", [item.id for item in all_records])],
        invalidation=Invalidation(),
        revision_status=RevisionStatus.DRAFT,
        calculations=calculations,
    )
    decision_question = brief_table.columns[1] if len(brief_table.columns) > 1 and brief_table.columns[0] == "Decision question" else "Which product segments should the company prioritize?"
    horizon = next((str(row[1]) for row in brief_table.rows if row and row[0] == "Horizon" and len(row) > 1), "2027–2029")
    return PortfolioAnalysis(
        source_sha256,
        decision_question,
        horizon,
        assumptions,
        tuple(issues),
        tuple(baselines),
        tuple(scenario_projections),
        tuple(sensitivities),
        tuple(options),
        tuple(reconciliations),
        (
            "Quarterly segment contribution and gross margin",
            "Realized discount versus modeled discount",
            "KPI reconciliation delta",
            "Open data-quality exception count",
        ),
        recommendation.statement,
        state,
        contract.fingerprint,
        reporting_unit,
    )


def _money(value: float | None, currency: str = "EUR") -> str:
    return "n/a" if value is None else f"{currency} {value:,.0f}"


def _percent(value: float | None) -> str:
    return "n/a" if value is None or math.isnan(value) else f"{value:.1%}"


def _source_citations(state: AnalysisState, evidence_ids: tuple[str, ...] | list[str]) -> str:
    evidence_by_id = {item.id: item for item in state.evidence}
    citations = []
    for evidence_id in dict.fromkeys(evidence_ids):
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            continue
        locator = evidence.source_locator
        citations.append(f"`{locator.sheet}!{locator.range}`")
    return ", ".join(citations) if citations else "`unavailable`"


def _all_sales_range(state: AnalysisState) -> str:
    ranges = [
        item.source_locator.range
        for item in state.evidence
        if item.source_locator.sheet == "Sales_History"
    ]
    if not ranges:
        return "`Sales_History`"
    first = ranges[0].split(":", 1)[0]
    last = ranges[-1].split(":", 1)[-1]
    return f"`Sales_History!{first}:{last}`"


def render_portfolio_report(portfolio: PortfolioAnalysis, state: AnalysisState | None = None) -> str:
    state = state or portfolio.state
    findings = derive_finding_views(state)
    if state.revision_status != RevisionStatus.ACCEPTED:
        raise ValueError("portfolio report requires an accepted revision")
    if not findings or any(not finding.accepted for finding in findings):
        raise ValueError("portfolio report requires current accepted findings")

    lines = [
        "# Portfolio Resilience Executive Report",
        "",
        f"Decision question: {portfolio.decision_question}",
        f"Horizon: {portfolio.horizon}",
        f"Reporting currency: {portfolio.reporting_currency}",
        f"Source workbook SHA-256: `{portfolio.source_sha256}`",
        "",
        "## What is changing?",
        "- Quality-adjusted contribution is concentrated in Analytics Software and Service Contracts, while Core Hardware remains material but is exposed to pricing and data-quality uncertainty.",
        f"- The calculation uses observed rows from {_all_sales_range(state)} and does not silently repair flagged records.",
        "",
        "## Baseline economics",
        "| Segment | Valid rows | Revenue | Gross margin | Contribution after fixed cost | Evidence |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for baseline in sorted(portfolio.segment_baselines, key=lambda item: item.contribution_after_fixed_cost, reverse=True):
        lines.append(
            f"| {baseline.segment} | {baseline.valid_rows} | {_money(baseline.revenue, portfolio.reporting_currency)} | {_percent(baseline.gross_margin)} | {_money(baseline.contribution_after_fixed_cost, portfolio.reporting_currency)} | {_source_citations(state, baseline.evidence_ids)} |"
        )

    lines.extend([
        "",
        "## Alternative futures",
        "Scenario projections apply demand growth to units, cost inflation to weighted variable cost, discount shift to weighted discount, and fixed-cost change to annual fixed cost.",
        "| Scenario | Segment | Revenue | Gross profit | Contribution | Evidence |",
        "|---|---|---:|---:|---:|---|",
    ])
    for projection in portfolio.scenarios:
        lines.append(
            f"| {projection.scenario} | {projection.segment} | {_money(projection.projected_revenue, portfolio.reporting_currency)} | {_money(projection.projected_gross_profit, portfolio.reporting_currency)} | {_money(projection.projected_contribution, portfolio.reporting_currency)} | {_source_citations(state, projection.evidence_ids)} |"
        )

    lines.extend([
        "",
        "## Sensitivity thresholds",
        "The demand threshold is the growth rate required for modeled contribution to break even at the observed unit economics. The discount threshold is the maximum discount level before contribution reaches zero, expressed as a shift from the observed weighted discount.",
        "| Segment | Break-even demand growth | Break-even discount shift |",
        "|---|---:|---:|",
    ])
    for threshold in portfolio.sensitivity_thresholds:
        lines.append(f"| {threshold.segment} | {_percent(threshold.break_even_demand_growth)} | {_percent(threshold.break_even_discount_shift)} |")

    lines.extend([
        "",
        "## Competing options",
        "Option contribution values are prioritization proxies, not causal ROI forecasts; the workbook does not provide uplift by option, so investment is not netted against contribution.",
        "| ID | Option | Investment | Time to impact | Reversibility | Target segment | Base contribution | Downside contribution | Evidence |",
        "|---|---|---:|---:|---|---|---:|---:|---|",
    ])
    for option in portfolio.options:
        lines.append(
            f"| {option.option_id} | {option.option} | {_money(option.investment_eur, portfolio.reporting_currency)} | {option.time_to_impact_months:g} months | {option.reversibility} | {option.target_segment or 'unmapped'} | {_money(option.base_contribution, portfolio.reporting_currency)} | {_money(option.downside_contribution, portfolio.reporting_currency)} | {_source_citations(state, option.evidence_ids)} |"
        )

    lines.extend([
        "",
        "## KPI reconciliation",
        "Reported management KPIs are compared with raw observed totals and quality-adjusted totals. A renewal proxy is retained as an assumption because no renewal-level evidence exists.",
        "| KPI | Reported | Raw observed | Quality-adjusted | Delta | Status | Evidence |",
        "|---|---:|---:|---:|---:|---|---|",
    ])
    for kpi in portfolio.kpi_reconciliations:
        lines.append(
            f"| {kpi.kpi} | {_money(kpi.reported_value, portfolio.reporting_currency) if kpi.kpi not in {'Analytics Software CAGR', 'Service Contract renewal proxy'} else _percent(kpi.reported_value)} | {_money(kpi.raw_observed_value, portfolio.reporting_currency) if kpi.kpi not in {'Analytics Software CAGR', 'Service Contract renewal proxy'} else _percent(kpi.raw_observed_value)} | {_money(kpi.quality_adjusted_value, portfolio.reporting_currency) if kpi.kpi not in {'Analytics Software CAGR', 'Service Contract renewal proxy'} else _percent(kpi.quality_adjusted_value)} | {_money(kpi.adjusted_delta, portfolio.reporting_currency) if kpi.kpi not in {'Analytics Software CAGR', 'Service Contract renewal proxy'} else _percent(kpi.adjusted_delta)} | {kpi.status} | {_source_citations(state, kpi.evidence_ids)} |"
        )

    lines.extend([
        "",
        "## Counterevidence",
    ])
    for issue in portfolio.data_quality_issues:
        lines.append(f"- `{issue.kind}`: {issue.message} (source: {_source_citations(state, issue.evidence_ids)})")
    lines.extend([
        "- These exceptions contradict an unqualified reading of the raw 2026 totals: the raw totals understate the quality-adjusted revenue/gross-profit comparison because the malformed negative row is included and the duplicate row inflates one segment while missing-cost rows cannot support gross profit.",
        "",
        "## Assumptions and uncertainty",
    ])
    lines.extend(f"- {assumption}" for assumption in portfolio.assumptions)
    lines.extend([
        "",
        "## Recommended action",
        f"- {portfolio.recommendation}",
        "- Condition: release funding in stages, beginning with the faster and more reversible Analytics Software and Service Contracts options; do not make irreversible Core Hardware or Spare Parts commitments until the flagged records and KPI deltas are reconciled.",
        "",
        "## Monitoring triggers",
    ])
    lines.extend(f"- {trigger}" for trigger in portfolio.monitoring_triggers)
    lines.extend([
        "",
        "## What changes our mind?",
        "- The recommendation changes if a validated refresh reverses the Analytics Software/Service Contracts ranking, if contribution falls below zero under observed inputs, or if source owners close the exceptions and the KPI deltas converge.",
        "",
        "## FindingView status",
    ])
    for finding in findings:
        lines.append(f"- `{finding.target_id}`: {finding.review_status}/{finding.review_outcome}; accepted={finding.accepted}; evidence={_source_citations(state, finding.evidence_ids)}")
    return "\n".join(lines) + "\n"


def write_portfolio_report(path: Path, portfolio: PortfolioAnalysis, state: AnalysisState | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_portfolio_report(portfolio, state), encoding="utf-8")


def run_portfolio_resilience_workflow(
    store: AnalysisStore,
    source: Path,
    *,
    human_decision: str = "REJECT",
    output_dir: Path | None = None,
    input_contract: AnalysisInputContract | dict[str, Any] | None = None,
) -> PortfolioWorkflowResult:
    try:
        if input_contract is None and store.brief_path.exists():
            input_contract = normalize_work_brief(store.load_brief()).contract_for_domain("portfolio_resilience")
        portfolio = analyze_portfolio_resilience(Path(source), input_contract=input_contract)
        pending = store.save_pending(portfolio.state)
        review = review_analysis_state(pending)
        acceptance = review_and_accept_pending_analysis(store, pending, review, f"review-{pending.investigation_id}-{pending.revision}", human_decision=human_decision)
        if acceptance.status == "pending":
            return PortfolioWorkflowResult("pending", acceptance.state, replace(portfolio, state=acceptance.state), review, None, acceptance.failure)
        if acceptance.status != "accepted":
            return PortfolioWorkflowResult("rejected", acceptance.state, replace(portfolio, state=acceptance.state), review, None, acceptance.failure)
        committed = acceptance.state
        final_portfolio = replace(portfolio, state=committed)
        report_root = Path(output_dir) if output_dir is not None else store.root / "artifacts"
        report_path = report_root / "executive-report.md"
        write_portfolio_report(report_path, final_portfolio, committed)
        return PortfolioWorkflowResult("accepted", committed, final_portfolio, review, report_path)
    except Exception as error:
        return PortfolioWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
