from __future__ import annotations

from app.services.helpers.sys_core_physics_plugin import (
    L1_SANHE_SKILL_ID,
    SYS_CORE_PHYSICS_BUNDLE_SRC_KEY,
    extract_sanhe_clusters,
    run_l1_branch_gov_kill_mix_plugin,
    run_l1_branch_liuchong_plugin,
    run_l1_branch_liuhe_plugin,
    run_l1_branch_sanhe_plugin,
    run_sys_core_physics_bundle_plugin,
)


def test_extract_sanhe() -> None:
    pt = {"composite_field_impact": {"sanhe_clusters": [{"branches": ["巳", "酉", "丑"], "energy_vault_status": "AGGREGATED"}]}}
    rows = extract_sanhe_clusters(pt)
    assert len(rows) == 1
    assert rows[0]["branches"] == ["巳", "酉", "丑"]


def test_run_l1_branch_sanhe_plugin_row() -> None:
    pt = {"composite_field_impact": {"sanhe_clusters": [{"branches": ["巳", "酉", "丑"], "energy_vault_status": "AGGREGATED"}]}}
    row = run_l1_branch_sanhe_plugin(physics_tensor=pt, metadata={})
    assert row.get("confidence_score", 0) >= 0.9
    assert row.get("skill_id") == L1_SANHE_SKILL_ID
    assert len(row.get("sanhe_clusters") or []) == 1


def test_run_named_l1_plugins_write_standard_shape() -> None:
    pt: dict = {
        "meta": {},
        SYS_CORE_PHYSICS_BUNDLE_SRC_KEY: {
            "composite_field_impact": {"sanhe_clusters": [{"branches": ["寅", "午", "戌"], "nodes": []}]},
            "l1_atomic_pipeline": {"steps": [{"op_id": "x", "label": "y"}]},
        },
    }
    md = {
        "conflict_matrix": {
            "points": [
                {"kind": "clash", "positions": ["year_branch", "day_branch"], "detail": "子午冲"},
                {"kind": "combine", "positions": ["month_branch", "hour_branch"], "detail": "子丑合"},
            ]
        }
    }
    synth = {
        **pt,
        "composite_field_impact": pt[SYS_CORE_PHYSICS_BUNDLE_SRC_KEY]["composite_field_impact"],
        "l1_atomic_pipeline": pt[SYS_CORE_PHYSICS_BUNDLE_SRC_KEY]["l1_atomic_pipeline"],
    }
    sanhe = run_l1_branch_sanhe_plugin(physics_tensor=synth, metadata=md)
    liuhe = run_l1_branch_liuhe_plugin(physics_tensor=synth, metadata=md)
    chong = run_l1_branch_liuchong_plugin(physics_tensor=synth, metadata=md)
    gkm = run_l1_branch_gov_kill_mix_plugin(physics_tensor=synth, metadata=md)
    bundle = run_sys_core_physics_bundle_plugin(physics_tensor=pt, metadata=md)
    assert isinstance(sanhe, dict) and sanhe.get("sanhe_clusters")
    assert isinstance(liuhe, dict) and liuhe.get("evidence") is not None
    assert isinstance(chong, dict)
    assert isinstance(gkm, dict)
    assert isinstance(bundle, dict)
    assert bundle.get("sanhe_clusters")
    assert SYS_CORE_PHYSICS_BUNDLE_SRC_KEY not in pt

