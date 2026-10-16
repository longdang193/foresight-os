from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.ev_capacity_investment import EVAnalysis, analyze_ev_capacity_investment
from foresight_os.analysis.evidence_workflow import attach_review_record
from foresight_os.analysis.portfolio_resilience import PortfolioAnalysis, analyze_portfolio_resilience
from foresight_os.analysis.powerbi_strategic_portfolio import PowerBIAnalysis, analyze_powerbi_strategic_portfolio
from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.supplier_resilience import SupplierAnalysis, analyze_supplier_resilience
from foresight_os.analysis.technology_radar import TechnologyAnalysis, analyze_technology_radar
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
from foresight_os.analysis.workbook_inputs import read_workbook
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError


@dataclass(frozen=True)
class ValidatorCheck:
    exercise: str
    check_type: str
    metric: str
    expected: Any
    actual: Any
    passed: bool
    evidence_ids: tuple[str, ...] = ()
    detail: str = ""


@dataclass(frozen=True)
class ValidatorResult:
    source_sha256: str
    checks: tuple[ValidatorCheck, ...]
    failures: tuple[ValidatorCheck, ...]
    analyses: dict[str, Any]
    state: AnalysisState

    @property
    def all_passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class ValidatorWorkflowResult:
    status: str
    analysis: AnalysisState | None
    result: ValidatorResult | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _table(workbook: Any, sheet: str) -> Any:
    for table in workbook.tables:
        if table.sheet == sheet:
            return table
    raise ToolbeltError(f"validator requires sheet: {sheet}")


def _rows(table: Any) -> list[dict[str, Any]]:
    return [dict(zip(table.columns, row, strict=False)) for row in table.rows]


def _row_evidence(table: Any, index: int, digest: str) -> Evidence:
    values = dict(zip(table.columns, table.rows[index], strict=False))
    provenance = table.row_provenance[index]
    row_range = f"{provenance[0].coordinate}:{provenance[-1].coordinate}"
    evidence_id = "validator-evidence-" + hashlib.sha256(f"{digest}:{table.sheet}:{row_range}".encode()).hexdigest()[:16]
    return Evidence(
        evidence_id,
        SourceLocator(digest, table.sheet, row_range, "record", "foresight_validator_recipe", f"{table.sheet} row"),
        digest,
        date.today().isoformat(),
        json.dumps(values, sort_keys=True, default=str),
    )


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _normalise(value: str) -> str:
    return " ".join(value.lower().replace("–", "-").split())


def _check(
    exercise: str,
    check_type: str,
    metric: str,
    expected: Any,
    actual: Any,
    passed: bool,
    evidence_ids: tuple[str, ...],
    detail: str = "",
) -> ValidatorCheck:
    return ValidatorCheck(exercise, check_type, metric, expected, actual, passed, tuple(dict.fromkeys(evidence_ids)), detail)


def _numeric_check(
    exercise: str,
    metric: str,
    expected: float,
    actual: float | None,
    unit: str,
    evidence_ids: tuple[str, ...],
) -> ValidatorCheck:
    tolerance = max(0.01, abs(expected) * 1e-5)
    if unit == "units":
        tolerance = max(tolerance, 1.0)
    passed = actual is not None and math.isclose(actual, expected, abs_tol=tolerance, rel_tol=0.0)
    return _check(exercise, "numeric", metric, expected, actual, passed, evidence_ids, f"tolerance={tolerance:g} {unit}")


def _issue_check(
    issue_id: str,
    exercise: str,
    expected_behavior: str,
    passed: bool,
    actual: Any,
    evidence_id: str,
    detail: str = "",
) -> ValidatorCheck:
    return _check(exercise, "planted_issue", issue_id, expected_behavior, actual, passed, (evidence_id,), detail)


def _reasoning_check(
    exercise: str,
    expected_check: str,
    expected_interpretation: str,
    passed: bool,
    actual: Any,
    evidence_id: str,
    detail: str = "",
) -> ValidatorCheck:
    return _check(exercise, "reasoning", expected_check, expected_interpretation, actual, passed, (evidence_id,), detail)


def _build_validator_state(
    source_sha256: str,
    key_evidence: list[Evidence],
    checks: tuple[ValidatorCheck, ...],
    analyses: dict[str, Any],
) -> AnalysisState:
    evidence_by_id: dict[str, Evidence] = {item.id: item for item in key_evidence}
    for analysis in analyses.values():
        for item in analysis.state.evidence:
            evidence_by_id.setdefault(item.id, item)
    evidence = list(evidence_by_id.values())
    all_ids = [item.id for item in evidence]
    check_ids = [item.evidence_ids[0] for item in checks if item.evidence_ids]
    check_ids = list(dict.fromkeys(check_ids))
    claims: list[AnalyticalRecord] = []
    relationships: list[Relationship] = []
    calculations: list[CalculationRecord] = []
    for exercise, analysis in analyses.items():
        exercise_checks = [item for item in checks if item.exercise == exercise]
        evidence_ids = list(dict.fromkeys(item for check in exercise_checks for item in check.evidence_ids))
        if not evidence_ids:
            evidence_ids = list(analysis.state.evidence[:3])
            evidence_ids = [item.id for item in evidence_ids]
        claim = AnalyticalRecord(
            f"validator-claim-{exercise.lower().replace(' ', '-')}",
            f"{exercise} passed {sum(item.passed for item in exercise_checks)} of {len(exercise_checks)} deterministic validation checks.",
            Basis.DERIVED,
            Assessment.SUPPORTED if all(item.passed for item in exercise_checks) else Assessment.UNCERTAIN,
            evidence_ids=evidence_ids,
            assumptions=("The exercise analyzer is the canonical calculation path for the workbook.",),
            uncertainty=("A failed or incomplete source check limits the corresponding exercise conclusion.",),
            confidence_rationale="Validation compares expected workbook checks with analyzer outputs without rewriting source data.",
            disconfirmation_conditions=("A fresh source refresh changes a validated numerical or reasoning check.",),
            monitoring_indicators=("Re-run the validator after source or recipe changes.",),
        )
        claims.append(claim)
        for evidence_id in claim.evidence_ids:
            relation_id = f"{claim.id}-supports-{evidence_id}"
            relationships.append(Relationship(relation_id, evidence_id, claim.id, "supports"))
        for check in exercise_checks:
            if check.check_type == "numeric" and isinstance(check.actual, (int, float)):
                calculations.append(
                    CalculationRecord(
                        f"validator-{exercise.lower().replace(' ', '-')}-{check.metric.lower().replace(' ', '-').replace('/', '-')}",
                        MeasurementKey(exercise, check.metric, "validator", "value"),
                        "deterministic analyzer output compared with key workbook expected value",
                        list(check.evidence_ids),
                        float(check.actual),
                        "value",
                        [f"validator:{check.metric}"],
                    )
                )
    implication_ids = list(dict.fromkeys(check_ids or all_ids[:10]))
    implication = AnalyticalRecord(
        "validator-priority-implication",
        "The completed exercises support selective, staged decisions: protect validated economics and resilience, preserve optionality under uncertainty, and escalate only when monitoring signposts clear the stated thresholds.",
        Basis.DERIVED,
        Assessment.SUPPORTED if not any(not item.passed for item in checks) else Assessment.UNCERTAIN,
        evidence_ids=implication_ids,
        assumptions=("Source anomalies remain visible and are not silently repaired.", "Observed history is kept distinct from scenario assumptions.",),
        uncertainty=("Validation proves the workbook workflows and planted checks, not future outcomes.",),
        confidence_rationale="The cross-exercise conclusion is grounded in accepted child-workflow calculations and validator checks.",
        disconfirmation_conditions=("A later source refresh reverses the validated check set or weakens the underlying evidence quality.",),
        monitoring_indicators=("Run the validator after workbook, recipe, or semantic-model changes.",),
    )
    claims.append(implication)
    for claim in claims[:-1]:
        relation_id = f"{claim.id}-informs-{implication.id}"
        relationships.append(Relationship(relation_id, claim.id, implication.id, "informs"))
    recommendation = AnalyticalRecord(
        "validator-recommendation",
        "Conditional recommendation: release the three remaining exercise workflows only with their anomaly registers, cited FindingViews, deterministic calculations, and monitoring triggers preserved; revisit any exercise whose validator check fails.",
        Basis.DERIVED,
        Assessment.SUPPORTED if not any(not item.passed for item in checks) else Assessment.UNCERTAIN,
        evidence_ids=list(dict.fromkeys(implication.evidence_ids + all_ids[:5])),
        assumptions=("The validator key is the accepted control set for these exercises.",),
        uncertainty=("The validator does not substitute for human decision ownership.",),
        confidence_rationale="The recommendation is conditional on every check remaining reproducible and accepted.",
        disconfirmation_conditions=("Any material check fails, source provenance changes, or an accepted FindingView becomes stale.",),
        monitoring_indicators=("Check status, source hashes, review validity, and report regeneration on each run.",),
    )
    claims.append(recommendation)
    for evidence_id in recommendation.evidence_ids:
        relation_id = f"{recommendation.id}-supports-{evidence_id}"
        relationships.append(Relationship(relation_id, evidence_id, recommendation.id, "supports"))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation.id}", implication.id, recommendation.id, "informs"))
    revision_items = [item.id for item in [*evidence, *calculations, *claims]]
    return AnalysisState(
        "foresightos-validator",
        1,
        evidence=evidence,
        claims=claims[:-2],
        implications=[implication],
        recommendations=[recommendation],
        relationships=relationships,
        revisions=[Revision("revision-1", 1, "validator run pending acceptance", revision_items)],
        invalidation=Invalidation(),
        revision_status=RevisionStatus.DRAFT,
        calculations=calculations,
    )


def _expected_rows(tables: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    return _rows(tables["Planted_Issues"]), _rows(tables["Expected_Reasoning"]), _rows(tables["Expected_Numerical_Checks"])


def validate_exercises(validator_source: Path, exercise_dir: Path, input_contract: AnalysisInputContract | dict[str, Any] | None = None, *, workbook_context: Any | None = None) -> ValidatorResult:
    validator_source = Path(validator_source)
    exercise_dir = Path(exercise_dir)
    workbook = read_workbook(
        validator_source,
        SheetSelection(sheet_names=("Overview", "Planted_Issues", "Expected_Reasoning", "Expected_Numerical_Checks"), include_hidden=True, include_hidden_rows=True),
        workbook_context=workbook_context,
    )
    source_sha256 = workbook.workbook_sha256
    tables = {table.sheet: table for table in workbook.tables}
    key_evidence = [
        _row_evidence(table, index, source_sha256)
        for table in tables.values()
        for index in range(len(table.rows))
        if table.sheet != "Overview"
    ]
    evidence_by_row: dict[tuple[str, int], Evidence] = {}
    for table in tables.values():
        for index in range(len(table.rows)):
            evidence_by_row[(table.sheet, index)] = _row_evidence(table, index, source_sha256)
    planted_rows, reasoning_rows, numerical_rows = _expected_rows(tables)
    file_map = {
        "Portfolio": ("01_Portfolio_Resilience.xlsx", analyze_portfolio_resilience),
        "Supplier": ("02_Supplier_Resilience.xlsx", analyze_supplier_resilience),
        "EV": ("03_EV_Capacity_Investment.xlsx", analyze_ev_capacity_investment),
        "Technology": ("04_Technology_Radar.xlsx", analyze_technology_radar),
        "Power BI": ("05_PowerBI_Strategic_Portfolio.xlsx", analyze_powerbi_strategic_portfolio),
    }
    def contract_for(exercise: str) -> AnalysisInputContract | dict[str, Any] | None:
        if input_contract is None:
            return None
        aliases = {
            "Portfolio": "portfolio_resilience",
            "Supplier": "supplier_resilience",
            "EV": "ev_capacity_investment",
            "Technology": "technology_radar",
            "Power BI": "powerbi_strategic_portfolio",
        }
        if isinstance(input_contract, dict) and aliases.get(exercise) in input_contract:
            return input_contract[aliases[exercise]]
        if isinstance(input_contract, dict) and exercise in input_contract:
            return input_contract[exercise]
        if isinstance(input_contract, dict) and input_contract.get("domain"):
            return input_contract
        if isinstance(input_contract, dict):
            return None
        return input_contract

    analyses: dict[str, Any] = {
        exercise: analyzer(exercise_dir / filename, input_contract=contract_for(exercise), workbook_context=workbook_context)
        for exercise, (filename, analyzer) in file_map.items()
    }
    checks: list[ValidatorCheck] = []
    portfolio: PortfolioAnalysis = analyses["Portfolio"]
    ev: EVAnalysis = analyses["EV"]
    powerbi: PowerBIAnalysis = analyses["Power BI"]
    issue_kinds = {
        "P-01": ("Portfolio", {"DUPLICATE_ROW"}),
        "P-02": ("Portfolio", {"MISSING_COST"}),
        "P-03": ("Portfolio", {"MALFORMED_DISCOUNT"}),
        "P-04": ("Portfolio", {"KPI_MISMATCH"}),
        "S-01": ("Supplier", {"DUPLICATE_LINE"}),
        "S-02": ("Supplier", {"MISSING_ALTERNATIVES"}),
        "S-03": ("Supplier", set()),
        "S-04": ("Supplier", {"LOW_COST_HIGH_RISK"}),
        "E-01": ("EV", {"MISSING_EXPANSION_COST"}),
        "E-02": ("EV", {"KPI_MISMATCH"}),
        "E-03": ("EV", {"POLICY_CONFLICT"}),
        "T-01": ("Technology", {"DUPLICATE_SOURCE_FAMILY"}),
        "T-02": ("Technology", {"NAIVE_SCORE_RISK"}),
        "PB-01": ("Power BI", {"DUPLICATE_FACT"}),
        "PB-02": ("Power BI", {"MISSING_TARGET"}),
        "PB-03": ("Power BI", {"STALE_REFRESH"}),
        "PB-04": ("Power BI", {"FILTER_CONTEXT_TRAP"}),
        "PB-05": ("Power BI", {"CONTRADICTORY_FORWARD_SIGNAL"}),
    }
    for index, row in enumerate(planted_rows):
        issue_id = str(row["Issue_ID"])
        exercise, required_kinds = issue_kinds[issue_id]
        analysis = analyses[exercise]
        observed_kinds = {item.kind for item in analysis.data_quality_issues}
        if issue_id == "P-04":
            passed = any(item.status == "MISMATCH" for item in analysis.kpi_reconciliations)
            actual = [(item.kpi, item.status) for item in analysis.kpi_reconciliations]
            detail = "Reported KPIs are compared with quality-adjusted source calculations."
        elif issue_id == "S-03":
            passed = any("USD=0.92" in item and "CNY=0.13" in item for item in analysis.assumptions)
            actual = "explicit deterministic FX normalization assumption"
            detail = "Mixed-currency aggregation is allowed only because the recipe declares the FX normalization and reporting currency."
        else:
            passed = required_kinds.issubset(observed_kinds)
            actual = sorted(observed_kinds)
            detail = "Required planted issue kind is present in the analyzer output."
        checks.append(_issue_check(issue_id, exercise, str(row["Expected_Behavior"]), passed, actual, evidence_by_row[("Planted_Issues", index)].id, detail))
    for index, row in enumerate(numerical_rows):
        exercise = str(row["Exercise"])
        metric = str(row["Metric"])
        expected = float(row["Expected_Value"])
        actual: float | None = None
        if exercise == "Portfolio" and metric.startswith("2026 revenue"):
            actual = sum(item.revenue for item in portfolio.segment_baselines)
        elif exercise == "Portfolio" and metric.startswith("2026 gross profit"):
            actual = sum(item.gross_profit for item in portfolio.segment_baselines)
        elif exercise == "EV" and "demand" in metric.lower():
            scenario = metric.split()[1]
            actual = next((item.demand_units for item in ev.scenarios if item.scenario == scenario), None)
        elif exercise == "EV" and "practical existing capacity" in metric.lower():
            actual = next((item.practical_capacity for item in ev.scenarios), None)
        elif exercise == "Power BI" and metric.startswith("2025"):
            actual = powerbi.revenue_2025_jan_sep
        elif exercise == "Power BI" and metric.startswith("2026 Jan-Sep revenue"):
            actual = powerbi.revenue_2026_jan_sep
        elif exercise == "Power BI" and "YoY" in metric:
            actual = powerbi.yoy_revenue_growth
        checks.append(_numeric_check(exercise, metric, expected, actual, str(row["Unit"]), (evidence_by_row[("Expected_Numerical_Checks", index)].id,)))
    for index, row in enumerate(reasoning_rows):
        exercise = str(row["Exercise"])
        expected_check = str(row["Expected_Check"])
        expected_interpretation = str(row["Expected_Interpretation"])
        actual: Any = ""
        passed = False
        analysis = analyses[exercise]
        normalized = _normalise(expected_check)
        if exercise == "Portfolio" and normalized.startswith("deduplicate"):
            passed = "DUPLICATE_ROW" in {item.kind for item in portfolio.data_quality_issues} and any(item.status == "MISMATCH" for item in portfolio.kpi_reconciliations)
            actual = "duplicate excluded and KPI reconciliation retained"
        elif exercise == "Portfolio":
            passed = "staged" in portfolio.recommendation.lower() and "defer" in portfolio.recommendation.lower()
            actual = portfolio.recommendation
        elif exercise == "Supplier" and normalized.startswith("assess spend"):
            passed = bool(analysis.concentration_metrics) and any(item.criticality_weighted > 0 and item.alternatives_weighted >= 0 for item in analysis.concentration_metrics)
            actual = "concentration, criticality, and alternatives are separate metric fields"
        elif exercise == "Supplier":
            passed = any(item.top_country_share > item.top_supplier_share for item in analysis.concentration_metrics) and "LOW_COST_HIGH_RISK" in {item.kind for item in analysis.data_quality_issues}
            actual = "country concentration is compared with supplier concentration and criticality"
        elif exercise == "EV" and normalized.startswith("separate observed"):
            passed = any(item.basis.lower() == "observed" for item in ev.demand_history) and any(item.basis.lower() == "projected" for item in ev.scenarios)
            actual = "observed demand history and projected scenarios retain separate basis fields"
        elif exercise == "EV":
            passed = "MISSING_EXPANSION_COST" in {item.kind for item in ev.data_quality_issues} and "policy" in " ".join(ev.monitoring_triggers).lower()
            actual = "missing South cost remains provisional and policy/infrastructure triggers are monitored"
        elif exercise == "Technology" and normalized.startswith("collapse syndicated"):
            ai = next(item for item in analysis.assessments if item.technology == "AI Engineering Copilots")
            passed = ai.independent_source_families < ai.signal_count
            actual = f"AI copilots: {ai.signal_count} signals, {ai.independent_source_families} independent source families"
        elif exercise == "Technology":
            actions = {item.technology: item.action_category for item in analysis.assessments}
            passed = actions.get("SiC Power Electronics") == "Invest" and actions.get("Zonal Architecture") == "Experiment" and actions.get("Solid-State Batteries") == "Monitor"
            actual = actions
        elif exercise == "Power BI" and normalized.startswith("reconcile"):
            required = {"DUPLICATE_FACT", "MISSING_TARGET", "STALE_REFRESH", "FILTER_CONTEXT_TRAP"}
            passed = required.issubset({item.kind for item in powerbi.data_quality_issues})
            actual = sorted(item.kind for item in powerbi.data_quality_issues)
        elif exercise == "Power BI" and normalized.startswith("contrast"):
            passed = "CONTRADICTORY_FORWARD_SIGNAL" in {item.kind for item in powerbi.data_quality_issues} and powerbi.yoy_revenue_growth > 0
            actual = f"booked YoY={powerbi.yoy_revenue_growth:.6f}; contradiction retained"
        elif exercise == "Power BI":
            passed = "stage" in powerbi.recommendation.lower() and "conditional" in powerbi.recommendation.lower()
            actual = powerbi.recommendation
        checks.append(_reasoning_check(exercise, expected_check, expected_interpretation, passed, actual, evidence_by_row[("Expected_Reasoning", index)].id))
    checks_tuple = tuple(checks)
    failures = tuple(item for item in checks_tuple if not item.passed)
    state = _build_validator_state(source_sha256, key_evidence, checks_tuple, analyses)
    return ValidatorResult(source_sha256, checks_tuple, failures, analyses, state)


def _citations(state: AnalysisState, ids: tuple[str, ...] | list[str]) -> str:
    by_id = {item.id: item for item in state.evidence}
    citations = [f"`{by_id[item].source_locator.sheet}!{by_id[item].source_locator.range}`" for item in dict.fromkeys(ids) if item in by_id]
    return ", ".join(citations) or "`unavailable`"


def render_validator_report(result: ValidatorResult, state: AnalysisState | None = None) -> str:
    state = state or result.state
    if state.revision_status != RevisionStatus.ACCEPTED or any(not item.accepted for item in derive_finding_views(state)):
        raise ValueError("validator report requires current accepted findings")
    lines = [
        "# ForesightOS Exercise Validation Report",
        "",
        f"Validator key SHA-256: `{result.source_sha256}`",
        "",
        "## Validation summary",
        f"- Checks passed: {len(result.checks) - len(result.failures)}/{len(result.checks)}",
        f"- Status: {'PASS' if result.all_passed else 'FAIL'}",
        "- Source workbooks remain unchanged; planted anomalies are surfaced rather than silently repaired.",
        "",
        "## Numerical checks",
        "| Exercise | Metric | Expected | Actual | Status | Evidence |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in result.checks:
        if item.check_type == "numeric":
            lines.append(f"| {item.exercise} | {item.metric} | {item.expected} | {item.actual} | {'PASS' if item.passed else 'FAIL'} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Planted-issue coverage", "| Exercise | Issue | Status | Observed behavior | Evidence |", "|---|---|---|---|---|"])
    for item in result.checks:
        if item.check_type == "planted_issue":
            lines.append(f"| {item.exercise} | {item.metric} | {'PASS' if item.passed else 'FAIL'} | {item.actual} | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Reasoning checks", "| Exercise | Check | Status | Result | Evidence |", "|---|---|---|---|---|"])
    for item in result.checks:
        if item.check_type == "reasoning":
            lines.append(f"| {item.exercise} | {item.metric} | {'PASS' if item.passed else 'FAIL'} | {item.actual} | {_citations(state, item.evidence_ids)} |")
    lines.extend([
        "",
        "## Cross-exercise insights",
        "- Portfolio economics support staged Analytics Software and Service Contracts emphasis, while unresolved source rows constrain irreversible Core Hardware commitments.",
        "- Supplier resilience is driven by criticality, substitutability, geography, and currency normalization together; nominal unit cost is not a sufficient risk screen.",
        "- EV capacity has a persistent modeled gap, but high demand alone does not justify irreversible expansion while policy, infrastructure, and option-cost evidence remain conditional.",
        "- Technology signals are strongest for SiC and zonal architecture; syndicated AI-copilot coverage supports experimentation, not proof of deployment.",
        "- Power BI booked growth is positive after deduplication, but forward signals and semantic-model validity support selective or stage-gated allocation rather than broad acceleration.",
        "",
        "## Recommended action",
        "- Conditional release: keep each workflow’s anomaly register, source citations, deterministic calculations, accepted FindingViews, and monitoring triggers in the delivery package.",
        "",
        "## FindingView status",
    ])
    lines.extend(f"- `{item.target_id}`: {item.review_status}/{item.review_outcome}; accepted={item.accepted}; evidence={_citations(state, item.evidence_ids)}" for item in derive_finding_views(state))
    return "\n".join(lines) + "\n"


def run_validator_workflow(
    store: AnalysisStore,
    validator_source: Path,
    exercise_dir: Path,
    *,
    human_decision: str = "REJECT",
    output_dir: Path | None = None,
    input_contract: AnalysisInputContract | dict[str, Any] | None = None,
) -> ValidatorWorkflowResult:
    try:
        if input_contract is None and store.brief_path.exists():
            input_contract = {
                contract.domain: contract.to_dict()
                for contract in normalize_work_brief(store.load_brief()).contracts
            }
        result = validate_exercises(Path(validator_source), Path(exercise_dir), input_contract=input_contract)
        pending = store.save_pending(result.state)
        review = review_analysis_state(pending)
        decision = human_decision.upper()
        if decision in {"PENDING", "PENDING_REVIEW"}:
            return ValidatorWorkflowResult("pending", pending, replace(result, state=pending), review, None)
        if decision != "ACCEPT" or not result.all_passed or not review.accepted:
            rejected = store.commit_revision(pending, expected_revision=pending.revision, accepted=False)
            reason = "explicit acceptance was not granted" if decision != "ACCEPT" else "validator checks or review failed"
            return ValidatorWorkflowResult("rejected", rejected, replace(result, state=rejected), review, None, reason)
        reviewed = attach_review_record(pending, review, f"review-{pending.investigation_id}-{pending.revision}")
        committed = store.commit_revision(reviewed, expected_revision=reviewed.revision, accepted=True)
        final = replace(result, state=committed)
        report_path = (Path(output_dir) if output_dir is not None else store.root / "artifacts") / "executive-report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_validator_report(final, committed), encoding="utf-8")
        return ValidatorWorkflowResult("accepted", committed, final, review, report_path)
    except Exception as error:
        return ValidatorWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
