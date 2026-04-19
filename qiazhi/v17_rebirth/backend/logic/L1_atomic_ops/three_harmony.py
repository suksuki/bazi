from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    relation_effect_multiplier,
    summarize_relation_conditions,
)

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_branch_sanhe",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "地支三合/半合全十神通用协同性算法。",
    "Rationale": "量化合局中的能量聚变与资源绑定过程。"
}

DECLARED_PARAMS = {
    "FUSION_MID_GAIN": 1.45,       # 中神聚变增益系数
    "LOCK_RATIO": 0.35,            # 资源锁定比例 (协同绑定强度)
    "MIN_HARMONY_STRESS": 0.40     # 触发三合感应的最低应力阈值
}


def run_three_harmony(*, source_abs: float, target_abs: float, lock_ratio: float = 0.35) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(lock_ratio or 0.0)))
    locked = min(src, tgt) * ratio
    return {"effect": "combine", "abs_locked": round(locked, 4), "vector": "binding"}


def _collect_rows(physics_tensor: Dict[str, Any]) -> List[dict]:
    # V17.99：直接从 interaction_v2 几何事实中提取，不再依赖 L0 应力图
    meta = physics_tensor.get("meta", {})
    iv2 = meta.get("interaction_v2", {})
    
    # 合并三合与半合事件
    harmony_hits = iv2.get("san_he", []) + iv2.get("ban_he", [])
    
    if not harmony_hits:
        return []
    
    from v17_rebirth.backend.logic.configs.manager import get_plugin_config
    local_cfg = get_plugin_config("l1.physics.op_branch_sanhe")
    mid_gain = float(local_cfg.get("FUSION_MID_GAIN", DECLARED_PARAMS["FUSION_MID_GAIN"]))
    lock_ratio = float(local_cfg.get("LOCK_RATIO", DECLARED_PARAMS["LOCK_RATIO"]))
    min_harmony_stress = float(local_cfg.get("MIN_HARMONY_STRESS", DECLARED_PARAMS["MIN_HARMONY_STRESS"]))

    rows = []
    scores = physics_tensor.get("ten_gods_absolute", {})
    for hit in harmony_hits:
        # 提取参与地支
        branches = hit.get("group") or hit.get("pair") or []
        strength = float(hit.get("stress") or hit.get("strength") or (1.0 if len(branches) >= 3 else 0.55))
        if strength < min_harmony_stress:
            continue
        condition = summarize_relation_conditions(
            relation_family="sanhe",
            pair_or_group=[str(x) for x in branches],
            interaction_v2=iv2,
        )
        mid_branches = [b for b in branches if b in {"子", "午", "卯", "酉"}]
        mid_branch = mid_branches[0] if mid_branches else (branches[0] if branches else "")
        
        from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import _branch_dominant_ten_god
        fp = physics_tensor.get("four_pillars", {})
        day_gz = str(fp.get("day", "")).strip()
        dm = day_gz[0] if len(day_gz) >= 2 else "壬"
        mid_god = _branch_dominant_ten_god(mid_branch, dm) if mid_branch else "核心"
        target_abs = float(scores.get(mid_god, 0.0) or 0.0)
        peer_gods = [_branch_dominant_ten_god(branch, dm) for branch in branches if branch]
        source_abs = max([float(scores.get(god, 0.0) or 0.0) for god in peer_gods] or [target_abs, 0.0])
        combo = run_three_harmony(source_abs=source_abs, target_abs=target_abs, lock_ratio=lock_ratio)
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        impact_ratio = (mid_gain - 1.0) * max(0.5, strength) * cond_mul
        priority = min(0.98, 0.78 + 0.17 * max(0.0, strength))

        meta = {
            "fusion_state": "ACTIVE",
            "target_god": mid_god,
            "harmony_strength": round(strength, 3),
            "match_ratio": round(max(0.0, min(1.0, max(0.5, strength) * cond_mul)), 3),
            "lock_ratio": round(lock_ratio, 3),
            "locked_energy": float(combo.get("abs_locked", 0.0) or 0.0),
            "condition_state": condition["condition_state"],
            "condition_blockers": list(condition["blockers"]),
            "condition_multiplier": cond_mul,
        }
        if condition["condition_state"] == "supported":
            meta["impact_ratio"] = round(impact_ratio, 2)
        rows.append({
            "plugin": "l1.physics.op_branch_sanhe",
            "fact": f"三合/半合聚势激活：核心枢纽 {mid_god} 触发 {mid_gain}x 能量聚变（{condition['condition_state']}）。",
            "label": "将执行节奏拆分为两段，先稳态验证再扩张。",
            "priority": round(priority, 3),
            "meta": meta,
        })
    return rows


@dataclass
class ThreeHarmonyPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_branch_sanhe"
    causal_tier: int = 4
    registry_priority: float = 0.68

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ThreeHarmonyPlugin()
