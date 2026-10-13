from collections import deque
from typing import Any, Callable, Iterable

from foresight_os.domain.relationships import ImpactDirection


_PROVENANCE_RELATIONS = {"supports", "derived_from", "depends_on", "informs"}


def _graph(value: Any) -> Any:
    return value.graph if hasattr(value, "investigation_id") and hasattr(value, "analysis_revision") else value


def _indexes(value: Any) -> dict[str, dict[str, list[str]]]:
    return getattr(value, "indexes", None) or {}


def _bounded_reach(
    start: str,
    neighbors: Callable[[str], Iterable[str]],
    limit: int,
    depth: int | None = None,
) -> tuple[list[str], bool]:
    if limit <= 0:
        return [], False
    queue = deque([(start, 0)])
    visited = {start}
    reached: set[str] = set()
    while queue:
        current, current_depth = queue.popleft()
        if depth is not None and current_depth >= depth:
            continue
        for neighbor in sorted(set(neighbors(current))):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            reached.add(neighbor)
            if len(reached) > limit:
                return sorted(reached)[:limit], True
            queue.append((neighbor, current_depth + 1))
    return sorted(reached), False


def _impact_neighbors(graph: Any, record_id: str) -> list[str]:
    indexes = _indexes(graph)
    if indexes:
        return sorted(
            set(indexes.get("impact_forward", indexes.get("forward", {})).get(record_id, ()))
            | set(indexes.get("impact_reverse", indexes.get("reverse", {})).get(record_id, ()))
        )
    neighbors = []
    for _, target, data in graph.out_edges(record_id, data=True):
        if data.get("impact") == ImpactDirection.FORWARD.value:
            neighbors.append(target)
    for source, _, data in graph.in_edges(record_id, data=True):
        if data.get("impact") == ImpactDirection.REVERSE.value:
            neighbors.append(source)
    return sorted(set(neighbors))


def get_impacted_records_complete(graph: Any, changed_id: str) -> list[str]:
    graph = _graph(graph)
    reached, _ = _bounded_reach(
        changed_id,
        lambda node: _impact_neighbors(graph, node),
        limit=max(len(graph), 1),
    )
    return reached


def get_impacted_records(graph: Any, changed_id: str, limit: int = 100) -> list[str]:
    graph = _graph(graph)
    reached, _ = _bounded_reach(
        changed_id,
        lambda node: _impact_neighbors(graph, node),
        limit=limit,
    )
    return reached


def _provenance_neighbors(graph: Any, record_id: str) -> list[str]:
    indexes = _indexes(graph)
    if indexes:
        return sorted(set(indexes.get("provenance", {}).get(record_id, ())))
    neighbors = []
    for source, _, data in graph.in_edges(record_id, data=True):
        if data.get("provenance_direction", "forward") == "forward" and data.get("relation_type") in _PROVENANCE_RELATIONS:
            neighbors.append(source)
    for _, target, data in graph.out_edges(record_id, data=True):
        if data.get("provenance_direction") == "reverse" and data.get("relation_type") in _PROVENANCE_RELATIONS:
            neighbors.append(target)
    return sorted(set(neighbors))


def trace_provenance(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    graph = _graph(graph)
    reached, _ = _bounded_reach(
        record_id,
        lambda node: _provenance_neighbors(graph, node),
        limit=limit,
    )
    return reached


def nx_ancestors(graph: Any, record_id: str) -> set[str]:
    graph = _graph(graph)
    ancestors: set[str] = set()
    queue = deque([record_id])
    while queue:
        current = queue.popleft()
        for source in _provenance_neighbors(graph, current):
            if source not in ancestors and source != record_id:
                ancestors.add(source)
                queue.append(source)
    return ancestors


def get_evidence(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    graph = _graph(graph)
    provenance = trace_provenance(graph, record_id, limit=max(limit, 0))
    return [node for node in provenance if graph.nodes[node].get("kind") == "evidence"][:limit]


def get_counterevidence(graph: Any, record_id: str, limit: int = 50) -> list[str]:
    graph = _graph(graph)
    indexes = _indexes(graph)
    if indexes:
        values = indexes.get("counterevidence", {}).get(record_id, ())
    else:
        values = (
            source
            for source, _, data in graph.in_edges(record_id, data=True)
            if data.get("evidence_role") == "counterevidence" or data.get("relation_type") == "contradicts"
        )
    return sorted(set(values))[:limit]


def get_context(graph: Any, record_id: str, limit: int = 50, depth: int | None = None) -> dict[str, Any]:
    view = graph
    graph = _graph(graph)
    provenance, provenance_truncated = _bounded_reach(
        record_id,
        lambda node: _provenance_neighbors(graph, node),
        limit=limit,
    )
    evidence = [node for node in provenance if graph.nodes[node].get("kind") == "evidence"]
    counterevidence_values = get_counterevidence(graph, record_id, limit=max(limit + 1, 0))
    counterevidence_truncated = len(counterevidence_values) > limit
    counterevidence = counterevidence_values[:limit]
    selected, impact_truncated = _bounded_reach(
        record_id,
        lambda node: _impact_neighbors(graph, node),
        limit=limit,
        depth=depth,
    )
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
