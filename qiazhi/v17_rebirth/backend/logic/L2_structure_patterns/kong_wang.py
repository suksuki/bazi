"""空亡：比劫相对正官的「空转比」超阈时触发。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "刻画承诺与执行之间的落空风险，提示回执与验收。"
PLUGIN_RATIONALE = "空亡属结构摩擦中的信息态，在官印链条偏脆时与六穿、三刑形成互补事实。"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    peer = float(deity_scores.get("比肩", 0.0))
    rob = float(deity_scores.get("劫财", 0.0))
    officer = float(deity_scores.get("正官", 0.0))
    void_ratio = round((peer + rob + 1.0) / (officer + 6.0), 3)
    if void_ratio < 0.75:
        return []
    return [
        {
            "plugin": "kong_wang",
            "fact": f"空亡波动抬升，信号空转比约 {void_ratio:.2f}。",
            "label": "高风险动作加一层回执确认，避免信息落空。",
            "priority": min(0.9, 0.58 + void_ratio / 4.0),
        }
    ]


@dataclass
class KongWangPlugin(V17PluginSpec):
    plugin_id: str = "kong_wang"
    causal_tier: int = 3
    registry_priority: float = 0.58

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = KongWangPlugin()
