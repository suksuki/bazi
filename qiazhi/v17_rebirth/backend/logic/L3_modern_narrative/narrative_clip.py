"""现代叙事夹片：流动性与风控提示（占位，可接 wealth_risk 脱水逻辑）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "把财星偏强转写为现金流与承诺节奏的显式对齐提示。"
PLUGIN_RATIONALE = "L3 面向现代决策语境，在物理与结构事实之后做「可执行」软着陆。"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    cai = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    if cai < 22:
        return []
    return [
        {
            "plugin": "narrative_clip",
            "fact": "财星信号偏强，现金流与承诺节奏需要显式对齐。",
            "label": "把资源承诺写入可验收里程碑，避免口头扩张。",
            "priority": 0.62,
            "conflict_level": 2,
        }
    ]


@dataclass
class NarrativeClipPlugin(V17PluginSpec):
    plugin_id: str = "narrative_clip"
    causal_tier: int = 2
    registry_priority: float = 0.48

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = NarrativeClipPlugin()
