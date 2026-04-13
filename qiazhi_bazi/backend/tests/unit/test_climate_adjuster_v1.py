"""V8.0：调候 manifest 插件写入 meta，供 L2 主轴能量乘权。"""
from __future__ import annotations

from app.plugins.classical.climate_adjuster_v1 import run_climate_adjuster_v1


def test_run_climate_adjuster_writes_element_mods_for_month_branch() -> None:
    pt: dict = {"meta": {"month_branch": "午"}, "deity_scores": {}}
    md = {"pillars": {"month": {"branch": "申"}}}  # tensor.meta 优先
    out = run_climate_adjuster_v1(physics_tensor=pt, metadata=md)
    assert out.get("climate_element_mods", {}).get("fire") == 1.18
    cfc = pt["meta"]["climate_field_correction_v1"]
    assert cfc["month_branch"] == "午"
    assert cfc["element_mods"]["fire"] == 1.18
    assert cfc["element_mods"]["water"] == 0.88


def test_run_climate_adjuster_falls_back_to_metadata_month_branch() -> None:
    pt: dict = {"meta": {}, "deity_scores": {}}
    md = {"pillars": {"month": {"branch": "午"}}}
    run_climate_adjuster_v1(physics_tensor=pt, metadata=md)
    assert pt["meta"]["climate_field_correction_v1"]["month_branch"] == "午"
