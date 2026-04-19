from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    relation_effect_multiplier,
    summarize_stem_fusion_conditions,
)

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_stem_fusion",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "天干五合（化气/羁绊）动力学模型。",
    "Rationale": "量化天干合化过程中的能量转移与性质改变。"
}

DECLARED_PARAMS = {
    "TRANSFORM_EFFICIENCY": 0.85,    # 成功化气时的能量转化率
    "STUCK_DAMPING": 0.35           # 羁绊（合而不化）时的能量削减比例
}

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta", {})
    fusion_v1 = meta.get("stem_fusion_v1", {})
    cases = fusion_v1.get("cases", [])
    
    if not cases:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_stem_fusion")
    trans_eff = float(cfg.get("TRANSFORM_EFFICIENCY", DECLARED_PARAMS["TRANSFORM_EFFICIENCY"]))
    stuck_damp = float(cfg.get("STUCK_DAMPING", DECLARED_PARAMS["STUCK_DAMPING"]))

    rows = []
    for c in cases:
        mode = c.get("mode")
        stems = c.get("stems") or []
        lab = "".join(stems)
        condition = summarize_stem_fusion_conditions(c)
        
        # 简单处理：如果是羁绊，对参与的第一个天干对应的十神产生减速
        # 如果是化气，对化出五行对应的十神产生增益
        from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import ten_god_from_stems
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        if mode == "stuck":
            target_god = ten_god_from_stems(dm, stems[0]) if stems else "被合神"
            cond_mul = relation_effect_multiplier(condition["condition_state"])
            match_ratio = max(0.0, min(1.0, max(0.25, float(condition["branch_hua_ratio"] or 0.0) + 0.2) * cond_mul))
            rows.append({
                "plugin": "l1.physics.op_stem_fusion",
                "fact": f"天干羁绊 [{lab}]：能量处于僵持态，{target_god} 能级削减 {int(stuck_damp*100)}%（{condition['condition_trigger']}）。",
                "priority": 0.67,
                "meta": {
                    "target_god": target_god,
                    "match_ratio": round(match_ratio, 3),
                    "condition_state": condition["condition_state"],
                    "condition_trigger": condition["condition_trigger"],
                    "branch_hua_ratio": condition["branch_hua_ratio"],
                    "condition_multiplier": cond_mul,
                }
            })
        elif mode == "transformed":
            hua_el = c.get("hua_element")
            # 找到日主对应化出五行的十神名
            from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map
            g2e = _get_god_to_element_map(dm)
            target_god = next((g for g, e in g2e.items() if e == hua_el), "化气神")
            
            cond_mul = relation_effect_multiplier(condition["condition_state"])
            match_ratio = max(0.0, min(1.0, max(0.35, float(condition["branch_hua_ratio"] or 0.0) + (0.35 if condition["condition_state"] == "formed" else 0.0)) * max(cond_mul, 0.35)))
            meta = {
                "target_god": target_god,
                "match_ratio": round(match_ratio, 3),
                "condition_state": condition["condition_state"],
                "condition_trigger": condition["condition_trigger"],
                "branch_hua_ratio": condition["branch_hua_ratio"],
                "condition_multiplier": cond_mul,
            }
            if condition["condition_state"] == "formed":
                meta["impact_ratio"] = trans_eff * cond_mul
            rows.append({
                "plugin": "l1.physics.op_stem_fusion",
                "fact": f"天干化气 [{lab}→{hua_el}]：能量聚变成功，{target_god} 能级大幅提升（{condition['condition_trigger']}）。",
                "priority": 0.85,
                "meta": meta,
            })
            
    return rows

@dataclass
class StemFusionPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_stem_fusion"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = StemFusionPlugin()
