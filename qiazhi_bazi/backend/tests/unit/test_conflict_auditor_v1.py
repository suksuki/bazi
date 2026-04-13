"""V9.0：冲突拓扑法典与 aggregate 乘子。"""
from __future__ import annotations

from app.plugins.classical.conflict_auditor_v1 import compute_conflict_topology_v1, load_conflict_manifest


def test_compute_conflict_topology_single_clash_uses_kind_default() -> None:
    md = {
        "conflict_matrix": {
            "points": [{"kind": "clash", "detail": "寅申冲", "positions": ["month_branch", "year_branch"]}]
        }
    }
    doc = load_conflict_manifest()
    out = compute_conflict_topology_v1(md, doc=doc)
    assert out["aggregate_conflict_linear_factor"] == doc["KIND_LINEAR"]["clash"]["linear_multiplier"]
    assert len(out["entries"]) == 1
    assert out["entries"][0]["source"] == "KIND_DEFAULT"


def test_compute_conflict_detail_override_matches_entry_id() -> None:
    md = {
        "conflict_matrix": {
            "points": [{"kind": "clash", "detail": "子午冲", "positions": ["year_branch", "day_branch"]}]
        }
    }
    doc = load_conflict_manifest()
    out = compute_conflict_topology_v1(md, doc=doc)
    assert out["entries"][0]["manifest_entry_id"] == "Entry_04"
    assert out["entries"][0]["linear_multiplier"] == 0.8
    assert out["aggregate_conflict_linear_factor"] == 0.8
    pair_rows = [e for e in out["entries"] if e.get("source") == "Manifest_PAIR_DECAYS"]
    assert len(pair_rows) == 1
    assert "水能量" in str(pair_rows[0].get("element_loss_display") or "")
    assert "火能量" in str(pair_rows[0].get("element_loss_display") or "")
    assert pair_rows[0].get("manifest_entry_id") == "Manifest_Entry_09"
    mods = out["element_conflict_mods"]
    assert abs(float(mods["water"]) - 0.85) < 1e-9
    assert abs(float(mods["fire"]) - 0.75) < 1e-9


def test_manifest_change_changes_aggregate(monkeypatch, tmp_path) -> None:
    import json
    from pathlib import Path

    p = tmp_path / "conflict_manifest.json"
    base = {
        "ENGINE": {"schema_version": "test"},
        "KIND_LINEAR": {"clash": {"linear_multiplier": 0.95, "label_zh": "冲"}, "default": {"linear_multiplier": 1.0, "label_zh": "默"}},
        "OVERRIDES": [],
        "BOUNDS": {"aggregate_floor": 0.35, "per_point_floor": 0.55},
    }
    p.write_text(json.dumps(base), encoding="utf-8")
    monkeypatch.setenv("QIAZHI_CONFLICT_MANIFEST_PATH", str(p))
    md = {"conflict_matrix": {"points": [{"kind": "clash", "detail": "x", "positions": []}]}}
    a = compute_conflict_topology_v1(md)["aggregate_conflict_linear_factor"]
    base["KIND_LINEAR"]["clash"]["linear_multiplier"] = 0.7
    p.write_text(json.dumps(base), encoding="utf-8")
    b = compute_conflict_topology_v1(md)["aggregate_conflict_linear_factor"]
    assert a == 0.95
    assert b == 0.7


def test_legacy_gamma_flag_matches_old_formula() -> None:
    md = {
        "conflict_matrix": {
            "points": [
                {"kind": "clash", "detail": "a"},
                {"kind": "clash", "detail": "b"},
            ]
        }
    }
    out = compute_conflict_topology_v1(md, physics_config={"CONFLICT_USE_LEGACY_GAMMA": True, "conflict_penalty_gamma": 0.12})
    assert out["version"] == "legacy_gamma"
    assert abs(float(out["aggregate_conflict_linear_factor"]) - 0.76) < 1e-9
