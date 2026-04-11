"""财星破印：财印同存且无透干官杀通关 → 印 Abs 防御坍缩；并写入路由偏置供 CausalRouter。"""
from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping

from app.plugins.base_physics.core_operators.core_conflict_common import (
    append_polarity_seed,
    axis_abs,
    pillars_dict,
    record_applied,
    stems_have_official_kill_between,
    stem_by_pillar,
    day_stem,
    ordered_stems_for_pass,
)
from app.skills.physics_rules import deity_from_self_and_target_stem

OP_ID = "L1_OP_WEALTH_SEAL"
SKILL_ID = "l1_wealth_seal_01"


def apply_op_wealth_seal(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_CORE_CONFLICT_OPS_ENABLE", 1.0)) < 0.5:
        return []
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict):
        return []
    cai_max = max(axis_abs(axes, "正财"), axis_abs(axes, "偏财"))
    yin_max = max(axis_abs(axes, "正印"), axis_abs(axes, "偏印"))
    if cai_max <= 1e-9 or yin_max <= 1e-9:
        return []

    pillars = pillars_dict(metadata)
    ds = day_stem(pillars)
    if not ds:
        return []
    stems = ordered_stems_for_pass(pillars)
    cai_idx: set[int] = set()
    yin_idx: set[int] = set()
    for i, pk in enumerate(("year", "month", "day", "hour")):
        st = str(stem_by_pillar(pillars).get(pk) or "")
        if not st:
            continue
        dv = deity_from_self_and_target_stem(day_stem=ds, target_stem=st)
        if dv in ("正财", "偏财"):
            cai_idx.add(i)
        if dv in ("正印", "偏印"):
            yin_idx.add(i)
    if stems_have_official_kill_between(stems, day_stem=ds, cai_indices=cai_idx, yin_indices=yin_idx):
        return []

    collapse = max(0.0, min(0.9, float(settings.get("L1_WEALTH_SEAL_COLLAPSE", 0.22))))
    factor = max(0.05, 1.0 - collapse)
    touched: List[str] = []
    for y in ("正印", "偏印"):
        blk = axes.get(y)
        if not isinstance(blk, dict):
            continue
        old = float(blk.get("absolute_energy") or 0.0)
        if old <= 1e-9:
            continue
        blk["absolute_energy"] = round(old * factor, 4)
        touched.append(y)

    if not touched:
        return []

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        d_cai = "正财" if axis_abs(axes, "正财") >= axis_abs(axes, "偏财") else "偏财"
        d_yin = "正印" if axis_abs(axes, "正印") >= axis_abs(axes, "偏印") else "偏印"
        append_polarity_seed(meta, pattern="CAI_XING_PO_YIN", deity=d_yin, delta_a=0.32, delta_b=-0.32, plugin_a=OP_ID)
        record_applied(meta, OP_ID)
        meta["l1_wealth_seal_v1"] = {"collapse_ratio": round(collapse, 4), "deities_scaled": touched}
        meta["wealth_seal_routing"] = {
            "yin_factor": float(settings.get("L1_WEALTH_SEAL_ROUTING_YIN_FACTOR", 0.82)),
            "cai_factor": float(settings.get("L1_WEALTH_SEAL_ROUTING_CAI_FACTOR", 1.08)),
        }

    total = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in axes if isinstance(axes.get(d), dict)) or 1.0
    for d, b in list(axes.items()):
        if isinstance(b, dict):
            ae = float(b.get("absolute_energy") or 0.0)
            b["relative_percentage"] = round(100.0 * ae / total, 2)

    return [
        {
            "plugin": "base.core_conflict.wealth_seal",
            "edge": ["财星", "印星"],
            "delta": {"seal_collapse": round(collapse, 4), "scaled_deities": touched},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
