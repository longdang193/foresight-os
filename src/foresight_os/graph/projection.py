from dataclasses import dataclass
from typing import Any

try:
    import networkx as nx
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    nx = None
    _IMPORT_ERROR = exc

from foresight_os.domain.models import AnalysisState
from foresight_os.domain.relationships import relationship_rule


@dataclass(frozen=True)
class GraphView:
    graph: Any
    investigation_id: str
    analysis_revision: int
    indexes: dict[str, dict[str, list[str]]] | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self.graph, name)


def build_graph(state: AnalysisState) -> GraphView:
    if nx is None:
        raise RuntimeError("NetworkX is required only for graph projection queries") from _IMPORT_ERROR
    graph = nx.MultiDiGraph()
    records = [
        (item.id, "evidence", item)
        for item in state.evidence
    ] + [
        (item.id, kind, item)
        for kind, collection in (
            ("claim", state.claims),
            ("implication", state.implications),
            ("recommendation", state.recommendations),
            ("artifact", state.artifacts),
        )
        for item in collection
    ]
    for record_id, kind, record in sorted(records, key=lambda item: item[0]):
        graph.add_node(record_id, kind=kind, record=record)
    for relation in sorted(state.relationships, key=lambda item: (item.from_id, item.to_id, item.relation_type, item.id)):
        graph.add_edge(
            relation.from_id,
            relation.to_id,
            key=relation.id,
            relation_type=relation.relation_type.lower(),
            impact=relationship_rule(relation.relation_type).impact.value,
            semantic_direction=relationship_rule(relation.relation_type).semantic_direction,
            provenance_direction=relationship_rule(relation.relation_type).provenance_direction,
            evidence_role=relationship_rule(relation.relation_type).evidence_role,
        )
    impact_forward: dict[str, list[str]] = {}
    impact_reverse: dict[str, list[str]] = {}
    provenance: dict[str, list[str]] = {}
    support: dict[str, list[str]] = {}
    counterevidence: dict[str, list[str]] = {}
    for source, target, data in graph.edges(data=True):
        if data["impact"] == "forward":
            impact_forward.setdefault(source, []).append(target)
        elif data["impact"] == "reverse":
            impact_reverse.setdefault(target, []).append(source)
        if data.get("provenance_direction") == "forward":
            provenance.setdefault(target, []).append(source)
        elif data.get("provenance_direction") == "reverse":
            provenance.setdefault(source, []).append(target)
        if data.get("evidence_role") == "support":
            support.setdefault(target, []).append(source)
        if data.get("evidence_role") == "counterevidence":
            counterevidence.setdefault(target, []).append(source)
    indexes = {name: {key: sorted(set(values)) for key, values in mapping.items()} for name, mapping in {
        "impact_forward": impact_forward,
        "impact_reverse": impact_reverse,
        "forward": impact_forward,
        "reverse": impact_reverse,
        "provenance": provenance,
        "support": support,
        "counterevidence": counterevidence,
    }.items()}
    return GraphView(graph, state.investigation_id, state.revision, indexes)
