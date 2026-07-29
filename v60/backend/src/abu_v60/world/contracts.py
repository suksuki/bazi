from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorldEventStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    COMMITTED = "COMMITTED"
    SETTLED = "SETTLED"
    CANCELED = "CANCELED"


class WorldClock(BaseModel):
    model_config = ConfigDict(frozen=True)

    world_ref: str = Field(min_length=1)
    epoch: int = Field(ge=0)
    tick: int = Field(ge=0)
    rate_numerator: int = Field(ge=0)
    rate_denominator: int = Field(gt=0)


class WorldClockEpoch(BaseModel):
    """One immutable wall-clock-to-world-time mapping."""

    model_config = ConfigDict(frozen=True)

    world_ref: str = Field(min_length=1)
    epoch: int = Field(ge=0)
    start_tick: int = Field(ge=0)
    rate_numerator: int = Field(ge=0)
    rate_denominator: int = Field(gt=0)
    anchored_at: datetime

    @model_validator(mode="after")
    def anchored_at_is_timezone_aware(self) -> WorldClockEpoch:
        if self.anchored_at.tzinfo is None:
            raise ValueError("world_clock_epoch_requires_timezone")
        return self

    def project_tick(self, observed_at: datetime) -> int:
        if observed_at.tzinfo is None:
            raise ValueError("world_clock_observation_requires_timezone")
        elapsed = observed_at - self.anchored_at
        elapsed_microseconds = max(
            0,
            (
                elapsed.days * 86_400 * 1_000_000
                + elapsed.seconds * 1_000_000
                + elapsed.microseconds
            ),
        )
        tick_delta = (elapsed_microseconds * self.rate_numerator) // (
            self.rate_denominator * 1_000_000
        )
        return self.start_tick + tick_delta


class WorldEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    actor_ref: str | None = None
    event_type: str = Field(min_length=1)
    due_tick: int = Field(ge=0)
    committed_tick: int | None = Field(default=None, ge=0)
    status: WorldEventStatus
    correlation_id: str = Field(min_length=1)
    causation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def committed_events_have_a_tick(self) -> WorldEvent:
        if self.status in {WorldEventStatus.COMMITTED, WorldEventStatus.SETTLED} and (
            self.committed_tick is None
        ):
            raise ValueError("committed_world_event_requires_committed_tick")
        return self
