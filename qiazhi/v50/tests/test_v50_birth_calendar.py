from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars


def _birth(**updates: object) -> BirthInputCanonical:
    payload: dict[str, object] = {
        "birth_input_id": "birth.calendar.test",
        "name": "测试档案",
        "gender": "unknown",
        "calendar_type": "solar",
        "birth_date": "1987-05-12",
        "birth_time": "18:00",
        "birth_location": "Shanghai",
        "timezone": "Asia/Shanghai",
        "input_quality": "user_birth_profile",
    }
    payload.update(updates)
    return BirthInputCanonical(**payload)


def test_solar_birth_profile_resolves_four_pillars_deterministically() -> None:
    resolved = resolve_birth_input_pillars(_birth())

    assert [resolved.year_pillar, resolved.month_pillar, resolved.day_pillar, resolved.hour_pillar] == [
        "丁卯",
        "乙巳",
        "辛酉",
        "丁酉",
    ]
    assert resolved.input_quality == "calendar_derived_pillars"
    assert resolved.pillar_fact_source == "calendar_derived_formal"
    assert "local_civil_time_used_true_solar_time_not_applied" in resolved.warnings


def test_lunar_and_solar_inputs_for_same_moment_resolve_same_pillars() -> None:
    solar = resolve_birth_input_pillars(_birth())
    lunar = resolve_birth_input_pillars(
        _birth(calendar_type="lunar", birth_date="1987-04-15", lunar_leap_month=False)
    )

    assert (lunar.year_pillar, lunar.month_pillar, lunar.day_pillar, lunar.hour_pillar) == (
        solar.year_pillar,
        solar.month_pillar,
        solar.day_pillar,
        solar.hour_pillar,
    )


def test_existing_explicit_pillars_remain_readable_but_are_not_silently_verified() -> None:
    explicit = _birth(
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
        input_quality="explicit_pillars",
    )

    resolved = resolve_birth_input_pillars(explicit)

    assert [resolved.year_pillar, resolved.month_pillar, resolved.day_pillar, resolved.hour_pillar] == [
        "丁巳",
        "乙巳",
        "乙丑",
        "乙酉",
    ]
    assert resolved.input_quality == "unverified_legacy_pillars"
    assert resolved.pillar_fact_source == "unverified_legacy"
    assert "supplied_pillars_not_calendar_verified" in resolved.warnings


def test_invalid_lunar_date_is_rejected_without_fabricating_pillars() -> None:
    with pytest.raises(BirthCalendarResolutionError, match="birth_calendar_resolution_failed"):
        resolve_birth_input_pillars(_birth(calendar_type="lunar", birth_date="1987-05-31"))
