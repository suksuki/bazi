from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_muku",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支墓库（辰戌丑未）门态算法。",
    "Rationale": "量化墓库对能量的收纳与释放效应。"
}

DECLARED_PARAMS = {
    "STORAGE_EFFICIENCY": 0.35,      # 墓库的能量收纳（锁定）比例
    "OPEN_GATE_BOOST": 1.50         # 开库（冲刑）时的瞬时能级爆发倍率
}

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    # 从 L0 探测结果中获取墓库地支
    branches = physics_tensor.get("four_pillars", {})
    br_list = [str(b) for b in branches.values() if b]
    muku_brs = [b for b in br_list if b in {"辰", "戌", "丑", "未"}]
    
    if not muku_brs:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_branch_muku")
    storage = float(cfg.get("STORAGE_EFFICIENCY", DECLARED_PARAMS["STORAGE_EFFICIENCY"]))

    rows = []
    for br in set(muku_brs):
        # 简单逻辑：墓库对主气十神产生能量收敛项
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        god = _branch_dominant_ten_god(br, dm)

        rows.append({
            "plugin": "l1.physics.op_branch_muku",
            "fact": f"地支【{br}】墓库位激活：对 {god} 产生能量收纳锁定效应 ({int(storage*100)}%)。",
            "priority": 0.73,
            "meta": {
                "impact_ratio": -storage, # 正值代表释放，负值代表回笼收纳
                "target_god": god,
                "muku_state": "CLOSED"
            }
        })
    return rows

@dataclass
class MukuGatePlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_muku"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = MukuGatePlugin()
