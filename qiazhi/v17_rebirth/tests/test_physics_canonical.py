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
