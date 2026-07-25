from __future__ import annotations

from functools import lru_cache

from lunar_python import Solar


STEMS = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")
JIAZI = tuple(
    f"{STEMS[index % len(STEMS)]}{BRANCHES[index % len(BRANCHES)]}"
    for index in range(60)
)
MONTH_BRANCH_ORDER = tuple("寅卯辰巳午未申酉戌亥子丑")
HOUR_BRANCH_ORDER = BRANCHES
BIRTH_YEAR_MIN = 1900
BIRTH_YEAR_MAX = 2100

FIVE_TIGERS_START = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}
FIVE_RATS_START = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}


def month_pillar_options(*, year_pillar: str) -> list[str]:
    _validate_cycle_pillar(year_pillar, "year")
    start_stem = FIVE_TIGERS_START[year_pillar[0]]
    start_index = STEMS.index(start_stem)
    return [
        f"{STEMS[(start_index + offset) % len(STEMS)]}{branch}"
        for offset, branch in enumerate(MONTH_BRANCH_ORDER)
    ]


def hour_pillar_options(*, day_pillar: str) -> list[str]:
    _validate_cycle_pillar(day_pillar, "day")
    start_stem = FIVE_RATS_START[day_pillar[0]]
    start_index = STEMS.index(start_stem)
    return [
        f"{STEMS[(start_index + offset) % len(STEMS)]}{branch}"
        for offset, branch in enumerate(HOUR_BRANCH_ORDER)
    ]


def linked_month_pillar(*, year_pillar: str, month_branch: str) -> str:
    return next(
        pillar
        for pillar in month_pillar_options(year_pillar=year_pillar)
        if pillar[1] == month_branch
    )


def linked_hour_pillar(*, day_pillar: str, hour_branch: str) -> str:
    return next(
        pillar
        for pillar in hour_pillar_options(day_pillar=day_pillar)
        if pillar[1] == hour_branch
    )


@lru_cache(maxsize=1)
def _cached_birth_year_options() -> dict[str, tuple[int, ...]]:
    output: dict[str, list[int]] = {pillar: [] for pillar in JIAZI}
    for year in range(BIRTH_YEAR_MIN, BIRTH_YEAR_MAX + 1):
        pillars = {
            Solar.fromYmd(year, 1, 15).getLunar().getYearInGanZhiExact(),
            Solar.fromYmd(year, 7, 1).getLunar().getYearInGanZhiExact(),
        }
        for pillar in pillars:
            if pillar in output:
                output[pillar].append(year)
    return {pillar: tuple(years) for pillar, years in output.items()}


def birth_year_options_by_pillar() -> dict[str, list[int]]:
    return {
        pillar: list(years)
        for pillar, years in _cached_birth_year_options().items()
    }


@lru_cache(maxsize=1)
def _cached_cycle_year_options() -> dict[str, tuple[int, ...]]:
    output: dict[str, list[int]] = {pillar: [] for pillar in JIAZI}
    for year in range(BIRTH_YEAR_MIN, BIRTH_YEAR_MAX + 1):
        pillar = Solar.fromYmd(year, 7, 1).getLunar().getYearInGanZhiExact()
        output[pillar].append(year)
    return {pillar: tuple(years) for pillar, years in output.items()}


def cycle_year_options_by_pillar() -> dict[str, list[int]]:
    return {
        pillar: list(years)
        for pillar, years in _cached_cycle_year_options().items()
    }


def branches_by_stem() -> dict[str, list[str]]:
    return {
        stem: [pillar[1] for pillar in JIAZI if pillar[0] == stem]
        for stem in STEMS
    }


def stems_by_branch() -> dict[str, list[str]]:
    return {
        branch: [pillar[0] for pillar in JIAZI if pillar[1] == branch]
        for branch in BRANCHES
    }


def _validate_cycle_pillar(value: str, slot: str) -> None:
    if value not in JIAZI:
        raise ValueError(f"invalid_{slot}_pillar:{value}")
