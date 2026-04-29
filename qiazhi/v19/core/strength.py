from __future__ import annotations

from typing import Any, Dict

from v19.core.chart import GENERATES


V19_STRENGTH_VERSION = "v19.core_strength.v1"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float) -> float:
    return round(_clamp01(value), 3)


def evaluate_strength(features: Dict[str, Any]) -> Dict[str, Any]:
    day_element = str((features.get("day_master") or {}).get("element") or "")
    element_weights = dict(features.get("element_weights") or {})
    ten_god_weights = dict(features.get("ten_god_weights") or {})
    supporting_element = ""
    for source, target in GENERATES.items():
        if target == day_element:
            supporting_element = source
            break
    same_score = float(element_weights.get(day_element, 0.0))
    support_score_raw = same_score + float(element_weights.get(supporting_element, 0.0)) * 0.72
    pressure_score_raw = (
        float(ten_god_weights.get("wealth", 0.0)) * 0.9
        + float(ten_god_weights.get("officer", 0.0)) * 0.86
        + float(ten_god_weights.get("output", 0.0)) * 0.62
    )
    denominator = max(0.1, support_score_raw + pressure_score_raw)
    support_score = _clamp01(support_score_raw / denominator)
    pressure_score = _clamp01(pressure_score_raw / denominator)
    tendency = "balanced"
    if support_score >= pressure_score + 0.18:
        tendency = "strong"
    elif pressure_score >= support_score + 0.18:
        tendency = "weak"
    max_ten_god = max([float(value) for value in ten_god_weights.values()] or [1.0])
    ten_god_strengths = {
        key: {"score": _round(float(value) / max(0.1, max_ten_god)), "raw_weight": round(float(value), 3)}
        for key, value in ten_god_weights.items()
    }
    return {
        "version": V19_STRENGTH_VERSION,
        "chart_id": features["chart_id"],
        "day_master_strength": {
            "support_score": round(support_score, 3),
            "pressure_score": round(pressure_score, 3),
            "tendency": tendency,
        },
        "ten_god_strengths": ten_god_strengths,
        "element_weights": {key: round(float(value), 3) for key, value in element_weights.items()},
        "guardrails": ["STRENGTH_IS_MODEL_OUTPUT", "NO_THEME_CONCLUSION", "NO_USER_OUTPUT"],
    }
