"""寅巳申三刑：依赖四柱地支（physics_tensor.four_pillars），用于层级碰撞实验。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "检测寅巳申三刑齐见时的结构摩擦与突发张力。"
PLUGIN_RATIONALE = "地支三刑为硬结构事件，应在十神格局标签之后给出独立风险事实。"


def _pillar_branches(four: Dict[str, Any]) -> str:
    zs = ""
    for k in ("year", "month", "day", "hour"):
        p = str(four.get(k) or "")
        if len(p) >= 2:
            zs += p[1]
    return zs


@dataclass
class TripleBranchPenaltyPlugin(V17PluginSpec):
    plugin_id: str = "triple_branch_penalty"
    causal_tier: int = 3
    registry_priority: float = 0.85

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        four = physics_tensor.get("four_pillars") if isinstance(physics_tensor, dict) else {}
        if not isinstance(four, dict):
            return []
        zs = _pillar_branches(four)
        if "寅" in zs and "巳" in zs and "申" in zs:
            tension = 0.92
            return [
                V17Fact(
                    plugin_id=self.plugin_id,
                    text="寅巳申三刑齐见，结构摩擦与突发张力显著抬升。",
                    causal_tier=self.causal_tier,
                    priority=0.93,
                    decision_hint="先守法度与契约边界，再谈突破；避免多线并行硬冲。",
                    meta={"physics_tension": tension},
                )
            ]
        return []


PLUGIN = TripleBranchPenaltyPlugin()
