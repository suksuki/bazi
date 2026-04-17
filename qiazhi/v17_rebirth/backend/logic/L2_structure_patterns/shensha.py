"""神煞场：官印财合成「扰动/护持」热度指标。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "把传统神煞语义压缩为可排序的风险热度，供叙事层引用。"
PLUGIN_RATIONALE = "作为 L2 辅助标签，不取代刑冲合害，而提示边界与节奏校准。"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    officer = float(deity_scores.get("正官", 0.0))
    print_star = float(deity_scores.get("偏印", 0.0))
    wealth = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    shensha_heat = round((officer * 0.45 + print_star * 0.35 + wealth * 0.2) / 10.0, 3)
    if shensha_heat <= 1.2:
        return []
    return [
        {
            "plugin": "shensha",
            "fact": f"神煞场显化增强，护持/扰动强度 {shensha_heat:.2f}。",
            "label": "先校准边界与节奏，再决定扩张或防守。",
            "priority": min(0.95, 0.55 + shensha_heat / 5.0),
        }
    ]


@dataclass
class ShenshaPlugin(V17PluginSpec):
    plugin_id: str = "shensha"
    causal_tier: int = 3
    registry_priority: float = 0.52

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ShenshaPlugin()
