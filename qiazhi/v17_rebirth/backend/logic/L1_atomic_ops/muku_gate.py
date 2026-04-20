from __future__ import annotations
from typing import Any, Dict, List
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    infer_manifestation_state,
    relation_effect_multiplier,
    summarize_relation_conditions,
)
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import build_work_evidence

V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_muku",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支墓库（辰戌丑未）门态算法。",
    "Rationale": "量化墓库对能量的收纳与释放效应。"
}

DECLARED_PARAMS = {
    "STORAGE_EFFICIENCY": 0.35,      # 墓库的能量收纳（锁定）比例
    "OPEN_GATE_BOOST": 1.50         # 开库（冲刑）时的瞬时能级爆发倍率
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _branch_only(token: Any) -> str:
    raw = str(token or "").strip()
    if len(raw) >= 2:
        return raw[-1]
    return raw


def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    # 从 L0 探测结果中获取墓库地支
    branches = physics_tensor.get("four_pillars", {})
    br_list = [_branch_only(b) for b in branches.values() if str(b or "").strip()]
    muku_brs = [b for b in br_list if b in {"辰", "戌", "丑", "未"}]
    
    if not muku_brs:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    cfg = get_plugin_config("l1.physics.op_branch_muku")
    storage = float(cfg.get("STORAGE_EFFICIENCY", DECLARED_PARAMS["STORAGE_EFFICIENCY"]))
    open_gate_boost = float(cfg.get("OPEN_GATE_BOOST", DECLARED_PARAMS["OPEN_GATE_BOOST"]))
    meta = physics_tensor.get("meta", {}) if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2", {}) if isinstance(meta.get("interaction_v2"), dict) else {}
    open_pairs = []
    for hit in iv2.get("liu_chong", []) if isinstance(iv2.get("liu_chong"), list) else []:
        pair = hit.get("pair") if isinstance(hit, dict) else None
        if isinstance(pair, list):
            open_pairs.extend([str(br) for br in pair if str(br) in {"辰", "戌", "丑", "未"}])

    rows = []
    for br in set(muku_brs):
        # 简单逻辑：墓库对主气十神产生能量收敛项
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        god = _branch_dominant_ten_god(br, dm)
        is_open = br in open_pairs
        condition = summarize_relation_conditions(
            relation_family="muku",
            pair_or_group=[br],
            interaction_v2=iv2,
        )
        manifestation_state = infer_manifestation_state(
            rows=[{"pair": [br], "origin_type": condition.get("origin_type")}],
            relation_family="muku",
            member_set=[br],
            origin_types=[str(condition.get("origin_type") or "")],
        )
        interaction_layer = detect_interaction_layer(
            None,
            relation_family="muku",
            member_key="pair",
        )
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
        open_ratio = _clamp(open_gate_boost - 1.0, 0.1, 0.8)
        impact_ratio = round((open_ratio if is_open else -storage) * cond_mul, 2)
        state = "OPEN" if is_open else "CLOSED"
        fact = (
            f"地支【{br}】墓库开门：对 {god} 释放 {int(open_ratio * 100)}% 能量回流。"
            if is_open
            else f"地支【{br}】墓库位激活：对 {god} 产生能量收纳锁定效应 ({int(storage*100)}%)。"
        )
        priority = 0.81 if is_open else 0.73

        meta_payload = {
            "target_god": god,
            "muku_state": state,
            "storage_efficiency": round(storage, 3),
            "open_gate_boost": round(open_gate_boost, 3),
            "impact_ratio": impact_ratio,
            "match_ratio": round(_clamp((0.85 if is_open else 0.65) * cond_mul * origin_mul, 0.0, 1.0), 3),
            "condition_state": condition["condition_state"],
            "condition_blockers": list(condition["blockers"]),
            "interaction_layer": interaction_layer,
            "manifestation_state": manifestation_state,
            "condition_multiplier": cond_mul,
            "origin_type": condition.get("origin_type"),
            "origin_multiplier": round(origin_mul, 3),
            "work_evidence": build_work_evidence(
                relation_family="muku",
                target_god=god,
                members=[br],
                effect_type="release" if is_open else "storage",
                layer=interaction_layer,
                origin_scope=str(condition.get("origin_type") or "natal"),
                condition_state=condition["condition_state"],
                impact_ratio=impact_ratio,
                match_ratio=round(_clamp((0.85 if is_open else 0.65) * cond_mul * origin_mul, 0.0, 1.0), 3),
                path_strength=abs(impact_ratio) * (1.0 if is_open else 0.86),
                targets=[god],
            ),
            "static_basis": build_static_basis(
                physics_tensor=physics_tensor,
                target_god=god,
                relation_family="muku",
                relation_members=[br],
            ),
        }
        rows.append({
            "plugin": "l1.physics.op_branch_muku",
            "fact": fact,
            "priority": priority,
            "meta": meta_payload
        })
    return rows

@dataclass
class MukuGatePlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_muku"
    causal_tier: int = 4

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)

PLUGIN = MukuGatePlugin()
