from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


V17_SKILL_MANIFEST = {
    "id": "modern.topic.wealth_profile.v1",
    "Layer": "L3",
    "Skill_Type": "TopicDecoder",
    "Domain": "Narrative",
    "Description": "财富专题解码器：从十神、体用、格局、盲派、象法、调候和关系动力中提取财富画像。",
    "Rationale": "先生成可审计的 wealth_profile，再允许 LLM 写财富专属断言；插件本身不改物理层和参数。",
}


def _profile(analysis: Dict[str, Any]) -> Dict[str, Any]:
    profile = analysis.get("wealth_profile")
    return profile if isinstance(profile, dict) else {}


def _common_meta(*, physics_tensor: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    score = float(profile.get("score") or 0.0)
    confidence = float(profile.get("confidence") or 0.0)
    return {
        "observe_only": True,
        "claim_type": "topic_profile_observation",
        "entity_scope": "topic_profile",
        "exclusivity_key": "topic_decoder:wealth",
        "source_event": "topic_decoder",
        "wealth_profile": profile,
        "topic_profile": "wealth",
        "topic_profile_label": "财富画像",
        "macro_topic": "wealth",
        "macro_topic_label": "财富",
        "match_ratio": round(max(0.0, min(1.0, score)), 3),
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "logic_level": "L3",
        "interaction_layer": "topic_decoder",
        "manifestation_state": str(profile.get("stance") or "").strip() or "watch",
        "origin_type": "cross_layer_topic_decoder",
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god="",
            relation_family="topic_wealth_profile",
            relation_members=list((profile.get("source_gods") or {}).keys())
            if isinstance(profile.get("source_gods"), dict)
            else [],
        ),
        "origin_multiplier": relation_origin_multiplier("mixed"),
    }


@dataclass
class WealthProfilePlugin(V17PluginSpec):
    plugin_id: str = "modern.topic.wealth_profile.v1"
    causal_tier: int = 2
    registry_priority: float = 0.63

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = resolve_wealth_profile(physics_tensor)
        profile = _profile(analysis)
        if not profile:
            return []
        channels = profile.get("primary_channels") if isinstance(profile.get("primary_channels"), list) else []
        top_channel = channels[0] if channels and isinstance(channels[0], dict) else {}
        channel_label = str(top_channel.get("label") or "财富通道").strip()
        score = round(float(profile.get("score") or 0.0) * 100)
        risk = round(float(profile.get("risk") or 0.0) * 100)
        usable = str(profile.get("usable_state") or "unclear").strip()
        fact = f"财富画像：主通道「{channel_label}」，激活度 {score}%，风险 {risk}%，可用状态 {usable}。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": min(0.88, max(0.52, float(profile.get("score") or 0.0))),
                "label": "财富专题画像",
                "meta": _common_meta(physics_tensor=physics_tensor, profile=profile),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = WealthProfilePlugin()
