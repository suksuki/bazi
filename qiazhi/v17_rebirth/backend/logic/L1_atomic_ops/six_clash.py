from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import relation_origin_multiplier
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


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
            stress = 0.65
            if isinstance(hit.get("stress"), (int, float)):
                try:
                    stress = max(0.35, min(1.0, float(hit.get("stress"))))
                except (TypeError, ValueError):
                    stress = 0.65
            origin_type = str(hit.get("origin_type") or "natal").strip()
            origin_mul = relation_origin_multiplier(origin_type)
            rows.append(
                {
                    "plugin": self.plugin_id,
                    "fact": f"检测到地支六冲 [{label}]：结构对撞成立，{target_god or '目标神'} 进入高扰动态。",
                    "label": "先控波动，再谈放大",
                    "priority": 0.83,
                    "meta": {
                        "impact_ratio": -0.15,
                        "match_ratio": round(max(0.0, min(0.96, stress * origin_mul)), 3),
                        "target_god": target_god,
                        "clash_pair": pair[:2],
                        "relation_family": "liu_chong",
                        "origin_type": origin_type,
                        "origin_multiplier": round(origin_mul, 3),
                    },
                }
            )
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = SixClashPlugin()
