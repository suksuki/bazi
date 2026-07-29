from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from abu_v60.game import DreamEpisodeContract, DreamPhase
from abu_v60.provenance import content_hash

_OUTCOME_VISIBLE_PHASES = {DreamPhase.REVEALED, DreamPhase.COMPLETED}
_ENTRY_TREE_STATE = "DORMANT_QUESTION"


class EpisodePublicProjection:
    """Project mutable canonical objects through one Episode disclosure horizon."""

    def actor(
        self,
        *,
        episode: DreamEpisodeContract,
        phase: DreamPhase,
        timeline: Mapping[str, Any],
        current_state: Mapping[str, Any],
    ) -> dict[str, Any]:
        outcome_visible = phase in _OUTCOME_VISIBLE_PHASES
        visible_event_refs = {episode.baseline_event_ref}
        if outcome_visible:
            visible_event_refs.add(episode.world_event_ref)

        public_events = tuple(
            dict(event)
            for event in timeline.get("events", ())
            if str(event.get("world_event_ref", "")) in visible_event_refs
        )
        projection_as_of_tick = episode.due_tick if outcome_visible else episode.cutoff_tick
        state_event_refs = {
            str(value)
            for key, value in current_state.items()
            if key.endswith("_event_ref") and value
        }
        timeline_has_later_event = any(
            int(event.get("world_tick", -1)) > projection_as_of_tick
            for event in timeline.get("events", ())
        )
        state_is_safe = (
            outcome_visible
            and not timeline_has_later_event
            and state_event_refs.issubset(visible_event_refs)
        )
        public_state = dict(current_state) if state_is_safe else None
        projection = {
            "projection_as_of_tick": projection_as_of_tick,
            "public_timeline": {
                "timeline_version": int(timeline.get("timeline_version", 1)),
                "events": public_events,
            },
            "state": public_state,
            "state_visibility": (
                "CURRENT_COMMITTED" if state_is_safe else "WITHHELD_OUTSIDE_EPISODE_HORIZON"
            ),
        }
        return {
            **projection,
            "projection_hash": content_hash(projection),
        }

    def tree(
        self,
        *,
        episode: DreamEpisodeContract,
        phase: DreamPhase,
        organ_projection_hash: str,
        phenotype: Mapping[str, Any],
    ) -> dict[str, Any]:
        settled = phase in {
            DreamPhase.REVEAL_READY,
            DreamPhase.REVEALED,
            DreamPhase.COMPLETED,
        }
        state = (
            episode.tree_state_after_settlement
            if settled
            else episode.tree_state_on_entry or _ENTRY_TREE_STATE
        )
        projection = {
            "episode_ref": episode.episode_ref,
            "episode_version": episode.episode_version,
            "projection_version": 2 if settled else 1,
            "state": state,
            "organ_projection_hash": organ_projection_hash,
            "phenotype": dict(phenotype),
        }
        return {
            **projection,
            "projection_hash": content_hash(projection),
        }
