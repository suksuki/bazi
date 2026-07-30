from __future__ import annotations

from typing import Any

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.provenance import content_hash
from abu_v60.story import EpisodeTransitionContract


def candidate_source_lineage_is_valid(
    *,
    catalog: ActiveEpisodeCatalog,
    candidate: GroveCandidateDefinition,
    source_question_ref: str,
    event_payload: dict[str, Any],
) -> bool:
    """Verify that one replayed source belongs to a Grove candidate's chain."""

    try:
        root = catalog.for_question(candidate.question_ref)
    except ValueError:
        return False
    if (
        not root.entrypoint
        or root.actor_ref != candidate.actor_ref
        or root.tree_ref != candidate.tree_ref
    ):
        return False

    current = root
    incoming: EpisodeTransitionContract | None = None
    visited: set[str] = set()
    while True:
        if current.question_ref in visited:
            return False
        visited.add(current.question_ref)
        if current.question_ref == source_question_ref:
            break
        transition = catalog.transition_after(current.question_ref)
        if transition is None:
            return False
        try:
            current = catalog.for_question(transition.to_question_ref)
        except ValueError:
            return False
        incoming = transition

    if (
        current.actor_ref != candidate.actor_ref
        or current.tree_ref != candidate.tree_ref
    ):
        return False

    candidate_ref = event_payload.get("source_candidate_ref")
    candidate_hash = event_payload.get("source_candidate_hash")
    if (candidate_ref is None) != (candidate_hash is None):
        return False
    if candidate_ref is not None and (
        candidate_ref != candidate.candidate_ref
        or candidate_hash != candidate.candidate_hash
    ):
        return False
    if current.question_ref != root.question_ref and candidate_ref is None:
        return False

    source_episode_ref = event_payload.get("source_episode_ref")
    source_episode_version = event_payload.get("source_episode_version")
    source_episode_contract_hash = event_payload.get(
        "source_episode_contract_hash"
    )
    episode_lineage_values = (
        source_episode_ref,
        source_episode_version,
        source_episode_contract_hash,
    )
    if any(value is not None for value in episode_lineage_values):
        if (
            source_episode_ref != current.episode_ref
            or source_episode_version != current.episode_version
            or source_episode_contract_hash
            != content_hash(current.model_dump(mode="json"))
        ):
            return False
    elif current.question_ref != root.question_ref:
        return False

    transition_ref = event_payload.get("source_transition_ref")
    transition_hash = event_payload.get("source_transition_hash")
    if incoming is None:
        return transition_ref is None and transition_hash is None
    return (
        transition_ref == incoming.transition_ref
        and transition_hash
        == content_hash(incoming.model_dump(mode="json"))
    )
