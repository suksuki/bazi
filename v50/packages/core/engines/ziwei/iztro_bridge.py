from __future__ import annotations

import json
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.contracts.birth import BirthInputCanonical


ROOT = Path(__file__).resolve().parents[4]
BRIDGE = ROOT / "tools" / "ziwei-iztro" / "bridge.mjs"
PACKAGE_LOCK = ROOT / "tools" / "ziwei-iztro" / "package-lock.json"
HOUR_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


class IztroZiweiUnavailable(RuntimeError):
    pass


def calculate_iztro_plate(
    *,
    birth_input: BirthInputCanonical,
    analysis_year: int | None = None,
    language: str = "zh-CN",
) -> dict[str, Any]:
    if not BRIDGE.exists() or not PACKAGE_LOCK.exists():
        raise IztroZiweiUnavailable("iztro_bridge_not_installed")
    time_index, time_warnings = _time_index(birth_input.birth_time)
    if time_index is None:
        raise IztroZiweiUnavailable("ziwei_birth_time_required")
    if birth_input.gender.value not in {"male", "female"}:
        raise IztroZiweiUnavailable("ziwei_gender_required")
    year = analysis_year or date.today().year
    payload = {
        "calendar_type": birth_input.calendar_type.value,
        "birth_date": birth_input.birth_date,
        "time_index": time_index,
        "gender": birth_input.gender.value,
        "is_leap_month": bool(birth_input.lunar_leap_month),
        "analysis_date": f"{year}-1-1",
        "language": language,
    }
    try:
        result = json.loads(_run_bridge(json.dumps(payload, ensure_ascii=False, sort_keys=True)))
    except json.JSONDecodeError as exc:
        raise IztroZiweiUnavailable("iztro_bridge_invalid_json") from exc
    expected_pillars = [
        birth_input.year_pillar,
        birth_input.month_pillar,
        birth_input.day_pillar,
        birth_input.hour_pillar,
    ]
    actual_pillars = str(result.get("chinese_date") or "").split()
    warnings = list(time_warnings)
    comparable = all(expected_pillars) and len(actual_pillars) == 4
    differences = [
        label
        for label, expected, actual in zip(("year", "month", "day", "hour"), expected_pillars, actual_pillars, strict=False)
        if expected and expected != actual
    ]
    critical_differences = [label for label in differences if label != "month"]
    pillar_alignment = not comparable or not critical_differences
    if critical_differences:
        warnings.append("ziwei_bazi_pillar_mismatch")
    elif differences == ["month"]:
        warnings.append("ziwei_bazi_month_pillar_convention_difference")
    approximate = "approximate" in birth_input.input_quality or any("approximate" in item for item in birth_input.warnings)
    if approximate:
        warnings.append("ziwei_birth_time_approximate")
    result["warnings"] = warnings
    result["pillar_alignment"] = pillar_alignment
    result["pillar_differences"] = differences
    result["reasoning_ready"] = pillar_alignment and not approximate
    return result


@lru_cache(maxsize=512)
def _run_bridge(payload_json: str) -> str:
    try:
        completed = subprocess.run(
            ["node", str(BRIDGE)],
            input=payload_json,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IztroZiweiUnavailable(f"iztro_bridge_failed:{type(exc).__name__}") from exc
    if completed.returncode != 0:
        message = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unknown_error"
        raise IztroZiweiUnavailable(f"iztro_bridge_failed:{message[:240]}")
    return completed.stdout


def _time_index(value: str) -> tuple[int | None, list[str]]:
    text = value.strip()
    if not text:
        return None, []
    if text.endswith("时") and text[0] in HOUR_BRANCHES:
        branch = text[0]
        return (0 if branch == "子" else HOUR_BRANCHES.index(branch)), (["ziwei_named_rat_hour_ambiguous"] if branch == "子" else [])
    try:
        hour = int(text.split(":", 1)[0])
    except (ValueError, IndexError):
        return None, []
    if not 0 <= hour <= 23:
        return None, []
    return (12 if hour == 23 else (hour + 1) // 2), []
