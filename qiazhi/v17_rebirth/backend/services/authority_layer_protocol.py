from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from v17_rebirth.backend.logic.configs.manager import get_v17_constants


def _cfg() -> Dict[str, Any]:
    return get_v17_constants().get("AUTHORITY_LAYER", {})


def _cfg_float(key: str, default: float) -> float:
    try:
        return float(_cfg().get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _cfg_bool(key: str, default: bool) -> bool:
    value = _cfg().get(key, default)
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text not in {"", "0", "false", "no", "off"}


def _clean_list(values: Iterable[Any] | None = None) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _normalize_score_map(raw: Mapping[str, Any] | None = None) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for god, value in (raw or {}).items():
        name = str(god or "").strip()
        if not name:
            continue
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        if abs(score) <= 0.0:
            continue
        out[name] = round(score, 4)
    return out


def clamp_soft_bias_map(
    *,
    hard_scores: Mapping[str, Any] | None = None,
    bias_map: Mapping[str, Any] | None = None,
    max_bias_ratio: float | None = None,
    soft_bias_floor: float | None = None,
) -> Dict[str, float]:
    hard = _normalize_score_map(hard_scores)
    raw_bias = _normalize_score_map(bias_map)
    ratio = float(max_bias_ratio if max_bias_ratio is not None else _cfg_float("MAX_BIAS_RATIO", 0.35))
    floor = float(soft_bias_floor if soft_bias_floor is not None else _cfg_float("SOFT_BIAS_FLOOR", 0.06))
    out: Dict[str, float] = {}
    for god, value in raw_bias.items():
        hard_score = abs(float(hard.get(god, 0.0)))
        limit = max(floor, hard_score * ratio)
        out[god] = round(min(value, limit), 4)
    return out


def preserve_hard_top(
    *,
    hard_scores: Mapping[str, Any] | None = None,
    ranked_gods: List[str] | None = None,
    override_forbidden: bool | None = None,
) -> List[str]:
    if not ranked_gods:
        return []
    if override_forbidden is None:
        override_forbidden = _cfg_bool("OVERRIDE_FORBIDDEN", True)
    if not override_forbidden:
        return list(ranked_gods)
    normalized = _normalize_score_map(hard_scores)
    if not normalized:
        return list(ranked_gods)
    hard_rank = sorted(normalized.items(), key=lambda item: item[1], reverse=True)
    hard_top = hard_rank[0][0]
    if hard_top in ranked_gods[:1]:
        return list(ranked_gods)
    reordered = [hard_top]
    reordered.extend(god for god in ranked_gods if god != hard_top)
    return reordered


def build_authority_layer_protocol(
    *,
    hard_constraint_source: Iterable[Any] | None = None,
    structure_enhancement_source: Iterable[Any] | None = None,
    soft_bias_source: Iterable[Any] | None = None,
    max_bias_ratio: float | None = None,
    override_forbidden: bool | None = None,
) -> Dict[str, Any]:
    resolved_ratio = float(max_bias_ratio if max_bias_ratio is not None else _cfg_float("MAX_BIAS_RATIO", 0.35))
    resolved_override = bool(
        override_forbidden if override_forbidden is not None else _cfg_bool("OVERRIDE_FORBIDDEN", True)
    )
    hard_sources = _clean_list(hard_constraint_source)
    structure_sources = _clean_list(structure_enhancement_source)
    soft_sources = _clean_list(soft_bias_source)
    return {
        "contract": "v17.authority.layer_protocol.v1",
        "authority_level": 1,
        "override_forbidden": resolved_override,
        "max_bias_ratio": round(resolved_ratio, 4),
        "hard_constraint_source": hard_sources,
        "structure_enhancement_source": structure_sources,
        "soft_bias_source": soft_sources,
        "summary": {
            "hard_constraint_count": len(hard_sources),
            "structure_enhancement_count": len(structure_sources),
            "soft_bias_count": len(soft_sources),
        },
    }
