from __future__ import annotations

import pytest
from pydantic import ValidationError

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input


def test_birth_input_requires_time_unless_unknown_hour() -> None:
    with pytest.raises(ValidationError):
        BirthInput(birth_date="1990-02-04")


def test_birth_input_unknown_hour_is_allowed_without_fabricating_hour_pillar() -> None:
    birth_input = BirthInput(
        input_id="birth-unknown-hour",
        birth_date="1990-02-04",
        timezone="Asia/Shanghai",
        unknown_hour=True,
    )

    result = build_chart_context_from_birth_input(
        reading_id="birth-contract-unknown-hour",
        birth_input=birth_input,
    )

    assert result.status == "pending"
    assert result.chart_context is None
    assert result.four_pillar_result.status == "pending"
    assert result.four_pillar_result.pillars == {}
    assert "hour" in result.four_pillar_result.missing_pillars
    assert result.four_pillar_result.chart_build_source.source_type == "birth_input"
    assert result.four_pillar_result.conversion_trace is not None
    assert "unknown_hour_blocks_hour_pillar" in result.four_pillar_result.conversion_trace.boundary_flags
    assert "unknown_hour_blocks_hour_pillar" in result.failures


def test_birth_input_resolves_true_solar_time_with_known_place() -> None:
    birth_input = BirthInput(
        input_id="birth-true-solar",
        birth_date="1990-02-04",
        birth_time="23:30",
        timezone="Asia/Seoul",
        birth_place="Seoul",
        use_true_solar_time=True,
    )

    result = build_chart_context_from_birth_input(
        reading_id="birth-contract-true-solar",
        birth_input=birth_input,
    )

    assert result.status == "ready"
    assert result.chart_context is not None
    assert result.four_pillar_result.pillars == {
        "year": "庚午",
        "month": "戊寅",
        "day": "庚子",
        "hour": "丁亥",
    }
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert trace.status == "ready"
    assert trace.timezone == "Asia/Seoul"
    assert trace.use_true_solar_time is True
    assert "timezone_assumption_recorded" in trace.boundary_flags
    assert "late_zi_hour_boundary_recorded" in trace.boundary_flags
    assert "true_solar_time_adjustment_recorded" in trace.boundary_flags
    assert trace.missing_requirements == []


def test_solar_birth_input_builds_ready_chart_context() -> None:
    birth_input = BirthInput(
        input_id="birth-solar-ready",
        birth_date="1990-02-04",
        birth_time="23:30",
        timezone="Asia/Shanghai",
    )

    result = build_chart_context_from_birth_input(
        reading_id="birth-contract-ready",
        birth_input=birth_input,
    )

    assert result.status == "ready"
    assert result.failures == []
    assert result.chart_context is not None
    assert result.four_pillar_result.pillars == {
        "year": "庚午",
        "month": "戊寅",
        "day": "庚子",
        "hour": "戊子",
    }
    assert result.chart_context.day_master == "庚"
    assert result.chart_context.input_pillars["source"] == "birth_input"
    assert result.chart_context.input_pillars["chart_build_source"]["status"] == "ready"
    assert result.chart_context.input_pillars["conversion_trace"]["status"] == "ready"
    assert "late_zi_hour_boundary_recorded" in result.chart_context.input_pillars["conversion_trace"]["boundary_flags"]


def test_lunar_birth_input_builds_ready_chart_context() -> None:
    birth_input = BirthInput(
        input_id="birth-lunar",
        calendar_type="lunar",
        birth_date="1990-01-09",
        birth_time="09:00",
        timezone="Asia/Shanghai",
    )

    result = build_chart_context_from_birth_input(
        reading_id="birth-contract-lunar",
        birth_input=birth_input,
    )

    assert result.status == "ready"
    assert result.chart_context is not None
    assert result.four_pillar_result.pillars == {
        "year": "己巳",
        "month": "丁丑",
        "day": "庚子",
        "hour": "辛巳",
    }
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert trace.status == "ready"
    assert "lunar_calendar_conversion_recorded" in trace.boundary_flags
    assert trace.missing_requirements == []


def test_lunar_leap_month_birth_input_records_boundary() -> None:
    birth_input = BirthInput(
        input_id="birth-lunar-leap",
        calendar_type="lunar",
        birth_date="2020-04-01",
        birth_time="09:00",
        timezone="Asia/Shanghai",
        lunar_is_leap_month=True,
    )

    result = build_chart_context_from_birth_input(
        reading_id="birth-contract-lunar-leap",
        birth_input=birth_input,
    )

    assert result.status == "ready"
    assert result.chart_context is not None
    assert result.four_pillar_result.pillars == {
        "year": "庚子",
        "month": "辛巳",
        "day": "丙寅",
        "hour": "癸巳",
    }
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert "lunar_calendar_conversion_recorded" in trace.boundary_flags
    assert "lunar_leap_month_recorded" in trace.boundary_flags
