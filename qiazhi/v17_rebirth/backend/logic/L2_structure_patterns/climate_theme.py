from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import (
    resolve_climate_theme,
)
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _theme_analysis(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_climate_theme(physics_tensor)


def _theme(analysis: Dict[str, Any]) -> Dict[str, Any]:
    theme = analysis.get("climate_theme")
    return theme if isinstance(theme, dict) else {}


def _focus_labels(theme: Dict[str, Any]) -> List[str]:
    rows = theme.get("source_focus")
    if not isinstance(rows, list):
        return []
    labels: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("scope_label") or row.get("scope") or "").strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def _match_ratio(theme: Dict[str, Any], fallback: float) -> float:
    confidence = float(theme.get("confidence") or 0.0)
    return round(max(fallback, min(0.9, confidence)), 3)


def _common_meta(
    *,
    physics_tensor: Dict[str, Any],
    analysis: Dict[str, Any],
    relation_family: str,
    match_ratio: float,
) -> Dict[str, Any]:
    theme = _theme(analysis)
    target_god = str(analysis.get("target_god") or "").strip()
    focus_labels = _focus_labels(theme)
    return {
        "observe_only": True,
        "claim_type": "pattern_observation",
        "entity_scope": "pattern",
        "exclusivity_key": "climate_theme",
        "source_event": "climate_theme",
        "climate_theme": theme,
        "climate_state": str(theme.get("state") or "").strip(),
        "climate_prompt_digest": str(theme.get("prompt_digest") or "").strip(),
        "match_ratio": match_ratio,
        "interaction_layer": "cross_layer",
        "manifestation_state": "manifested",
        "origin_type": str(theme.get("origin_type") or "runtime"),
        "origin_multiplier": relation_origin_multiplier(str(theme.get("origin_type") or "runtime")),
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god=target_god,
            relation_family=relation_family,
            relation_members=focus_labels,
        ),
        "target_god": target_god,
    }


@dataclass
class ClimateAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.climate.axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.77

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _theme_analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": (
                    f"调候主轴：当前处于「{str(theme.get('state') or '未定')}」；"
                    f"寒热轴 {float(theme.get('thermal_index') or 0.0):+.2f}；"
                    f"燥湿轴 {float(theme.get('moisture_index') or 0.0):+.2f}；"
                    f"张力 {float(theme.get('climate_tension') or 0.0):.2f}。"
                ),
                "priority": 0.77,
                "label": "调候主轴",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="climate_axis",
                    match_ratio=_match_ratio(theme, 0.62),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ClimateTenGodFitPlugin(V17PluginSpec):
    plugin_id: str = "classical.climate.ten_god_fit.v1"
    causal_tier: int = 3
    registry_priority: float = 0.76

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _theme_analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        favored = [str(item).strip() for item in theme.get("favored_gods") or [] if str(item).strip()]
        strained = [str(item).strip() for item in theme.get("strained_gods") or [] if str(item).strip()]
        parts: List[str] = []
        if favored:
            parts.append("更顺势 " + "/".join(favored[:3]))
        if strained:
            parts.append("更承压 " + "/".join(strained[:3]))
        if not parts:
            parts.append("当前未形成显著的十神调候偏向")
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "调候十神适配：" + "；".join(parts) + "。",
                "priority": 0.76,
                "label": "十神适配",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="climate_ten_god_fit",
                    match_ratio=_match_ratio(theme, 0.58),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ClimatePatternSurvivalPlugin(V17PluginSpec):
    plugin_id: str = "classical.climate.pattern_survival.v1"
    causal_tier: int = 3
    registry_priority: float = 0.75

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _theme_analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        rows_raw = theme.get("pattern_survival") if isinstance(theme.get("pattern_survival"), list) else []
        parts: List[str] = []
        for row in rows_raw[:3]:
            if not isinstance(row, dict):
                continue
            label = str(row.get("label") or row.get("key") or "").strip()
            bucket = str(row.get("bucket") or "").strip()
            delta = float(row.get("delta") or 0.0)
            if not label:
                continue
            parts.append(f"{label}{bucket} {delta:+.2f}")
        if not parts:
            parts.append("当前未形成显著的格局存续修正")
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "调候格局存续：" + "；".join(parts) + "。",
                "priority": 0.75,
                "label": "格局存续",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="climate_pattern_survival",
                    match_ratio=_match_ratio(theme, 0.56),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ClimateSummaryPlugin(V17PluginSpec):
    plugin_id: str = "classical.climate.summary.v1"
    causal_tier: int = 3
    registry_priority: float = 0.74

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _theme_analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        digest = str(theme.get("prompt_digest") or "").strip() or "调候摘要待定"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "调候专题收束：" + digest + "。",
                "priority": 0.74,
                "label": "调候收束",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="climate_summary",
                    match_ratio=_match_ratio(theme, 0.54),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    ClimateAxisPlugin(),
    ClimateTenGodFitPlugin(),
    ClimatePatternSurvivalPlugin(),
    ClimateSummaryPlugin(),
]
