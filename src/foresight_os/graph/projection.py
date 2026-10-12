from typing import Any

try:
    import networkx as nx
except ImportError as exc:  # pragma: no cover - exercised only without optional dependency
    nx = None
    _IMPORT_ERROR = exc

from foresight_os.domain.models import AnalysisState
from foresight_os.domain.relationships import relationship_rule


def build_graph(state: AnalysisState) -> Any:
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
    return graph
