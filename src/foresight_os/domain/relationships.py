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
    semantic_direction: str = "forward"
    provenance_direction: str = "forward"
    evidence_role: str = "context"


ANALYTICAL = frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION})
RELATIONSHIP_RULES: dict[str, RelationshipRule] = {
    "supports": RelationshipRule(
        frozenset({RecordKind.EVIDENCE}) | ANALYTICAL,
        ANALYTICAL,
        ImpactDirection.FORWARD,
        semantic_direction="source supports target",
        provenance_direction="forward",
        evidence_role="support",
    ),
    "contradicts": RelationshipRule(
        frozenset({RecordKind.EVIDENCE}) | ANALYTICAL,
        ANALYTICAL,
        ImpactDirection.FORWARD,
        semantic_direction="source contradicts target",
        provenance_direction="forward",
        evidence_role="counterevidence",
    ),
    "derived_from": RelationshipRule(
        ANALYTICAL,
        frozenset({RecordKind.EVIDENCE}) | ANALYTICAL,
        ImpactDirection.REVERSE,
        semantic_direction="source derives from target",
        provenance_direction="forward",
        evidence_role="support",
    ),
    "depends_on": RelationshipRule(
        frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        ImpactDirection.REVERSE,
        semantic_direction="source depends on target",
        provenance_direction="forward",
        evidence_role="context",
    ),
    "informs": RelationshipRule(
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION}),
        frozenset({RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        ImpactDirection.FORWARD,
        semantic_direction="source informs target",
        provenance_direction="forward",
        evidence_role="support",
    ),
    "produces": RelationshipRule(
        frozenset({RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION}),
        frozenset({RecordKind.ARTIFACT}),
        ImpactDirection.FORWARD,
        semantic_direction="source produces target",
        provenance_direction="forward",
        evidence_role="context",
    ),
    "supersedes": RelationshipRule(
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        frozenset({RecordKind.EVIDENCE, RecordKind.CLAIM, RecordKind.IMPLICATION, RecordKind.RECOMMENDATION, RecordKind.ARTIFACT}),
        ImpactDirection.NONE,
        semantic_direction="source supersedes target",
        provenance_direction="none",
        evidence_role="context",
    ),
}


def relationship_rule(relation_type: str) -> RelationshipRule:
    try:
        return RELATIONSHIP_RULES[relation_type.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown relationship type: {relation_type}") from exc
