from datetime import UTC, datetime, timedelta

import pytest
from abu_v60.world import WorldClock, WorldClockEpoch, WorldEvent, WorldEventStatus
from pydantic import ValidationError


def test_world_clock_uses_integer_tick_and_rational_rate() -> None:
    clock = WorldClock(
        world_ref="world:abu",
        epoch=0,
        tick=0,
        rate_numerator=1,
        rate_denominator=4,
    )
    assert clock.tick == 0
    assert clock.rate_denominator == 4


def test_committed_world_event_requires_commit_tick() -> None:
    with pytest.raises(ValidationError, match="committed_world_event_requires_committed_tick"):
        WorldEvent(
            event_ref="event:1",
            world_ref="world:abu",
            event_type="ENCOUNTER_SETTLED",
            due_tick=5,
            status=WorldEventStatus.COMMITTED,
            correlation_id="correlation:1",
            causation_id="cause:1",
        )


def test_world_epoch_projects_integer_tick_from_rational_wall_clock() -> None:
    anchored_at = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)
    epoch = WorldClockEpoch(
        world_ref="world:abu",
        epoch=3,
        start_tick=24,
        rate_numerator=1,
        rate_denominator=60,
        anchored_at=anchored_at,
    )

    assert epoch.project_tick(anchored_at + timedelta(seconds=59)) == 24
    assert epoch.project_tick(anchored_at + timedelta(seconds=60)) == 25
    assert epoch.project_tick(anchored_at + timedelta(minutes=3, seconds=17)) == 27


def test_world_epoch_never_rewinds_before_anchor() -> None:
    anchored_at = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)
    epoch = WorldClockEpoch(
        world_ref="world:abu",
        epoch=3,
        start_tick=24,
        rate_numerator=2,
        rate_denominator=1,
        anchored_at=anchored_at,
    )

    assert epoch.project_tick(anchored_at - timedelta(days=1)) == 24
