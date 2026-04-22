"""单元：六柱张量完备性与元数据稳定门控。"""
from __future__ import annotations

import asyncio

from v17_rebirth.backend.services.physics_canonical import (
    PhysicsCanonicalService,
    V17PhysicsMetadata,
    six_pillars_tensor_complete,
)


def test_six_pillars_incomplete_missing_hour() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": ""},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert six_pillars_tensor_complete(pt) is False


def test_six_pillars_complete() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert six_pillars_tensor_complete(pt) is True


def test_v17_physics_metadata_stable_requires_flag() -> None:
    ok_pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
        "meta": {"v17_physics_stable": True},
    }
    assert asyncio.run(V17PhysicsMetadata(ok_pt).is_stable()) is True

    bad = dict(ok_pt)
    bad["meta"] = {"v17_physics_stable": False}
    assert asyncio.run(V17PhysicsMetadata(bad).is_stable()) is False


def test_v17_physics_metadata_missing_meta_unstable() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
    }
    assert asyncio.run(V17PhysicsMetadata(pt).is_stable()) is False


def test_physics_canonical_materializes_ten_god_prompt_contract_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
            "luck_pillar": "庚戌",
            "flow_pillar": "丙午",
            "ten_gods_base_l0": {"偏印": 34.54, "七杀": 13.22},
            "ten_gods_decomposition_l0": {
                "偏印": {
                    "manifest": 20.0,
                    "root": 14.54,
                    "momentum": 0.0,
                    "momentum_month_order": 0.0,
                    "momentum_stage": 0.0,
                    "momentum_stage_lu": 0.0,
                    "momentum_stage_blade": 0.0,
                    "momentum_stage_general": 0.0,
                    "momentum_structure": 0.0,
                    "momentum_auxiliary": 0.0,
                    "momentum_other": 0.0,
                    "hidden": 0.0,
                    "total": 34.54,
                },
                "七杀": {
                    "manifest": 12.42,
                    "root": 0.0,
                    "momentum": 0.8,
                    "momentum_month_order": 0.0,
                    "momentum_stage": 0.0,
                    "momentum_stage_lu": 0.0,
                    "momentum_stage_blade": 0.0,
                    "momentum_stage_general": 0.0,
                    "momentum_structure": 0.0,
                    "momentum_auxiliary": 0.8,
                    "momentum_other": 0.0,
                    "hidden": 0.0,
                    "total": 13.22,
                },
            },
            "ten_gods_runtime": {"偏印": 34.54, "七杀": 13.22},
            "total_energy_index": 147.68,
        }
    )

    joined = "\n".join(rows)
    assert "十神解释合同" in joined
    assert "显化、根气、势能、潜藏残值" in joined
    assert "绝对物理强度" in joined
    assert "十神分解：" in joined
    assert "十神势能细项：" in joined


def test_physics_canonical_materializes_core_flux_summary_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
            "luck_pillar": "庚戌",
            "flow_pillar": "丙午",
            "meta": {
                "god_ring_authority": {
                    "core_flux_meta": {
                        "interaction_matrix": [
                            {
                                "source": "食神",
                                "target": "偏财",
                                "net": 0.386,
                                "support_ratio": 0.82,
                                "resist_ratio": 0.18,
                            },
                            {
                                "source": "伤官",
                                "target": "正官",
                                "net": -0.417,
                                "support_ratio": 0.14,
                                "resist_ratio": 0.86,
                            },
                        ],
                        "tension_pairs": [
                            {
                                "left": "伤官",
                                "right": "正官",
                                "mode": "tension",
                                "score": 0.317,
                            }
                        ],
                    }
                }
            },
        }
    )

    joined = "\n".join(rows)
    assert "做功解释合同" in joined
    assert "做功方向矩阵" in joined
    assert "食神->偏财" in joined
    assert "伤官->正官" in joined
    assert "做功回路" in joined


def test_physics_canonical_frontloads_relation_and_pattern_percentages() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
            "luck_pillar": "庚戌",
            "flow_pillar": "丙午",
            "energy_meta": {
                "relation_formation_summary": [
                    {
                        "formation_label": "寅午戌三合火局",
                        "formation_percent": 78.6,
                        "family_factor": 3.5,
                        "status": "受扰成局",
                        "conflict_damping": 0.77,
                        "projection_preview": ["劫财65%", "比肩35%"],
                    }
                ]
            },
            "meta": {
                "plugin_claims": [
                    {
                        "plugin_id": "classical.pattern.officer.v1",
                        "pattern_candidate": "正官格",
                        "pattern_confidence_percent": 65.0,
                        "target_god": "正官",
                        "pattern_scope_label": "原局",
                    }
                ]
            },
        }
    )

    joined = "\n".join(rows)
    assert "合化解释合同" in joined
    assert "寅午戌三合火局 78.6%" in joined
    assert "格局解释合同" in joined
    assert "正官格 65.0%" in joined


def test_physics_canonical_materializes_relation_dynamics_and_runtime_field_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
            "luck_pillar": "庚戌",
            "flow_pillar": "丙午",
            "energy_meta": {
                "relation_dynamics_summary": [
                    {
                        "label": "子午六冲",
                        "energy_axis": "激发",
                        "energy_effect_ratio": 0.58,
                        "stability_delta_ratio": -0.74,
                        "free_energy_lock_ratio": 0.0,
                        "note": "冲不等于没能量，而是把静态资源推成动态事件。",
                    },
                    {
                        "label": "寅午戌三合火局",
                        "energy_axis": "组织化",
                        "energy_effect_ratio": 0.52,
                        "stability_delta_ratio": 0.31,
                        "free_energy_lock_ratio": 0.18,
                        "note": "合局更像组织化与重分配，不等于总能量线性增加。",
                    },
                ]
            },
        }
    )

    joined = "\n".join(rows)
    assert "关系动力学合同" in joined
    assert "子午六冲 激发58%" in joined
    assert "稳定-74%" in joined
    assert "寅午戌三合火局 组织化52%" in joined
    assert "运流解释合同" in joined
    assert "大运更像背景场" in joined
