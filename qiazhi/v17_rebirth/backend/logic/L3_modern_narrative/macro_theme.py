from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L3_modern_narrative.macro_theme_core import resolve_macro_theme
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


V17_SKILL_MANIFEST = {
    "id": "modern.macro.theme.v1",
    "Layer": "L3",
    "Skill_Type": "MacroTheme",
    "Domain": "Narrative",
    "Description": "宏观象主题层：把财富、事业、感情、性格组织成可解释、可学习、可由 LLM 消费的结构化画像。",
    "Rationale": "L3 只读底层事实、体用裁决和专题信号，输出宏观主题激活度，不反写物理参数。",
}


def _analysis(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_macro_theme(physics_tensor)


def _theme(analysis: Dict[str, Any]) -> Dict[str, Any]:
    theme = analysis.get("macro_theme")
    return theme if isinstance(theme, dict) else {}


def _topic(theme: Dict[str, Any], topic_id: str) -> Dict[str, Any]:
    rows = theme.get("topics") if isinstance(theme.get("topics"), list) else []
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "").strip() == topic_id:
            return row
    return {}


def _common_meta(
    *,
    physics_tensor: Dict[str, Any],
    theme: Dict[str, Any],
    topic: Dict[str, Any],
    topic_id: str,
) -> Dict[str, Any]:
    score = float(topic.get("score") or 0.0)
    return {
        "observe_only": True,
        "claim_type": "macro_theme_observation",
        "entity_scope": "macro_topic",
        "exclusivity_key": f"macro_theme:{topic_id}",
        "source_event": "macro_theme",
        "macro_theme": theme,
        "macro_topic": topic_id,
        "macro_topic_label": str(topic.get("label") or "").strip(),
        "match_ratio": round(max(0.0, min(1.0, score)), 3),
        "confidence": round(max(0.0, min(1.0, float(topic.get("confidence") or theme.get("confidence") or 0.0))), 3),
        "logic_level": "L3",
        "interaction_layer": "macro_theme",
        "manifestation_state": str(topic.get("stance") or "").strip() or "watch",
        "origin_type": "cross_layer_macro",
        "origin_multiplier": relation_origin_multiplier("mixed"),
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god="",
            relation_family=f"macro_{topic_id}",
            relation_members=list(topic.get("source_topics") or []),
        ),
    }


@dataclass
class MacroThemeTopicPlugin(V17PluginSpec):
    topic_id: str = ""
    plugin_id: str = "modern.macro.topic.v1"
    causal_tier: int = 2
    registry_priority: float = 0.66

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = _analysis(physics_tensor)
        theme = _theme(analysis)
        if not theme:
            return []
        topic = _topic(theme, self.topic_id)
        if not topic:
            return []
        label = str(topic.get("label") or self.topic_id).strip()
        summary = str(topic.get("summary") or "").strip()
        score = round(float(topic.get("score") or 0.0) * 100)
        risk = round(float(topic.get("risk") or 0.0) * 100)
        fact = summary or f"宏观象主题：{label} 激活度 {score}%，风险 {risk}%。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": min(0.88, max(0.52, float(topic.get("score") or 0.0))),
                "label": f"宏观象：{label}",
                "meta": _common_meta(
                    physics_tensor=physics_tensor,
                    theme=theme,
                    topic=topic,
                    topic_id=self.topic_id,
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    MacroThemeTopicPlugin(
        topic_id="wealth",
        plugin_id="modern.macro.wealth.v1",
        registry_priority=0.72,
    ),
    MacroThemeTopicPlugin(
        topic_id="career",
        plugin_id="modern.macro.career.v1",
        registry_priority=0.71,
    ),
    MacroThemeTopicPlugin(
        topic_id="relationship",
        plugin_id="modern.macro.relationship.v1",
        registry_priority=0.70,
    ),
    MacroThemeTopicPlugin(
        topic_id="personality",
        plugin_id="modern.macro.personality.v1",
        registry_priority=0.69,
    ),
]
