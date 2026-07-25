from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.contracts import BirthInputCanonical, CalendarType
from core.engines.bazi.chart_constraints import validate_four_pillars
from core.engines.bazi.pillar_cycle import linked_hour_pillar


BIRTH_PILLAR_ENGINE_VERSION = "v50.birth_pillar_engine.v2"
FORMAL_HOUR_RULE_VERSION = "v50.five_rats.formal_day.v1"


class BirthCalendarResolutionError(ValueError):
    pass


def resolve_birth_input_pillars(birth_input: BirthInputCanonical) -> BirthInputCanonical:
    """Resolve four pillars from a local civil birth datetime without making a mingli judgment."""
    _validate_timezone(birth_input.timezone)
    supplied = _pillars(birth_input)
    supplied_count = sum(bool(str(value or "").strip()) for value in supplied)
    if supplied_count not in {0, 4}:
        raise BirthCalendarResolutionError("partial_supplied_pillars_not_allowed")
    if supplied_count == 4:
        issues = validate_four_pillars(supplied)
        if issues:
            raise BirthCalendarResolutionError(issues[0].code)

        source_mode = _supplied_source_mode(birth_input.input_quality)
        if source_mode == "calendar_verified":
            derived = _calendar_pillars(birth_input)
            if supplied != derived:
                raise BirthCalendarResolutionError("supplied_pillars_calendar_mismatch")
            return birth_input.model_copy(update={
                "pillar_fact_source": "calendar_verified_supplied",
            })
        if source_mode == "hypothetical":
            return _with_warning(
                birth_input.model_copy(update={
                    "pillar_fact_source": "structurally_legal_hypothetical",
                }),
                "not_resolved_to_real_birth_datetime",
            )
        return birth_input.model_copy(update={
            "input_quality": "unverified_legacy_pillars",
            "pillar_fact_source": "unverified_legacy",
            "warnings": list(dict.fromkeys([
                *birth_input.warnings,
                "supplied_pillars_not_calendar_verified",
            ])),
        })

    pillars = _calendar_pillars(birth_input)
    warnings = list(birth_input.warnings)
    if birth_input.true_solar_time_policy not in {"applied", "not_requested"}:
        warnings.append("local_civil_time_used_true_solar_time_not_applied")
    return birth_input.model_copy(update={
        "year_pillar": pillars[0],
        "month_pillar": pillars[1],
        "day_pillar": pillars[2],
        "hour_pillar": pillars[3],
        "input_quality": "calendar_derived_pillars",
        "pillar_fact_source": "calendar_derived_formal",
        "warnings": list(dict.fromkeys(warnings)),
    })


def _calendar_pillars(birth_input: BirthInputCanonical) -> tuple[str, str, str, str]:
    try:
        parsed_date = datetime.strptime(birth_input.birth_date, "%Y-%m-%d")
        parsed_time = datetime.strptime(birth_input.birth_time, "%H:%M")
    except ValueError as exc:
        raise BirthCalendarResolutionError("invalid_birth_date_or_time") from exc
    if birth_input.calendar_type not in {CalendarType.SOLAR, CalendarType.LUNAR}:
        raise BirthCalendarResolutionError("solar_or_lunar_calendar_required")
    try:
        from lunar_python import Lunar, Solar
    except Exception as exc:  # pragma: no cover - deployment dependency boundary
        raise BirthCalendarResolutionError("lunar_python_dependency_unavailable") from exc
    try:
        if birth_input.calendar_type == CalendarType.SOLAR:
            lunar = Solar.fromYmdHms(
                parsed_date.year,
                parsed_date.month,
                parsed_date.day,
                parsed_time.hour,
                parsed_time.minute,
                0,
            ).getLunar()
        else:
            month = -parsed_date.month if birth_input.lunar_leap_month else parsed_date.month
            lunar = Lunar.fromYmdHms(
                parsed_date.year,
                month,
                parsed_date.day,
                parsed_time.hour,
                parsed_time.minute,
                0,
            )
        eight_char = lunar.getEightChar()
        eight_char.setSect(2)
        day_pillar = eight_char.getDay()
        dependency_hour = eight_char.getTime()
        pillars: tuple[str, str, str, str] = (
            eight_char.getYear(),
            eight_char.getMonth(),
            day_pillar,
            linked_hour_pillar(
                day_pillar=day_pillar,
                hour_branch=dependency_hour[1],
            ),
        )
    except Exception as exc:
        raise BirthCalendarResolutionError("birth_calendar_resolution_failed") from exc
    if validate_four_pillars(pillars):
        raise BirthCalendarResolutionError("birth_calendar_returned_invalid_pillars")
    return pillars


def _pillars(birth_input: BirthInputCanonical) -> tuple[str, str, str, str]:
    return birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar


def _validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise BirthCalendarResolutionError("invalid_birth_timezone") from exc


def _supplied_source_mode(input_quality: str) -> str:
    normalized = str(input_quality or "").strip()
    if normalized in {
        "calendar_verified_supplied",
        "calendar_derived_pillars",
        "user_birth_profile",
        "user_confirmed",
        "user_confirmed_approximate",
        "profile_archive",
    }:
        return "calendar_verified"
    if normalized in {
        "structurally_legal_hypothetical",
        "hypothetical_pillar_structure",
        "sexagenary_cycle_structural_sandbox",
    }:
        return "hypothetical"
    return "legacy_unverified"


def _with_warning(birth_input: BirthInputCanonical, warning: str) -> BirthInputCanonical:
    if warning in birth_input.warnings:
        return birth_input
    return birth_input.model_copy(update={
        "warnings": [*birth_input.warnings, warning],
    })
