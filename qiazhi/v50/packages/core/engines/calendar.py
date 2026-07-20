from __future__ import annotations

from core.contracts.birth import BirthInputCanonical, CalendarNormalizationResult


HOUR_BRANCH_BY_RANGE: tuple[tuple[int, str], ...] = (
    (23, "子"),
    (1, "丑"),
    (3, "寅"),
    (5, "卯"),
    (7, "辰"),
    (9, "巳"),
    (11, "午"),
    (13, "未"),
    (15, "申"),
    (17, "酉"),
    (19, "戌"),
    (21, "亥"),
)


def normalize_birth_input(birth_input: BirthInputCanonical) -> CalendarNormalizationResult:
    warnings: list[str] = []
    missing_fields: list[str] = []
    hour_branch = _hour_branch_from_time(birth_input.birth_time)
    if not hour_branch:
        missing_fields.append("hour_branch")
        warnings.append("birth_time_could_not_resolve_hour_branch")
    if not birth_input.birth_location:
        warnings.append("birth_location_missing")
    if not all([birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar]):
        missing_fields.append("pillars")
        warnings.append("bazi_material_engine_requires_explicit_pillars_until_calendar_engine_is_implemented")
    confidence = 1.0
    if warnings:
        confidence = max(0.35, 1.0 - 0.15 * len(warnings))
    return CalendarNormalizationResult(
        normalization_id=f"calendar:{birth_input.birth_input_id}",
        birth_input_id=birth_input.birth_input_id,
        solar_date=birth_input.birth_date if birth_input.calendar_type.value == "solar" else "",
        lunar_date=birth_input.birth_date if birth_input.calendar_type.value == "lunar" else "",
        hour_branch=hour_branch,
        timezone=birth_input.timezone,
        true_solar_offset_minutes=None,
        warnings=warnings,
        missing_fields=missing_fields,
        confidence=round(confidence, 3),
    )


def _hour_branch_from_time(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.endswith("时") and len(text) >= 2:
        branch = text[-2]
        if branch in "子丑寅卯辰巳午未申酉戌亥":
            return branch
    try:
        hour = int(text.split(":", 1)[0])
    except ValueError:
        return ""
    if hour == 23:
        return "子"
    for start, branch in HOUR_BRANCH_BY_RANGE[1:]:
        if start <= hour < start + 2:
            return branch
    if 0 <= hour < 1:
        return "子"
    return ""
