from collections import deque
from typing import Any

from foresight_os.domain.relationships import ImpactDirection


def _graph(value: Any) -> Any:
    return value.graph if hasattr(value, "investigation_id") and hasattr(value, "analysis_revision") else value


def _ordered(values: set[str], limit: int) -> list[str]:
    return sorted(values)[:limit]


def _impact_neighbors(graph: Any, record_id: str) -> list[str]:
    neighbors = []
    for _, target, data in graph.out_edges(record_id, data=True):
        if data["impact"] == ImpactDirection.FORWARD.value:
            neighbors.append(target)
    for source, _, data in graph.in_edges(record_id, data=True):
        if data["impact"] == ImpactDirection.REVERSE.value:
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
    graph = _graph(graph)
    queue = deque([changed_id])
    reached: set[str] = set()
    visited = {changed_id}
    while queue and len(reached) < limit:
        current = queue.popleft()
        for neighbor in _impact_neighbors(graph, current):
            if neighbor not in visited:
                visited.add(neighbor)
                reached.add(neighbor)
                if len(reached) >= limit:
                    break
                queue.append(neighbor)
    return sorted(reached)


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
    def bounded_ancestors(max_items: int) -> tuple[list[str], bool]:
        queue = deque([record_id])
        reached: set[str] = set()
        while queue and len(reached) <= max_items:
            current = queue.popleft()
            for source in sorted(graph.predecessors(current)):
                if source not in reached and source != record_id:
                    reached.add(source)
                    queue.append(source)
                    if len(reached) > max_items:
                        break
        values = sorted(reached)
        return values[:max_items], len(values) > max_items

    provenance, provenance_truncated = bounded_ancestors(limit)
    evidence = [node for node in provenance if graph.nodes[node].get("kind") == "evidence"]
    counterevidence_values = sorted(
        source
        for source, _, data in graph.in_edges(record_id, data=True)
        if data.get("relation_type") == "contradicts"
    )
    counterevidence_truncated = len(counterevidence_values) > limit
    counterevidence = counterevidence_values[:limit]
    if depth is None:
        selected = get_impacted_records(graph, record_id, limit)
        impact_truncated = len(get_impacted_records(graph, record_id, limit + 1)) > limit
    else:
        queue = deque([(record_id, 0)])
        bounded: set[str] = set()
        while queue and len(bounded) <= limit:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for neighbor in _impact_neighbors(graph, current):
                if neighbor not in bounded and neighbor != record_id:
                    bounded.add(neighbor)
                    queue.append((neighbor, current_depth + 1))
                    if len(bounded) > limit:
                        break
        selected = sorted(bounded)[:limit]
        impact_truncated = len(bounded) > limit
    evidence = evidence[:limit]
    evidence_truncated = len([node for node in provenance if graph.nodes[node].get("kind") == "evidence"]) > limit
    return {
        "provenance": provenance,
        "evidence": evidence,
        "counterevidence": counterevidence,
        "impacted": selected,
        "investigation_id": getattr(view, "investigation_id", None),
        "analysis_revision": getattr(view, "analysis_revision", None),
        "depth": depth,
        "limit": limit,
        "truncated_provenance": provenance_truncated,
        "truncated_evidence": evidence_truncated,
        "truncated_counterevidence": counterevidence_truncated,
        "truncated_impact": impact_truncated,
        "truncated": any((provenance_truncated, evidence_truncated, counterevidence_truncated, impact_truncated)),
    }
