from __future__ import annotations

from abu_v60.dream.first_slice import (
    FUTURE_EVENT_REF,
    HISTORY_EVENT_REF,
    first_episode_contract,
)
from abu_v60.dream.return_slice import (
    RETURN_FUTURE_EVENT_REF,
    RETURN_HISTORY_EVENT_REF,
    return_episode_contract,
)
from abu_v60.experience import EpisodePublicProjection
from abu_v60.game import DreamPhase


def _timeline() -> dict[str, object]:
    return {
        "timeline_version": 1,
        "events": [
            {
                "world_event_ref": HISTORY_EVENT_REF,
                "world_tick": 0,
                "summary": "baseline",
            },
            {
                "world_event_ref": FUTURE_EVENT_REF,
                "world_tick": 12,
                "summary": "first outcome",
            },
            {
                "world_event_ref": RETURN_HISTORY_EVENT_REF,
                "world_tick": 12,
                "summary": "return baseline",
            },
            {
                "world_event_ref": RETURN_FUTURE_EVENT_REF,
                "world_tick": 24,
                "summary": "return outcome",
            },
        ],
    }


def test_actor_projection_never_crosses_the_current_episode_horizon() -> None:
    projector = EpisodePublicProjection()
    state = {
        "location": "south-slope-old-channel",
        "last_committed_event_ref": RETURN_HISTORY_EVENT_REF,
        "last_settled_event_ref": RETURN_FUTURE_EVENT_REF,
    }

    observing = projector.actor(
        episode=first_episode_contract(),
        phase=DreamPhase.OBSERVING,
        timeline=_timeline(),
        current_state=state,
    )
    assert observing["projection_as_of_tick"] == 0
    assert observing["state"] is None
    assert [
        event["world_event_ref"]
        for event in observing["public_timeline"]["events"]
    ] == [HISTORY_EVENT_REF]

    revealed = projector.actor(
        episode=first_episode_contract(),
        phase=DreamPhase.REVEALED,
        timeline=_timeline(),
        current_state=state,
    )
    assert revealed["projection_as_of_tick"] == 12
    assert revealed["state"] is None
    assert {
        event["world_event_ref"]
        for event in revealed["public_timeline"]["events"]
    } == {HISTORY_EVENT_REF, FUTURE_EVENT_REF}


def test_actor_state_is_disclosed_only_when_it_matches_the_visible_episode() -> None:
    projector = EpisodePublicProjection()
    timeline = _timeline()
    timeline["events"] = [
        event
        for event in timeline["events"]
        if event["world_tick"] >= 12
    ]
    state = {
        "location": "south-slope-old-channel",
        "last_committed_event_ref": RETURN_HISTORY_EVENT_REF,
        "last_settled_event_ref": RETURN_FUTURE_EVENT_REF,
    }

    projection = projector.actor(
        episode=return_episode_contract(),
        phase=DreamPhase.COMPLETED,
        timeline=timeline,
        current_state=state,
    )

    assert projection["state"] == state
    assert projection["state_visibility"] == "CURRENT_COMMITTED"
    assert {
        event["world_event_ref"]
        for event in projection["public_timeline"]["events"]
    } == {RETURN_HISTORY_EVENT_REF, RETURN_FUTURE_EVENT_REF}


def test_tree_projection_uses_episode_state_not_global_tree_state() -> None:
    projector = EpisodePublicProjection()
    episode = return_episode_contract()
    common = {
        "episode": episode,
        "organ_projection_hash": "a" * 64,
        "phenotype": {"semantic_status": "FORMAL_FACTS_ONLY"},
    }

    observing = projector.tree(phase=DreamPhase.OBSERVING, **common)
    settled = projector.tree(phase=DreamPhase.REVEAL_READY, **common)

    assert observing["state"] == "RETURN_BASELINE_COMMITTED"
    assert observing["projection_version"] == 1
    assert settled["state"] == "RETURN_FRUIT_MATURED"
    assert settled["projection_version"] == 2
    assert observing["projection_hash"] != settled["projection_hash"]
