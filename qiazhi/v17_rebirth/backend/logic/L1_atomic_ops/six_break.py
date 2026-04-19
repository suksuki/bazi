from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    relation_effect_multiplier,
    summarize_relation_conditions,
)

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_liupo",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支六破（冲突态）动力学干扰算法。",
    "Rationale": "量化「破」关系导致的局部结构不稳与微小能量泄露。"
}

DECLARED_PARAMS = {
    "BREAK_LOSS": 0.08,             # 六破导致的局部损耗比例
    "FRICTION_COEFF": 0.25           # 摩擦干扰系数 (影响决策平滑度)
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    hits = iv2.get("liu_po", [])
    
    if not hits:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_branch_liupo")
    loss = float(cfg.get("BREAK_LOSS", DECLARED_PARAMS["BREAK_LOSS"]))
    friction_coeff = float(cfg.get("FRICTION_COEFF", DECLARED_PARAMS["FRICTION_COEFF"]))

    rows = []
    scores = physics_tensor.get("ten_gods_absolute", {})
    for hit in hits:
        pair = hit.get("pair") or []
        lab = "".join(pair) if pair else "六破"
        
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        target_br = pair[1] if len(pair) >= 2 else (pair[0] if pair else "")
        god = _branch_dominant_ten_god(target_br, dm) if target_br else "受损神"
        source_br = pair[0] if len(pair) >= 1 else target_br
        source_god = _branch_dominant_ten_god(source_br, dm) if source_br else god
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=god,
            day_master=dm,
            focus_branches=pair,
        )
        if projection:
            god = max(projection.items(), key=lambda item: item[1])[0]
        source_abs = float(scores.get(source_god, 0.0) or 0.0)
        target_abs = float(scores.get(god, 0.0) or 0.0)
        effective_loss = loss * (1.0 + _clamp(friction_coeff, 0.0, 1.0))
        impact = -_clamp(effective_loss, 0.02, 0.5)
        condition = summarize_relation_conditions(
            relation_family="liu_po",
            pair_or_group=[str(x) for x in pair],
            interaction_v2=iv2,
        )
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
        priority = min(0.92, 0.7 + 0.2 * _clamp(friction_coeff, 0.0, 1.0))
        balance_ratio = min(source_abs, target_abs) / max(max(source_abs, target_abs), 1.0)
        match_ratio = _clamp(
            (0.18 + effective_loss * 1.95 + _clamp(friction_coeff, 0.0, 1.0) * 0.14 + balance_ratio * 0.14)
            * max(0.55, cond_mul)
            * origin_mul,
            0.0,
            0.72,
        )

        rows.append({
            "plugin": "l1.physics.op_branch_liupo",
            "fact": f"检测到地支六破 [{lab}]：局部结构摩擦，{god} 能级产生 {int(abs(impact)*100)}% 损耗。",
            "priority": round(priority, 3),
            "meta": {
                "impact_ratio": round(impact, 2),
                "match_ratio": round(match_ratio, 3),
                "target_god": god,
                "projection_share": round(float((projection or {}).get(god, 1.0)), 4),
                "cluster_projection": projection,
                "friction_coeff": round(friction_coeff, 3),
                "break_loss": round(loss, 3),
                "balance_ratio": round(balance_ratio, 3),
                "condition_state": condition["condition_state"],
                "condition_blockers": list(condition["blockers"]),
                "condition_multiplier": round(cond_mul, 3),
                "origin_type": condition.get("origin_type"),
                "origin_multiplier": round(origin_mul, 3),
            }
        })
    return rows

@dataclass
class SixBreakPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liupo"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = SixBreakPlugin()
