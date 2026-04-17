"""羊刃逢冲：刃支被冲 → 全局熵不稳定度注入（经流水线 metrics 汇总）。"""
from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping

from app.plugins.base_physics.core_operators.core_conflict_common import (
    STEM_YANG_BLADE_BRANCH,
    append_polarity_seed,
    branch_by_pillar,
    day_stem,
    pillars_dict,
    record_applied,
)
from app.plugins.base_physics.core_operators.op_interdimensional import branch_pillar_in_clash_or_punish

OP_ID = "L1_OP_BLADE_CLASH"
SKILL_ID = "l1_blade_clash_01"


def apply_op_blade_clash(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
    conflict_points: List[Any],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_CORE_CONFLICT_OPS_ENABLE", 1.0)) < 0.5:
        return []
    pillars = pillars_dict(metadata)
    ds = day_stem(pillars)
    blade = STEM_YANG_BLADE_BRANCH.get(ds, "")
    if not blade:
        return []
    branches = branch_by_pillar(pillars)
    hit_pillar = ""
    for pk, br in branches.items():
        if br == blade:
            hit_pillar = pk
            break
    if not hit_pillar or not conflict_points:
        return []
    if not branch_pillar_in_clash_or_punish(branch_pillar=hit_pillar, conflict_points=conflict_points):
        return []

    inst = max(0.0, min(1.5, float(settings.get("L1_BLADE_CLASH_INSTABILITY", 0.85))))
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        append_polarity_seed(meta, pattern="YANG_REN_FENG_CHONG", deity="劫财", delta_a=0.4, delta_b=-0.4, plugin_a=OP_ID)
        record_applied(meta, OP_ID)
        meta["l1_blade_clash_v1"] = {"blade_branch": blade, "pillar": hit_pillar, "instability_score": round(inst, 4)}

    return [
        {
            "plugin": "base.core_conflict.blade_clash",
            "edge": [hit_pillar, blade],
            "delta": {"instability_score": round(inst, 4), "blade_branch": blade},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
