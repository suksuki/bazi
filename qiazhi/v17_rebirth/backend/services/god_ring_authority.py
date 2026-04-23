from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


def _clean_gods(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        god = str(value or "").strip()
        if not god or god in seen:
            continue
        seen.add(god)
        out.append(god)
    return out


def resolve_god_ring_authority(
    raw_physics: Dict[str, Any],
    ranked_pairs: Iterable[Tuple[str, float]],
) -> Dict[str, Any]:
    pt = raw_physics if isinstance(raw_physics, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}

    use_gods = _clean_gods(authority.get("use_gods"))
    taboo_gods = _clean_gods(authority.get("taboo_gods"))
    if use_gods or taboo_gods:
        effect_scores = authority.get("effect_scores") if isinstance(authority.get("effect_scores"), dict) else {}
        graph_meta = authority.get("core_graph_meta") if isinstance(authority.get("core_graph_meta"), dict) else {}
        flux_meta = authority.get("core_flux_meta") if isinstance(authority.get("core_flux_meta"), dict) else {}
        tongguan_gods = _clean_gods(authority.get("tongguan_gods"))
        return {
            "god_of_use": use_gods,
            "god_of_taboo": taboo_gods,
            "tongguan_gods": tongguan_gods,
            "source": str(authority.get("source") or "").strip() or "god_ring_authority",
            "mode": str(authority.get("mode") or "").strip() or "authority",
            "confidence": float(authority.get("confidence") or 0.0),
            "display_mode": "authority",
            "label_of_use": "USE",
            "label_of_taboo": "TABOO",
            "dual_role_candidates": list(authority.get("dual_role_candidates") or []),
            "core_use_candidates": list(authority.get("core_use_candidates") or []),
            "core_taboo_candidates": list(authority.get("core_taboo_candidates") or []),
            "effect_scores": effect_scores,
            "core_graph_meta": graph_meta,
            "core_flux_meta": flux_meta,
            "core_path_count": int(authority.get("core_path_count") or 0),
            "core_paths_preview": list(authority.get("core_paths_preview") or []),
            "positive_work": dict(authority.get("positive_work") or {}),
            "negative_work": dict(authority.get("negative_work") or {}),
            "stage_bias": dict(authority.get("stage_bias") or {}),
            "judgement_bias": dict(authority.get("judgement_bias") or {}),
            "judgement_bias_entries": list(authority.get("judgement_bias_entries") or []),
            "judgement_bias_protocol": dict(authority.get("judgement_bias_protocol") or {}),
            "blind_theme": dict(authority.get("blind_theme") or {}),
            "blind_bias": dict(authority.get("blind_bias") or {}),
            "blind_bias_protocol": dict(authority.get("blind_bias_protocol") or {}),
            "authority_layer_protocol": dict(authority.get("authority_layer_protocol") or {}),
            "climate_modifier_layer": dict(authority.get("climate_modifier_layer") or {}),
            "stage_bias_protocol": dict(authority.get("stage_bias_protocol") or {}),
        }

    ranked = [(str(name or "").strip(), float(score or 0.0)) for name, score in ranked_pairs if str(name or "").strip()]
    fallback_use = [name for name, _score in ranked[:2]]
    fallback_taboo = [name for name, _score in ranked[-2:]] if len(ranked) >= 2 else []
    return {
        "god_of_use": fallback_use,
        "god_of_taboo": fallback_taboo,
        "tongguan_gods": [],
        "source": "score_proxy",
        "mode": "fallback_rank",
        "confidence": 0.0,
        "display_mode": "rank_proxy",
        "label_of_use": "主导",
        "label_of_taboo": "弱势",
        "dual_role_candidates": [],
        "core_use_candidates": [],
        "core_taboo_candidates": [],
        "effect_scores": {},
        "core_graph_meta": {},
        "core_flux_meta": {},
        "core_path_count": 0,
        "core_paths_preview": [],
        "positive_work": {},
        "negative_work": {},
        "stage_bias": {},
        "judgement_bias": {},
        "judgement_bias_entries": [],
        "judgement_bias_protocol": {},
        "blind_theme": {},
        "blind_bias": {},
        "blind_bias_protocol": {},
        "authority_layer_protocol": {},
        "climate_modifier_layer": {},
        "stage_bias_protocol": {},
    }
