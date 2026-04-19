from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    infer_manifestation_state,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.configs.manager import get_plugin_config


def _energy_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    raw = physics_tensor.get("energy_meta")
    return raw if isinstance(raw, dict) else {}


def _top_two(scores: Dict[str, float]) -> List[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]


def _dominant_ratio(scores: Dict[str, float]) -> float:
    top2 = _top_two(scores)
    if len(top2) < 2:
        return 1.0
    return float(top2[0][1]) / max(float(top2[1][1]), 1.0)


def _projection_meta(physics_tensor: Dict[str, Any], base_god: str) -> Dict[str, Any]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    month_gz = str(four.get("month", "")).strip()
    daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
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


def _ziping_family_profile(scores: Dict[str, float], *, family: str) -> Dict[str, Any]:
    top_two = _top_two(scores)
    top_ratio = float(top_two[0][1] / max(top_two[1][1], 1.0)) if len(top_two) >= 2 else 1.0
    rows: List[Dict[str, Any]] = []
    if family == "ziping_balance":
        rows.append({"strength_ratio": top_ratio, "pillars": ["natal"]})
    if family == "ziping_month_command":
        rows.append({"pillars": ["natal", "flow"]})
    if family == "ziping_yongshen":
        rows.append({"pillars": ["natal"]})
    return {
        "rows": rows,
        "relation_family": family,
    }


def _ziping_interaction_meta(
    *,
    family: str,
    scores: Dict[str, float],
    top_god: str,
    interaction_layer: str = "branch",
) -> Dict[str, Any]:
    profile = _ziping_family_profile(scores=scores, family=family)
    top_two = _top_two(scores)
    ratio = float(top_two[0][1] / max(top_two[1][1], 1.0)) if len(top_two) >= 2 else 1.0
    return {
        "interaction_layer": detect_interaction_layer(
            {"interaction_layer": interaction_layer},
            relation_family=family,
            member_key="branches",
        ),
        "manifestation_state": infer_manifestation_state(
            rows=profile["rows"],
            relation_family=profile["relation_family"],
            member_set=[],
            origin_types=["natal"],
        ),
        "origin_type": "natal",
        "origin_multiplier": relation_origin_multiplier("natal"),
        "top_ratio": round(ratio, 3),
        "ziping_focus_god": top_god,
    }


ZIPING_DEFAULTS = {
    "classical.ziping.month_command.v1": {
        "MATCH_RATIO_TOP": 0.88,
        "MATCH_RATIO_OTHER": 0.72,
    },
    "classical.ziping.balance.v1": {
        "BALANCE_STRONG_RATIO": 1.8,
        "BALANCE_MODERATE_RATIO": 1.3,
        "MATCH_RATIO_MIN": 0.45,
        "MATCH_RATIO_GAIN": 0.22,
        "MATCH_RATIO_MAX": 0.9,
    },
    "classical.ziping.yongshen.v1": {
        "MATCH_RATIO_BASE": 0.58,
        "MATCH_RATIO_GAIN": 0.14,
        "MATCH_RATIO_MAX": 0.84,
    },
}


def _ziping_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    defaults = ZIPING_DEFAULTS.get(plugin_id, {})
    return float(cfg.get(key, defaults.get(key, fallback)))


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
        scores = deity_scores_from_tensor(physics_tensor)
        top2 = _top_two(scores)
        top_god = top2[0][0] if top2 else ""
        match_ratio_top = _ziping_cfg(self.plugin_id, "MATCH_RATIO_TOP", 0.88)
        match_ratio_other = _ziping_cfg(self.plugin_id, "MATCH_RATIO_OTHER", 0.72)
        match_ratio = match_ratio_top if top_god == god else match_ratio_other
        interaction_meta = _ziping_interaction_meta(
            family="ziping_month_command",
            scores=scores,
            top_god=top_god,
            interaction_layer="branch",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平月令法：月支{branch or '未知'}主气落在 {god}，本局应先以月令定旺衰、再论其余结构。",
                "priority": 0.83,
                "label": "月令定盘",
                "meta": {
                    "month_command_god": god,
                    "month_branch": branch,
                    "match_ratio": match_ratio,
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, god),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=god,
                        relation_family="ziping_month_command",
                        relation_members=[branch] if branch else [],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
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
        strong_ratio = _ziping_cfg(self.plugin_id, "BALANCE_STRONG_RATIO", 1.8)
        moderate_ratio = _ziping_cfg(self.plugin_id, "BALANCE_MODERATE_RATIO", 1.3)
        match_ratio_min = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MIN", 0.45)
        match_ratio_gain = _ziping_cfg(self.plugin_id, "MATCH_RATIO_GAIN", 0.22)
        match_ratio_max = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.9)
        if ratio >= strong_ratio:
            state = "偏枯偏势"
        elif ratio >= moderate_ratio:
            state = "偏旺有主轴"
        else:
            state = "相对均衡"
        match_ratio = min(
            match_ratio_max,
            max(
                match_ratio_min,
                0.48 + match_ratio_gain * min(1.0, max(0.0, ratio - 1.0)),
            ),
        )
        interaction_meta = _ziping_interaction_meta(
            family="ziping_balance",
            scores=scores,
            top_god=g1,
            interaction_layer="branch",
        )
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
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, g1),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=g1,
                        relation_family="ziping_balance",
                        relation_members=[],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
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
        ratio = _dominant_ratio(scores)
        if god in {"比肩", "劫财", "正印", "偏印"}:
            yong = "财官"
            reason = "比印偏重，宜以财官疏导与收束。"
        elif god in {"食神", "伤官", "正财", "偏财"}:
            yong = "印官"
            reason = "食伤财势外放，宜以印官节制并收口。"
        else:
            yong = "印比"
            reason = "官杀承压偏重，宜以印比承载与护身。"
        base = _ziping_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.58)
        gain = _ziping_cfg(self.plugin_id, "MATCH_RATIO_GAIN", 0.14)
        cap = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.84)
        interaction_meta = _ziping_interaction_meta(
            family="ziping_yongshen",
            scores=scores,
            top_god=god,
            interaction_layer="branch",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平用神建议：本局可优先观察「{yong}」线。{reason}",
                "priority": 0.8,
                "label": "用神先看",
                "meta": {
                    "yongshen_axis": yong,
                    "dominant_god": god,
                    "match_ratio": round(
                        min(cap, max(base, base + gain * min(1.0, max(0.0, ratio - 1.0)))),
                        3,
                    ),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, god),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=god,
                        relation_family="ziping_yongshen",
                        relation_members=[],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    ZiPingMonthCommandPlugin(),
    ZiPingBalancePlugin(),
    ZiPingYongShenPlugin(),
]
