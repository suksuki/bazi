from __future__ import annotations

from typing import Any, Dict


def _clamp01(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return max(0.0, min(1.0, numeric))


def _manifestation_weight(state: str) -> float:
    normalized = str(state or "").strip().lower()
    if normalized == "manifested":
        return 1.0
    if normalized == "supported":
        return 0.84
    if normalized == "contested":
        return 0.58
    if normalized == "latent":
        return 0.42
    return 0.5


def _confidence_label(score: float) -> str:
    if score >= 0.82:
        return "高置信"
    if score >= 0.64:
        return "中高置信"
    if score >= 0.48:
        return "中置信"
    return "低置信"


def is_pattern_family_plugin(plugin_id: str, meta: Dict[str, Any] | None = None) -> bool:
    source_name = str(plugin_id or "").strip()
    info = meta if isinstance(meta, dict) else {}
    claim_type = str(info.get("claim_type") or "").strip().lower()
    entity_scope = str(info.get("entity_scope") or "").strip().lower()
    if entity_scope == "pattern":
        return True
    if claim_type.startswith("pattern_"):
        return True
    return source_name.startswith("classical.") or source_name == "ten_god_pattern"


def derive_pattern_confidence(
    *,
    plugin_id: str,
    meta: Dict[str, Any] | None,
    priority: float,
    salience_weight: float,
) -> Dict[str, Any]:
    info = dict(meta or {})
    if not is_pattern_family_plugin(plugin_id, info):
        return info

    match_ratio = _clamp01(info.get("match_ratio"), 0.5)
    origin_multiplier = max(0.0, min(1.25, float(info.get("origin_multiplier", 1.0) or 1.0)))
    origin_support = max(0.0, min(1.0, origin_multiplier / 1.1 if origin_multiplier > 0 else 0.0))
    manifestation_support = _manifestation_weight(str(info.get("manifestation_state") or ""))

    projection_share = _clamp01(info.get("projection_share"), 0.0)
    dominant_ratio = max(1.0, float(info.get("dominant_ratio", 1.0) or 1.0))
    dominant_support = max(0.0, min(1.0, (dominant_ratio - 1.0) / 1.5))
    profile_support = _clamp01(info.get("top_share", info.get("profile_share", 0.0)), 0.0)
    candidate_support = 1.0 if str(info.get("claim_type") or "").strip() == "pattern_candidate" else 0.8
    priority_support = _clamp01(priority, 0.5)
    salience_support = _clamp01(salience_weight, 0.5)

    score = (
        0.34 * match_ratio
        + 0.16 * origin_support
        + 0.16 * manifestation_support
        + 0.12 * max(projection_share, profile_support)
        + 0.10 * dominant_support
        + 0.06 * priority_support
        + 0.06 * salience_support
    ) * candidate_support
    score = max(0.0, min(0.96, score))

    info["pattern_confidence"] = round(score, 4)
    info["pattern_confidence_percent"] = round(score * 100.0, 1)
    info["pattern_confidence_label"] = _confidence_label(score)
    info["pattern_confidence_breakdown"] = {
        "match_ratio": round(match_ratio, 4),
        "origin_support": round(origin_support, 4),
        "manifestation_support": round(manifestation_support, 4),
        "projection_support": round(max(projection_share, profile_support), 4),
        "dominant_support": round(dominant_support, 4),
        "priority_support": round(priority_support, 4),
        "salience_support": round(salience_support, 4),
        "candidate_support": round(candidate_support, 4),
    }
    return info
