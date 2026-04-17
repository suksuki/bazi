"""干支维轴算子测试（不经过 app.services）。"""
from __future__ import annotations

from app.plugins.base_physics.core_operators import op_interdimensional
from app.plugins.base_physics.core_operators.op_interdimensional import StemBranchCouplingEngine
from app.plugins.base.interactions import l1_atomic_plugin


def test_stem_branch_engine_same_pillar_conductivity():
    pillars = {"year": {"stem": "甲", "branch": "子"}}
    eng = StemBranchCouplingEngine(
        pillars=pillars,
        stems_by_pillar={"year": "甲"},
        branches_by_pillar={"year": "子"},
        merged_config={"CONDUCTIVITY_DECAY_RATE": 0.7, "INTERDIMENSIONAL_BARRIER_STRENGTH": 1.0, "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0},
    )
    assert eng.causal_conductivity_base({"pillar": "year", "stem": "甲"}, {"pillar": "year", "branch": "子"}) == 1.0


def test_stem_branch_engine_root_cross_pillar():
    """通根：甲在寅中有根 → 跨柱基础 0.8，再乘衰减。"""
    pillars = {
        "year": {"stem": "甲", "branch": "寅"},
        "month": {"stem": "庚", "branch": "午"},
    }
    eng = StemBranchCouplingEngine(
        pillars=pillars,
        stems_by_pillar={"year": "甲", "month": "庚"},
        branches_by_pillar={"year": "寅", "month": "午"},
        merged_config={
            "CONDUCTIVITY_DECAY_RATE": 0.7,
            "INTERDIMENSIONAL_BARRIER_STRENGTH": 0.0,
            "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0,
        },
    )
    c = eng.causal_conductivity_base({"pillar": "year", "stem": "甲"}, {"pillar": "month", "branch": "午"})
    assert abs(c - 0.8) < 1e-9


def test_stem_branch_engine_no_root_zero():
    eng = StemBranchCouplingEngine(
        pillars={},
        stems_by_pillar={"year": "庚", "month": "乙"},
        branches_by_pillar={"year": "子", "month": "午"},
        merged_config={"CONDUCTIVITY_DECAY_RATE": 0.7, "INTERDIMENSIONAL_BARRIER_STRENGTH": 0.0, "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0},
    )
    c = eng.causal_conductivity_base({"pillar": "year", "stem": "庚"}, {"pillar": "month", "branch": "午"})
    assert c == 0.0


def test_stem_branch_engine_clash_activation_half():
    """无通根但月支柱参与其它冲点 → 基础 0.5。"""
    eng = StemBranchCouplingEngine(
        pillars={},
        stems_by_pillar={"year": "庚", "month": "乙"},
        branches_by_pillar={"year": "子", "month": "午"},
        merged_config={"CONDUCTIVITY_DECAY_RATE": 0.7, "INTERDIMENSIONAL_BARRIER_STRENGTH": 0.0, "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0},
    )
    act = [{"kind": "clash", "positions": ["month_branch", "day_branch"], "detail": "子午"}]
    c = eng.causal_conductivity_base(
        {"pillar": "year", "stem": "庚"},
        {"pillar": "month", "branch": "午"},
        activation_conflict_points=act,
    )
    assert abs(c - 0.5) < 1e-9


def test_shield_log_line_format():
    s = op_interdimensional.shield_log_line("甲", "午")
    assert "[CAUSAL_SHIELDED]" in s
    assert "甲" in s and "午" in s
    assert "无功干扰" in s


def test_compute_solid_ghost_ratio():
    steps = [{"conductivity_effective": 0.5}, {"conductivity_effective": 1.0}]
    r = op_interdimensional.compute_solid_ghost_ratio(
        steps=steps,
        dimensional_shield_logs=["x"],
        ghost_damping=0.3,
    )
    assert "solid_fraction" in r and "ghost_fraction" in r
    assert abs(r["solid_fraction"] + r["ghost_fraction"] - 1.0) < 1e-6


def test_run_l1_mixed_positions_emits_shield_log():
    """庚干无通根于子/午/辰/子 → 跨维传导 0，全屏蔽日志。"""
    pillars = {
        "year": {"stem": "庚", "branch": "子"},
        "month": {"stem": "甲", "branch": "午"},
        "day": {"stem": "丙", "branch": "辰"},
        "hour": {"stem": "壬", "branch": "子"},
    }
    branches = {k: str(v["branch"]) for k, v in pillars.items()}
    points = [{"kind": "clash", "positions": ["year_stem", "month_branch"], "detail": "干克支（测）"}]

    def pillar_raw(_: str) -> float:
        return 50.0

    steps, _, _, shield_logs = l1_atomic_plugin.run_l1_atomic_plugin_pool(
        points=points,
        branches=branches,
        pillars=pillars,
        day_stem="丙",
        pillar_raw=pillar_raw,
        params={
            "L1_CLASH_INTENSITY": 1.0,
            "L1_OP_PROD_ETA": 1.0,
            "L1_OP_DEST_ETA": 1.0,
            "L1_OP_CONN_ETA": 1.0,
            "INTERDIMENSIONAL_CONDUCTIVITY": 0.0,
            "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0,
        },
        settings={"GRAVE_BURST_MULTIPLIER": 1.3},
    )
    clash = [s for s in steps if s.get("plugin") == "base.clash"]
    assert len(clash) == 1
    assert float((clash[0].get("delta") or {}).get("abs_loss") or 0) == 0.0
    assert len(shield_logs) >= 1
    assert "无功干扰" in shield_logs[0]


def test_physics_settings_shim_import():
    from app.physics_settings import DEFAULT_PHYSICS_SETTINGS

    assert "INTERDIMENSIONAL_BARRIER_STRENGTH" in DEFAULT_PHYSICS_SETTINGS
