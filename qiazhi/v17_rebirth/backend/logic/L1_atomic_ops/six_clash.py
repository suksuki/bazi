from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import build_work_evidence
from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import build_static_basis, relation_origin_multiplier
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_liuchong",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支六冲对撞扰动算法。",
    "Rationale": "量化冲支之间的结构对撞、目标神波动与运行态扰动，统一接入 L1 关系算子标准协议。",
}

DECLARED_PARAMS = {
    "DEFAULT_STRESS": 0.65,
    "MIN_STRESS": 0.35,
    "MAX_STRESS": 1.0,
    "BASE_IMPACT_RATIO": -0.15,
    "PRIORITY_BASE": 0.83,
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


@dataclass
class SixClashPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liuchong"
    causal_tier: int = 4
    registry_priority: float = 0.77

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
        iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
        clashes = iv2.get("liu_chong") if isinstance(iv2.get("liu_chong"), list) else []
        if not clashes:
            return []
        cfg = get_plugin_config(self.plugin_id)
        default_stress = float(cfg.get("DEFAULT_STRESS", DECLARED_PARAMS["DEFAULT_STRESS"]))
        min_stress = float(cfg.get("MIN_STRESS", DECLARED_PARAMS["MIN_STRESS"]))
        max_stress = float(cfg.get("MAX_STRESS", DECLARED_PARAMS["MAX_STRESS"]))
        base_impact_ratio = float(cfg.get("BASE_IMPACT_RATIO", DECLARED_PARAMS["BASE_IMPACT_RATIO"]))
        priority_base = float(cfg.get("PRIORITY_BASE", DECLARED_PARAMS["PRIORITY_BASE"]))

        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"

        rows: List[Dict[str, Any]] = []
        for hit in clashes:
            if not isinstance(hit, dict):
                continue
            pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
            if len(pair) < 2:
                continue
            gods = [_branch_dominant_ten_god(branch, dm) for branch in pair]
            target_god = gods[0] if gods and gods[0] else (gods[1] if len(gods) > 1 else "")
            label = "".join(pair[:2])
            stress = default_stress
            if isinstance(hit.get("stress"), (int, float)):
                try:
                    stress = _clamp(float(hit.get("stress")), min_stress, max_stress)
                except (TypeError, ValueError):
                    stress = default_stress
            origin_type = str(hit.get("origin_type") or "natal").strip()
            origin_mul = relation_origin_multiplier(origin_type)
            rows.append(
                {
                    "plugin": self.plugin_id,
                    "fact": f"检测到地支六冲 [{label}]：结构对撞成立，{target_god or '目标神'} 进入高扰动态。",
                    "label": "先控波动，再谈放大",
                    "priority": round(priority_base, 3),
                    "meta": {
                        "impact_ratio": round(base_impact_ratio, 3),
                        "match_ratio": round(max(0.0, min(0.96, stress * origin_mul)), 3),
                        "target_god": target_god,
                        "clash_pair": pair[:2],
                        "relation_family": "liu_chong",
                        "clash_stress": round(stress, 3),
                        "origin_type": origin_type,
                        "origin_multiplier": round(origin_mul, 3),
                        "work_evidence": build_work_evidence(
                            relation_family="liu_chong",
                            target_god=target_god,
                            members=pair[:2],
                            effect_type="harm",
                            layer="branch",
                            origin_scope=origin_type,
                            impact_ratio=round(base_impact_ratio, 3),
                            match_ratio=round(max(0.0, min(0.96, stress * origin_mul)), 3),
                            path_strength=abs(base_impact_ratio) * max(0.35, stress) * max(0.72, origin_mul),
                            targets=[target_god],
                        ),
                        "static_basis": build_static_basis(
                            physics_tensor=physics_tensor,
                            target_god=target_god,
                            relation_family="liu_chong",
                            relation_members=pair[:2],
                        ),
                    },
                }
            )
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = SixClashPlugin()
