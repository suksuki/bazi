from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from core.engines.bazi.chart_constraints import validate_four_pillars
from core.engines.bazi.pillar_cycle import (
    HOUR_BRANCH_ORDER,
    JIAZI,
    MONTH_BRANCH_ORDER,
    hour_pillar_options,
    month_pillar_options,
)


CHART_KEY_SEPARATOR = "|"
UNIVERSE_SIZE = len(JIAZI) * len(MONTH_BRANCH_ORDER) * len(JIAZI) * len(HOUR_BRANCH_ORDER)

_JIAZI_INDEX = {pillar: index for index, pillar in enumerate(JIAZI)}
_MONTH_OPTIONS = {pillar: tuple(month_pillar_options(year_pillar=pillar)) for pillar in JIAZI}
_HOUR_OPTIONS = {pillar: tuple(hour_pillar_options(day_pillar=pillar)) for pillar in JIAZI}
_MONTH_INDEX = {
    year: {pillar: index for index, pillar in enumerate(options)}
    for year, options in _MONTH_OPTIONS.items()
}
_HOUR_INDEX = {
    day: {pillar: index for index, pillar in enumerate(options)}
    for day, options in _HOUR_OPTIONS.items()
}


@dataclass(frozen=True)
class StructuralUniverseAudit:
    record_count: int
    unique_chart_key_count: int
    duplicate_count: int
    structurally_valid_count: int
    structurally_invalid_count: int
    invalid_reason_distribution: dict[str, int]
    content_sha256: str


def chart_key(pillars: Sequence[str]) -> str:
    if len(pillars) != 4:
        raise ValueError("four_pillars_required")
    return CHART_KEY_SEPARATOR.join(pillars)


def parse_chart_key(value: str) -> tuple[str, str, str, str]:
    pillars = tuple(value.split(CHART_KEY_SEPARATOR))
    if len(pillars) != 4:
        raise ValueError("invalid_chart_key")
    return pillars  # type: ignore[return-value]


def iter_structural_universe() -> Iterator[tuple[str, str, str, str]]:
    """Rebuild the 60 x 12 x 60 x 12 universe from formal V50 rules."""
    for year_pillar in JIAZI:
        for month_pillar in _MONTH_OPTIONS[year_pillar]:
            for day_pillar in JIAZI:
                for hour_pillar in _HOUR_OPTIONS[day_pillar]:
                    yield year_pillar, month_pillar, day_pillar, hour_pillar


def chart_index(pillars: Sequence[str]) -> int:
    if len(pillars) != 4:
        raise ValueError("four_pillars_required")
    year, month, day, hour = pillars
    try:
        year_index = _JIAZI_INDEX[year]
        month_index = _MONTH_INDEX[year][month]
        day_index = _JIAZI_INDEX[day]
        hour_index = _HOUR_INDEX[day][hour]
    except KeyError as exc:
        issues = structural_invalid_reasons(pillars)
        raise ValueError(issues[0] if issues else "chart_not_in_structural_universe") from exc
    return (((year_index * 12) + month_index) * 60 + day_index) * 12 + hour_index


def pillars_at_index(index: int) -> tuple[str, str, str, str]:
    if not 0 <= index < UNIVERSE_SIZE:
        raise IndexError(index)
    day_hour_block, hour_index = divmod(index, 12)
    year_month_block, day_index = divmod(day_hour_block, 60)
    year_index, month_index = divmod(year_month_block, 12)
    year = JIAZI[year_index]
    day = JIAZI[day_index]
    return year, _MONTH_OPTIONS[year][month_index], day, _HOUR_OPTIONS[day][hour_index]


def structural_invalid_reasons(pillars: Sequence[str]) -> tuple[str, ...]:
    return tuple(issue.code for issue in validate_four_pillars(pillars))


def audit_structural_universe() -> StructuralUniverseAudit:
    seen = bytearray(UNIVERSE_SIZE)
    digest = hashlib.sha256()
    invalid_reasons: Counter[str] = Counter()
    record_count = 0
    duplicate_count = 0
    valid_count = 0

    for pillars in iter_structural_universe():
        record_count += 1
        reasons = structural_invalid_reasons(pillars)
        if reasons:
            invalid_reasons.update(reasons)
        else:
            valid_count += 1
        index = chart_index(pillars)
        if seen[index]:
            duplicate_count += 1
        else:
            seen[index] = 1
        digest.update(chart_key(pillars).encode("utf-8"))
        digest.update(b"\n")

    unique_count = sum(seen)
    return StructuralUniverseAudit(
        record_count=record_count,
        unique_chart_key_count=unique_count,
        duplicate_count=duplicate_count,
        structurally_valid_count=valid_count,
        structurally_invalid_count=record_count - valid_count,
        invalid_reason_distribution=dict(sorted(invalid_reasons.items())),
        content_sha256=digest.hexdigest(),
    )


def month_options_for(year_pillar: str) -> tuple[str, ...]:
    return _MONTH_OPTIONS[year_pillar]


def hour_options_for(day_pillar: str) -> tuple[str, ...]:
    return _HOUR_OPTIONS[day_pillar]
