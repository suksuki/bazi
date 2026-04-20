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
        return {
            "god_of_use": use_gods,
            "god_of_taboo": taboo_gods,
            "source": str(authority.get("source") or "").strip() or "god_ring_authority",
            "mode": str(authority.get("mode") or "").strip() or "authority",
            "confidence": float(authority.get("confidence") or 0.0),
        }

    ranked = [(str(name or "").strip(), float(score or 0.0)) for name, score in ranked_pairs if str(name or "").strip()]
    fallback_use = [name for name, _score in ranked[:2]]
    fallback_taboo = [name for name, _score in ranked[-2:]] if len(ranked) >= 2 else []
    return {
        "god_of_use": fallback_use,
        "god_of_taboo": fallback_taboo,
        "source": "score_proxy",
        "mode": "fallback_rank",
        "confidence": 0.0,
    }
