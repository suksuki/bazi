from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, STEM_ELEMENT, ten_god_from_stems
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    relation_effect_multiplier,
    summarize_stem_fusion_conditions,
)
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import build_work_evidence

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_stem_fusion",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "天干五合（化气/羁绊）动力学模型。",
    "Rationale": "量化天干合化过程中的能量转移与性质改变。"
}

DECLARED_PARAMS = {
    "TRANSFORM_EFFICIENCY": 0.85,    # 成功化气时的能量转化率
    "STUCK_DAMPING": 0.35           # 羁绊（合而不化）时的能量削减比例
}

ELEMENT_ALIASES = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _parse_gz(gz: str) -> tuple[str, str]:
    raw = str(gz or "").strip()
    if len(raw) < 2:
        return "", ""
    return raw[0], raw[1]


def _normalize_element_name(element: str) -> str:
    raw = str(element or "").strip()
    return ELEMENT_ALIASES.get(raw.lower(), raw)


def _visible_cluster_weights(physics_tensor: Dict[str, Any], *, target_element: str, day_master: str) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    fp = physics_tensor.get("four_pillars", {}) if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    visible_gz = [fp.get(key, "") for key in ("year", "month", "day", "hour")]
    visible_gz.extend([physics_tensor.get("luck_pillar", ""), physics_tensor.get("flow_pillar", "")])
    for gz in visible_gz:
        stem, _branch = _parse_gz(str(gz or ""))
        if not stem or STEM_ELEMENT.get(stem) != target_element:
            continue
        god = ten_god_from_stems(day_master, stem)
        weights[god] = weights.get(god, 0.0) + 0.55
    return weights


def _element_cluster_projection(*, physics_tensor: Dict[str, Any], target_element: str, day_master: str) -> Dict[str, float]:
    from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _get_god_to_element_map

    g2e = _get_god_to_element_map(day_master)
    candidate_gods = [god for god, element in g2e.items() if element == target_element]
    if not candidate_gods:
        return {}

    weights: Dict[str, float] = {god: 0.0 for god in candidate_gods}
    fp = physics_tensor.get("four_pillars", {}) if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    branch_gz = [fp.get(key, "") for key in ("year", "month", "day", "hour")]
    branch_gz.extend([physics_tensor.get("luck_pillar", ""), physics_tensor.get("flow_pillar", "")])
    for gz in branch_gz:
        _stem, branch = _parse_gz(str(gz or ""))
        if not branch:
            continue
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != target_element:
                continue
            god = ten_god_from_stems(day_master, hidden_stem)
            if god in weights:
                weights[god] = weights.get(god, 0.0) + float(hidden_weight)

    for god, weight in _visible_cluster_weights(
        physics_tensor,
        target_element=target_element,
        day_master=day_master,
    ).items():
        if god in weights:
            weights[god] = weights.get(god, 0.0) + weight

    total = sum(weights.values())
    if total <= 0:
        uniform = round(1.0 / len(candidate_gods), 4)
        return {god: uniform for god in candidate_gods}
    return {
        god: round(weight / total, 4)
        for god, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)
        if weight > 0
    }

def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    meta = physics_tensor.get("meta", {})
    fusion_v1 = meta.get("stem_fusion_v1", {})
    cases = fusion_v1.get("cases", [])
    
    if not cases:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_stem_fusion")
    trans_eff = float(cfg.get("TRANSFORM_EFFICIENCY", DECLARED_PARAMS["TRANSFORM_EFFICIENCY"]))
    stuck_damp = float(cfg.get("STUCK_DAMPING", DECLARED_PARAMS["STUCK_DAMPING"]))

    rows = []
    for c in cases:
        mode = c.get("mode")
        stems = c.get("stems") or []
        lab = "".join(stems)
        condition = summarize_stem_fusion_conditions(c)
        
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        
        if mode == "stuck":
            target_god = ten_god_from_stems(dm, stems[0]) if stems else "被合神"
            cond_mul = relation_effect_multiplier(condition["condition_state"])
            origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
            branch_ratio = max(0.0, min(1.0, float(condition["branch_hua_ratio"] or 0.0)))
            support_penalty = 0.92 if condition["month_supports"] else 0.82
            match_ratio = max(
                0.0,
                min(
                    0.7,
                    (0.18 + branch_ratio * 0.28 + (0.05 if branch_ratio >= 0.45 else 0.0))
                    * max(0.5, cond_mul)
                    * origin_mul
                    * support_penalty,
                ),
            )
            rows.append({
                "plugin": "l1.physics.op_stem_fusion",
                "fact": f"天干羁绊 [{lab}]：能量处于僵持态，{target_god} 能级削减 {int(stuck_damp*100)}%（{condition['condition_trigger']}）。",
                "priority": 0.67,
                "meta": {
                    "target_god": target_god,
                    "match_ratio": round(match_ratio, 3),
                    "condition_state": condition["condition_state"],
                    "condition_trigger": condition["condition_trigger"],
                    "branch_hua_ratio": condition["branch_hua_ratio"],
                    "condition_multiplier": cond_mul,
                    "origin_type": condition.get("origin_type"),
                    "origin_multiplier": round(origin_mul, 3),
                    "work_evidence": build_work_evidence(
                        relation_family="stem_fusion",
                        target_god=target_god,
                        members=stems,
                        effect_type="stuck",
                        layer="stem",
                        origin_scope=str(condition.get("origin_type") or "natal"),
                        condition_state=condition["condition_state"],
                        impact_ratio=-round(stuck_damp, 3),
                        match_ratio=round(match_ratio, 3),
                        path_strength=stuck_damp * max(0.55, branch_ratio + 0.25),
                        targets=[target_god],
                    ),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=target_god,
                        relation_family="stem_fusion",
                        relation_members=stems,
                    ),
                },
            })
        elif mode == "transformed":
            hua_el = _normalize_element_name(str(c.get("hua_element") or ""))
            cond_mul = relation_effect_multiplier(condition["condition_state"])
            origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
            branch_ratio = max(0.0, min(1.0, float(condition["branch_hua_ratio"] or 0.0)))
            formed_bonus = 0.2 if condition["condition_state"] == "formed" else 0.04
            month_bonus = 0.12 if condition["month_supports"] else 0.02
            match_ratio = max(
                0.0,
                min(
                    0.9,
                    (0.22 + branch_ratio * 0.38 + formed_bonus + month_bonus) * max(cond_mul, 0.5) * origin_mul,
                ),
            )
            projection = _element_cluster_projection(
                physics_tensor=physics_tensor,
                target_element=hua_el,
                day_master=dm,
            )
            target_shares = projection or {"化气神": 1.0}
            for god, share in sorted(target_shares.items(), key=lambda item: item[1], reverse=True):
                projected_match = round(
                    max(
                        0.0,
                        min(0.95, match_ratio * max(0.62, float(share))),
                    ),
                    3,
                )
                meta = {
                    "target_god": god,
                    "match_ratio": projected_match,
                    "projection_share": round(float(share), 4),
                    "cluster_projection": projection,
                    "condition_state": condition["condition_state"],
                    "condition_trigger": condition["condition_trigger"],
                    "branch_hua_ratio": condition["branch_hua_ratio"],
                    "condition_multiplier": cond_mul,
                    "origin_type": condition.get("origin_type"),
                    "origin_multiplier": round(origin_mul, 3),
                    "work_evidence": build_work_evidence(
                        relation_family="stem_fusion",
                        target_god=god,
                        members=stems,
                        effect_type="transform",
                        layer="stem",
                        origin_scope=str(condition.get("origin_type") or "natal"),
                        condition_state=condition["condition_state"],
                        impact_ratio=round(trans_eff * cond_mul * max(0.28, float(share)), 3) if condition["condition_state"] == "formed" else 0.0,
                        match_ratio=projected_match,
                        path_strength=trans_eff * max(0.55, branch_ratio + 0.2) * max(0.62, float(share)),
                        targets=list((projection or {}).keys()) or [god],
                    ),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=god,
                        relation_family="stem_fusion",
                        relation_members=stems,
                    ),
                }
                if condition["condition_state"] == "formed":
                    meta["impact_ratio"] = round(trans_eff * cond_mul * max(0.28, float(share)), 3)
                rows.append({
                    "plugin": "l1.physics.op_stem_fusion",
                    "fact": f"天干化气 [{lab}→{hua_el}]：能量聚变成功，{god} 能级被显著抬升（{condition['condition_trigger']}）。",
                    "priority": round(0.85 * max(0.82, float(share)), 3),
                    "meta": meta,
                })
            
    return rows

@dataclass
class StemFusionPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_stem_fusion"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = StemFusionPlugin()
