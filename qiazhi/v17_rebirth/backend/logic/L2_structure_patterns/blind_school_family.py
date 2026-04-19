from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _interaction_v2(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2")
    return iv2 if isinstance(iv2, dict) else {}


def _top_god(scores: Dict[str, float]) -> str:
    if not scores:
        return ""
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[0][0]


@dataclass
class BlindWorkAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.work_axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        iv2 = _interaction_v2(physics_tensor)
        axis = ""
        detail = ""
        if iv2.get("liu_chong"):
            axis = "冲应"
            detail = "先看冲起之事，事件多由外部撞击显形。"
        elif iv2.get("sanxing"):
            axis = "刑压"
            detail = "先看内压与摩擦，做功重在硬结构消耗。"
        elif iv2.get("san_he") or iv2.get("ban_he"):
            axis = "合势"
            detail = "先看合局成势，做功重在资源如何被绑定与放大。"
        else:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派做功主轴：本局宜以「{axis}」为先。{detail}",
                "priority": 0.79,
                "label": "做功主轴",
                "meta": {"blind_axis": axis, "match_ratio": 0.84},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class BlindResponseChainPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.response_chain.v1"
    causal_tier: int = 3
    registry_priority: float = 0.78

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_god(scores)
        if not top:
            return []
        iv2 = _interaction_v2(physics_tensor)
        if iv2.get("liu_chong"):
            line = f"{top} 被外力引发，宜先论近应、突发与触发点。"
        elif iv2.get("san_he") or iv2.get("ban_he"):
            line = f"{top} 被合局牵动，宜先论联动、结盟与资源归并。"
        elif iv2.get("sanxing"):
            line = f"{top} 受刑压牵制，宜先论阻滞、卡点与代价。"
        else:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派应链提示：{line}",
                "priority": 0.78,
                "label": "应链判断",
                "meta": {"response_top_god": top, "match_ratio": 0.78},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class BlindSymbolTriggerPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.symbol_trigger.v1"
    causal_tier: int = 3
    registry_priority: float = 0.76

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_god(scores)
        if not top:
            return []
        iv2 = _interaction_v2(physics_tensor)
        if iv2.get("liu_chong"):
            symbol = "动象先起"
        elif iv2.get("san_he") or iv2.get("ban_he"):
            symbol = "成局成势"
        elif iv2.get("sanxing"):
            symbol = "压象先显"
        else:
            symbol = "主轴浮现"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派触发象：{top} 当前呈现「{symbol}」语义，可作为快速断事入口。",
                "priority": 0.76,
                "label": "触发象",
                "meta": {"symbol_top_god": top, "blind_symbol": symbol, "match_ratio": 0.74},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class BlindTimingWindowPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.timing_window.v1"
    causal_tier: int = 3
    registry_priority: float = 0.75

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        iv2 = _interaction_v2(physics_tensor)
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_god(scores)
        if iv2.get("liu_chong"):
            phase = "近应"
            detail = "冲象已起，优先观察突发触发点与短周期兑现。"
        elif iv2.get("sanxing"):
            phase = "迟应"
            detail = "刑压偏重，事件多经积压后显形，宜防拖延与反复。"
        elif iv2.get("san_he") or iv2.get("ban_he"):
            phase = "联应"
            detail = "合势成局，事件常借助关系链与资源链逐步兑现。"
        else:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派应期窗：当前以「{phase}」为主。{detail}",
                "priority": 0.75,
                "label": "应期窗口",
                "meta": {"blind_phase": phase, "timing_top_god": top, "match_ratio": 0.73},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class BlindSummaryPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.summary.v1"
    causal_tier: int = 3
    registry_priority: float = 0.74

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_god(scores)
        if not top:
            return []
        iv2 = _interaction_v2(physics_tensor)
        if iv2.get("liu_chong"):
            route = "冲起事，由主神承压见应。"
        elif iv2.get("sanxing"):
            route = "刑成压，由主神背负结构代价。"
        elif iv2.get("san_he") or iv2.get("ban_he"):
            route = "合成势，由主神牵动资源归并。"
        else:
            route = "主神浮现，可先以象定事。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派断口收束：以 {top} 为断口，{route}",
                "priority": 0.74,
                "label": "断口收束",
                "meta": {"blind_summary_top_god": top, "blind_route": route, "match_ratio": 0.72},
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    BlindWorkAxisPlugin(),
    BlindResponseChainPlugin(),
    BlindSymbolTriggerPlugin(),
    BlindTimingWindowPlugin(),
    BlindSummaryPlugin(),
]
