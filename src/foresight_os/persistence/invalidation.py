from collections import defaultdict, deque
from dataclasses import replace

from foresight_os.domain.models import AnalysisState, Invalidation, Revision
from foresight_os.domain.relationships import ImpactDirection, relationship_rule


def invalidate_dependencies(state: AnalysisState, changed_ids: list[str], reason: str) -> AnalysisState:
    if reason in state.invalidation.reasons and set(changed_ids).issubset(set(state.invalidation.reassessment_ids)):
        return state

    edges = defaultdict(list)
    for relationship in state.relationships:
        direction = relationship_rule(relationship.relation_type).impact
        if direction == ImpactDirection.FORWARD:
            edges[relationship.from_id].append(relationship.to_id)
        elif direction == ImpactDirection.REVERSE:
            edges[relationship.to_id].append(relationship.from_id)

    known_ids = {
        item.id
        for collection in [state.evidence, state.claims, state.implications, state.recommendations, state.artifacts]
        for item in collection
    }
    queue = deque(changed_ids)
    reached = set(changed_ids)
    while queue:
        current = queue.popleft()
        for dependent in edges[current]:
            if dependent not in reached:
                reached.add(dependent)
                queue.append(dependent)

    if not set(changed_ids).issubset(known_ids):
        reached.update(item.id for item in [*state.claims, *state.implications, *state.recommendations, *state.artifacts])
    artifact_ids = {item.id for item in state.artifacts}
    reassessment_ids = sorted(reached - artifact_ids)
    stale_artifact_ids = sorted(reached & artifact_ids)
    invalidation = Invalidation(
        stale_artifact_ids=sorted(set(state.invalidation.stale_artifact_ids) | set(stale_artifact_ids)),
        reassessment_ids=sorted(set(state.invalidation.reassessment_ids) | set(reassessment_ids)),
        reasons=[*state.invalidation.reasons, reason],
    )
    revision_number = state.revision + 1
    revision = Revision(
        f"revision-{revision_number}",
        revision_number,
        reason,
        [item.id for collection in [state.evidence, state.claims, state.implications, state.recommendations, state.artifacts] for item in collection],
    )
    return replace(state, revision=revision_number, revisions=[*state.revisions, revision], invalidation=invalidation)
