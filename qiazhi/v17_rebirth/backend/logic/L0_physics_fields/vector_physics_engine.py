"""
V17.31：矢量冲突应力引擎（L0 层 — Vector Phase）。

在 L0 ten_gods_absolute 的基础上，为每一对存在关系（冲/合/害/破）的柱位
计算矢量应力 F = G_v17 · (Q_i · Q_j) / d^k。

物理常数定义：
  CLASH  (冲): G = +1.0
  距离衰减指数 k = 1.35
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_HIDDEN,
    STEM_ELEMENT,
    ten_god_from_stems,
)

# ── 引力/斥力常数 G_v17 ──────────────────────────────────────────────────────

RELATION_COEFFICIENT: Dict[str, float] = {
    "clash":       1.0,    # 冲 — 全额能量爆发（斥力，正值）
    "combination": -0.8,   # 合 — 旧测试兼容的吸引向量
    "harm":        0.5,    # 害 — 中度扰动
    "pierce":      0.5,    # 破/穿 — 中度扰动
}

# 距离衰减指数 k ∈ [1.2, 1.5]（近距离冲突权重更高）
DISTANCE_DECAY_EXPONENT: float = 1.35

# Fact 权重提升阈值
STRESS_BOOST_TIER0_WEIGHT: float = 0.95
STRESS_BOOST_TOP_N: int = 5

ALPHA_CLASH: float = -0.15         # 冲力：双向湮灭 (-15%)
GREEDY_COMBINATION_DAMPING: float = 0.3

# ── 柱距映射 ──────────────────────────────────────────────────────────────────

# 四柱位置索引：year=0, month=1, day=2, hour=3
PILLAR_INDEX: Dict[str, int] = {
    "year": 0,
    "month": 1,
    "day": 2,
    "hour": 3,
}

TEN_GOD_CLUSTER_MATES: Dict[str, str] = {
    "比肩": "劫财",
    "劫财": "比肩",
    "食神": "伤官",
    "伤官": "食神",
    "偏财": "正财",
    "正财": "偏财",
    "七杀": "正官",
    "正官": "七杀",
    "偏印": "正印",
    "正印": "偏印",
}


def pillar_distance(p1: str, p2: str) -> int:
    i1 = PILLAR_INDEX.get(p1)
    i2 = PILLAR_INDEX.get(p2)
    if i1 is None or i2 is None:
        return 3
    d = abs(i1 - i2)
    return max(1, d)


# ── 地支主气能量查询 ──────────────────────────────────────────────────────────

def _branch_dominant_ten_god(branch: str, daymaster: str) -> str:
    hidden = BRANCH_HIDDEN.get(branch, [])
    if not hidden:
        return ""
    main_stem = hidden[0][0]
    return ten_god_from_stems(daymaster, main_stem)


def _branch_dominant_energy(
    branch: str,
    daymaster: str,
    ten_gods_absolute: Dict[str, float],
) -> float:
    god = _branch_dominant_ten_god(branch, daymaster)
    if not god:
        return 0.0
    direct = ten_gods_absolute.get(god)
    if isinstance(direct, (int, float)):
        return float(direct)
    mate = TEN_GOD_CLUSTER_MATES.get(god, "")
    sibling = ten_gods_absolute.get(mate, 0.0) if mate else 0.0
    return float(sibling or 0.0)


# ── 物理核心：矢量应力计算 ────────────────────────────────────────────────────

@dataclass
class StressEvent:
    relation_type: str
    source_key: str
    branches: List[str]
    pillars: List[str]
    q_i: float
    q_j: float
    god_i: str
    god_j: str
    distance: int
    g_coefficient: float
    raw_stress: float
    damped_stress: float
    damping_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_type": self.relation_type,
            "source_key": self.source_key,
            "branches": self.branches,
            "pillars": self.pillars,
            "god_i": self.god_i,
            "god_j": self.god_j,
            "distance": self.distance,
            "raw_stress": round(self.raw_stress, 4),
            "damped_stress": round(self.damped_stress, 4),
            "damping_applied": self.damping_applied,
        }


def calc_interaction_stress(
    q_i: float,
    q_j: float,
    distance: int,
    g_coefficient: float,
    decay_exponent: float = DISTANCE_DECAY_EXPONENT,
) -> float:
    if q_i <= 0 or q_j <= 0 or distance <= 0:
        return 0.0
    d_k = math.pow(float(distance), decay_exponent)
    return g_coefficient * (q_i * q_j) / d_k


def compute_stress_events(
    *,
    daymaster: str,
    branches: Dict[str, str],
    ten_gods_absolute: Dict[str, float],
    interaction_v2: Dict[str, Any],
) -> List[StressEvent]:
    if not daymaster or not branches or not ten_gods_absolute or not isinstance(interaction_v2, dict):
        return []

    events: List[StressEvent] = []
    relation_map: List[Tuple[str, str, float]] = [
        ("liu_chong", "clash", RELATION_COEFFICIENT["clash"]),
        ("liu_he", "combination", RELATION_COEFFICIENT["combination"]),
        ("sanhe", "combination", RELATION_COEFFICIENT["combination"]),
        ("san_he", "combination", RELATION_COEFFICIENT["combination"]),
        ("san_hui", "combination", RELATION_COEFFICIENT["combination"]),
        ("liu_hai", "harm", RELATION_COEFFICIENT["harm"]),
        ("liu_po", "pierce", RELATION_COEFFICIENT["pierce"]),
    ]

    for v2_key, relation_type, g_coeff in relation_map:
        hits = interaction_v2.get(v2_key)
        if not isinstance(hits, list):
            continue
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            pair = hit.get("pair") or hit.get("group") or hit.get("branches")
            pillars = hit.get("pillars")
            if not isinstance(pair, list) or len(pair) < 2:
                continue
            
            if not isinstance(pillars, list) or len(pillars) < 2:
                pillars = ["unknown", "unknown", "unknown"][:len(pair)]

            br_i, br_j = str(pair[0]), str(pair[1])
            p_i, p_j = str(pillars[0]), str(pillars[1])

            q_i = _branch_dominant_energy(br_i, daymaster, ten_gods_absolute)
            q_j = _branch_dominant_energy(br_j, daymaster, ten_gods_absolute)
            god_i = _branch_dominant_ten_god(br_i, daymaster)
            god_j = _branch_dominant_ten_god(br_j, daymaster)
            d = pillar_distance(p_i, p_j)

            raw_f = calc_interaction_stress(q_i, q_j, d, g_coeff)

            events.append(StressEvent(
                relation_type=relation_type,
                source_key=v2_key,
                branches=[str(b) for b in pair],
                pillars=[str(p) for p in pillars],
                q_i=q_i,
                q_j=q_j,
                god_i=god_i,
                god_j=god_j,
                distance=d,
                g_coefficient=g_coeff,
                raw_stress=raw_f,
                damped_stress=raw_f,
            ))

    events.sort(key=lambda x: abs(x.damped_stress), reverse=True)
    return events


def build_clash_stress_map(
    *,
    daymaster: str,
    branches: Dict[str, str],
    ten_gods_absolute: Dict[str, float],
    interaction_v2: Dict[str, Any],
) -> Dict[str, Any]:
    events = compute_stress_events(
        daymaster=daymaster,
        branches=branches,
        ten_gods_absolute=ten_gods_absolute,
        interaction_v2=interaction_v2,
    )

    top_plugin_ids: List[str] = []
    for ev in events[:STRESS_BOOST_TOP_N]:
        pid = _relation_to_plugin_id(ev.relation_type)
        if pid and pid not in top_plugin_ids:
            top_plugin_ids.append(pid)

    total_clash = sum(ev.damped_stress for ev in events if ev.relation_type == "clash")
    total_combination = sum(
        abs(ev.damped_stress)
        for ev in events
        if ev.relation_type == "combination"
    )
    damping_applied = any(ev.damping_applied for ev in events)
    
    return {
        "version": "vector_stress.v1",
        "events": [ev.to_dict() for ev in events],
        "top_stress_plugin_ids": top_plugin_ids,
        "total_clash_energy": round(total_clash, 4),
        "total_combination_energy": round(total_combination, 4),
        "net_vector": round(sum(ev.damped_stress for ev in events), 4),
        "damping_applied": damping_applied,
        "energy_deltas": {}, 
    }


def _relation_to_plugin_id(relation_type: str) -> str:
    mapping = {
        "clash": "l1.physics.op_branch_liuchong",
        "combination": "l1.physics.op_branch_liuhe",
        "harm": "l1.physics.op_branch_liuhai",
        "pierce": "l1.physics.op_branch_liupo",
    }
    return mapping.get(relation_type, "")


def boost_high_stress_facts(
    hits: Dict[str, Dict[str, Any]],
    stress_map: Dict[str, Any],
) -> None:
    top_ids = stress_map.get("top_stress_plugin_ids")
    if not isinstance(top_ids, list):
        return
    for pid in top_ids:
        if pid in hits:
            hits[pid]["priority"] = max(
                float(hits[pid].get("priority", 0.0)),
                STRESS_BOOST_TIER0_WEIGHT,
            )
            hits[pid].setdefault("evidence", {})["stress_boosted"] = True
