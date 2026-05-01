from __future__ import annotations

from v20.core.constants import BRANCHES, STEMS
from v20.corpus.canonical_case import CanonicalCase

SEXAGENARY_CYCLE = tuple(f"{STEMS[index % 10]}{BRANCHES[index % 12]}" for index in range(60))
MONTH_BRANCHES = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")
FULL_CORPUS_CASE_COUNT = 60 * 12 * 60 * 12

_MONTH_START_STEM_INDEX = {
    "甲": 2,
    "己": 2,
    "乙": 4,
    "庚": 4,
    "丙": 6,
    "辛": 6,
    "丁": 8,
    "壬": 8,
    "戊": 0,
    "癸": 0,
}

_HOUR_START_STEM_INDEX = {
    "甲": 0,
    "己": 0,
    "乙": 2,
    "庚": 2,
    "丙": 4,
    "辛": 4,
    "丁": 6,
    "壬": 6,
    "戊": 8,
    "癸": 8,
}


def sample_corpus_cases(limit: int = 12) -> tuple[CanonicalCase, ...]:
    rows: list[CanonicalCase] = []
    for index, stem in enumerate(STEMS):
        if len(rows) >= limit:
            break
        branch = BRANCHES[index % len(BRANCHES)]
        rows.append(
            CanonicalCase(
                case_id=f"v20.corpus.sample.{index:03d}",
                pillar_displays=(f"{stem}{branch}", "戊辰", "甲午", "辛酉"),
            )
        )
    return tuple(rows)


def canonical_case_at(index: int) -> CanonicalCase:
    if index < 0 or index >= FULL_CORPUS_CASE_COUNT:
        raise IndexError(f"V20 full corpus index out of range: {index}")
    hour_branch_index = index % 12
    day_index = (index // 12) % 60
    month_branch_index = (index // (12 * 60)) % 12
    year_index = (index // (12 * 60 * 12)) % 60

    year = SEXAGENARY_CYCLE[year_index]
    day = SEXAGENARY_CYCLE[day_index]
    month = month_pillar_for(year[0], month_branch_index)
    hour = hour_pillar_for(day[0], hour_branch_index)
    return CanonicalCase(
        case_id=f"v20.full_corpus.case.{index:06d}",
        pillar_displays=(year, month, day, hour),
        corpus_space="valid_year_month_day_hour_pillar_space_518400",
    )


def iter_canonical_cases(start: int = 0, limit: int = 12) -> tuple[CanonicalCase, ...]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    end = min(FULL_CORPUS_CASE_COUNT, start + limit)
    return tuple(canonical_case_at(index) for index in range(start, end))


def month_pillar_for(year_stem: str, month_branch_index: int) -> str:
    if year_stem not in _MONTH_START_STEM_INDEX:
        raise ValueError(f"Unsupported year stem: {year_stem}")
    if month_branch_index < 0 or month_branch_index >= len(MONTH_BRANCHES):
        raise IndexError(f"Month branch index out of range: {month_branch_index}")
    stem = STEMS[(_MONTH_START_STEM_INDEX[year_stem] + month_branch_index) % len(STEMS)]
    return f"{stem}{MONTH_BRANCHES[month_branch_index]}"


def hour_pillar_for(day_stem: str, hour_branch_index: int) -> str:
    if day_stem not in _HOUR_START_STEM_INDEX:
        raise ValueError(f"Unsupported day stem: {day_stem}")
    if hour_branch_index < 0 or hour_branch_index >= len(BRANCHES):
        raise IndexError(f"Hour branch index out of range: {hour_branch_index}")
    stem = STEMS[(_HOUR_START_STEM_INDEX[day_stem] + hour_branch_index) % len(STEMS)]
    return f"{stem}{BRANCHES[hour_branch_index]}"
