from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.configs.manager import get_plugin_config, resolve_config_number
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import build_static_basis, relation_effect_multiplier, summarize_relation_conditions

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_liuhai",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支六害（六穿）动力学损耗算法。",
    "Rationale": "量化「穿」态下秩序削弱，给出硬损伤度。"
}

DECLARED_PARAMS = {
    "PENETRATION_RATIO": 0.45,
    "CLASH_LOSS_RATIO": "ref(global.CLASH_LOSS_RATIO)"
}


def run_six_pierce(*, source_abs: float, target_abs: float, penetration_ratio: float = 0.45) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(penetration_ratio or 0.0)))
    damage = min(src, tgt) * ratio
    return {"effect": "pierce", "abs_loss": round(damage, 4), "vector": "penetration"}


def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    # V17.99：直接从 interaction_v2 几何事实中提取
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    
    # 六害/六穿只读取 liu_hai；六破由独立插件 six_break 处理
    pierce_hits = iv2.get("liu_hai", [])
    
    if not pierce_hits:
        return []
    
    cfg = get_plugin_config("l1.physics.op_branch_liuhai")
    penetration_ratio = resolve_config_number(cfg.get("PENETRATION_RATIO", DECLARED_PARAMS["PENETRATION_RATIO"]), 0.45)
    clash_loss_ratio = resolve_config_number(cfg.get("CLASH_LOSS_RATIO", DECLARED_PARAMS["CLASH_LOSS_RATIO"]), 0.12)

    rows = []
    scores = physics_tensor.get("ten_gods_absolute", {})
    for hit in pierce_hits:
        pair = hit.get("pair") or []
        br_i = pair[0] if len(pair) >= 1 else ""
        br_j = pair[1] if len(pair) >= 2 else ""
        
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        god_i = _branch_dominant_ten_god(br_i, dm) if br_i else "源神"
        god_j = _branch_dominant_ten_god(br_j, dm) if br_j else "目标"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=god_j,
            day_master=dm,
            focus_branches=pair,
        )
        if projection:
            god_j = max(projection.items(), key=lambda item: item[1])[0]
        source_abs = float(scores.get(god_i, 0.0) or 0.0)
        target_abs = float(scores.get(god_j, 0.0) or 0.0)
        pierce = run_six_pierce(source_abs=source_abs, target_abs=target_abs, penetration_ratio=penetration_ratio)
        effective_ratio = min(0.5, max(0.02, clash_loss_ratio * penetration_ratio))
        condition = summarize_relation_conditions(
            relation_family="liuhai",
            pair_or_group=[str(x) for x in pair],
            interaction_v2=iv2,
        )
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
        balance_ratio = min(source_abs, target_abs) / max(max(source_abs, target_abs), 1.0)
        pair_strength = 1.0 if len(pair) >= 2 else 0.65
        match_ratio = min(
            0.84,
            max(
                0.0,
                (0.26 + penetration_ratio * 0.3 + balance_ratio * 0.16 + effective_ratio * 0.78 + (0.08 if pair_strength >= 1.0 else 0.0))
                * max(0.55, cond_mul)
                * origin_mul,
            ),
        )

        rows.append({
            "plugin": "l1.physics.op_branch_liuhai",
            "fact": f"地支六穿激活 -> 目标 {god_j} 产生 {int(effective_ratio*100)}% 局部应力损耗。",
            "label": "关键动作加一层确认，压低冲动决策误差。",
            "priority": round(min(0.96, 0.8 + effective_ratio), 3),
            "meta": {
                "impact_ratio": round(-effective_ratio, 2),
                "match_ratio": round(match_ratio, 3),
                "target_god": god_j,
                "projection_share": round(float((projection or {}).get(god_j, 1.0)), 4),
                "cluster_projection": projection,
                "shielding_status": "FAILED",
                "penetration_ratio": round(penetration_ratio, 3),
                "clash_loss_ratio": round(clash_loss_ratio, 3),
                "abs_loss": float(pierce.get("abs_loss", 0.0) or 0.0),
                "balance_ratio": round(balance_ratio, 3),
                "condition_state": condition["condition_state"],
                "condition_blockers": list(condition["blockers"]),
                "condition_multiplier": round(cond_mul, 3),
                "origin_type": condition.get("origin_type"),
                "origin_multiplier": round(origin_mul, 3),
                "static_basis": build_static_basis(
                    physics_tensor=physics_tensor,
                    target_god=god_j,
                    relation_family="liuhai",
                    relation_members=pair,
                ),
            }
        })
    return rows


@dataclass
class SixPiercePlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_liuhai"
    causal_tier: int = 4
    registry_priority: float = 0.62

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = SixPiercePlugin()
