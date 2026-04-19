from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_effect_multiplier,
    summarize_relation_conditions,
)

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_liuhe",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支六合稳定态协同算法。",
    "Rationale": "量化一对一地支吸引力导致的资源锁定与局部能级提升。"
}

DECLARED_PARAMS = {
    "HARMONY_GAIN": 1.15,          # 六合的基础增益倍率
    "STABILITY_WEIGHT": 0.85        # 六合状态的稳定性权重
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    hits = iv2.get("liu_he", [])
    
    if not hits:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_branch_liuhe")
    gain = float(cfg.get("HARMONY_GAIN", DECLARED_PARAMS["HARMONY_GAIN"]))
    stability_weight = float(cfg.get("STABILITY_WEIGHT", DECLARED_PARAMS["STABILITY_WEIGHT"]))

    rows = []
    scores = physics_tensor.get("ten_gods_absolute", {})
    for hit in hits:
        pair = hit.get("pair") or []
        lab = "".join(pair) if pair else "六合"
        condition = summarize_relation_conditions(
            relation_family="liuhe",
            pair_or_group=[str(x) for x in pair],
            interaction_v2=iv2,
        )
        # 六合通常倾向于提升被化气/主气方的能级
        # 这里统一对参与地支的主十神进行增益
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        target_br = pair[0] if pair else ""
        god = _branch_dominant_ten_god(target_br, dm) if target_br else "协作神"
        partner_br = pair[1] if len(pair) >= 2 else target_br
        partner_god = _branch_dominant_ten_god(partner_br, dm) if partner_br else god
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=god,
            day_master=dm,
            focus_branches=pair,
        )
        if projection:
            god = max(projection.items(), key=lambda item: item[1])[0]
        source_abs = float(scores.get(partner_god, 0.0) or 0.0)
        target_abs = float(scores.get(god, 0.0) or 0.0)
        locked_energy = round(min(source_abs, target_abs) * _clamp(stability_weight, 0.0, 1.0), 4)
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
        impact = (gain - 1.0) * _clamp(stability_weight, 0.3, 1.0) * cond_mul
        priority = min(0.94, 0.72 + 0.1 * _clamp(stability_weight, 0.0, 1.0))
        balance_ratio = min(source_abs, target_abs) / max(max(source_abs, target_abs), 1.0)
        stability_factor = _clamp(stability_weight, 0.0, 1.0)
        support_bonus = 0.06 if condition["condition_state"] == "supported" else 0.0
        match_ratio = _clamp(
            (0.24 + 0.3 * stability_factor + 0.24 * balance_ratio + (0.08 if len(pair) >= 2 else 0.0) + support_bonus)
            * max(0.55, cond_mul)
            * origin_mul,
            0.0,
            0.86,
        )

        meta = {
            "target_god": god,
            "projection_share": round(float((projection or {}).get(god, 1.0)), 4),
            "cluster_projection": projection,
            "stability_weight": round(stability_weight, 3),
            "match_ratio": round(match_ratio, 3),
            "locked_energy": locked_energy,
            "balance_ratio": round(balance_ratio, 3),
            "condition_state": condition["condition_state"],
            "condition_blockers": list(condition["blockers"]),
            "condition_multiplier": cond_mul,
            "origin_type": condition.get("origin_type"),
            "origin_multiplier": round(origin_mul, 3),
            "static_basis": build_static_basis(
                physics_tensor=physics_tensor,
                target_god=god,
                relation_family="liuhe",
                relation_members=pair,
            ),
        }
        if condition["condition_state"] == "supported":
            meta["impact_ratio"] = round(impact, 2)
        rows.append({
            "plugin": "l1.physics.op_branch_liuhe",
            "fact": f"检测到地支六合 [{lab}]：资源稳定绑定，{god} 能级提升 {int(impact*100)}%（{condition['condition_state']}）。",
            "priority": round(priority, 3),
            "meta": meta,
        })
    return rows

@dataclass
class SixHarmonyPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liuhe"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = SixHarmonyPlugin()
