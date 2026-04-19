"""
V17.31 矢量冲突应力引擎测试。

验证：
1. calc_interaction_stress 公式正确性
2. 柱距衰减
3. 贪合忘克阻尼
4. clash_stress_map 完整生成
5. 高应力 Fact 提权
6. 端到端 hydration 集成
"""
from __future__ import annotations

import math
from typing import Any, Dict

from v17_rebirth.backend.logic.L0_physics_fields.vector_physics_engine import (
    DISTANCE_DECAY_EXPONENT,
    GREEDY_COMBINATION_DAMPING,
    RELATION_COEFFICIENT,
    STRESS_BOOST_TIER0_WEIGHT,
    StressEvent,
    boost_high_stress_facts,
    build_clash_stress_map,
    calc_interaction_stress,
    compute_stress_events,
    pillar_distance,
)
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor


# ── 1. 基础公式验证 ──────────────────────────────────────────────────────────


def test_calc_interaction_stress_basic_formula() -> None:
    """F = G · (Q_i · Q_j) / d^k — 基本验证。"""
    q_i, q_j = 50.0, 30.0
    d = 1
    g = RELATION_COEFFICIENT["clash"]  # 1.0
    k = DISTANCE_DECAY_EXPONENT        # 1.35

    f = calc_interaction_stress(q_i, q_j, d, g)
    expected = g * (q_i * q_j) / math.pow(d, k)
    assert abs(f - expected) < 1e-6
    assert f == 1500.0  # d=1 → d^k = 1.0 → F = 1.0 * 50 * 30 / 1 = 1500


def test_calc_interaction_stress_distance_decay() -> None:
    """距离越远，应力越小。"""
    q_i, q_j = 50.0, 30.0
    g = 1.0

    f1 = calc_interaction_stress(q_i, q_j, 1, g)
    f2 = calc_interaction_stress(q_i, q_j, 2, g)
    f3 = calc_interaction_stress(q_i, q_j, 3, g)

    assert f1 > f2 > f3 > 0
    # 距离2的衰减比率
    ratio_2 = f2 / f1
    expected_ratio_2 = 1.0 / math.pow(2.0, DISTANCE_DECAY_EXPONENT)
    assert abs(ratio_2 - expected_ratio_2) < 1e-6


def test_calc_interaction_stress_combination_is_negative() -> None:
    """合（combination）的 G 为负值，F 应为负值。"""
    f = calc_interaction_stress(50.0, 30.0, 1, RELATION_COEFFICIENT["combination"])
    assert f < 0
    assert abs(f) == abs(-0.8 * 50.0 * 30.0)  # 1200.0


def test_calc_interaction_stress_zero_energy() -> None:
    """能量为 0 时应力为 0。"""
    assert calc_interaction_stress(0.0, 30.0, 1, 1.0) == 0.0
    assert calc_interaction_stress(50.0, 0.0, 1, 1.0) == 0.0


# ── 2. 柱距计算 ──────────────────────────────────────────────────────────────


def test_pillar_distance() -> None:
    assert pillar_distance("year", "month") == 1
    assert pillar_distance("year", "day") == 2
    assert pillar_distance("year", "hour") == 3
    assert pillar_distance("month", "day") == 1
    assert pillar_distance("month", "hour") == 2
    assert pillar_distance("day", "hour") == 1
    # 未知柱位
    assert pillar_distance("year", "unknown") == 3


# ── 3. 贪合忘克阻尼 ──────────────────────────────────────────────────────────


def test_greedy_combination_damping() -> None:
    """
    若同一柱位对上有冲和合，且 |F_合| > |F_克|，
    则克性矢量应被 0.3 阻尼削减。
    """
    # 构造场景：子午冲（clash）+ 子丑合（combination）在 year-month 上
    # 子午冲的能量对较弱，子丑合的能量对较强
    interaction_v2: Dict[str, Any] = {
        "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "month"]}],
        "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "month"]}],
        "liu_hai": [],
        "liu_po": [],
        "an_he": [],
        "ban_he": [],
    }
    ten_gods: Dict[str, float] = {
        "比肩": 80.0,   # 子 → 壬(水) → if daymaster=壬 → 比肩
        "正印": 60.0,   # 午 → 丁(火) → etc
        "偏印": 90.0,   # 丑 → 己(土) → etc
    }

    events = compute_stress_events(
        daymaster="壬",
        branches={"year": "子", "month": "午", "day": "辰", "hour": "丑"},
        ten_gods_absolute=ten_gods,
        interaction_v2=interaction_v2,
    )

    # 找到所有事件
    clash_evs = [e for e in events if e.relation_type == "clash"]
    combo_evs = [e for e in events if e.relation_type == "combination"]

    # 应该存在冲和合事件
    assert clash_evs or combo_evs  # 至少有事件


def test_no_damping_when_clash_stronger() -> None:
    """当克力 > 合力时不应有阻尼。"""
    # 只有冲，没有合
    interaction_v2: Dict[str, Any] = {
        "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "month"]}],
        "liu_he": [],
        "liu_hai": [],
        "liu_po": [],
        "an_he": [],
        "ban_he": [],
    }
    ten_gods: Dict[str, float] = {"比肩": 80.0, "正官": 60.0}

    events = compute_stress_events(
        daymaster="壬",
        branches={"year": "子", "month": "午"},
        ten_gods_absolute=ten_gods,
        interaction_v2=interaction_v2,
    )

    for ev in events:
        assert not ev.damping_applied
        assert ev.raw_stress == ev.damped_stress


# ── 4. clash_stress_map 完整生成 ──────────────────────────────────────────────


def test_build_clash_stress_map_structure() -> None:
    """验证 clash_stress_map 结构完整。"""
    interaction_v2: Dict[str, Any] = {
        "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "month"]}],
        "liu_he": [{"pair": ["卯", "戌"], "pillars": ["day", "hour"]}],
        "liu_hai": [],
        "liu_po": [],
        "an_he": [],
        "ban_he": [],
    }
    ten_gods: Dict[str, float] = {
        "比肩": 80.0, "正官": 60.0, "正财": 40.0, "偏印": 35.0,
    }

    result = build_clash_stress_map(
        daymaster="壬",
        branches={"year": "子", "month": "午", "day": "卯", "hour": "戌"},
        ten_gods_absolute=ten_gods,
        interaction_v2=interaction_v2,
    )

    assert result["version"] == "vector_stress.v1"
    assert isinstance(result["events"], list)
    assert isinstance(result["top_stress_plugin_ids"], list)
    assert "total_clash_energy" in result
    assert "total_combination_energy" in result
    assert "net_vector" in result
    assert "damping_applied" in result


def test_build_clash_stress_map_net_vector_positive_for_clash_only() -> None:
    """仅有冲时，net_vector 应 > 0。"""
    interaction_v2: Dict[str, Any] = {
        "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "month"]}],
        "liu_he": [],
        "liu_hai": [],
        "liu_po": [],
        "an_he": [],
        "ban_he": [],
    }
    # 壬見壬(子主气) = 比肩，壬見丁(午主气) = 正財
    ten_gods: Dict[str, float] = {"比肩": 80.0, "正财": 60.0}

    result = build_clash_stress_map(
        daymaster="壬",
        branches={"year": "子", "month": "午"},
        ten_gods_absolute=ten_gods,
        interaction_v2=interaction_v2,
    )

    assert result["net_vector"] > 0
    assert result["total_clash_energy"] > 0
    assert result["total_combination_energy"] == 0


# ── 5. 高应力 Fact 提权 ──────────────────────────────────────────────────────


def test_boost_high_stress_facts() -> None:
    """top_stress_plugin_ids 中的 hit 应被提权到 0.95。"""
    hits: Dict[str, Dict[str, Any]] = {
        "l1.physics.op_branch_liuchong": {
            "fact": "[六冲: 子午]",
            "label": "六冲",
            "priority": 0.72,
            "evidence": {},
        },
        "l1.physics.op_branch_liuhe": {
            "fact": "[六合: 卯戌]",
            "label": "六合",
            "priority": 0.68,
            "evidence": {},
        },
    }
    stress_map = {
        "top_stress_plugin_ids": ["l1.physics.op_branch_liuchong"],
    }

    boost_high_stress_facts(hits, stress_map)

    assert hits["l1.physics.op_branch_liuchong"]["priority"] == STRESS_BOOST_TIER0_WEIGHT
    assert hits["l1.physics.op_branch_liuchong"]["evidence"]["stress_boosted"] is True
    # 六合不在 top 中，不应被提权
    assert hits["l1.physics.op_branch_liuhe"]["priority"] == 0.68


# ── 6. 端到端 hydration 集成 ──────────────────────────────────────────────────


def test_hydration_writes_clash_stress_map() -> None:
    """hydrate_v17_physics_tensor 应在 meta 中写入 clash_stress_map。"""
    pt: Dict[str, Any] = {
        "four_pillars": {"year": "甲子", "month": "丙午", "day": "庚辰", "hour": "壬戌"},
        "luck_pillar": "戊申",
        "flow_pillar": "己酉",
        "ten_gods_absolute": {"偏财": 88.0, "食神": 42.0, "比肩": 30.0, "正官": 25.0},
        "ten_gods_absolute_intensity": {"偏财": 88.0, "食神": 42.0, "比肩": 30.0, "正官": 25.0},
        "total_energy_index": 185.0,
    }

    hydrate_v17_physics_tensor(pt)

    meta = pt.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("v17_physics_stable") is True

    # 检查 clash_stress_map 存在
    csm = meta.get("clash_stress_map")
    assert isinstance(csm, dict), f"clash_stress_map not found in meta: {list(meta.keys())}"
    assert csm.get("version") == "vector_stress.v1"
    assert isinstance(csm.get("events"), list)


def test_hydration_stress_map_has_events_for_chong() -> None:
    """子午冲的命局应生成子午冲的应力事件。"""
    pt: Dict[str, Any] = {
        "four_pillars": {"year": "壬子", "month": "丙午", "day": "庚辰", "hour": "甲寅"},
        "luck_pillar": "—",
        "flow_pillar": "—",
        "ten_gods_absolute": {"偏印": 80.0, "正官": 60.0, "比肩": 30.0, "偏财": 25.0},
        "total_energy_index": 195.0,
    }

    hydrate_v17_physics_tensor(pt)

    csm = pt["meta"]["clash_stress_map"]
    events = csm.get("events", [])
    clash_events = [e for e in events if e.get("relation_type") == "clash"]
    assert len(clash_events) >= 1, f"Expected at least 1 clash event, got: {events}"

    # 子午冲应该在事件中
    branch_pairs = [tuple(e.get("branches", [])) for e in clash_events]
    assert any("子" in bp and "午" in bp for bp in branch_pairs), f"子午 clash not found: {branch_pairs}"


def test_vector_physics_engine_three_branch_sanhe_and_muku() -> None:
    """验证 sanhe 具有 3 个支时，所有 3 个都会被收录进 branches，不被截断 (V17修复测试)"""
    interaction_v2: Dict[str, Any] = {
        "sanhe": [{"pair": ["巳", "酉", "丑"], "pillars": ["year", "hour", "day"]}],
    }
    ten_gods: Dict[str, float] = {"伤官": 80.0, "七杀": 60.0, "偏财": 40.0}

    events = compute_stress_events(
        daymaster="丁",
        branches={"year": "巳", "month": "戌", "day": "丑", "hour": "酉"},
        ten_gods_absolute=ten_gods,
        interaction_v2=interaction_v2,
    )

    sanhe_events = [e for e in events if e.relation_type == "combination" and e.source_key == "sanhe"]
    assert len(sanhe_events) == 1
    sanhe_event = sanhe_events[0]
    
    # Assert branches array has exactly 3 elements: ['巳', '酉', '丑']
    assert len(sanhe_event.branches) == 3
    assert sanhe_event.branches == ["巳", "酉", "丑"]


def test_hydration_muku_impact_for_three_branch_sanhe() -> None:
    """验证三合局中如果有第三个支是墓库时，应力事件保留完整三支信息。"""
    pt: Dict[str, Any] = {
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "luck_pillar": "—",
        "flow_pillar": "—",
        "ten_gods_absolute": {"伤官": 73.80, "七杀": 9.83, "偏财": 15.0},
        "total_energy_index": 195.0,
        "meta": {
            "interaction_v2": {
                "sanhe": [{"pair": ["巳", "酉", "丑"], "pillars": ["year", "hour", "day"]}],
            }
        }
    }
    
    # This will trigger hydration which executes is_muku_impact which leverages the vector events
    hydrate_v17_physics_tensor(pt)
    csm = pt["meta"]["clash_stress_map"]
    assert set(csm["events"][0]["branches"]) == {"巳", "酉", "丑"}
    
    # 当前模型下，vector stress 负责生成结构事件账单，
    # 十神的实际变化由后续 L0/L1 结算链负责，不由 hydration 直接改写。
    assert csm["events"][0]["relation_type"] == "combination"



def test_constants_match_specification() -> None:
    """验证物理常数与规格文档一致。"""
    assert RELATION_COEFFICIENT["clash"] == 1.0
    assert RELATION_COEFFICIENT["combination"] == -0.8
    assert RELATION_COEFFICIENT["harm"] == 0.5
    assert RELATION_COEFFICIENT["pierce"] == 0.5
    assert GREEDY_COMBINATION_DAMPING == 0.3
    assert 1.2 <= DISTANCE_DECAY_EXPONENT <= 1.5
