from collections import deque
from typing import Any

from foresight_os.domain.relationships import ImpactDirection


def _graph(value: Any) -> Any:
    return value.graph if hasattr(value, "investigation_id") and hasattr(value, "analysis_revision") else value


def _ordered(values: set[str], limit: int) -> list[str]:
    return sorted(values)[:limit]


def _impact_neighbors(graph: Any, record_id: str) -> list[str]:
    neighbors = []
    for source, target, data in graph.edges(data=True):
        if data["impact"] == ImpactDirection.FORWARD.value and source == record_id:
            neighbors.append(target)
        elif data["impact"] == ImpactDirection.REVERSE.value and target == record_id:
            neighbors.append(source)
    return sorted(neighbors)


def get_impacted_records_complete(graph: Any, changed_id: str) -> list[str]:
    graph = _graph(graph)
    queue = deque([changed_id])
    reached: set[str] = set()
    visited = {changed_id}
    while queue:
        current = queue.popleft()
        for neighbor in _impact_neighbors(graph, current):
            if neighbor not in visited:
                visited.add(neighbor)
                reached.add(neighbor)
                queue.append(neighbor)
    return sorted(reached)


def get_impacted_records(graph: Any, changed_id: str, limit: int = 100) -> list[str]:
    return get_impacted_records_complete(graph, changed_id)[:limit]


def trace_provenance(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    return sorted(nx_ancestors(graph, record_id))[:limit]


def nx_ancestors(graph: Any, record_id: str) -> set[str]:
    graph = _graph(graph)
    ancestors: set[str] = set()
    queue = deque([record_id])
    while queue:
        current = queue.popleft()
        for source in sorted(graph.predecessors(current)):
            if source not in ancestors:
                ancestors.add(source)
                queue.append(source)
    return ancestors


def get_evidence(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    graph = _graph(graph)
    return sorted(node for node in nx_ancestors(graph, record_id) if graph.nodes[node].get("kind") == "evidence")[:limit]


def get_counterevidence(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    graph = _graph(graph)
    values = {
        source
        for source, target, data in graph.edges(data=True)
        if target == record_id and data.get("relation_type") == "contradicts"
    }
    return sorted(values)[:limit]


def get_context(graph: Any, record_id: str, limit: int = 50, depth: int | None = None) -> dict[str, Any]:
    view = graph
    graph = _graph(graph)
    provenance_full = trace_provenance(graph, record_id, limit=len(graph.nodes))
    evidence_full = get_evidence(graph, record_id, limit=len(graph.nodes))
    counterevidence_full = get_counterevidence(graph, record_id, limit=len(graph.nodes))
    impacted = get_impacted_records_complete(graph, record_id)
    if depth is None:
        selected = impacted[:limit]
    else:
        queue = deque([(record_id, 0)])
        bounded: set[str] = set()
        while queue:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for neighbor in _impact_neighbors(graph, current):
                if neighbor not in bounded and neighbor != record_id:
                    bounded.add(neighbor)
                    queue.append((neighbor, current_depth + 1))
        selected = sorted(bounded)[:limit]
    return {
        "provenance": provenance_full[:limit],
        "evidence": evidence_full[:limit],
        "counterevidence": counterevidence_full[:limit],
        "impacted": selected,
        "investigation_id": getattr(view, "investigation_id", None),
        "analysis_revision": getattr(view, "analysis_revision", None),
        "depth": depth,
        "limit": limit,
        "truncated_provenance": len(provenance_full) > limit,
        "truncated_evidence": len(evidence_full) > limit,
        "truncated_counterevidence": len(counterevidence_full) > limit,
        "truncated_impact": len(selected) < len(impacted) if depth is None else len(selected) < len(impacted),
        "truncated": any((len(provenance_full) > limit, len(evidence_full) > limit, len(counterevidence_full) > limit, len(selected) < len(impacted))),
    }
