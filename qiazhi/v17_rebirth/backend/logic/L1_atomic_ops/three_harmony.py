"""三合协同：以十神分数量化「食伤生财」绑定强度（脱水场信号）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "检测三合/生克链上的资源绑定（食伤与财星协同）是否达到显著阈值。"
PLUGIN_RATIONALE = "三合为 L1 原子层「合」态入口，为 L2 资源格局与风险叙事提供结构性先验。"


def run_three_harmony(*, source_abs: float, target_abs: float, lock_ratio: float = 0.3) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(lock_ratio or 0.0)))
    locked = min(src, tgt) * ratio
    return {"effect": "combine", "abs_locked": round(locked, 4), "vector": "binding"}


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    food = float(deity_scores.get("食神", 0.0))
    wealth = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    result = run_three_harmony(source_abs=food, target_abs=wealth, lock_ratio=0.32)
    locked = float(result.get("abs_locked", 0.0))
    if locked < 4.0:
        return []
    return [
        {
            "plugin": "three_harmony",
            "fact": f"三合协同增强，资源绑定强度约 {locked:.1f}。",
            "label": "将执行节奏拆分为两段，先稳态验证再扩张。",
            "priority": min(0.95, 0.55 + locked / 20.0),
        }
    ]


@dataclass
class ThreeHarmonyPlugin(V17PluginSpec):
    plugin_id: str = "three_harmony"
    causal_tier: int = 4
    registry_priority: float = 0.68

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ThreeHarmonyPlugin()
