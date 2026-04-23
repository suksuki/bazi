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
                    "effect_scores": {
                        "正官": {
                            "authority_profile": "高能躁动",
                            "authority_energy": 1.12,
                            "authority_stability": 0.18,
                            "authority_volatility": 0.64,
                            "authority_use_score": 0.42,
                            "authority_taboo_score": 0.88,
                        },
                        "正印": {
                            "authority_profile": "低能稳态",
                            "authority_energy": 0.72,
                            "authority_stability": 0.46,
                            "authority_volatility": 0.12,
                            "authority_use_score": 0.84,
                            "authority_taboo_score": 0.14,
                        },
                    },
                    "judgement_bias_protocol": {
                        "summary": {
                            "entry_count": 3,
                            "total_use_bias": 0.42,
                            "total_taboo_bias": 0.28,
                        }
                    },
                    "stage_bias_protocol": {
                        "summary": {
                            "entry_count": 2,
                            "total_use_boost": 0.18,
                            "total_taboo_boost": 0.06,
                            "total_stability_boost": 0.09,
                            "total_volatility_boost": 0.12,
                        }
                    },
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
    assert "体用双轴合同" in joined
    assert "正官 高能躁动" in joined
    assert "判定偏置合同" in joined
    assert "阶段偏置摘要" in joined


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
                "climate_field": {
                    "state": "偏暖",
                    "thermal_index": 0.42,
                    "moisture_index": 0.18,
                    "climate_tension": 0.26,
                    "source_by_element": {
                        "火": {"thermal": 1.2, "moisture": -0.8},
                        "木": {"thermal": 0.4, "moisture": 0.5},
                    },
                },
                "climate_modifier_layer": {
                    "yongshen_priority_delta": {"食神": 0.12, "正印": -0.08},
                },
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
            "meta": {
                "climate_theme": {
                    "contract": "v17.climate.theme.v1",
                    "state": "偏暖",
                    "favored_gods": ["食神", "正财"],
                    "strained_gods": ["正印"],
                    "pattern_survival": [{"label": "食伤财链", "bucket": "存续增强", "delta": 0.22}],
                    "prompt_digest": "偏暖，食神/正财顺势，正印承压，食伤财链存续增强",
                }
            },
        }
    )

    joined = "\n".join(rows)
    assert "调候合同" in joined
    assert "调候摘要：偏暖" in joined
    assert "调候修正层：食神+0.12" in joined
    assert "调候专题合同" in joined
    assert "调候专题摘要：偏暖" in joined
    assert "食伤财链存续增强" in joined
    assert "关系动力学合同" in joined
    assert "子午六冲 激发58%" in joined
    assert "稳定-74%" in joined
    assert "寅午戌三合火局 组织化52%" in joined
    assert "运流解释合同" in joined
    assert "大运更像背景场" in joined


def test_physics_canonical_materializes_blind_theme_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "luck_pillar": "己亥",
            "flow_pillar": "丙午",
            "meta": {
                "blind_theme": {
                    "contract": "v17.blind.theme.v1",
                    "primary_route": "食伤制杀",
                    "body_mode": "disturbed_body",
                    "use_candidates": ["食伤", "七杀"],
                    "taboo_candidates": ["强印"],
                    "house_roles": {"食伤": "outside", "七杀": "inside", "偏财": "inside"},
                    "runtime_switches": ["己亥运中食伤生财抢权"],
                    "prompt_digest": "主线食伤制杀；体态扰体未换体；家里七杀/偏财；家外食伤",
                }
            },
        }
    )

    joined = "\n".join(rows)
    assert "盲派专题合同" in joined
    assert "不直接覆盖最终 authority" in joined
    assert "盲派专题摘要" in joined
    assert "主线食伤制杀" in joined
    assert "家里七杀/偏财" in joined


def test_physics_canonical_materializes_xiangfa_theme_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "luck_pillar": "庚子",
            "flow_pillar": "丙午",
            "meta": {
                "xiangfa_theme": {
                    "contract": "v17.xiangfa.theme.v1",
                    "authority_bridge_mode": "disabled",
                    "semantic_mapping": ["体用主轴偏向「食神 / 正财」", "家外「食伤」牵动家内「七杀 / 偏财」"],
                    "evidence": ["体用裁决来源：食神 / 正财 / 正印"],
                    "narrative_hint": ["当前叙事不宜只讲吉凶，应同时描述收益和代价。"],
                    "event_framing": ["主用与代价并存，适合叙述为“机会伴随成本”"],
                    "prompt_digest": "体用主轴偏向「食神 / 正财」；主用与代价并存，适合叙述为“机会伴随成本”",
                    "source_topics": ["authority", "blind", "climate"],
                }
            },
        }
    )

    joined = "\n".join(rows)
    assert "象法专题合同" in joined
    assert "不修改能量、不写入 bias" in joined
    assert "象法证据：体用裁决来源：食神 / 正财 / 正印" in joined
    assert "象法专题摘要：" in joined
    assert "来源 authority/blind/climate" in joined


def test_physics_canonical_materializes_blind_bias_bridge_lines() -> None:
    rows = PhysicsCanonicalService.materialize_prompt_lines(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "luck_pillar": "庚子",
            "flow_pillar": "丙午",
            "meta": {
                "god_ring_authority": {
                    "effect_scores": {
                        "伤官": {
                            "authority_profile": "高能躁动",
                            "authority_energy": 1.06,
                            "authority_stability": 0.24,
                            "authority_volatility": 0.58,
                            "authority_use_score": 0.76,
                            "authority_taboo_score": 0.18,
                        }
                    },
                    "blind_bias_protocol": {
                        "contract": "v17.blind.bias.v1",
                        "authority_bridge_mode": "bias_only",
                        "primary_route": "食伤生财",
                        "body_mode": "disturbed_body",
                        "summary": {
                            "use_total": 0.31,
                            "taboo_total": 0.18,
                            "switch_count": 1,
                        },
                    },
                }
            },
        }
    )

    joined = "\n".join(rows)
    assert "盲派桥接合同" in joined
    assert "bias_only" in joined
    assert "食伤生财" in joined
    assert "推用0.31" in joined
