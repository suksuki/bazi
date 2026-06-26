from __future__ import annotations

from typing import Literal

from pydantic import Field

from v30.contracts import V30Model
from v30.core.constants import BRANCHES, STEMS


PillarPosition = Literal["year", "month", "day", "hour", "luck", "flow_year", "flow_month"]


class Pillar(V30Model):
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    position: str

    @property
    def display(self) -> str:
        return f"{self.stem}{self.branch}"


class PillarSet(V30Model):
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar

    def as_map(self) -> dict[str, Pillar]:
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "hour": self.hour,
        }


def parse_pillar(display: str, position: str) -> Pillar:
    value = str(display or "").strip()
    if len(value) != 2:
        raise ValueError(f"{position} pillar must be two characters.")
    stem, branch = value[0], value[1]
    if stem not in STEMS:
        raise ValueError(f"{position} stem is not supported: {stem}")
    if branch not in BRANCHES:
        raise ValueError(f"{position} branch is not supported: {branch}")
    return Pillar(stem=stem, branch=branch, position=position)


def pillar_set_from_displays(year: str, month: str, day: str, hour: str) -> PillarSet:
    return PillarSet(
        year=parse_pillar(year, "year"),
        month=parse_pillar(month, "month"),
        day=parse_pillar(day, "day"),
        hour=parse_pillar(hour, "hour"),
    )
