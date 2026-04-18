from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_sanxing",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支三刑硬结构冲突检测算法。",
    "Rationale": "量化三刑导致的「活性熵增」损耗。"
}

DECLARED_PARAMS = {
    "ENTROPY_LOSS": 0.12,          # 熵增损耗比例 (活性剥离)
    "PENALTY_PRIORITY": 0.93        # 事实输出优先级
}


def _pillar_branches(four: Dict[str, Any]) -> str:
    zs = ""
    for k in ("year", "month", "day", "hour"):
        p = str(four.get(k) or "")
        if len(p) >= 2:
            zs += p[1]
    return zs


@dataclass
class TripleBranchPenaltyPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_sanxing"
    causal_tier: int = 3
    registry_priority: float = 0.85

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        loss = float(cfg.get("ENTROPY_LOSS", DECLARED_PARAMS["ENTROPY_LOSS"]))
        prio = float(cfg.get("PENALTY_PRIORITY", DECLARED_PARAMS["PENALTY_PRIORITY"]))

        four = physics_tensor.get("four_pillars") if isinstance(physics_tensor, dict) else {}
        if not isinstance(four, dict):
            return []
        zs = _pillar_branches(four)
        if "寅" in zs and "巳" in zs and "申" in zs:
            return [
                V17Fact(
                    plugin_id=self.plugin_id,
                    text=f"三刑激发：{int(loss*100)}% 活跃能量转化为「物理张力」，该部分能级暂不可用。",
                    causal_tier=self.causal_tier,
                    priority=prio,
                    decision_hint="先守法度与契约边界，再谈突破；避免多线并行硬冲。",
                    meta={
                        "entropy_loss": loss,
                        "energy_state": "INACTIVE_STRESSED"
                    },
                )
            ]
        return []


PLUGIN = TripleBranchPenaltyPlugin()
