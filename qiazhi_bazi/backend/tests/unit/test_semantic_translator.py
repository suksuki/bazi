from __future__ import annotations

from app.core.config.physics_settings import resolve_physics_settings
from app.semantic_translator import attach_semantic_labels_to_physics_meta, build_semantic_label_bundle


def test_build_semantic_label_bundle_no_floats_in_lines():
    settings = resolve_physics_settings(None)
    pt = {
        "deity_energy_axes": {"比肩": {"absolute_energy": 3.3}},
        "abs_nodes": {},
        "meta": {"params": {"CF_FLOATING_DECAY": 0.22}, "global_entropy": 0.41},
        "confidence": 0.55,
    }
    bundle = build_semantic_label_bundle(physics_tensor=pt, physics_settings=settings)
    lines = bundle.get("verified_fact_lines") or []
    assert any("VF·十神" in str(x) for x in lines)
    blob = "\n".join(str(x) for x in lines)
    assert "3.3" not in blob
    assert "0.22" not in blob


def test_attach_semantic_labels_to_physics_meta_writes_meta():
    pt: dict = {"meta": {"params": {"CF_FLOATING_DECAY": 0.2}}, "deity_energy_axes": {}}
    attach_semantic_labels_to_physics_meta(pt, physics_settings=resolve_physics_settings(None))
    assert isinstance(pt.get("meta"), dict)
    assert isinstance(pt["meta"].get("semantic_label_bundle_v1"), dict)
