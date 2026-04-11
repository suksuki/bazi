"""劫财见财：劫财与正财同柱或同透天干 → 正财 Abs 分配率损耗。"""
from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping, Set

from app.plugins.base_physics.core_operators.core_conflict_common import (
    append_polarity_seed,
    axis_abs,
    day_stem,
    pillar_deities,
    pillars_dict,
    record_applied,
    stem_by_pillar,
)
from app.skills.physics_rules import deity_from_self_and_target_stem

OP_ID = "L1_OP_ROBBER_WEALTH"
SKILL_ID = "l1_robber_wealth_01"


def apply_op_robber_wealth(
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
    pillars = pillars_dict(metadata)
    ds = day_stem(pillars)
    if not ds:
        return []

    per_pillar = pillar_deities(ds, pillars)
    same_pillar = any({"劫财", "正财"} <= (per_pillar.get(pk) or set()) for pk in per_pillar)

    stems = [str(stem_by_pillar(pillars).get(k) or "") for k in ("year", "month", "day", "hour")]
    stem_deities: Set[str] = set()
    for st in stems:
        if st:
            stem_deities.add(deity_from_self_and_target_stem(day_stem=ds, target_stem=st))
    co_stem = "劫财" in stem_deities and "正财" in stem_deities

    if not (same_pillar or co_stem):
        return []
    if axis_abs(axes, "正财") <= 1e-9:
        return []

    loss = max(0.0, min(0.85, float(settings.get("L1_ROBBER_WEALTH_ALLOC_LOSS", 0.18))))
    blk = axes.get("正财")
    if not isinstance(blk, dict):
        return []
    old = float(blk.get("absolute_energy") or 0.0)
    new_abs = round(max(0.0, old * (1.0 - loss)), 4)
    blk["absolute_energy"] = new_abs

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        append_polarity_seed(meta, pattern="JIE_JIAN_ZHENG_CAI", deity="正财", delta_a=0.3, delta_b=-0.3, plugin_a=OP_ID)
        record_applied(meta, OP_ID)
        meta["l1_robber_wealth_v1"] = {
            "alloc_loss": round(loss, 4),
            "same_pillar": same_pillar,
            "co_stem": co_stem,
            "正财_abs_before": round(old, 4),
        }

    total = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in axes if isinstance(axes.get(d), dict)) or 1.0
    for d, b in list(axes.items()):
        if isinstance(b, dict):
            ae = float(b.get("absolute_energy") or 0.0)
            b["relative_percentage"] = round(100.0 * ae / total, 2)

    return [
        {
            "plugin": "base.core_conflict.robber_wealth",
            "edge": ["劫财", "正财"],
            "delta": {"alloc_loss_ratio": round(loss, 4), "正财_abs_after": new_abs},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
