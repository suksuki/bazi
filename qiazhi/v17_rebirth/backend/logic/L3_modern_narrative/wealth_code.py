from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


V17_SKILL_MANIFEST = {
    "id": "modern.topic.wealth_code.v1",
    "Layer": "L3",
    "Skill_Type": "TopicDecoder",
    "Domain": "Narrative",
    "Description": "财富密码解码器：从八字象义、财富画像、十神路径和财库线索中识别财富路径。",
    "Rationale": "把财富专题从摘要升级为可审计路径；插件只输出结构化 wealth_code，不改体用和参数。",
}


def _code(analysis: Dict[str, Any]) -> Dict[str, Any]:
    code = analysis.get("wealth_code")
    return code if isinstance(code, dict) else {}


def _common_meta(*, physics_tensor: Dict[str, Any], wealth_code: Dict[str, Any]) -> Dict[str, Any]:
    score = float(wealth_code.get("score") or 0.0)
    confidence = float(wealth_code.get("confidence") or 0.0)
    primary = wealth_code.get("primary_wealth_path") if isinstance(wealth_code.get("primary_wealth_path"), dict) else {}
    source = wealth_code.get("wealth_source") if isinstance(wealth_code.get("wealth_source"), dict) else {}
    return {
        "observe_only": True,
        "claim_type": "topic_code_observation",
        "entity_scope": "topic_code",
        "exclusivity_key": "topic_decoder:wealth_code",
        "source_event": "wealth_code",
        "wealth_code": wealth_code,
        "topic_profile": "wealth",
        "topic_profile_label": "财富密码",
        "macro_topic": "wealth",
        "macro_topic_label": "财富",
        "primary_path_id": str(primary.get("id") or ""),
        "primary_path_label": str(primary.get("plain_name") or ""),
        "wealth_source_material": str(source.get("material") or ""),
        "match_ratio": round(max(0.0, min(1.0, score)), 3),
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "logic_level": "L3",
        "interaction_layer": "topic_decoder",
        "manifestation_state": "observed",
        "origin_type": "cross_layer_wealth_code_decoder",
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god="",
            relation_family="topic_wealth_code",
            relation_members=[str(primary.get("id") or ""), str(source.get("ten_god") or "")],
        ),
        "origin_multiplier": relation_origin_multiplier("mixed"),
    }


@dataclass
class WealthCodePlugin(V17PluginSpec):
    plugin_id: str = "modern.topic.wealth_code.v1"
    causal_tier: int = 2
    registry_priority: float = 0.625

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = resolve_wealth_code(physics_tensor)
        wealth_code = _code(analysis)
        if not wealth_code:
            return []
        primary = wealth_code.get("primary_wealth_path") if isinstance(wealth_code.get("primary_wealth_path"), dict) else {}
        source = wealth_code.get("wealth_source") if isinstance(wealth_code.get("wealth_source"), dict) else {}
        path_label = str(primary.get("plain_name") or "财富路径").strip()
        source_label = str(source.get("plain_source") or "财富来源待观察").strip()
        risk = round(float(wealth_code.get("risk") or 0.0) * 100)
        fact = f"财富密码：主路径「{path_label}」，财源偏向「{source_label}」，风险 {risk}%。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": fact,
                "priority": min(0.9, max(0.52, float(wealth_code.get("score") or 0.0))),
                "label": "财富密码",
                "meta": _common_meta(physics_tensor=physics_tensor, wealth_code=wealth_code),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = WealthCodePlugin()
