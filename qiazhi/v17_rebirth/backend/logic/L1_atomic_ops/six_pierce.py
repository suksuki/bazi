"""六穿态：以比劫对正官的穿透量刻画结构耗散（脱水场信号）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "量化「穿」态下秩序被削弱的程度，提示需加确认链路的场景。"
PLUGIN_RATIONALE = "六穿为 L1 冲穿类原子算子，先于 L2 官印叙事给出硬损伤度。"


def run_six_pierce(*, source_abs: float, target_abs: float, penetration_ratio: float = 0.45) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(penetration_ratio or 0.0)))
    damage = min(src, tgt) * ratio
    return {"effect": "pierce", "abs_loss": round(damage, 4), "vector": "penetration"}


def _collect_rows(deity_scores: Dict[str, float]) -> List[dict]:
    peer = float(deity_scores.get("比肩", 0.0))
    officer = float(deity_scores.get("正官", 0.0))
    result = run_six_pierce(source_abs=peer, target_abs=officer, penetration_ratio=0.42)
    loss = float(result.get("abs_loss", 0.0))
    if loss < 3.0:
        return []
    return [
        {
            "plugin": "six_pierce",
            "fact": f"六穿态激活，结构穿透损耗约 {loss:.1f}。",
            "label": "关键动作加一层确认，压低冲动决策误差。",
            "priority": min(0.9, 0.5 + loss / 18.0),
        }
    ]


@dataclass
class SixPiercePlugin(V17PluginSpec):
    plugin_id: str = "six_pierce"
    causal_tier: int = 4
    registry_priority: float = 0.62

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = SixPiercePlugin()
