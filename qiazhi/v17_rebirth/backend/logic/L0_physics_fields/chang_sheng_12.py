from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]

PLUGIN_SUMMARY = "将日主十神能量映射到长生十二宫阶段，给出节律型事实锚点。"
PLUGIN_RATIONALE = "先建立「气数阶段」叙事，再让 L2 格局与刑冲类算子在同一语义坐标下对齐。"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    total = sum(float(v or 0.0) for v in deity_scores.values())
    if total <= 0:
        return []
    strongest = max(deity_scores.items(), key=lambda kv: float(kv[1] or 0.0))
    stage_idx = int(abs(total + float(strongest[1]))) % 12
    stage = _STAGES[stage_idx]
    score = float(strongest[1] or 0.0)
    return [
        {
            "plugin": "chang_sheng_12",
            "fact": f"长生十二宫映射至「{stage}」位，主轴神 {strongest[0]} 强度 {score:.1f}。",
            "label": "按阶段推进：先完成当前位阶任务，再切换策略节拍。",
            "priority": min(0.88, 0.5 + score / 80.0),
        }
    ]


@dataclass
class ChangSheng12Plugin(V17PluginSpec):
    plugin_id: str = "chang_sheng_12"
    causal_tier: int = 5
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ChangSheng12Plugin()
