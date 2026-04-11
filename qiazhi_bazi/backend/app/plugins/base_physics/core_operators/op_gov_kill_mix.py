"""官杀混杂：正官与七杀同透天干 → 决策效率指标下调。"""
from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping, Set

from app.plugins.base_physics.core_operators.core_conflict_common import (
    append_polarity_seed,
    day_stem,
    pillars_dict,
    record_applied,
    stem_by_pillar,
)
from app.skills.physics_rules import deity_from_self_and_target_stem

OP_ID = "L1_OP_GOV_KILL_MIX"
SKILL_ID = "l1_gov_kill_mix_01"


def apply_op_gov_kill_mix(
    *,
    physics_tensor: MutableMapping[str, Any],
    metadata: Any,
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    if float(settings.get("L1_CORE_CONFLICT_OPS_ENABLE", 1.0)) < 0.5:
        return []
    pillars = pillars_dict(metadata)
    ds = day_stem(pillars)
    if not ds:
        return []
    stem_deities: Set[str] = set()
    for pk in ("year", "month", "day", "hour"):
        st = str(stem_by_pillar(pillars).get(pk) or "")
        if st:
            stem_deities.add(deity_from_self_and_target_stem(day_stem=ds, target_stem=st))
    if not ("正官" in stem_deities and "七杀" in stem_deities):
        return []

    ineff = max(0.0, min(0.95, float(settings.get("L1_GOV_KILL_EFFICIENCY_LOSS", 0.35))))
    eff_index = round(max(0.0, 1.0 - ineff), 4)
    meta = physics_tensor.setdefault("meta", {})
    if isinstance(meta, dict):
        append_polarity_seed(meta, pattern="GUAN_SHA_HUN_ZA", deity="正官", delta_a=0.25, delta_b=-0.25, plugin_a=OP_ID)
        record_applied(meta, OP_ID)
        meta["decision_efficiency_index"] = eff_index
        meta["l1_gov_kill_mix_v1"] = {"efficiency_loss": round(ineff, 4), "efficiency_index": eff_index}

    return [
        {
            "plugin": "base.core_conflict.gov_kill_mix",
            "edge": ["正官", "七杀"],
            "delta": {"decision_efficiency_index": eff_index, "efficiency_loss": round(ineff, 4)},
            "l1_operator_id": OP_ID,
            "l1_operator_ids": [OP_ID],
            "skill_ids": [SKILL_ID],
        }
    ]
