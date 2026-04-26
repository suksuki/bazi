from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import resolve_bazi_image
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


V17_SKILL_MANIFEST = {
    "id": "v17.symbolic.bazi_image.v1",
    "Layer": "L0",
    "Skill_Type": "SymbolicBasis",
    "Domain": "Physics",
    "Description": "八字象义底座：把天干、地支、十神、宫位、藏透和库象转成只读象义事实。",
    "Rationale": "为财富密码、事业、感情等专题提供可审计的象义材料；不裁决体用，不修改参数。",
}


def _image(analysis: Dict[str, Any]) -> Dict[str, Any]:
    image = analysis.get("bazi_image")
    return image if isinstance(image, dict) else {}


def _common_meta(*, image: Dict[str, Any]) -> Dict[str, Any]:
    confidence = float(image.get("confidence") or 0.0) if image.get("confidence") is not None else 0.0
    if not confidence:
        facts = image.get("symbolic_facts") if isinstance(image.get("symbolic_facts"), list) else []
        confidence = 0.78 if facts else 0.62
    return {
        "observe_only": True,
        "claim_type": "symbolic_image_observation",
        "entity_scope": "symbolic_basis",
        "exclusivity_key": "symbolic:bazi_image",
        "source_event": "bazi_image",
        "bazi_image": image,
        "symbolic_layer": "bazi_image",
        "match_ratio": round(max(0.0, min(1.0, confidence)), 3),
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "logic_level": "L0",
        "interaction_layer": "symbolic_image",
        "manifestation_state": "observed",
        "origin_type": "l0_symbolic_basis",
    }


@dataclass
class BaziImagePlugin(V17PluginSpec):
    plugin_id: str = "v17.symbolic.bazi_image.v1"
    causal_tier: int = 5
    registry_priority: float = 0.655

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        analysis = resolve_bazi_image(physics_tensor)
        image = _image(analysis)
        if not image:
            return []
        digest = str(image.get("prompt_digest") or "").strip()
        if not digest:
            day_master = str(image.get("day_master_stem") or "").strip()
            digest = f"日主{day_master}，已生成干支材质与宫位象义。" if day_master else "已生成干支材质与宫位象义。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"八字象义：{digest}",
                "priority": 0.66,
                "label": "八字象义底座",
                "meta": _common_meta(image={**image, "confidence": analysis.get("confidence", 0.0)}),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = BaziImagePlugin()
