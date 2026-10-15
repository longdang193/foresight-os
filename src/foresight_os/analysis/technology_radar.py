from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.review_workflow import review_and_accept_pending_analysis
from foresight_os.analysis.workbook_inputs import require_table, row_evidence, table_rows
from foresight_os.domain.analysis_inputs import AnalysisInputContract, normalize_work_brief
from foresight_os.domain.challenge import derive_finding_views
from foresight_os.domain.models import AnalyticalRecord, AnalysisState, Assessment, Basis, CalculationRecord, Evidence, Invalidation, MeasurementKey, Relationship, Revision, RevisionStatus, SourceLocator
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import SheetSelection, ToolbeltError, spreadsheet_read


@dataclass(frozen=True)
class TechnologyDataQualityIssue:
    kind: str
    message: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class TechnologyAssessment:
    technology: str
    signal_count: int
    independent_source_families: int
    evidence_strength: float
    media_volume: int
    deployment_evidence_count: int
    company_relevance: float
    potential_impact: float
    urgency: float
    naive_product: float
    action_category: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class TechnologyScenario:
    technology: str
    scenario: str
    implication: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class TechnologyAnalysis:
    source_sha256: str
    decision_question: str
    horizon: str
    assumptions: tuple[str, ...]
    data_quality_issues: tuple[TechnologyDataQualityIssue, ...]
    assessments: tuple[TechnologyAssessment, ...]
    scenarios: tuple[TechnologyScenario, ...]
    signposts: tuple[dict[str, Any], ...]
    recommendation: str
    state: AnalysisState
    contract_fingerprint: str = ""

@dataclass(frozen=True)
class TechnologyWorkflowResult:
    status: str
    analysis: AnalysisState | None
    technology: TechnologyAnalysis | None
    review: ReviewResult | None
    report_path: Path | None
    failure: str | None = None


def _table(workbook: Any, sheet: str) -> Any:
    return require_table(workbook, sheet)

def _rows(table: Any) -> list[dict[str, Any]]:
    return table_rows(table)

def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

def _row_evidence(table: Any, index: int, digest: str) -> Evidence:
    return row_evidence(table, index, digest, f"{table.sheet} row", units="index", transformation="technology_radar_recipe", evidence_prefix="technology")

def _record(record_id: str, statement: str, evidence_ids: list[str], assumptions: tuple[str, ...], uncertainty: tuple[str, ...], disconfirmation: tuple[str, ...], monitoring: tuple[str, ...]) -> AnalyticalRecord:
    return AnalyticalRecord(record_id, statement, Basis.DERIVED, Assessment.SUPPORTED, evidence_ids=list(dict.fromkeys(evidence_ids)), assumptions=assumptions, uncertainty=uncertainty, confidence_rationale="Derived from source-family adjusted signals and explicit relevance/impact scoring.", disconfirmation_conditions=disconfirmation, monitoring_indicators=monitoring)

def _canonical_source(source: str, notes: str) -> str:
    value = source.strip()
    if "same vendor" in value.lower() or "syndicated" in notes.lower() or "identical underlying" in notes.lower():
        return "Vendor press release"
    return value

def _action(evidence_strength: float, deployment: int, relevance: float, impact: float, urgency: float) -> str:
    if evidence_strength >= 4.0 and deployment >= 3 and relevance >= 4.0 and impact >= 4.0:
        return "Invest"
    if (impact >= 4.0 and deployment >= 1 and relevance >= 3.0 and urgency >= 3.0) or (urgency >= 4.0 and relevance >= 4.0):
        return "Experiment"
    return "Monitor"

def analyze_technology_radar(source: Path, input_contract: AnalysisInputContract | dict[str, Any] | None = None) -> TechnologyAnalysis:
    source = Path(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    workbook = spreadsheet_read(source, SheetSelection(sheet_names=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"), include_hidden=True, include_hidden_rows=True))
    brief, signal_table, relevance_table, competitor_table, signpost_table, priority_table = [_table(workbook, item) for item in ("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring")]
    contract = AnalysisInputContract.from_dict(input_contract) if input_contract is not None else AnalysisInputContract(
        domain="technology_radar",
        required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
        units="index",
        compatibility_assumption="legacy technology radar scope",
    )
    contract.validate()
    selected_technologies = set(contract.entity_scope)
    signals, relevances, competitors, signposts, priorities = [_rows(table) for table in (signal_table, relevance_table, competitor_table, signpost_table, priority_table)]
    evidence: list[Evidence] = []
    by_row: dict[tuple[str, int], Evidence] = {}
    for table in (signal_table, relevance_table, competitor_table, signpost_table, priority_table):
        for index in range(len(table.rows)):
            by_row[(table.sheet, index)] = _row_evidence(table, index, digest)
            evidence.append(by_row[(table.sheet, index)])
    by_technology: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, row in enumerate(signals):
        if selected_technologies and str(row.get("Technology")) not in selected_technologies:
            continue
        by_technology.setdefault(str(row.get("Technology")), []).append((index, row))
    relevance_by_technology = {str(row.get("Technology")): row for row in relevances}
    priority_by_technology = {str(row.get("Technology")): row for row in priorities}
    issues: list[TechnologyDataQualityIssue] = []
    assessments: list[TechnologyAssessment] = []
    for technology, items in sorted(by_technology.items()):
        canonical = [_canonical_source(str(row.get("Source_Family", "")), str(row.get("Notes", ""))) for _, row in items]
        independent = set(canonical)
        quality = sum(_number(row.get("Source_Quality_1_5")) or 0.0 for _, row in items) / len(items) if items else 0.0
        media_volume = sum(1 for _, row in items if str(row.get("Metric")) == "media_mentions")
        deployment = sum(1 for _, row in items if str(row.get("Metric")) in {"capacity", "design_win", "supplier_contract", "platform_launch", "pilot_line", "commercial_route"})
        if len(canonical) != len(independent):
            duplicated = sorted(source for source in set(canonical) if canonical.count(source) > 1)
            related = tuple(by_row[(signal_table.sheet, index)].id for index, _ in items)
            issues.append(TechnologyDataQualityIssue("DUPLICATE_SOURCE_FAMILY", f"{technology} contains repeated or syndicated evidence from {', '.join(duplicated)}; count it once for corroboration.", related))
        if media_volume >= 2 and deployment == 0:
            issues.append(TechnologyDataQualityIssue("MEDIA_VOLUME_WITHOUT_DEPLOYMENT", f"{technology} has media volume without a deployment metric in the signal rows.", tuple(by_row[(signal_table.sheet, index)].id for index, _ in items)))
        assessment_row = relevance_by_technology.get(technology, {})
        priority_row = priority_by_technology.get(technology, {})
        naive = _number(priority_row.get("Naive_Product")) or 0.0
        if priority_row.get("Caution"):
            issues.append(TechnologyDataQualityIssue("NAIVE_SCORE_RISK", f"{technology} has a multiplicative priority score that must not be treated as an investment decision without reversibility and uncertainty review.", (by_row[(priority_table.sheet, next((i for i, row in enumerate(priorities) if str(row.get("Technology")) == technology), 0))].id,)))
        relevance = _number(assessment_row.get("Company_Relevance_1_5")) or 0.0
        impact = _number(assessment_row.get("Potential_Impact_1_5")) or 0.0
        urgency = _number(assessment_row.get("Urgency_1_5")) or 0.0
        assessments.append(TechnologyAssessment(technology, len(items), len(independent), quality, media_volume, deployment, relevance, impact, urgency, naive, _action(quality, deployment, relevance, impact, urgency), tuple(by_row[(signal_table.sheet, index)].id for index, _ in items)))
    assumptions = ("Source families are canonicalized before counting corroboration; syndicated vendor stories are not independent sources.", "Evidence strength is separated from media volume and company relevance.", "Action categories preserve reversibility: strong evidence can justify investment, while transformative but uncertain technologies remain monitor/experiment candidates.", "Competitor actions are corroborating context, not proof of commercial success.")
    relationships: list[Relationship] = []
    claims: list[AnalyticalRecord] = []
    for item in assessments:
        claim = _record(f"technology-signal-{item.technology.lower().replace(' ', '-')}", f"{item.technology} has {item.signal_count} signals, {item.independent_source_families} independent source families, evidence strength {item.evidence_strength:.1f}/5, and is categorized as {item.action_category}.", list(item.evidence_ids), assumptions, ("Source-family dependence can overstate corroboration when media volume rises without deployment evidence.",), (f"Independent evidence and deployment signposts change the {item.technology} action category.",), (f"Independent source count, deployment evidence, and signpost progress for {item.technology}.",))
        claims.append(claim)
        relationships.extend(Relationship(f"{claim.id}-supports-{evidence_id}", evidence_id, claim.id, "supports") for evidence_id in claim.evidence_ids)
    scenarios: list[TechnologyScenario] = []
    for item in assessments:
        scenarios.extend((TechnologyScenario(item.technology, "Acceleration", "Increase exposure if independent deployment signposts are exceeded.", item.evidence_ids), TechnologyScenario(item.technology, "Base", f"Maintain the {item.action_category.lower()} posture while evidence accumulates.", item.evidence_ids), TechnologyScenario(item.technology, "Delay", "Preserve optionality and avoid irreversible commitment if signposts remain weak.", item.evidence_ids)))
    quality_ids = [evidence_id for issue in issues for evidence_id in issue.evidence_ids]
    quality = _record("technology-data-quality", f"The technology radar contains {len(issues)} source-independence or scoring caveats that must be retained in the recommendation.", quality_ids or [item.id for item in evidence], assumptions, ("Removing syndicated stories or changing source quality can change evidence rankings.",), ("Independent deployment evidence resolves the source-family and scoring caveats.",), ("Source-family count, media-to-deployment ratio, and signpost status.",))
    claims.append(quality)
    relationships.extend(Relationship(f"{quality.id}-supports-{evidence_id}", evidence_id, quality.id, "supports") for evidence_id in quality.evidence_ids)
    action_by_technology = {item.technology: item.action_category for item in assessments}
    implication = _record("technology-priority-implication", "; ".join(f"{technology}: {action.lower()}" for technology, action in sorted(action_by_technology.items())) + ".", [item.id for item in evidence], assumptions, ("Priority scores are not causal return forecasts and do not capture execution capacity.",), ("Independent deployment evidence reverses the relative ranking or materially changes reversibility.",), ("Technology-specific signposts, competitor actions, and deployment evidence.",))
    relationships.extend(Relationship(f"{claim.id}-informs-{implication.id}", claim.id, implication.id, "informs") for claim in claims)
    recommendation_text = "Use a conditional radar posture: " + ", ".join(f"{technology} = {action.lower()}" for technology, action in sorted(action_by_technology.items())) + " until independent deployment signposts exceed the workbook thresholds."
    recommendation = _record("technology-recommendation", recommendation_text, [item.id for item in evidence], assumptions, ("The workbook does not quantify investment returns or implementation cost.",), ("Signposts fail for two review windows or independent deployment evidence changes the action category.",), ("Independent design wins, SOP platforms, measured productivity, qualified battery pilots, and regulator-approved routes.",))
    relationships.append(Relationship(f"{implication.id}-informs-{recommendation.id}", implication.id, recommendation.id, "informs"))
    recommendation = replace(recommendation, relationship_ids=[item.id for item in relationships if item.to_id == recommendation.id])
    calculations = [CalculationRecord(f"technology-{item.technology.lower().replace(' ', '-')}-evidence", MeasurementKey(item.technology, "independent_source_families", "current", "families"), "count(distinct canonical_source_family)", list(item.evidence_ids), float(item.independent_source_families), "families", [f"Signals:{item}" for item in item.evidence_ids]) for item in assessments]
    state = AnalysisState("technology-radar", 1, evidence=evidence, claims=claims, implications=[implication], recommendations=[recommendation], relationships=relationships, revisions=[Revision("revision-1", 1, "technology radar analysis pending acceptance", [item.id for item in [*evidence, *calculations, *claims, implication, recommendation]])], invalidation=Invalidation(), revision_status=RevisionStatus.DRAFT, calculations=calculations)
    decision_question = next((str(row[1]) for row in brief.rows if row and row[0] == "Decision question" and len(row) > 1), "Which emerging technologies should the company prioritize?")
    horizon = next((str(row[1]) for row in brief.rows if row and row[0] == "Horizon" and len(row) > 1), "24–36 months")
    return TechnologyAnalysis(digest, decision_question, horizon, assumptions, tuple(issues), tuple(assessments), tuple(scenarios), tuple(signposts), recommendation.statement, state, contract.fingerprint)

def _citations(state: AnalysisState, ids: tuple[str, ...] | list[str]) -> str:
    by_id = {item.id: item for item in state.evidence}
    return ", ".join(f"`{by_id[item].source_locator.sheet}!{by_id[item].source_locator.range}`" for item in dict.fromkeys(ids) if item in by_id) or "`unavailable`"

def render_technology_report(technology: TechnologyAnalysis, state: AnalysisState | None = None) -> str:
    state = state or technology.state
    if state.revision_status != RevisionStatus.ACCEPTED or any(not item.accepted for item in derive_finding_views(state)):
        raise ValueError("technology report requires current accepted findings")
    lines = ["# Technology Radar Executive Report", "", f"Decision question: {technology.decision_question}", f"Horizon: {technology.horizon}", f"Source workbook SHA-256: `{technology.source_sha256}`", "", "## What is changing?", "- The radar separates independent source evidence from media volume and strategic relevance.", "", "## Signal quality", "| Technology | Signals | Independent source families | Evidence strength | Media volume | Deployment evidence | Relevance | Impact | Urgency | Evidence |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for item in technology.assessments:
        lines.append(f"| {item.technology} | {item.signal_count} | {item.independent_source_families} | {item.evidence_strength:.1f}/5 | {item.media_volume} | {item.deployment_evidence_count} | {item.company_relevance:.1f}/5 | {item.potential_impact:.1f}/5 | {item.urgency:.1f}/5 | {_citations(state, item.evidence_ids)} |")
    lines.extend(["", "## Competing hypotheses", "- Positive hypothesis: independent deployments and customer/competitor actions indicate a durable adoption curve.", "- Counterhypothesis: media volume, patents, and syndicated announcements are ahead of repeatable commercial deployment.", "", "## Alternative futures", "| Technology | Scenario | Implication | Evidence |", "|---|---|---|---|"])
    lines.extend(f"| {item.technology} | {item.scenario} | {item.implication} | {_citations(state, item.evidence_ids)} |" for item in technology.scenarios)
    lines.extend(["", "## Action category", "| Technology | Action | Evidence |", "|---|---|---|"])
    lines.extend(f"| {item.technology} | {item.action_category} | {_citations(state, item.evidence_ids)} |" for item in technology.assessments)
    lines.extend(["", "## Counterevidence"])
    lines.extend(f"- `{issue.kind}`: {issue.message} (source: {_citations(state, issue.evidence_ids)})" for issue in technology.data_quality_issues)
    lines.extend(["", "## Assumptions and uncertainty"])
    lines.extend(f"- {item}" for item in technology.assumptions)
    lines.extend(["", "## Recommended action", f"- {technology.recommendation}", "", "## Signposts", "| Technology | Signpost | Threshold | Review window | Decision rule |", "|---|---|---:|---|---|"])
    lines.extend(f"| {row.get('Technology')} | {row.get('Signpost')} | {row.get('Threshold')} | {row.get('Review_Window')} | {row.get('Decision_Rule')} |" for row in technology.signposts)
    lines.extend(["", "## What changes our mind?", "- Change the posture only when independent source families and deployment signposts, not media volume alone, cross the relevant threshold.", "", "## FindingView status"])
    lines.extend(f"- `{item.target_id}`: {item.review_status}/{item.review_outcome}; accepted={item.accepted}; evidence={_citations(state, item.evidence_ids)}" for item in derive_finding_views(state))
    return "\n".join(lines) + "\n"

def run_technology_radar_workflow(store: AnalysisStore, source: Path, *, human_decision: str = "REJECT", output_dir: Path | None = None, input_contract: AnalysisInputContract | dict[str, Any] | None = None) -> TechnologyWorkflowResult:
    try:
        if input_contract is None and store.brief_path.exists():
            input_contract = normalize_work_brief(store.load_brief()).contract_for_domain("technology_radar")
        technology = analyze_technology_radar(Path(source), input_contract=input_contract)
        pending = store.save_pending(technology.state)
        review = review_analysis_state(pending)
        acceptance = review_and_accept_pending_analysis(store, pending, review, f"review-{pending.investigation_id}-{pending.revision}", human_decision=human_decision)
        if acceptance.status == "pending":
            return TechnologyWorkflowResult("pending", acceptance.state, replace(technology, state=acceptance.state), review, None, acceptance.failure)
        if acceptance.status != "accepted":
            return TechnologyWorkflowResult("rejected", acceptance.state, replace(technology, state=acceptance.state), review, None, acceptance.failure)
        committed = acceptance.state
        final = replace(technology, state=committed)
        report_path = (Path(output_dir) if output_dir is not None else store.root / "artifacts") / "executive-report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_technology_report(final, committed), encoding="utf-8")
        return TechnologyWorkflowResult("accepted", committed, final, review, report_path)
    except Exception as error:
        return TechnologyWorkflowResult("failed", None, None, None, None, f"{type(error).__name__}: {error}")
