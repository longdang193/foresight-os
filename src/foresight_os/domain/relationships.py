from dataclasses import dataclass
from enum import StrEnum


class RecordKind(StrEnum):
    EVIDENCE = "evidence"
    CLAIM = "claim"
    IMPLICATION = "implication"
    RECOMMENDATION = "recommendation"
    ARTIFACT = "artifact"


class ImpactDirection(StrEnum):
    FORWARD = "forward"
    REVERSE = "reverse"
    NONE = "none"


@dataclass(frozen=True)
class RelationshipRule:
    sources: frozenset[RecordKind]
    targets: frozenset[RecordKind]
    impact: ImpactDirection


ANALYTICAL = frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION})
RELATIONSHIP_RULES: dict[str, RelationshipRule] = {
    "supports": RelationshipRule(frozenset({RecordKind.EVIDENCE}) | ANALYTICAL, ANALYTICAL, ImpactDirection.FORWARD),
    "contradicts": RelationshipRule(frozenset({RecordKind.EVIDENCE}) | ANALYTICAL, ANALYTICAL, ImpactDirection.FORWARD),
    "derived_from": RelationshipRule(ANALYTICAL, frozenset({RecordKind.EVIDENCE}) | ANALYTICAL, ImpactDirection.REVERSE),
    "depends_on": RelationshipRule(
        frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        ImpactDirection.REVERSE,
    ),
    "informs": RelationshipRule(
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION}),
        frozenset({RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        ImpactDirection.FORWARD,
    ),
    "produces": RelationshipRule(
        frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        frozenset({RecordKind.ARTIFACT}),
        ImpactDirection.FORWARD,
    ),
    "supersedes": RelationshipRule(
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        ImpactDirection.NONE,
    ),
}


def relationship_rule(relation_type: str) -> RelationshipRule:
    try:
        return RELATIONSHIP_RULES[relation_type.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown relationship type: {relation_type}") from exc
