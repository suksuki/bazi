from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, STEM_ELEMENT, ten_god_from_stems
from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    collect_origin_types_from_rows,
    choose_dominant_origin_type,
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


def _parse_gz(gz: str) -> tuple[str, str]:
    raw = str(gz or "").strip()
    if len(raw) < 2:
        return "", ""
    return raw[0], raw[1]


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


def _cluster_projection_weights(*, branches: List[str], day_master: str, physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    if not branches:
        return {}
    mid_branches = [branch for branch in branches if branch in {"子", "午", "卯", "酉"}]
    anchor_branch = mid_branches[0] if mid_branches else branches[0]
    main_hidden = BRANCH_HIDDEN.get(anchor_branch, [])
    target_element = STEM_ELEMENT.get(main_hidden[0][0], "") if main_hidden else ""
    if not target_element:
        return {}
    weights: Dict[str, float] = {}
    for branch in branches:
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != target_element:
                continue
            god = ten_god_from_stems(day_master, hidden_stem)
            weights[god] = weights.get(god, 0.0) + float(hidden_weight)
    for god, weight in _visible_cluster_weights(physics_tensor, target_element=target_element, day_master=day_master).items():
        weights[god] = weights.get(god, 0.0) + weight
    total = sum(weights.values())
    if total <= 0:
        return {}
    return {god: round(weight / total, 4) for god, weight in weights.items() if weight > 0}


def _sanhe_runtime_drag_meta(*, branches: List[str], interaction_v2: Dict[str, Any]) -> Dict[str, Any]:
    branch_set = {str(item) for item in branches if str(item).strip()}
    blocker_rows: List[Dict[str, Any]] = []
    for key, member_key in (("liu_hai", "pair"), ("liu_po", "pair"), ("liu_chong", "pair")):
        rows = interaction_v2.get(key) if isinstance(interaction_v2.get(key), list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            members = {str(item) for item in (row.get(member_key) or []) if str(item).strip()}
            if branch_set & members:
                blocker_rows.append(row)
    origin_types = collect_origin_types_from_rows(blocker_rows, member_key="pair")
    dominant_origin = choose_dominant_origin_type(origin_types)
    runtime_only = bool(origin_types) and all(origin != "natal" for origin in origin_types)
    return {
        "runtime_only_drag": runtime_only,
        "drag_origin_type": dominant_origin,
    }


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
        drag_meta = _sanhe_runtime_drag_meta(branches=[str(x) for x in branches], interaction_v2=iv2)
        effective_state = condition["condition_state"]
        cond_mul = relation_effect_multiplier(condition["condition_state"])
        if (
            condition["condition_state"] == "contested"
            and condition.get("origin_type") == "natal"
            and len(branches) >= 3
            and drag_meta["runtime_only_drag"]
        ):
            effective_state = "supported"
            cond_mul = 0.72
        origin_mul = float(condition.get("origin_multiplier", 1.0) or 1.0)
        impact_ratio = (mid_gain - 1.0) * max(0.5, strength) * cond_mul
        priority = min(0.98, 0.78 + 0.17 * max(0.0, strength))
        projection = _cluster_projection_weights(branches=[str(x) for x in branches], day_master=dm, physics_tensor=physics_tensor)

        target_shares = projection or {mid_god: 1.0}
        for god, share in sorted(target_shares.items(), key=lambda item: item[1], reverse=True):
            projected_impact = impact_ratio * max(0.28, float(share))
            projected_match = round(
                max(
                    0.0,
                    min(
                        1.0,
                        (0.35 + 0.35 * max(0.0, min(1.0, strength)) + (0.18 if len(branches) >= 3 else 0.0))
                        * max(0.55, cond_mul)
                        * origin_mul
                        * max(0.65, float(share)),
                    ),
                ),
                3,
            )
            meta = {
                "fusion_state": "ACTIVE",
                "target_god": god,
                "harmony_strength": round(strength, 3),
                "match_ratio": projected_match,
                "projection_share": round(float(share), 4),
                "cluster_projection": projection,
                "lock_ratio": round(lock_ratio, 3),
                "locked_energy": float(combo.get("abs_locked", 0.0) or 0.0),
                "condition_state": effective_state,
                "condition_blockers": list(condition["blockers"]),
                "condition_mode": "natal_core_with_runtime_drag" if effective_state != condition["condition_state"] else "direct",
                "condition_multiplier": cond_mul,
                "origin_type": condition.get("origin_type"),
                "origin_multiplier": round(origin_mul, 3),
            }
            if effective_state == "supported":
                meta["impact_ratio"] = round(projected_impact, 2)
            rows.append({
                "plugin": "l1.physics.op_branch_sanhe",
                "fact": f"三合/半合聚势激活：核心枢纽 {god} 触发 {mid_gain}x 能量聚变（{effective_state}）。",
                "label": "将执行节奏拆分为两段，先稳态验证再扩张。",
                "priority": round(priority * max(0.82, float(share)), 3),
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
