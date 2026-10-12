from collections import deque
from typing import Any

from foresight_os.domain.relationships import ImpactDirection


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


def get_impacted_records(graph: Any, changed_id: str, limit: int = 100) -> list[str]:
    queue = deque([changed_id])
    reached: set[str] = set()
    while queue and len(reached) < limit:
        current = queue.popleft()
        for neighbor in _impact_neighbors(graph, current):
            if neighbor not in reached and neighbor != changed_id:
                reached.add(neighbor)
                queue.append(neighbor)
    return sorted(reached)[:limit]


def trace_provenance(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    return sorted(nx_ancestors(graph, record_id))[:limit]


def nx_ancestors(graph: Any, record_id: str) -> set[str]:
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
    return sorted(node for node in nx_ancestors(graph, record_id) if graph.nodes[node].get("kind") == "evidence")[:limit]


def get_counterevidence(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    values = {
        source
        for source, target, data in graph.edges(data=True)
        if target == record_id and data.get("relation_type") == "contradicts"
    }
    return sorted(values)[:limit]


def get_context(graph: Any, record_id: str, limit: int = 50) -> dict[str, list[str]]:
    return {
        "provenance": trace_provenance(graph, record_id, limit),
        "evidence": get_evidence(graph, record_id, limit),
        "counterevidence": get_counterevidence(graph, record_id, limit),
        "impacted": get_impacted_records(graph, record_id, limit),
    }
