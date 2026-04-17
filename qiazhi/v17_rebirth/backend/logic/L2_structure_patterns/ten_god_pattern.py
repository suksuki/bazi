"""十神格局主轴判定（脱水版）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "在十神分分布上给出主轴格局标签，作为叙事与决策的标题锚。"
PLUGIN_RATIONALE = "格局为 L2 结构层总控，应在 L0 场与 L1 原子信号之后收敛命名。"


def judge_ten_god_pattern(deity_scores: Dict[str, float]) -> str:
    if not deity_scores:
        return "未定格"
    top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    name, score = top[0]
    if name == "正官" and score >= 40:
        return "正官格势强"
    if name in {"食神", "伤官"} and score >= 35:
        return "食伤外放格"
    if name in {"偏财", "正财"} and score >= 35:
        return "财星主导格"
    return f"{name}主轴格"


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    pattern = judge_ten_god_pattern(deity_scores)
    if pattern == "未定格":
        return []
    return [
        {
            "plugin": "ten_god_pattern",
            "fact": f"十神格局判定：{pattern}。",
            "label": "围绕主轴格局统一资源优先级，避免多线分散。",
            "priority": 0.78,
        }
    ]


@dataclass
class TenGodPatternPlugin(V17PluginSpec):
    plugin_id: str = "ten_god_pattern"
    causal_tier: int = 3
    registry_priority: float = 0.55

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = TenGodPatternPlugin()
