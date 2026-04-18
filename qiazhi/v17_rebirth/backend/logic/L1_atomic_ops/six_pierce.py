from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_liuhai",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支六害（六穿）动力学损耗算法。",
    "Rationale": "量化「穿」态下秩序削弱，给出硬损伤度。"
}

DECLARED_PARAMS = {
    "PENETRATION_RATIO": 0.45,
    "CLASH_LOSS_RATIO": "ref(global.CLASH_LOSS_RATIO)"
}


def run_six_pierce(*, source_abs: float, target_abs: float, penetration_ratio: float = 0.45) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(penetration_ratio or 0.0)))
    damage = min(src, tgt) * ratio
    return {"effect": "pierce", "abs_loss": round(damage, 4), "vector": "penetration"}


def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    # V17.99：直接从 interaction_v2 几何事实中提取
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    
    # 合并六害(贯)与六破事件
    pierce_hits = iv2.get("liu_hai", []) + iv2.get("liu_po", [])
    
    if not pierce_hits:
        return []
    
    rows = []
    for hit in pierce_hits:
        pair = hit.get("pair") or []
        br_j = pair[1] if len(pair) >= 2 else ""
        
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        god_j = _branch_dominant_ten_god(br_j, dm) if br_j else "目标"

        rows.append({
            "plugin": "six_pierce",
            "fact": f"地支六穿激活 -> 目标 {god_j} 产生 12% 局部应力损耗。",
            "label": "关键动作加一层确认，压低冲动决策误差。",
            "priority": 0.92,
            "meta": {
                "impact_ratio": -0.12,
                "target_god": god_j,
                "shielding_status": "FAILED"
            }
        })
    return rows


@dataclass
class SixPiercePlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liuhai"
    causal_tier: int = 4
    registry_priority: float = 0.62

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = SixPiercePlugin()
