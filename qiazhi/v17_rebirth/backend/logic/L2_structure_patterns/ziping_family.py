from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _energy_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    raw = physics_tensor.get("energy_meta")
    return raw if isinstance(raw, dict) else {}


def _top_two(scores: Dict[str, float]) -> List[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]


@dataclass
class ZiPingMonthCommandPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.month_command.v1"
    causal_tier: int = 3
    registry_priority: float = 0.83

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        meta = _energy_meta(physics_tensor)
        god = str(meta.get("month_command_god") or "").strip()
        season = meta.get("season_power") if isinstance(meta.get("season_power"), dict) else {}
        branch = str(season.get("month_branch") or "").strip()
        if not god:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平月令法：月支{branch or '未知'}主气落在 {god}，本局应先以月令定旺衰、再论其余结构。",
                "priority": 0.83,
                "label": "月令定盘",
                "meta": {
                    "month_command_god": god,
                    "month_branch": branch,
                    "match_ratio": 0.88,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingBalancePlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.balance.v1"
    causal_tier: int = 3
    registry_priority: float = 0.82

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top2 = _top_two(scores)
        if len(top2) < 2:
            return []
        (g1, v1), (_g2, v2) = top2
        ratio = v1 / max(v2, 1.0)
        if ratio >= 1.8:
            state = "偏枯偏势"
        elif ratio >= 1.3:
            state = "偏旺有主轴"
        else:
            state = "相对均衡"
        match_ratio = min(1.0, max(0.0, (ratio - 1.0) / 1.2))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平旺衰平衡：当前呈「{state}」态，{g1} 为主导神。",
                "priority": 0.82,
                "label": "旺衰平衡",
                "meta": {
                    "balance_state": state,
                    "dominant_god": g1,
                    "dominant_ratio": round(ratio, 3),
                    "match_ratio": round(match_ratio, 3),
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingYongShenPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.yongshen.v1"
    causal_tier: int = 3
    registry_priority: float = 0.8

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_two(scores)
        if not top:
            return []
        god = top[0][0]
        if god in {"比肩", "劫财", "正印", "偏印"}:
            yong = "财官"
            reason = "比印偏重，宜以财官疏导与收束。"
        elif god in {"食神", "伤官", "正财", "偏财"}:
            yong = "印官"
            reason = "食伤财势外放，宜以印官节制并收口。"
        else:
            yong = "印比"
            reason = "官杀承压偏重，宜以印比承载与护身。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平用神建议：本局可优先观察「{yong}」线。{reason}",
                "priority": 0.8,
                "label": "用神先看",
                "meta": {
                    "yongshen_axis": yong,
                    "dominant_god": god,
                    "match_ratio": 0.76,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    ZiPingMonthCommandPlugin(),
    ZiPingBalancePlugin(),
    ZiPingYongShenPlugin(),
]
