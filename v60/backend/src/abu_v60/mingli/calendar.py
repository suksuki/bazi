from __future__ import annotations

from datetime import date, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lunar_python import Lunar, Solar
from pydantic import BaseModel, ConfigDict, field_validator

from abu_v60.provenance import content_hash

CALENDAR_ENGINE_VERSION = "v60.birth-calendar.lunar-python-1.4.8.five-rats.v1"
STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")
FIVE_RATS_START = {
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


class BirthInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar_type: str
    birth_date: date
    birth_time: time
    timezone: str
    lunar_leap_month: bool = False
    true_solar_time_policy: str = "not_applied"

    @field_validator("calendar_type")
    @classmethod
    def validate_calendar_type(cls, value: str) -> str:
        if value not in {"solar", "lunar"}:
            raise ValueError("solar_or_lunar_calendar_required")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("invalid_birth_timezone") from exc
        return value

    @property
    def input_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class ChartPillars(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    year: str
    month: str
    day: str
    hour: str

    def ordered(self) -> list[str]:
        return [self.year, self.month, self.day, self.hour]


def resolve_four_pillars(birth_input: BirthInput) -> ChartPillars:
    eight_char = resolve_eight_char(birth_input)
    day_pillar = eight_char.getDay()
    dependency_hour = eight_char.getTime()
    chart = ChartPillars(
        year=eight_char.getYear(),
        month=eight_char.getMonth(),
        day=day_pillar,
        hour=linked_hour_pillar(day_pillar=day_pillar, hour_branch=dependency_hour[1]),
    )
    for pillar in chart.ordered():
        if len(pillar) != 2 or pillar[0] not in STEMS or pillar[1] not in BRANCHES:
            raise ValueError(f"calendar_returned_invalid_pillar:{pillar}")
    return chart


def resolve_eight_char(birth_input: BirthInput) -> object:
    """Return the pinned lunar-python EightChar object for internal compilers."""

    birth_date = birth_input.birth_date
    birth_time = birth_input.birth_time
    if birth_input.calendar_type == "solar":
        lunar = Solar.fromYmdHms(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            birth_time.hour,
            birth_time.minute,
            birth_time.second,
        ).getLunar()
    else:
        month = -birth_date.month if birth_input.lunar_leap_month else birth_date.month
        lunar = Lunar.fromYmdHms(
            birth_date.year,
            month,
            birth_date.day,
            birth_time.hour,
            birth_time.minute,
            birth_time.second,
        )
    eight_char = lunar.getEightChar()
    eight_char.setSect(2)
    return eight_char


def linked_hour_pillar(*, day_pillar: str, hour_branch: str) -> str:
    if len(day_pillar) != 2 or day_pillar[0] not in STEMS:
        raise ValueError("invalid_day_pillar")
    if hour_branch not in BRANCHES:
        raise ValueError("invalid_hour_branch")
    start_stem = FIVE_RATS_START[day_pillar[0]]
    stem = STEMS[(STEMS.index(start_stem) + BRANCHES.index(hour_branch)) % len(STEMS)]
    return f"{stem}{hour_branch}"
