from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import stable_ref


class StoryBeatKind(StrEnum):
    ARRIVAL = "ARRIVAL"
    OBSERVATION = "OBSERVATION"
    QUESTION = "QUESTION"
    DECISION = "DECISION"
    WORLD_CHANGE = "WORLD_CHANGE"
    REVEAL = "REVEAL"
    DEPARTURE = "DEPARTURE"


class StoryBeat(BaseModel):
    model_config = ConfigDict(frozen=True)

    beat_ref: str = Field(min_length=1)
    kind: StoryBeatKind
    source_ref: str = Field(min_length=1)
    actor_refs: tuple[str, ...] = ()
    asset_refs: tuple[str, ...] = ()
    dialogue_intent: str | None = None


class ScenePlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    scene_ref: str = Field(min_length=1)
    story_version: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    source_event_refs: tuple[str, ...] = ()
    decision_refs: tuple[str, ...] = ()
    beats: tuple[StoryBeat, ...] = ()


class EpisodeTransitionContract(BaseModel):
    """Append-only Story-owned edge between two immutable Episodes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    transition_ref: str = Field(min_length=1)
    transition_version: int = Field(ge=1)
    from_question_ref: str = Field(min_length=1)
    to_question_ref: str = Field(min_length=1)
    label: str = Field(min_length=1)
    runtime_status: Literal["ACTIVE", "RETIRED"]

    @model_validator(mode="after")
    def validate_distinct_endpoints(self) -> EpisodeTransitionContract:
        if self.from_question_ref == self.to_question_ref:
            raise ValueError("episode_transition_cannot_target_itself")
        return self


def episode_transition(
    *,
    from_question_ref: str,
    to_question_ref: str,
    label: str,
    transition_version: int = 1,
) -> EpisodeTransitionContract:
    identity = {
        "from": from_question_ref,
        "to": to_question_ref,
        "version": transition_version,
    }
    return EpisodeTransitionContract(
        transition_ref=stable_ref("v60-episode-transition", identity),
        transition_version=transition_version,
        from_question_ref=from_question_ref,
        to_question_ref=to_question_ref,
        label=label,
        runtime_status="ACTIVE",
    )
