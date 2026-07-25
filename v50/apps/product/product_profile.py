from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from core.contracts import BirthInputCanonical


def birth_input_from_profile(profile: dict[str, object]) -> BirthInputCanonical:
    pillars = list(profile.get("pillars") or ["", "", "", ""])
    pillars.extend([""] * (4 - len(pillars)))
    return BirthInputCanonical(
        birth_input_id=str(profile.get("birth_input_id") or f"profile:{profile['profile_id']}"),
        name=str(profile["display_name"]),
        gender=str(profile.get("gender") or "unknown"),
        calendar_type=str(profile.get("calendar_type") or "solar"),
        birth_date=str(profile["birth_date"]),
        birth_time=str(profile["birth_time"]),
        birth_location=str(profile.get("birth_location") or ""),
        timezone=str(profile["timezone"]),
        lunar_leap_month=profile.get("lunar_leap_month"),
        true_solar_time_policy=str(profile.get("true_solar_time_policy") or "not_applied"),
        year_pillar=str(pillars[0]),
        month_pillar=str(pillars[1]),
        day_pillar=str(pillars[2]),
        hour_pillar=str(pillars[3]),
        input_quality=str(profile.get("input_quality") or "profile_archive"),
        warnings=list(profile.get("warnings") or []),
    )


def account_profile_payload(
    *,
    user_id: str,
    birth_input: BirthInputCanonical,
    profile_id: str | None,
    persisted: bool,
) -> dict[str, object]:
    fingerprint_payload = {
        "gender": birth_input.gender.value,
        "calendar_type": birth_input.calendar_type.value,
        "birth_date": birth_input.birth_date,
        "birth_time": birth_input.birth_time,
        "birth_location": birth_input.birth_location.strip(),
        "timezone": birth_input.timezone,
        "lunar_leap_month": birth_input.lunar_leap_month,
    }
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    resolved_id = profile_id or f"v50-profile-{uuid4().hex[:20]}"
    return {
        "profile_id": resolved_id,
        "user_id": user_id,
        "birth_input_id": birth_input.birth_input_id,
        "profile_fingerprint": fingerprint,
        "display_name": birth_input.name.strip(),
        "gender": birth_input.gender.value,
        "calendar_type": birth_input.calendar_type.value,
        "birth_date": birth_input.birth_date,
        "birth_time": birth_input.birth_time,
        "birth_location": birth_input.birth_location.strip(),
        "timezone": birth_input.timezone,
        "lunar_leap_month": birth_input.lunar_leap_month,
        "true_solar_time_policy": birth_input.true_solar_time_policy,
        "input_quality": birth_input.input_quality,
        "warnings": list(birth_input.warnings),
        "pillars": [birth_input.year_pillar, birth_input.month_pillar, birth_input.day_pillar, birth_input.hour_pillar],
        "is_default": True,
        "deleted": False,
        "persisted": persisted,
        "storage": "v50_postgresql" if persisted else "memory_only",
        "boundary": "profile_is_user_owned_birth_material_not_training_or_global_policy",
    }


def deduplicate_profile_archive(values: list[dict[str, object]]) -> list[dict[str, object]]:
    """Hide old retry-created duplicates without deleting case-referenced rows."""

    unique: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in values:
        fingerprint = str(item.get("profile_fingerprint") or item.get("profile_id") or "")
        display_name = str(item.get("display_name") or "").strip().casefold()
        key = (fingerprint, display_name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
