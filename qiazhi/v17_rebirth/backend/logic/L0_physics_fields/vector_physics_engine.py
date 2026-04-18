"""
V17.31：矢量冲突应力引擎（L0 层 — Vector Phase）。

在 L0 ten_gods_absolute 的基础上，为每一对存在关系（冲/合/害/破）的柱位
计算矢量应力 F = G_v17 · (Q_i · Q_j) / d^k，并处理"贪合忘克"阻尼。

输出：
  - clash_stress_map: List[StressEvent]，按 |F| 降序排列
  - 高应力事件的 Fact 权重提升到 Tier 0 (0.95)

物理常数定义：
  CLASH  (冲): G = +1.0   — 全额能量爆发（斥力）
  COMBINATION (合): G = -0.8 — 能量耦合/束缚（引力）
  HARM   (害): G = +0.5   — 局部应力损耗
  PIERCE (破): G = +0.5   — 局部应力损耗
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
    "combination": -0.8,   # 合 — 能量耦合/束缚（引力，负值）
    "harm":        0.5,    # 害 — 局部应力损耗
    "pierce":      0.5,    # 破 — 局部应力损耗
}

# 距离衰减指数 k ∈ [1.2, 1.5]（近距离冲突权重更高）
DISTANCE_DECAY_EXPONENT: float = 1.35

# 贪合忘克阻尼系数
GREEDY_COMBINATION_DAMPING: float = 0.3

# Fact 权重提升阈值
STRESS_BOOST_TIER0_WEIGHT: float = 0.95
STRESS_BOOST_TOP_N: int = 5

# V17.32/33：能量转化效率常数 (Alpha)
ALPHA_CLASH: float = 0.15         # 冲力转化为显性 Qi 的效率（爆发）
ALPHA_COMBINATION: float = -0.10    # 合力对显性 Qi 的束缚系数（内敛）
ALPHA_HARM: float = 0.05          # 害/破的损耗系数

# ── 柱距映射 ──────────────────────────────────────────────────────────────────

# 四柱位置索引：year=0, month=1, day=2, hour=3
PILLAR_INDEX: Dict[str, int] = {
    "year": 0,
    "month": 1,
    "day": 2,
    "hour": 3,
}


def pillar_distance(p1: str, p2: str) -> int:
    """
    计算两柱之间的距离。
    相邻为 1，隔一柱为 2，隔两柱为 3。
    未知柱位返回 3（最大衰减）。
    """
    i1 = PILLAR_INDEX.get(p1)
    i2 = PILLAR_INDEX.get(p2)
    if i1 is None or i2 is None:
        return 3
    d = abs(i1 - i2)
    return max(1, d)


# ── 地支主气能量查询 ──────────────────────────────────────────────────────────

def _branch_dominant_ten_god(branch: str, daymaster: str) -> str:
    """返回地支主气（最高权重藏干）对应的十神名。"""
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
    """
    从 ten_gods_absolute 中查询该地支主气十神的绝对能量。
    若对应十神不存在于 scores 中，返回 0.0。
    """
    god = _branch_dominant_ten_god(branch, daymaster)
    if not god:
        return 0.0
    return float(ten_gods_absolute.get(god, 0.0))


# ── 应力事件 ──────────────────────────────────────────────────────────────────

@dataclass
class StressEvent:
    """一次矢量应力事件的完整记录。"""
    relation_type: str          # clash / combination / harm / pierce
    branches: List[str]         # 参与的地支
    pillars: List[str]          # 参与的柱位 (year/month/day/hour)
    q_i: float                  # 源柱地支主气能量
    q_j: float                  # 目标柱地支主气能量
    god_i: str                  # 源柱十神名
    god_j: str                  # 目标柱十神名
    distance: int               # 柱距
    g_coefficient: float        # G_v17 关系系数
    raw_stress: float           # 未经阻尼的 F 值
    damped_stress: float        # 经贪合忘克阻尼后的 F 值
    damping_applied: bool       # 是否应用了贪合阻尼

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_type": self.relation_type,
            "branches": self.branches,
            "pillars": self.pillars,
            "q_i": round(self.q_i, 2),
            "q_j": round(self.q_j, 2),
            "god_i": self.god_i,
            "god_j": self.god_j,
            "distance": self.distance,
            "g_coefficient": self.g_coefficient,
            "raw_stress": round(self.raw_stress, 4),
            "damped_stress": round(self.damped_stress, 4),
            "abs_stress": round(abs(self.damped_stress), 4),
            "damping_applied": self.damping_applied,
        }


# ── 核心计算函数 ──────────────────────────────────────────────────────────────

def calc_interaction_stress(
    q_i: float,
    q_j: float,
    distance: int,
    g_coefficient: float,
    *,
    decay_exponent: float = DISTANCE_DECAY_EXPONENT,
) -> float:
    """
    V17.31 矢量应力公式：

        F = G_v17 · (Q_i · Q_j) / d^k

    参数：
        q_i:             源柱十神绝对能量（来自 L0 ten_gods_absolute）
        q_j:             目标柱十神绝对能量
        distance:        柱距（相邻=1，隔一柱=2，隔两柱=3）
        g_coefficient:   关系系数（正=斥力/冲害，负=引力/合）
        decay_exponent:  距离衰减指数 k（默认 1.35）

    返回：
        F 应力值（正=斥力方向，负=引力方向）
    """
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
    """
    遍历 interaction_v2 中所有冲/合/害/破关系，
    逐一计算矢量应力 F 并返回 StressEvent 列表。

    参数：
        daymaster:          日主天干
        branches:           柱位→地支映射 {"year": "子", "month": "午", ...}
        ten_gods_absolute:  十神绝对能量 {"比肩": 85.6, "正官": 12.4, ...}
        interaction_v2:     L1 hydration 的 interaction_v2 结构体

    返回：
        StressEvent 列表，按 |damped_stress| 降序排列
    """
    if not daymaster or not branches or not ten_gods_absolute or not isinstance(interaction_v2, dict):
        return []

    events: List[StressEvent] = []

    # 映射关系类型 → (interaction_v2 的 key, G_v17 系数)
    relation_map: List[Tuple[str, str, float]] = [
        ("liu_chong", "clash", RELATION_COEFFICIENT["clash"]),
        ("liu_he", "combination", RELATION_COEFFICIENT["combination"]),
        ("liu_hai", "harm", RELATION_COEFFICIENT["harm"]),
        ("liu_po", "pierce", RELATION_COEFFICIENT["pierce"]),
        # 暗合 / 半合也视作合类
        ("an_he", "combination", RELATION_COEFFICIENT["combination"]),
        ("ban_he", "combination", RELATION_COEFFICIENT["combination"]),
    ]

    for v2_key, relation_type, g_coeff in relation_map:
        hits = interaction_v2.get(v2_key)
        if not isinstance(hits, list):
            continue
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            pair = hit.get("pair")
            pillars = hit.get("pillars")
            if not isinstance(pair, list) or len(pair) < 2:
                continue
            if not isinstance(pillars, list) or len(pillars) < 2:
                continue

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
                branches=[br_i, br_j],
                pillars=[p_i, p_j],
                q_i=q_i,
                q_j=q_j,
                god_i=god_i,
                god_j=god_j,
                distance=d,
                g_coefficient=g_coeff,
                raw_stress=raw_f,
                damped_stress=raw_f,  # 暂存，后续贪合忘克阻尼会修正
                damping_applied=False,
            ))

    # ── 贪合忘克处理 ──
    # 按柱位对分组，检查同一柱位对上是否同时存在合和克
    _apply_greedy_combination_damping(events)

    # 按 |damped_stress| 降序排列
    events.sort(key=lambda e: abs(e.damped_stress), reverse=True)
    return events


def _apply_greedy_combination_damping(events: List[StressEvent]) -> None:
    """
    贪合忘克：对同一柱位对，若 |F_合| > |F_克|，
    则对克性矢量（clash/harm/pierce）执行 0.3 的阻尼削减。
    """
    # 按柱位对分组
    pair_groups: Dict[Tuple[str, str], List[StressEvent]] = {}
    for ev in events:
        key = tuple(sorted(ev.pillars))  # type: ignore[arg-type]
        pair_groups.setdefault(key, []).append(ev)  # type: ignore[arg-type]

    for _pair_key, group in pair_groups.items():
        # 找出该对上的最大合力和最大克力
        max_combination_f = 0.0
        max_clash_f = 0.0
        for ev in group:
            f_abs = abs(ev.raw_stress)
            if ev.relation_type == "combination":
                max_combination_f = max(max_combination_f, f_abs)
            elif ev.relation_type in ("clash", "harm", "pierce"):
                max_clash_f = max(max_clash_f, f_abs)

        # 若 F_合 > F_克，对克性矢量施加阻尼
        if max_combination_f > max_clash_f and max_clash_f > 0:
            for ev in group:
                if ev.relation_type in ("clash", "harm", "pierce"):
                    ev.damped_stress = ev.raw_stress * GREEDY_COMBINATION_DAMPING
                    ev.damping_applied = True


# ── 对外接口：生成 clash_stress_map + Fact 提权列表 ──────────────────────────

def build_clash_stress_map(
    *,
    daymaster: str,
    branches: Dict[str, str],
    ten_gods_absolute: Dict[str, float],
    interaction_v2: Dict[str, Any],
) -> Dict[str, Any]:
    """
    构建完整的 clash_stress_map 并识别需要提权的高应力事件。

    返回：
        {
            "version": "vector_stress.v1",
            "events": [...],                   # StressEvent 列表（dicts）
            "top_stress_plugin_ids": [...],     # 前 N 个最高应力对应的 plugin_id
            "total_clash_energy": float,        # 所有斥力（正值）的应力总和
            "total_combination_energy": float,  # 所有引力（负值）的应力总和（取绝对值）
            "net_vector": float,                # 净矢量应力（正=整体斥力>引力）
            "damping_applied": bool,            # 是否有贪合忘克阻尼
        }
    """
    events = compute_stress_events(
        daymaster=daymaster,
        branches=branches,
        ten_gods_absolute=ten_gods_absolute,
        interaction_v2=interaction_v2,
    )

    total_clash = sum(ev.damped_stress for ev in events if ev.damped_stress > 0)
    total_combination = sum(abs(ev.damped_stress) for ev in events if ev.damped_stress < 0)
    net_vector = total_clash - total_combination
    any_damping = any(ev.damping_applied for ev in events)

    # 识别前 N 个最高应力事件对应的 plugin_id
    top_plugin_ids: List[str] = []
    energy_deltas: Dict[str, float] = {}
    
    for ev in events:
        # 记录前 N 个 ID 用于提权
        if len(top_plugin_ids) < STRESS_BOOST_TOP_N:
            pid = _relation_to_plugin_id(ev.relation_type)
            if pid and pid not in top_plugin_ids:
                top_plugin_ids.append(pid)
        
        # 转换应力为能量增量
        # 冲/害/破 (F > 0) -> 释放能量 (+)
        # 合 (F < 0) -> 束缚能量 (-)
        if ev.relation_type == "combination":
            dq = abs(ev.damped_stress) * ALPHA_COMBINATION
        elif ev.relation_type == "clash":
            dq = ev.damped_stress * ALPHA_CLASH
        else:
            dq = ev.damped_stress * ALPHA_HARM
        
        # 能量变动分摊到两个参与十神上
        energy_deltas[ev.god_i] = energy_deltas.get(ev.god_i, 0.0) + dq / 2
        energy_deltas[ev.god_j] = energy_deltas.get(ev.god_j, 0.0) + dq / 2

    return {
        "version": "vector_stress.v1",
        "events": [ev.to_dict() for ev in events],
        "top_stress_plugin_ids": top_plugin_ids,
        "total_clash_energy": round(total_clash, 4),
        "total_combination_energy": round(total_combination, 4),
        "net_vector": round(net_vector, 4),
        "damping_applied": any_damping,
        "energy_deltas": energy_deltas,  # 返回能量增量建议
    }


def _relation_to_plugin_id(relation_type: str) -> str:
    """将关系类型映射到 l1_manifest_hits 的 plugin_id。"""
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
    """
    将 clash_stress_map 中前 N 个最高应力冲突事件对应的
    Manifest Hit 的 priority 提升至 Tier 0 (0.95)。

    就地修改 hits dict。
    """
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
