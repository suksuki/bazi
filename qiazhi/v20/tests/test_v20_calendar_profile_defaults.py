from __future__ import annotations

from v20.core.calendar import chart_defaults_from_birth_input


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
