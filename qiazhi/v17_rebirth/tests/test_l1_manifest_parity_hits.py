from __future__ import annotations

from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor


def test_hydrate_v17_physics_tensor_populates_manifest_parity_hits() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "丙午",
            "day": "戊戌",
            "hour": "壬申",
        },
        "ten_gods_absolute_intensity": {"比肩": 22.0, "食神": 48.0, "正财": 31.0},
        "total_energy_index": 126.0,
    }

    hydrate_v17_physics_tensor(pt)

    meta = pt.get("meta") or {}
    hits = meta.get("l1_manifest_hits") or {}

    assert "l1.physics.op_status" in hits
    assert "l1.physics.op_branch_sanhe" in hits
    assert "l1.physics.op_branch_muku" in hits
    assert meta.get("l1_status_v1", {}).get("phase") == "帝旺"
    assert hits["l1.physics.op_status"].get("framework_standard") == "v17_manifest_unified"
    assert hits["l1.physics.op_branch_sanhe"].get("hit_source") == "l1_meta_hydration"
    assert isinstance(hits["l1.physics.op_branch_muku"].get("evidence"), dict)


def test_hydrate_v17_physics_tensor_populates_anhe_and_banhe_hits() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "乙巳",
            "day": "丙卯",
            "hour": "丁未",
        },
        "ten_gods_absolute_intensity": {"食神": 32.0, "偏印": 12.0},
        "total_energy_index": 62.0,
    }

    hydrate_v17_physics_tensor(pt)

    hits = (pt.get("meta") or {}).get("l1_manifest_hits") or {}
    assert "l1.physics.op_branch_anhe" in hits
    assert "l1.physics.op_branch_banhe" in hits


def test_hydrate_v17_physics_tensor_populates_sanhui_hits() -> None:
    pt = {
        "four_pillars": {
            "year": "甲寅",
            "month": "乙卯",
            "day": "丙辰",
            "hour": "丁巳",
        },
        "ten_gods_absolute_intensity": {"正印": 20.0, "食神": 32.0},
        "total_energy_index": 88.0,
    }

    hydrate_v17_physics_tensor(pt)

    meta = pt.get("meta") or {}
    hits = meta.get("l1_manifest_hits") or {}
    interaction_v2 = meta.get("interaction_v2") or {}

    assert "l1.physics.op_branch_sanhui" in hits
    assert interaction_v2.get("san_hui")
    assert hits["l1.physics.op_branch_sanhui"].get("label") == "三会成势"
