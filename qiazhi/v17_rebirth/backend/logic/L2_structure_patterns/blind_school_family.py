from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
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


def _top_ratio(scores: Dict[str, float]) -> float:
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if len(ordered) < 2:
        return 1.0
    return float(ordered[0][1]) / max(float(ordered[1][1]), 1.0)


def _blind_match_ratio(iv2: Dict[str, Any], scores: Dict[str, float], *, base: float, cap: float) -> float:
    ratio = _top_ratio(scores)
    structure_boost = 0.0
    if iv2.get("liu_chong"):
        structure_boost = 0.07
    elif iv2.get("sanxing"):
        structure_boost = 0.05
    elif iv2.get("san_he") or iv2.get("ban_he"):
        structure_boost = 0.06
    dominance_boost = min(0.08, max(0.0, (ratio - 1.0) * 0.08))
    return round(min(cap, max(0.42, base + structure_boost + dominance_boost)), 3)


def _blind_origin_meta(iv2: Dict[str, Any]) -> Dict[str, float | str]:
    origin_types: List[str] = []
    if iv2.get("liu_chong"):
        origin_types.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    elif iv2.get("sanxing"):
        origin_types.extend(collect_origin_types_from_rows(iv2.get("sanxing") or [], member_key="branches"))
    elif iv2.get("san_he"):
        origin_types.extend(collect_origin_types_from_rows(iv2.get("san_he") or [], member_key="group"))
    elif iv2.get("ban_he"):
        origin_types.extend(collect_origin_types_from_rows(iv2.get("ban_he") or [], member_key="pair"))
    origin_type = choose_dominant_origin_type(origin_types)
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def _blind_projection_meta(physics_tensor: Dict[str, Any], base_god: str) -> Dict[str, Any]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
    month_gz = str(four.get("month", "")).strip()
    month_branch = month_gz[1] if len(month_gz) >= 2 else ""
    projection = god_cluster_projection(
        physics_tensor=physics_tensor,
        base_god=base_god,
        day_master=daymaster,
        focus_branches=[month_branch] if month_branch else [],
    )
    return {
        "target_god": base_god,
        "projection_share": round(float((projection or {}).get(base_god, 1.0)), 4),
        "cluster_projection": projection,
    }


@dataclass
class BlindWorkAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.work_axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        iv2 = _interaction_v2(physics_tensor)
        scores = deity_scores_from_tensor(physics_tensor)
        origin_meta = _blind_origin_meta(iv2)
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
                "meta": {
                    "blind_axis": axis,
                    **_blind_projection_meta(physics_tensor, _top_god(scores)),
                    "match_ratio": round(min(0.88, _blind_match_ratio(iv2, scores, base=0.68, cap=0.88) * max(0.9, float(origin_meta["origin_multiplier"]))), 3),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=_top_god(scores),
                        relation_family="blind_work_axis",
                        relation_members=[],
                    ),
                    **origin_meta,
                },
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
        origin_meta = _blind_origin_meta(iv2)
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
                "meta": {
                    "response_top_god": top,
                    **_blind_projection_meta(physics_tensor, top),
                    "match_ratio": round(min(0.8, _blind_match_ratio(iv2, scores, base=0.57, cap=0.8) * max(0.9, float(origin_meta["origin_multiplier"]))), 3),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top,
                        relation_family="blind_response_chain",
                        relation_members=[],
                    ),
                    **origin_meta,
                },
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
        origin_meta = _blind_origin_meta(iv2)
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
                "meta": {
                    "symbol_top_god": top,
                    "blind_symbol": symbol,
                    **_blind_projection_meta(physics_tensor, top),
                    "match_ratio": round(min(0.8, _blind_match_ratio(iv2, scores, base=0.58, cap=0.8) * max(0.9, float(origin_meta["origin_multiplier"]))), 3),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top,
                        relation_family="blind_symbol_trigger",
                        relation_members=[],
                    ),
                    **origin_meta,
                },
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
        origin_meta = _blind_origin_meta(iv2)
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
                "meta": {
                    "blind_phase": phase,
                    "timing_top_god": top,
                    **_blind_projection_meta(physics_tensor, top),
                    "match_ratio": round(min(0.75, _blind_match_ratio(iv2, scores, base=0.53, cap=0.75) * max(0.9, float(origin_meta["origin_multiplier"]))), 3),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top,
                        relation_family="blind_timing_window",
                        relation_members=[],
                    ),
                    **origin_meta,
                },
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
        origin_meta = _blind_origin_meta(iv2)
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
                "meta": {
                    "blind_summary_top_god": top,
                    "blind_route": route,
                    **_blind_projection_meta(physics_tensor, top),
                    "match_ratio": round(min(0.71, _blind_match_ratio(iv2, scores, base=0.49, cap=0.71) * max(0.9, float(origin_meta["origin_multiplier"]))), 3),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top,
                        relation_family="blind_summary",
                        relation_members=[],
                    ),
                    **origin_meta,
                },
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
