from __future__ import annotations

from app.plugins.base_physics.manifest_loader import load_l1_physics_manifest, reload_l1_physics_manifest_for_tests


def test_l1_physics_manifest_loads():
    doc = load_l1_physics_manifest()
    assert doc.get("schema") == "l1_physics_manifest.v1"
    assert isinstance(doc.get("operators"), list)
    ids = {op["id"] for op in doc["operators"]}
    assert "base.physics.op_production" in ids
    assert "base.physics.op_destruction" in ids
    assert "base.physics.op_interdimensional" in ids
    assert "base.physics.op_shangguan_jian_guan" in ids
    tiers = doc.get("conductivity_tiers", {}).get("tiers", [])
    vals = {t["value"] for t in tiers}
    assert vals == {1.0, 0.8, 0.5, 0.0}


def test_manifest_reload_for_tests():
    a = load_l1_physics_manifest()
    b = reload_l1_physics_manifest_for_tests()
    assert a["version"] == b["version"]
