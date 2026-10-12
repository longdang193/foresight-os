import re
from dataclasses import dataclass

from foresight_os.domain.models import (
    AnalyticalRecord,
    Assessment,
    Basis,
    CalculationRecord,
    Evidence,
    Relationship,
)
from foresight_os.analysis.workbook import calculate_case_metrics


@dataclass(frozen=True)
class DraftAnalysis:
    evidence: list[Evidence]
    claims: list[AnalyticalRecord]
    implications: list[AnalyticalRecord]
    recommendations: list[AnalyticalRecord]
    relationships: list[Relationship]
    calculations: list[CalculationRecord]


def draft_analysis(evidence: list[Evidence]) -> DraftAnalysis:
    by_excerpt = {item.excerpt: item for item in evidence}
    by_key = {item.measurement_key: item for item in evidence if item.measurement_key is not None}
    demand_2030 = next(item for key, item in by_key.items() if key.region == "Northern Europe" and key.measure == "demand_index" and key.period == "2030")
    capacity_2030 = next(item for key, item in by_key.items() if key.region == "Northern Europe" and key.measure == "capacity_index" and key.period == "2030")
    demand_2024 = next(item for key, item in by_key.items() if key.region == "Northern Europe" and key.measure == "demand_index" and key.period == "2024")

    calculations = calculate_case_metrics(evidence)
    demand_growth = calculations["northern-demand-growth"]
    capacity_gap = calculations["northern-capacity-gap"]
    measurement_values = {
        item.measurement_key: float(re.search(r"=([-+]?[0-9]+(?:\.[0-9]+)?)", item.excerpt).group(1))
        for item in evidence
        if item.measurement_key is not None
    }
    demand_start_value = f"{measurement_values[demand_2024.measurement_key]:g}"
    demand_end_value = f"{measurement_values[demand_2030.measurement_key]:g}"
    capacity_end_value = f"{measurement_values[capacity_2030.measurement_key]:g}"

    growth_claim = AnalyticalRecord(
        "claim-northern-demand-growth",
        f"Northern Europe demand is forecast to rise from index {demand_start_value} in 2024 to {demand_end_value} in 2030.",
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=[demand_2024.id, demand_2030.id],
    )
    capacity_claim = AnalyticalRecord(
        "claim-northern-capacity-gap",
        f"Northern Europe capacity is forecast to reach index {capacity_end_value} in 2030, below forecast demand of {demand_end_value}.",
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=[demand_2030.id, capacity_2030.id],
    )
    growth_support = Relationship("relationship-demand-growth", demand_2030.id, growth_claim.id, "supports")
    capacity_support = Relationship("relationship-capacity-gap", capacity_2030.id, capacity_claim.id, "supports")
    growth_claim = AnalyticalRecord(
        growth_claim.id,
        growth_claim.statement,
        growth_claim.basis,
        growth_claim.assessment,
        evidence_ids=growth_claim.evidence_ids,
        relationship_ids=[growth_support.id],
    )
    capacity_claim = AnalyticalRecord(
        capacity_claim.id,
        capacity_claim.statement,
        capacity_claim.basis,
        capacity_claim.assessment,
        evidence_ids=capacity_claim.evidence_ids,
        relationship_ids=[capacity_support.id],
    )
    implication = AnalyticalRecord(
        "implication-capacity-constrained-growth",
        "Growth creates a capacity constraint that must be resolved before scaling service commitments.",
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=[demand_2030.id, capacity_2030.id],
    )
    implication_link = Relationship("relationship-claim-implication", capacity_claim.id, implication.id, "informs")
    implication = AnalyticalRecord(
        implication.id,
        implication.statement,
        implication.basis,
        implication.assessment,
        evidence_ids=implication.evidence_ids,
        relationship_ids=[implication_link.id],
    )
    recommendation = AnalyticalRecord(
        "recommendation-northern-attention",
        "Increase strategic attention on Northern Europe, conditional on validating expansion cost.",
        Basis.DERIVED,
        Assessment.SUPPORTED,
        evidence_ids=[demand_2030.id, capacity_2030.id],
    )
    recommendation_link = Relationship("relationship-implication-recommendation", implication.id, recommendation.id, "supports")
    recommendation = AnalyticalRecord(
        recommendation.id,
        recommendation.statement,
        recommendation.basis,
        recommendation.assessment,
        evidence_ids=recommendation.evidence_ids,
        relationship_ids=[recommendation_link.id],
    )
    return DraftAnalysis(
        evidence=list(by_excerpt.values()),
        claims=[growth_claim, capacity_claim],
        implications=[implication],
        recommendations=[recommendation],
        relationships=[growth_support, capacity_support, implication_link, recommendation_link],
        calculations=list(calculations.values()),
    )
