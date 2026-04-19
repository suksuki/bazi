from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts

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
    for hit in hits:
        pair = hit.get("pair") or []
        lab = "".join(pair) if pair else "六破"
        
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        target_br = pair[1] if len(pair) >= 2 else (pair[0] if pair else "")
        god = _branch_dominant_ten_god(target_br, dm) if target_br else "受损神"
        effective_loss = loss * (1.0 + _clamp(friction_coeff, 0.0, 1.0))
        impact = -_clamp(effective_loss, 0.02, 0.5)
        priority = min(0.92, 0.7 + 0.2 * _clamp(friction_coeff, 0.0, 1.0))
        match_ratio = _clamp(0.55 + _clamp(friction_coeff, 0.0, 1.0) * 0.35, 0.0, 1.0)

        rows.append({
            "plugin": "l1.physics.op_branch_liupo",
            "fact": f"检测到地支六破 [{lab}]：局部结构摩擦，{god} 能级产生 {int(abs(impact)*100)}% 损耗。",
            "priority": round(priority, 3),
            "meta": {
                "impact_ratio": round(impact, 2),
                "match_ratio": round(match_ratio, 3),
                "target_god": god,
                "friction_coeff": round(friction_coeff, 3),
                "break_loss": round(loss, 3),
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
