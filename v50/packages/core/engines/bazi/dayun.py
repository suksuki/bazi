from __future__ import annotations

from datetime import datetime
from typing import Any

from lunar_python import Lunar, Solar

from core.contracts.base import CalendarType, Gender
from core.contracts.birth import BirthInputCanonical
from core.engines.bazi.pillar_cycle import JIAZI


def annual_pillar(year: int) -> str:
    return Solar.fromYmd(year, 7, 1).getLunar().getYearInGanZhiExact()


def dayun_direction(*, year_pillar: str, gender: Gender) -> str:
    if gender not in {Gender.MALE, Gender.FEMALE}:
        return "unresolved"
    is_yang_year = year_pillar[:1] in set("甲丙戊庚壬")
    forward = (gender == Gender.MALE) == is_yang_year
    return "forward" if forward else "reverse"


def structural_dayun_sequence(
    *,
    year_pillar: str,
    month_pillar: str,
    gender: Gender,
    limit: int = 10,
) -> tuple[str, list[dict[str, Any]]]:
    """Derive direction and pillar order when no real birth-time anchor exists."""
    direction = dayun_direction(year_pillar=year_pillar, gender=gender)
    if direction == "unresolved":
        raise ValueError("gender_required_for_dayun_sequence")
    if month_pillar not in JIAZI:
        raise ValueError("invalid_month_pillar_for_dayun_sequence")
    step = 1 if direction == "forward" else -1
    month_index = JIAZI.index(month_pillar)
    return direction, [
        {
            "sequence_index": sequence_index,
            "pillar": JIAZI[(month_index + step * sequence_index) % len(JIAZI)],
            "start_year": None,
            "end_year": None,
            "start_age": None,
            "end_age": None,
        }
        for sequence_index in range(1, limit + 1)
    ]


def dayun_sequence(
    birth_input: BirthInputCanonical,
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if birth_input.gender not in {Gender.MALE, Gender.FEMALE}:
        raise ValueError("gender_required_for_dayun_sequence")
    gender_code = 1 if birth_input.gender == Gender.MALE else 0
    output: list[dict[str, Any]] = []
    for period in birth_lunar(birth_input).getEightChar().getYun(gender_code).getDaYun(limit):
        if period.getIndex() <= 0:
            continue
        output.append({
            "sequence_index": period.getIndex(),
            "pillar": period.getGanZhi(),
            "start_year": period.getStartYear(),
            "end_year": period.getEndYear(),
            "start_age": period.getStartAge(),
            "end_age": period.getEndAge(),
        })
    return output


def birth_lunar(birth_input: BirthInputCanonical):
    date = datetime.strptime(birth_input.birth_date, "%Y-%m-%d")
    clock = datetime.strptime(birth_input.birth_time, "%H:%M")
    if birth_input.calendar_type == CalendarType.LUNAR:
        month = -date.month if birth_input.lunar_leap_month else date.month
        return Lunar.fromYmdHms(
            date.year,
            month,
            date.day,
            clock.hour,
            clock.minute,
            0,
        )
    return Solar.fromYmdHms(
        date.year,
        date.month,
        date.day,
        clock.hour,
        clock.minute,
        0,
    ).getLunar()
