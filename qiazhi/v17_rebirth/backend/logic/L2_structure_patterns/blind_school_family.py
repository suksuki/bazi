from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import (
    build_blind_bias_protocol,
    resolve_blind_theme,
)
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


BLIND_MATCH_DEFAULTS = {
    "classical.blind.work_axis.v1": {
        "MATCH_RATIO_BASE": 0.68,
        "MATCH_RATIO_CAP": 0.88,
    },
    "classical.blind.response_chain.v1": {
        "MATCH_RATIO_BASE": 0.57,
        "MATCH_RATIO_CAP": 0.80,
    },
    "classical.blind.symbol_trigger.v1": {
        "MATCH_RATIO_BASE": 0.58,
        "MATCH_RATIO_CAP": 0.80,
    },
    "classical.blind.timing_window.v1": {
        "MATCH_RATIO_BASE": 0.53,
        "MATCH_RATIO_CAP": 0.75,
    },
    "classical.blind.summary.v1": {
        "MATCH_RATIO_BASE": 0.49,
        "MATCH_RATIO_CAP": 0.71,
    },
}

_BODY_MODE_LABELS = {
    "single_body": "单体稳轴",
    "dual_body": "双体并行",
    "disturbed_body": "扰体未换体",
    "shifted_body": "主线抢权",
}


def _plugin_match_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    defaults = BLIND_MATCH_DEFAULTS.get(plugin_id, {})
    return float(cfg.get(key, defaults.get(key, fallback)))


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


def _route_label(theme: Dict[str, Any]) -> str:
    return str(theme.get("primary_route") or "").strip() or "未定主线"


def _body_mode_label(theme: Dict[str, Any]) -> str:
    raw = str(theme.get("body_mode") or "").strip()
    return _BODY_MODE_LABELS.get(raw, raw or "未定体态")


def _inside_outside(theme: Dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    house_roles = theme.get("house_roles") if isinstance(theme.get("house_roles"), dict) else {}
    inside = [god for god, role in house_roles.items() if str(role).strip() == "inside"]
    outside = [god for god, role in house_roles.items() if str(role).strip() == "outside"]
    bridge = [god for god, role in house_roles.items() if str(role).strip() == "bridge"]
    return inside, outside, bridge


def _match_ratio(analysis: Dict[str, Any], *, base: float, cap: float) -> float:
    theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
    confidence = float(theme.get("confidence") or 0.0)
    hint = float(analysis.get("match_ratio_hint") or 0.42)
    origin_multiplier = relation_origin_multiplier(str(analysis.get("origin_type") or "natal"))
    ratio = max(base, hint * 0.62 + confidence * 0.28 + base * 0.18)
    ratio *= max(0.9, float(origin_multiplier))
    return round(min(cap, max(0.42, ratio)), 3)


def _common_meta(
    *,
    physics_tensor: Dict[str, Any],
    analysis: Dict[str, Any],
    relation_family: str,
    match_ratio: float,
) -> Dict[str, Any]:
    theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
    blind_bias_protocol = build_blind_bias_protocol(theme)
    target_god = str(analysis.get("target_god") or theme.get("target_god") or "").strip()
    return {
        "observe_only": True,
        "claim_type": "pattern_observation",
        "entity_scope": "pattern",
        "exclusivity_key": "blind_family",
        "source_event": "blind_theme",
        "blind_theme": theme,
        "blind_primary_route": _route_label(theme),
        "blind_body_mode": str(theme.get("body_mode") or "").strip(),
        "blind_relation_families": list(theme.get("relation_families") or []),
        "blind_runtime_switches": list(theme.get("runtime_switches") or []),
        "blind_narrative_focus": list(theme.get("narrative_focus") or []),
        "blind_bias_protocol": blind_bias_protocol,
        "match_ratio": match_ratio,
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god=target_god,
            relation_family=relation_family,
            relation_members=list(theme.get("relation_families") or []),
        ),
        "interaction_layer": str(analysis.get("interaction_layer") or "unknown"),
        "manifestation_state": str(analysis.get("manifestation_state") or "latent"),
        "origin_type": str(analysis.get("origin_type") or "natal"),
        "origin_multiplier": relation_origin_multiplier(str(analysis.get("origin_type") or "natal")),
        **_blind_projection_meta(physics_tensor, target_god),
    }


def _blind_analysis(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_blind_theme(physics_tensor)


@dataclass
class BlindWorkAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.blind.work_axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _blind_analysis(physics_tensor)
        theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
        if not theme:
            return []
        match_ratio = _match_ratio(
            analysis,
            base=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.68),
            cap=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.88),
        )
        inside, outside, bridge = _inside_outside(theme)
        detail_parts = [f"当前以「{_route_label(theme)}」为体", f"体态「{_body_mode_label(theme)}」"]
        if outside:
            detail_parts.append("家外" + "/".join(outside[:2]))
        if inside:
            detail_parts.append("家里" + "/".join(inside[:2]))
        if bridge:
            detail_parts.append("桥位" + "/".join(bridge[:1]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "盲派做功主轴：" + "；".join(detail_parts) + "。",
                "priority": 0.79,
                "label": "做功主轴",
                "meta": {
                    "blind_axis": _route_label(theme),
                    **_common_meta(
                        physics_tensor=physics_tensor,
                        analysis=analysis,
                        relation_family="blind_work_axis",
                        match_ratio=match_ratio,
                    ),
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
        analysis = _blind_analysis(physics_tensor)
        theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
        if not theme:
            return []
        match_ratio = _match_ratio(
            analysis,
            base=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.57),
            cap=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.80),
        )
        inside, outside, bridge = _inside_outside(theme)
        use_candidates = [str(item).strip() for item in theme.get("use_candidates") or [] if str(item).strip()]
        taboo_candidates = [str(item).strip() for item in theme.get("taboo_candidates") or [] if str(item).strip()]
        line_parts: List[str] = []
        if outside:
            line_parts.append("家外" + "/".join(outside[:2]))
        if bridge:
            line_parts.append("经由" + "/".join(bridge[:1]))
        if inside:
            line_parts.append("进入家里" + "/".join(inside[:2]))
        if use_candidates:
            line_parts.append("用侧" + "/".join(use_candidates[:2]))
        if taboo_candidates:
            line_parts.append("忌侧" + "/".join(taboo_candidates[:2]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "盲派应链提示：" + "；".join(line_parts or [theme.get("prompt_digest") or "主线做功待展开"]) + "。",
                "priority": 0.78,
                "label": "应链判断",
                "meta": {
                    "response_top_god": str(analysis.get("target_god") or ""),
                    **_common_meta(
                        physics_tensor=physics_tensor,
                        analysis=analysis,
                        relation_family="blind_response_chain",
                        match_ratio=match_ratio,
                    ),
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
        analysis = _blind_analysis(physics_tensor)
        theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
        if not theme:
            return []
        match_ratio = _match_ratio(
            analysis,
            base=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.58),
            cap=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.80),
        )
        families = [str(item).strip() for item in theme.get("relation_families") or [] if str(item).strip()]
        body_mode = str(theme.get("body_mode") or "").strip()
        if body_mode == "shifted_body":
            symbol = "主线抢权"
        elif body_mode == "disturbed_body" and "liu_chong" in families:
            symbol = "冲动起应"
        elif body_mode == "dual_body":
            symbol = "双体并行"
        elif any(f in families for f in ("san_he", "liuhe", "ban_he", "anhe")):
            symbol = "合势成像"
        elif "sanxing" in families:
            symbol = "刑压显形"
        else:
            symbol = "主轴浮现"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派触发象：当前呈现「{symbol}」，断口落在 {_route_label(theme)}。",
                "priority": 0.76,
                "label": "触发象",
                "meta": {
                    "symbol_top_god": str(analysis.get("target_god") or ""),
                    "blind_symbol": symbol,
                    **_common_meta(
                        physics_tensor=physics_tensor,
                        analysis=analysis,
                        relation_family="blind_symbol_trigger",
                        match_ratio=match_ratio,
                    ),
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
        analysis = _blind_analysis(physics_tensor)
        theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
        if not theme:
            return []
        match_ratio = _match_ratio(
            analysis,
            base=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.53),
            cap=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.75),
        )
        families = [str(item).strip() for item in theme.get("relation_families") or [] if str(item).strip()]
        body_mode = str(theme.get("body_mode") or "").strip()
        if "liu_chong" in families or body_mode in {"shifted_body", "disturbed_body"}:
            phase = "近应"
            detail = "结构先动，事件多在短周期内显形。"
        elif "sanxing" in families:
            phase = "迟应"
            detail = "刑压偏重，往往先积压后兑现。"
        elif any(f in families for f in ("san_he", "liuhe", "ban_he", "anhe", "san_hui")):
            phase = "联应"
            detail = "合势/会势偏强，更看关系链与资源链联动。"
        else:
            phase = "平推"
            detail = "主结构稳定推进，先看阶段性落点。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派应期窗：当前以「{phase}」为主。{detail}",
                "priority": 0.75,
                "label": "应期窗口",
                "meta": {
                    "blind_phase": phase,
                    "timing_top_god": str(analysis.get("target_god") or ""),
                    **_common_meta(
                        physics_tensor=physics_tensor,
                        analysis=analysis,
                        relation_family="blind_timing_window",
                        match_ratio=match_ratio,
                    ),
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
        analysis = _blind_analysis(physics_tensor)
        theme = analysis.get("blind_theme") if isinstance(analysis.get("blind_theme"), dict) else {}
        if not theme:
            return []
        match_ratio = _match_ratio(
            analysis,
            base=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.49),
            cap=_plugin_match_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.71),
        )
        digest = str(theme.get("prompt_digest") or "").strip() or f"主线{_route_label(theme)}"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"盲派断口收束：{digest}",
                "priority": 0.74,
                "label": "断口收束",
                "meta": {
                    "blind_summary_top_god": str(analysis.get("target_god") or ""),
                    "blind_route": _route_label(theme),
                    **_common_meta(
                        physics_tensor=physics_tensor,
                        analysis=analysis,
                        relation_family="blind_summary",
                        match_ratio=match_ratio,
                    ),
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
