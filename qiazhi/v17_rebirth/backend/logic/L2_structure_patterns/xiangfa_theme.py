from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L2_structure_patterns.xiangfa_theme_core import resolve_xiangfa_theme
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _analysis(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_xiangfa_theme(physics_tensor)


def _theme(analysis: Dict[str, Any]) -> Dict[str, Any]:
    theme = analysis.get("xiangfa_theme")
    return theme if isinstance(theme, dict) else {}


def _match_ratio(theme: Dict[str, Any], fallback: float) -> float:
    return round(max(fallback, min(0.88, float(theme.get("confidence") or 0.0))), 3)


def _common_meta(
    *,
    physics_tensor: Dict[str, Any],
    analysis: Dict[str, Any],
    relation_family: str,
    match_ratio: float,
) -> Dict[str, Any]:
    theme = _theme(analysis)
    return {
        "observe_only": True,
        "claim_type": "pattern_observation",
        "entity_scope": "pattern",
        "exclusivity_key": "xiangfa_theme",
        "source_event": "xiangfa_theme",
        "xiangfa_theme": theme,
        "match_ratio": match_ratio,
        "interaction_layer": "cross_layer",
        "manifestation_state": "manifested",
        "origin_type": "mixed",
        "origin_multiplier": relation_origin_multiplier("mixed"),
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god="",
            relation_family=relation_family,
            relation_members=list(theme.get("source_topics") or []),
        ),
    }


@dataclass
class XiangfaSemanticMappingPlugin(V17PluginSpec):
    plugin_id: str = "classical.xiangfa.semantic_mapping.v1"
    causal_tier: int = 3
    registry_priority: float = 0.69

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        mapping = [str(item).strip() for item in theme.get("semantic_mapping") or [] if str(item).strip()]
        fact = "象法语义映射：" + "；".join(mapping[:3] or ["当前未形成稳定的象法映射"]) + "。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": 0.69,
                "label": "语义映射",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="xiangfa_semantic_mapping",
                    match_ratio=_match_ratio(theme, 0.52),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class XiangfaEvidencePlugin(V17PluginSpec):
    plugin_id: str = "classical.xiangfa.evidence.v1"
    causal_tier: int = 3
    registry_priority: float = 0.68

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        evidence = [str(item).strip() for item in theme.get("evidence") or [] if str(item).strip()]
        fact = "象法证据串：" + "；".join(evidence[:3] or ["当前未形成稳定证据串"]) + "。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": 0.68,
                "label": "证据串",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="xiangfa_evidence",
                    match_ratio=_match_ratio(theme, 0.5),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class XiangfaNarrativeHintPlugin(V17PluginSpec):
    plugin_id: str = "classical.xiangfa.narrative_hint.v1"
    causal_tier: int = 3
    registry_priority: float = 0.67

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        hints = [str(item).strip() for item in theme.get("narrative_hint") or [] if str(item).strip()]
        fact = "象法叙事提示：" + "；".join(hints[:2] or ["当前叙事仍应保守"]) + "。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": 0.67,
                "label": "叙事提示",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="xiangfa_narrative_hint",
                    match_ratio=_match_ratio(theme, 0.48),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class XiangfaEventFramingPlugin(V17PluginSpec):
    plugin_id: str = "classical.xiangfa.event_framing.v1"
    causal_tier: int = 3
    registry_priority: float = 0.66

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        frames = [str(item).strip() for item in theme.get("event_framing") or [] if str(item).strip()]
        fact = "象法事件框架：" + "；".join(frames[:3] or ["当前事件框架待定"]) + "。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": 0.66,
                "label": "事件框架",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    analysis=analysis,
                    relation_family="xiangfa_event_framing",
                    match_ratio=_match_ratio(theme, 0.46),
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    XiangfaSemanticMappingPlugin(),
    XiangfaEvidencePlugin(),
    XiangfaNarrativeHintPlugin(),
    XiangfaEventFramingPlugin(),
]
