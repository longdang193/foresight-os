from collections import defaultdict, deque
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


@dataclass(frozen=True)
class RelationIndex:
    """Deterministic, typed projections over the canonical relationship set."""

    relationships: tuple[object, ...]

    @classmethod
    def from_state(cls, state: object) -> "RelationIndex":
        return cls(tuple(sorted(getattr(state, "relationships", ()), key=lambda item: (item.from_id, item.to_id, item.relation_type, item.id))))

    def _edges(self, direction: str) -> dict[str, tuple[str, ...]]:
        edges: dict[str, list[str]] = defaultdict(list)
        for relationship in self.relationships:
            rule = relationship_rule(relationship.relation_type)
            if direction == "impact":
                if rule.impact == ImpactDirection.FORWARD:
                    edges[relationship.from_id].append(relationship.to_id)
                elif rule.impact == ImpactDirection.REVERSE:
                    edges[relationship.to_id].append(relationship.from_id)
            elif direction == "material":
                if rule.provenance_direction == "forward":
                    edges[relationship.to_id].append(relationship.from_id)
                elif rule.provenance_direction == "reverse":
                    edges[relationship.from_id].append(relationship.to_id)
        return {key: tuple(sorted(set(value))) for key, value in edges.items()}

    def material_closure(self, target_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        edges = self._edges("material")
        visited = set(target_ids)
        queue = deque(sorted(visited))
        while queue:
            current = queue.popleft()
            for candidate in edges.get(current, ()):
                if candidate not in visited:
                    visited.add(candidate)
                    queue.append(candidate)
        return tuple(sorted(visited))

    def impacted_descendants(self, changed_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        edges = self._edges("impact")
        visited = set(changed_ids)
        queue = deque(sorted(visited))
        while queue:
            current = queue.popleft()
            for dependent in edges.get(current, ()):
                if dependent not in visited:
                    visited.add(dependent)
                    queue.append(dependent)
        return tuple(sorted(visited))

    def support_ids(self, target_id: str) -> tuple[str, ...]:
        return tuple(sorted({item.from_id for item in self.relationships if item.to_id == target_id and relationship_rule(item.relation_type).evidence_role == "support"}))

    def counterevidence_ids(self, target_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        targets = set(target_ids)
        return tuple(sorted({item.from_id for item in self.relationships if item.to_id in targets and item.relation_type.lower() == "contradicts"}))


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
