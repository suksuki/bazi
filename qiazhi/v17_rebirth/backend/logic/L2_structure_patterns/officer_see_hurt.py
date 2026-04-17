"""伤官见官结构张力（脱水版）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "检测正官与伤官同时偏强时的秩序—表达摩擦。"
PLUGIN_RATIONALE = "典型「做功」冲突对，为 Inbox 提供高优先级话术闸口。"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    officer = float(deity_scores.get("正官", 0.0))
    hurting = float(deity_scores.get("伤官", 0.0))
    if officer < 20 or hurting < 16:
        return []
    return [
        {
            "plugin": "officer_see_hurt",
            "fact": "伤官见官触发张力，表达与秩序存在摩擦。",
            "label": "先统一沟通口径，再推进外部谈判动作。",
            "priority": 0.9,
            "conflict_level": 4,
        }
    ]


@dataclass
class OfficerSeeHurtPlugin(V17PluginSpec):
    plugin_id: str = "officer_see_hurt"
    causal_tier: int = 3
    registry_priority: float = 0.88

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = OfficerSeeHurtPlugin()
