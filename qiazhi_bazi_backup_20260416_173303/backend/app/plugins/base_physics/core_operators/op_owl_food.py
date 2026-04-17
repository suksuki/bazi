"""枭神夺食：偏印×食神 → 食神 Abs 生存阻尼（η 读 physics_settings）。"""
from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping

from app.plugins.base_physics.core_operators.core_conflict_common import (
    append_polarity_seed,
    axis_abs,
    record_applied,
)

OP_ID = "L1_OP_OWL_FOOD"
SKILL_ID = "l1_owl_food_01"


def apply_op_owl_food(
    *,
    physics_tensor: MutableMapping[str, Any],
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_CORE_CONFLICT_OPS_ENABLE", 1.0)) < 0.5:
        return []
    axes = physics_tensor.get("deity_energy_axes")
    if not isinstance(axes, dict):
        return []
    pi = axis_abs(axes, "偏印")
    sh = axis_abs(axes, "食神")
    if pi <= 1e-9 or sh <= 1e-9:
        return []

    damp = max(0.0, min(0.95, float(settings.get("L1_OWL_FOOD_DAMPING", 0.15))))
    blk = axes.get("食神")
    if not isinstance(blk, dict):
        return []
    old = float(blk.get("absolute_energy") or 0.0)
    new_abs = round(max(0.0, old * (1.0 - damp)), 4)
    blk["absolute_energy"] = new_abs

    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        append_polarity_seed(meta, pattern="XIAO_SHEN_DUO_SHI", deity="食神", delta_a=0.28, delta_b=-0.28, plugin_a=OP_ID)
        record_applied(meta, OP_ID)
        meta["l1_owl_food_v1"] = {"damping": round(damp, 4), "食神_abs_before": round(old, 4), "食神_abs_after": new_abs}

    total = sum(float((axes.get(d) or {}).get("absolute_energy") or 0.0) for d in axes if isinstance(axes.get(d), dict)) or 1.0
    for d, b in list(axes.items()):
        if isinstance(b, dict):
            ae = float(b.get("absolute_energy") or 0.0)
            b["relative_percentage"] = round(100.0 * ae / total, 2)

    return [
        {
            "plugin": "base.core_conflict.owl_food",
            "edge": ["偏印", "食神"],
            "delta": {"survival_dampen": round(damp, 4), "target_deity": "食神", "absolute_energy_after": new_abs},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
