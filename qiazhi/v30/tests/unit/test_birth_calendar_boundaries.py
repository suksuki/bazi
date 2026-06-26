from __future__ import annotations

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input


def test_invalid_timezone_blocks_birth_input_without_fake_pillars() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="birth-boundary-invalid-timezone",
        birth_input=BirthInput(
            input_id="invalid-timezone",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Invalid/Timezone",
        ),
    )

    assert result.status == "blocked"
    assert result.chart_context is None
    assert result.four_pillar_result.pillars == {}
    assert result.four_pillar_result.missing_pillars == ["year", "month", "day", "hour"]
    assert "invalid_timezone" in result.failures
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert trace.status == "blocked"
    assert "valid_birth_datetime" in trace.missing_requirements


def test_invalid_date_blocks_birth_input_without_fake_pillars() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="birth-boundary-invalid-date",
        birth_input=BirthInput(
            input_id="invalid-date",
            birth_date="1990-02-31",
            birth_time="09:00",
            timezone="Asia/Shanghai",
        ),
    )

    assert result.status == "blocked"
    assert result.chart_context is None
    assert result.four_pillar_result.pillars == {}
    assert "invalid_birth_date" in result.failures


def test_invalid_time_blocks_birth_input_without_fake_pillars() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="birth-boundary-invalid-time",
        birth_input=BirthInput(
            input_id="invalid-time",
            birth_date="1990-02-04",
            birth_time="25:61",
            timezone="Asia/Shanghai",
        ),
    )

    assert result.status == "blocked"
    assert result.chart_context is None
    assert result.four_pillar_result.pillars == {}
    assert "invalid_birth_time" in result.failures


def test_late_zi_hour_boundary_is_recorded_for_ready_solar_conversion() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="birth-boundary-late-zi",
        birth_input=BirthInput(
            input_id="late-zi",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            gender="male",
        ),
    )

    assert result.status == "ready"
    assert result.chart_context is not None
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert "late_zi_hour_boundary_recorded" in trace.boundary_flags
    assert trace.missing_requirements == []


def test_solar_term_year_month_boundary_switches_pillars_without_guessing() -> None:
    before = build_chart_context_from_birth_input(
        reading_id="birth-boundary-solar-term-before",
        birth_input=BirthInput(
            input_id="solar-term-before",
            birth_date="1990-02-04",
            birth_time="09:00",
            timezone="Asia/Shanghai",
            gender="male",
        ),
    )
    after = build_chart_context_from_birth_input(
        reading_id="birth-boundary-solar-term-after",
        birth_input=BirthInput(
            input_id="solar-term-after",
            birth_date="1990-02-04",
            birth_time="11:00",
            timezone="Asia/Shanghai",
            gender="male",
        ),
    )

    assert before.status == "ready"
    assert after.status == "ready"
    assert before.four_pillar_result.pillars["year"] == "己巳"
    assert before.four_pillar_result.pillars["month"] == "丁丑"
    assert after.four_pillar_result.pillars["year"] == "庚午"
    assert after.four_pillar_result.pillars["month"] == "戊寅"
    assert before.four_pillar_result.conversion_trace is not None
    assert after.four_pillar_result.conversion_trace is not None
    assert "solar_term_year_month_boundary_recorded" in before.four_pillar_result.conversion_trace.boundary_flags
    assert "solar_term_year_month_boundary_recorded" in after.four_pillar_result.conversion_trace.boundary_flags


def test_true_solar_time_without_resolvable_place_is_blocked_without_fake_pillars() -> None:
    result = build_chart_context_from_birth_input(
        reading_id="birth-boundary-true-solar-no-place",
        birth_input=BirthInput(
            input_id="true-solar-no-place",
            birth_date="1990-02-04",
            birth_time="23:30",
            timezone="Asia/Shanghai",
            use_true_solar_time=True,
        ),
    )

    assert result.status == "blocked"
    assert result.chart_context is None
    assert result.four_pillar_result.pillars == {}
    assert "birth_place_longitude_resolution_required" in result.failures
    trace = result.four_pillar_result.conversion_trace
    assert trace is not None
    assert "birth_place_longitude_resolution" in trace.missing_requirements
