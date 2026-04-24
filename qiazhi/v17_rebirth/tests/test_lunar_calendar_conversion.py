from __future__ import annotations

from datetime import datetime

from lunar_python import Lunar

from v17_rebirth.backend.api.stream_v17_physics import (
    _run_v17_physics_core,
    _should_rebuild_physics_core,
)


def _solar_iso_from_lunar(year: int, month: int, day: int, hour: int, minute: int = 0) -> str:
    solar = Lunar.fromYmdHms(year, month, day, hour, minute, 0).getSolar()
    return datetime(
        int(solar.getYear()),
        int(solar.getMonth()),
        int(solar.getDay()),
        int(solar.getHour()),
        int(solar.getMinute()),
        int(solar.getSecond()),
    ).isoformat()


def test_lunar_birth_time_converts_to_solar_before_pillars() -> None:
    payload = _run_v17_physics_core(
        birth_time=datetime(2023, 2, 1, 8, 30),
        gender="female",
        flow_year=2026,
        calendar_type="lunar",
        lunar_is_leap_month=False,
    )

    assert payload["calendar_type"] == "lunar"
    assert payload["lunar_is_leap_month"] is False
    assert payload["birth_time_input"] == "2023-02-01T08:30:00"
    assert payload["birth_time_solar"] == _solar_iso_from_lunar(2023, 2, 1, 8, 30)
    assert payload["birth_time"] == payload["birth_time_solar"]


def test_lunar_leap_month_uses_negative_lunar_month() -> None:
    normal = _run_v17_physics_core(
        birth_time=datetime(2023, 2, 1, 8, 30),
        gender="female",
        flow_year=2026,
        calendar_type="lunar",
        lunar_is_leap_month=False,
    )
    leap = _run_v17_physics_core(
        birth_time=datetime(2023, 2, 1, 8, 30),
        gender="female",
        flow_year=2026,
        calendar_type="lunar",
        lunar_is_leap_month=True,
    )

    assert leap["lunar_is_leap_month"] is True
    assert leap["birth_time_solar"] == _solar_iso_from_lunar(2023, -2, 1, 8, 30)
    assert leap["birth_time_solar"] != normal["birth_time_solar"]


def test_physics_rebuild_detects_calendar_and_leap_month_changes() -> None:
    current = {
        "birth_time_input": "2023-02-01T08:30:00",
        "gender": "female",
        "flow_year": 2026,
        "calendar_type": "lunar",
        "lunar_is_leap_month": False,
    }

    assert not _should_rebuild_physics_core(
        current_physics=current,
        birth_time="2023-02-01T08:30:00",
        gender="female",
        flow_year=2026,
        calendar_type="lunar",
        lunar_is_leap_month=False,
    )
    assert _should_rebuild_physics_core(
        current_physics=current,
        birth_time="2023-02-01T08:30:00",
        gender="female",
        flow_year=2026,
        calendar_type="solar",
        lunar_is_leap_month=False,
    )
    assert _should_rebuild_physics_core(
        current_physics=current,
        birth_time="2023-02-01T08:30:00",
        gender="female",
        flow_year=2026,
        calendar_type="lunar",
        lunar_is_leap_month=True,
    )
