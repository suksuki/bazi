from __future__ import annotations

from v20.core.calendar import chart_defaults_from_birth_input
from v20.utils.calendar import resolve_luck_pillar, resolve_target_year


def test_v20_calendar_defaults_resolve_profile_birth_to_six_pillar_inputs() -> None:
    result = chart_defaults_from_birth_input(
        {"year": 1990, "month": 5, "day": 12, "hour": 10, "minute": 30, "gender": "male", "calendar": "solar"},
        selected_year=2026,
    )

    assert result["version"] == "v20.calendar_profile_defaults.v1"
    assert result["status"] == "ready"
    assert result["pillars"] == {"year": "庚午", "month": "辛巳", "day": "丁丑", "hour": "乙巳"}
    assert result["time_pillars"]["flow_year"] == "丙午"
    assert result["time_pillars"]["luck"] == "甲申"
    assert result["runtime_mutation"] is False


def test_v20_luck_resolution_does_not_guess_from_explicit_pillars() -> None:
    assert resolve_luck_pillar("庚午", "辛巳", "丁丑", "乙巳", target_year=2026) == ""


def test_v20_flow_year_pillar_resolves_to_matching_year() -> None:
    assert resolve_target_year("庚子") == 2020
    assert resolve_target_year("丙午") == 2026
