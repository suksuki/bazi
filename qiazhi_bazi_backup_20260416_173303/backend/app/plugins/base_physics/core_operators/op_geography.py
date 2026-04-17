"""地理方位场：用户朝向对五行矢量与十神 Abs 的演示性补丁（参数化，不调硬编码比例）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, MutableMapping

from app.skills.physics_rules import STEM_TO_ELEMENT, TEN_DEITIES

OP_ID = "L1_OP_GEOGRAPHY"
SKILL_ID = "l1_geography_field_01"

# 任务书：仅南→火、北→水做 Abs 演示增益；其余方位可传但不改场（避免未规格化的副作用）。
_DIRECTION_BOOST_ELEMENT: Dict[str, str] = {
    "南": "fire",
    "北": "water",
}


def _parse_source_stem(source: str) -> str:
    m = re.search(r"\.stem:([甲乙丙丁戊己庚辛壬癸])", source or "")
    if m:
        return m.group(1)
    m2 = re.search(r"\.hidden:([甲乙丙丁戊己庚辛壬癸])", source or "")
    if m2:
        return m2.group(1)
    return ""


def _element_energy_share_for_deity(trace_map: Dict[str, Any], deity: str, element: str) -> float:
    block = trace_map.get(deity) or {}
    base = block.get("base_energy") if isinstance(block, dict) else None
    if not isinstance(base, dict):
        return 0.0
    rows = base.get("contribution_sources")
    if not isinstance(rows, list) or not rows:
        return 0.0
    total = 0.0
    hit = 0.0
    for item in rows:
        if not isinstance(item, dict):
            continue
        ce = float(item.get("contribution_energy") or 0.0)
        total += ce
        stem = _parse_source_stem(str(item.get("source") or ""))
        if stem and STEM_TO_ELEMENT.get(stem) == element:
            hit += ce
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, hit / total))


def _trace_map(physics_tensor: Mapping[str, Any]) -> Dict[str, Any]:
    td = physics_tensor.get("deity_trace_details")
    if isinstance(td, dict) and td:
        return td
    meta = physics_tensor.get("meta")
    if isinstance(meta, dict):
        inner = meta.get("deity_trace_details")
        if isinstance(inner, dict):
            return inner
    return {}


def apply_op_geography(
    *,
    physics_tensor: MutableMapping[str, Any],
    physics_config: Mapping[str, Any] | None,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_OP_GEOGRAPHY_ENABLE", 1.0)) < 0.5:
        return []
    cfg = dict(physics_config or {})
    direction = str(cfg.get("user_target_direction") or cfg.get("USER_TARGET_DIRECTION") or "").strip()
    element = _DIRECTION_BOOST_ELEMENT.get(direction)
    if not element:
        return []

    boost = max(0.0, min(1.0, float(settings.get("GEOG_DIRECTION_ABS_BOOST", 0.15))))
    factor = 1.0 + boost

    vec = physics_tensor.get("vector")
    if isinstance(vec, dict) and element in vec:
        try:
            vec[element] = float(vec[element] or 0.0) * factor
        except (TypeError, ValueError):
            pass

    total_v = sum(float(vec.get(k, 0.0) or 0.0) for k in ("wood", "fire", "earth", "metal", "water")) if isinstance(vec, dict) else 0.0
    if total_v > 0 and isinstance(vec, dict):
        norm = physics_tensor.get("normalized")
        if isinstance(norm, dict):
            for k in ("wood", "fire", "earth", "metal", "water"):
                norm[k] = round(float(vec.get(k, 0.0) or 0.0) / total_v, 4)

    axes = physics_tensor.get("deity_energy_axes")
    trace_map = _trace_map(physics_tensor)
    if isinstance(axes, dict) and trace_map:
        for deity in TEN_DEITIES:
            blk = axes.get(deity)
            if not isinstance(blk, dict):
                continue
            share = _element_energy_share_for_deity(trace_map, deity, element)
            if share <= 0:
                continue
            adj = 1.0 + boost * share
            try:
                blk["absolute_energy"] = round(float(blk.get("absolute_energy") or 0.0) * adj, 4)
            except (TypeError, ValueError):
                continue

        s_abs = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in TEN_DEITIES if isinstance(axes.get(d), dict))
        if s_abs > 0:
            scores: Dict[str, float] = {}
            for deity in TEN_DEITIES:
                blk = axes.get(deity)
                if not isinstance(blk, dict):
                    continue
                pct = round(float(blk.get("absolute_energy") or 0.0) / s_abs * 100.0, 2)
                blk["relative_percentage"] = pct
                scores[deity] = pct
            physics_tensor["deity_scores"] = scores

    if "abs_nodes" in physics_tensor:
        del physics_tensor["abs_nodes"]

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["geography_field_patch_v1"] = {
            "direction": direction,
            "element": element,
            "boost_ratio": round(boost, 4),
            "field_factor": round(factor, 4),
        }

    return [
        {
            "plugin": "base.core_conflict.geography",
            "edge": [direction, element],
            "delta": {"boost_ratio": round(boost, 4), "target_element": element},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
