from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts

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

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    hits = iv2.get("liu_he", [])
    
    if not hits:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_branch_liuhe")
    gain = float(cfg.get("HARMONY_GAIN", DECLARED_PARAMS["HARMONY_GAIN"]))
    impact = gain - 1.0

    rows = []
    for hit in hits:
        pair = hit.get("pair") or []
        lab = "".join(pair) if pair else "六合"
        # 六合通常倾向于提升被化气/主气方的能级
        # 这里统一对参与地支的主十神进行增益
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        target_br = pair[0] if pair else ""
        god = _branch_dominant_ten_god(target_br, dm) if target_br else "协作神"

        rows.append({
            "plugin": "l1.physics.op_branch_liuhe",
            "fact": f"检测到地支六合 [{lab}]：资源稳定绑定，{god} 能级提升 {int(impact*100)}%。",
            "priority": 0.78,
            "meta": {
                "impact_ratio": round(impact, 2),
                "target_god": god
            }
        })
    return rows

@dataclass
class SixHarmonyPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liuhe"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = SixHarmonyPlugin()
