"""pattern_recognition_router：从格 profile 与 meta 写入。"""
from __future__ import annotations

from app.core.routing.pattern_recognition_router import evaluate_pattern_profile


def test_evaluate_pattern_profile_cong_writes_meta():
    physics_tensor: dict = {
        "normalized": {"wood": 0.05, "fire": 0.82, "earth": 0.05, "metal": 0.04, "water": 0.04},
        "meta": {},
    }
    metadata = {"pillars": {"day": {"stem": "庚"}}}  # 金日主，火占主导 → 从火
    settings = {"PATTERN_CONG_DOMINANCE": 0.5, "PATTERN_ETA_FLIP_GAIN": 1.15}
    out = evaluate_pattern_profile(physics_tensor=physics_tensor, metadata=metadata, settings=settings)
    assert out.get("pattern_kind") == "cong_fire"
    assert out.get("sovereignty_priority") is True
    meta = physics_tensor["meta"]
    assert meta["pattern_profile"]["pattern_name_zh"].startswith("从")


def test_evaluate_pattern_profile_none_when_balanced():
    physics_tensor: dict = {
        "normalized": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2},
        "meta": {},
    }
    out = evaluate_pattern_profile(
        physics_tensor=physics_tensor,
        metadata={"pillars": {"day": {"stem": "甲"}}},
        settings={"PATTERN_CONG_DOMINANCE": 0.55},
    )
    assert out.get("pattern_kind") == "none"
    assert out.get("sovereignty_priority") is False
