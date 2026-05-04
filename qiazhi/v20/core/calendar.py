from __future__ import annotations

from datetime import date
from typing import Any

from v20.core.constants import BRANCHES, STEMS

CALENDAR_DEFAULTS_VERSION = "v20.calendar_profile_defaults.v1"
MONTH_BRANCH_SEQUENCE = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
MONTH_START_STEM_BY_YEAR_STEM = {
    "甲": "丙",
    "己": "丙",
    "乙": "戊",
    "庚": "戊",
    "丙": "庚",
    "辛": "庚",
    "丁": "壬",
    "壬": "壬",
    "戊": "甲",
    "癸": "甲",
}
HOUR_START_STEM_BY_DAY_STEM = {
    "甲": "甲",
    "己": "甲",
    "乙": "丙",
    "庚": "丙",
    "丙": "戊",
    "辛": "戊",
    "丁": "庚",
    "壬": "庚",
    "戊": "壬",
    "癸": "壬",
}


def chart_defaults_from_birth_input(birth_input: dict[str, Any], *, selected_year: int | None = None) -> dict[str, object]:
    """Resolve a profile birth input into deterministic pillar defaults for the UI."""
    year = _int(birth_input.get("year"), 1990)
    month = _int(birth_input.get("month"), 1)
    day = _int(birth_input.get("day"), 1)
    hour = _int(birth_input.get("hour"), 0)
    minute = _int(birth_input.get("minute"), 0)
    target_year = int(selected_year or date.today().year)
    calendar_type = str(birth_input.get("calendar_type") or birth_input.get("calendar") or "solar").strip().lower()
    lunar_is_leap_month = _boolish(birth_input.get("lunar_is_leap_month") or birth_input.get("is_lunar_leap_month"))

    payload = {
        "version": CALENDAR_DEFAULTS_VERSION,
        "status": "ready",
        "selected_year": target_year,
        "pillars": {},
        "time_pillars": {},
        "calendar": {
            "input_calendar_type": "lunar" if calendar_type == "lunar" else "solar",
            "source": "lunar_python_eight_char",
        },
        "runtime_mutation": False,
        "guardrails": [
            "PROFILE_BIRTH_INPUT_TO_EXPLICIT_PILLARS_ONLY",
            "NO_RULE_MUTATION_FROM_PROFILE_CALENDAR",
            "TIME_PILLARS_ARE_CONTEXT_ONLY",
        ],
    }
    try:
        eight = None
        try:
            lunar = _lunar_from_birth(year, month, day, hour, minute, calendar_type, lunar_is_leap_month)
            eight = lunar.getEightChar()
            pillars = {
                "year": eight.getYear(),
                "month": eight.getMonth(),
                "day": eight.getDay(),
                "hour": eight.getTime(),
            }
            solar = lunar.getSolar()
            payload["calendar"]["effective_solar"] = {
                "year": int(solar.getYear()),
                "month": int(solar.getMonth()),
                "day": int(solar.getDay()),
                "hour": int(solar.getHour()),
                "minute": int(solar.getMinute()),
            }
        except Exception as exc:
            if calendar_type == "lunar":
                raise
            pillars = _approximate_solar_pillars(year, month, day, hour)
            payload["calendar"]["source"] = "v20_solar_approximate_jie_boundaries"
            payload["calendar"]["dependency_fallback"] = str(exc)
            payload["calendar"]["effective_solar"] = {
                "year": year,
                "month": month,
                "day": day,
                "hour": hour,
                "minute": minute,
            }
        if not all(_valid_pillar(value) for value in pillars.values()):
            raise ValueError("resolved pillar is invalid")
        payload["pillars"] = pillars
        payload["time_pillars"] = {
            "flow_year": _cycle_pillar(target_year - 4),
        }
        active_luck = (
            _active_luck_pillar(eight, birth_input, target_year)
            if eight is not None
            else _approximate_active_luck_pillar(pillars, birth_input, target_year)
        )
        if active_luck:
            time_pillars = payload["time_pillars"]
            if isinstance(time_pillars, dict):
                time_pillars["luck"] = active_luck["pillar"]
            payload["luck_cycle"] = active_luck
    except Exception as exc:
        payload["status"] = "unavailable"
        payload["error"] = str(exc)
    return payload


def _lunar_from_birth(year: int, month: int, day: int, hour: int, minute: int, calendar_type: str, leap_month: bool):
    try:
        from lunar_python import Lunar, Solar
    except Exception as exc:  # pragma: no cover - depends on optional local package
        raise RuntimeError(f"lunar_python unavailable: {exc}") from exc
    if calendar_type == "lunar":
        lunar_month = -month if leap_month else month
        return Lunar.fromYmdHms(year, lunar_month, day, hour, minute, 0)
    return Solar.fromYmdHms(year, month, day, hour, minute, 0).getLunar()


def _active_luck_pillar(eight: Any, birth_input: dict[str, Any], selected_year: int) -> dict[str, object]:
    gender = 0 if str(birth_input.get("gender") or "").lower() == "female" else 1
    yun = eight.getYun(gender)
    for row in yun.getDaYun():
        pillar = str(row.getGanZhi() or "")
        if not pillar:
            continue
        if int(row.getStartYear()) <= selected_year <= int(row.getEndYear()):
            return {
                "pillar": pillar,
                "start_year": int(row.getStartYear()),
                "end_year": int(row.getEndYear()),
                "start_age": int(row.getStartAge()),
                "end_age": int(row.getEndAge()),
                "source": "lunar_python_yun",
            }
    return {}


def _approximate_solar_pillars(year: int, month: int, day: int, hour: int) -> dict[str, str]:
    date(year, month, day)
    year_pillar = _year_pillar(year, month, day)
    month_pillar = _month_pillar(month, day, year_pillar[0])
    day_pillar = _day_pillar(year, month, day)
    hour_pillar = _hour_pillar(hour, day_pillar[0])
    return {"year": year_pillar, "month": month_pillar, "day": day_pillar, "hour": hour_pillar}


def _approximate_active_luck_pillar(pillars: dict[str, str], birth_input: dict[str, Any], selected_year: int) -> dict[str, object]:
    year_pillar = str(pillars.get("year") or "")
    month_pillar = str(pillars.get("month") or "")
    if not _valid_pillar(year_pillar) or not _valid_pillar(month_pillar):
        return {}
    gender = "female" if str(birth_input.get("gender") or "").lower() == "female" else "male"
    direction = _luck_direction(year_pillar[0], gender)
    month_index = _pillar_cycle_index(month_pillar)
    birth_year = _int(birth_input.get("year"), selected_year)
    age = selected_year - birth_year
    for index in range(15):
        start_age = 8 + index * 10
        end_age = start_age + 9
        if start_age <= age <= end_age:
            cycle_index = (month_index + index + 1) % 60 if direction == "forward" else (month_index - index - 1) % 60
            pillar = _cycle_pillar(cycle_index)
            return {
                "pillar": pillar,
                "start_year": birth_year + start_age,
                "end_year": birth_year + end_age,
                "start_age": start_age,
                "end_age": end_age,
                "source": "v20_solar_approximate_jie_boundaries",
            }
    return {}


def _year_pillar(year: int, month: int, day: int) -> str:
    bazi_year = year - 1 if month < 2 or (month == 2 and day < 4) else year
    return _cycle_pillar(bazi_year - 4)


def _month_pillar(month: int, day: int, year_stem: str) -> str:
    offset = _solar_month_offset(month, day)
    start_stem = MONTH_START_STEM_BY_YEAR_STEM[year_stem]
    stem = STEMS[(STEMS.index(start_stem) + offset) % 10]
    return f"{stem}{MONTH_BRANCH_SEQUENCE[offset]}"


def _day_pillar(year: int, month: int, day: int) -> str:
    return _cycle_pillar(_julian_day_number(year, month, day) + 49)


def _hour_pillar(hour: int, day_stem: str) -> str:
    branch_index = ((hour + 1) // 2) % 12
    start_stem = HOUR_START_STEM_BY_DAY_STEM[day_stem]
    return f"{STEMS[(STEMS.index(start_stem) + branch_index) % 10]}{BRANCHES[branch_index]}"


def _cycle_pillar(index: int) -> str:
    return f"{STEMS[index % 10]}{BRANCHES[index % 12]}"


def _solar_month_offset(month: int, day: int) -> int:
    thresholds = {1: 6, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6, 7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7}
    if month == 1:
        return 11 if day >= thresholds[month] else 10
    if month == 2:
        return 0 if day >= thresholds[month] else 11
    return month - 2 if day >= thresholds[month] else month - 3


def _luck_direction(year_stem: str, gender: str) -> str:
    yang_stem = year_stem in {"甲", "丙", "戊", "庚", "壬"}
    return "forward" if (yang_stem and gender == "male") or (not yang_stem and gender == "female") else "reverse"


def _pillar_cycle_index(pillar: str) -> int:
    for index in range(60):
        if _cycle_pillar(index) == pillar:
            return index
    return 0


def _julian_day_number(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - (y // 100) + (y // 400) - 32045


def _valid_pillar(value: object) -> bool:
    text = str(value or "")
    return len(text) == 2 and text[0] in STEMS and text[1] in BRANCHES


def _int(value: object, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}
