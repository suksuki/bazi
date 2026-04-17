"""五行相生流通审计：写入 physics_tensor.meta.energy_flow_audit（供 StreamBoard 因果链图）。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping

from app.core.config.physics_settings import resolve_physics_settings
from app.skills.physics_rules import ELEMENT_GENERATES

_CHAIN_ORDER = ("wood", "fire", "earth", "metal", "water")


def _normalized_vector(physics_tensor: Mapping[str, Any]) -> Dict[str, float]:
    n = physics_tensor.get("normalized")
    if isinstance(n, dict):
        out: Dict[str, float] = {}
        for k in _CHAIN_ORDER:
            try:
                out[k] = float(n.get(k, 0.0) or 0.0)
            except (TypeError, ValueError):
                out[k] = 0.0
        return out
    vec = physics_tensor.get("vector")
    if not isinstance(vec, dict):
        return {k: 0.0 for k in _CHAIN_ORDER}
    total = sum(float(vec.get(k, 0.0) or 0.0) for k in _CHAIN_ORDER)
    if total <= 0:
        return {k: 0.0 for k in _CHAIN_ORDER}
    return {k: round(float(vec.get(k, 0.0) or 0.0) / total, 6) for k in _CHAIN_ORDER}


def apply_energy_flow_audit(
    *,
    physics_tensor: MutableMapping[str, Any],
    physics_config: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """按 木→火→土→金→水→木 检测相邻相生段；两端 Abs（归一化场强）均大于阈值则为 FLOWING。"""
    settings = resolve_physics_settings(physics_config if isinstance(physics_config, dict) else None)
    threshold = max(1e-6, float(settings.get("FLOW_AUDITOR_ABS_THRESHOLD", 0.06)))
    nv = _normalized_vector(physics_tensor)
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    eff_raw = meta.get("l1_status_element_flow_efficiency") if isinstance(meta, dict) else None
    eff: Dict[str, float] = {}
    if isinstance(eff_raw, dict):
        for k in _CHAIN_ORDER:
            try:
                v = float(eff_raw.get(k, 1.0) or 1.0)
            except (TypeError, ValueError):
                v = 1.0
            eff[k] = max(0.05, min(2.5, v))
    else:
        eff = {k: 1.0 for k in _CHAIN_ORDER}
    segments: List[Dict[str, Any]] = []
    breaks: List[int] = []
    idx = 0
    for src in _CHAIN_ORDER:
        dst = ELEMENT_GENERATES.get(src, "")
        if not dst:
            continue
        a = float(nv.get(src, 0.0))
        b = float(nv.get(dst, 0.0))
        a_flow = a * eff.get(src, 1.0)
        b_flow = b * eff.get(dst, 1.0)
        flowing = a_flow > threshold and b_flow > threshold
        state = "FLOWING" if flowing else "BROKEN"
        seg = {
            "index": idx,
            "from": src,
            "to": dst,
            "from_abs": round(a, 6),
            "to_abs": round(b, 6),
            "from_abs_flow": round(a_flow, 6),
            "to_abs_flow": round(b_flow, 6),
            "flow_efficiency": {"from": round(eff.get(src, 1.0), 4), "to": round(eff.get(dst, 1.0), 4)},
            "threshold": round(threshold, 6),
            "state": state,
        }
        segments.append(seg)
        if not flowing:
            breaks.append(idx)
        idx += 1

    out = {
        "version": "flow_auditor.v1",
        "chain_order": list(_CHAIN_ORDER),
        "abs_threshold": round(threshold, 6),
        "status_flow_efficiency_applied": bool(eff_raw),
        "segments": segments,
        "break_indices": breaks,
        "break_count": len(breaks),
    }
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["energy_flow_audit"] = out
    return out
