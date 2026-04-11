from __future__ import annotations

from app.plugins.base_physics.core_operators.op_stem_fusion import apply_op_stem_fusion


def _full_axes(base: float = 3.0) -> dict:
    out = {}
    for d in (
        "比肩",
        "劫财",
        "正印",
        "偏印",
        "食神",
        "伤官",
        "正财",
        "偏财",
        "正官",
        "七杀",
    ):
        out[d] = {"absolute_energy": base, "relative_percentage": 10.0}
    return out


def test_stem_fusion_locked_when_hua_not_supported() -> None:
    """月令不助化、地支化神占比不足 → 合而不化 → is_locked + locked_deities。"""
    md = {
        "pillars": {
            "year": {"stem": "己", "branch": "未"},
            "month": {"stem": "甲", "branch": "寅"},
            "day": {"stem": "丙", "branch": "午"},
            "hour": {"stem": "丁", "branch": "巳"},
        }
    }
    tensor: dict = {
        "deity_energy_axes": _full_axes(4.0),
        "vector": {"wood": 2.0, "fire": 2.0, "earth": 2.0, "metal": 2.0, "water": 2.0},
        "meta": {},
    }
    settings = {
        "L1_STEM_FUSION_ENABLE": 1.0,
        "STEM_FUSION_BRANCH_SUPPORT_RATIO": 0.35,
        "STEM_FUSION_VECTOR_LEAK_RATIO": 0.12,
    }
    steps = apply_op_stem_fusion(physics_tensor=tensor, metadata=md, settings=settings)
    assert len(steps) == 1
    sf = (tensor.get("meta") or {}).get("stem_fusion_v1") or {}
    assert sf.get("is_locked") is True
    assert len(sf.get("locked_deities") or []) >= 1


def test_stem_fusion_transform_when_month_supports_hua() -> None:
    md = {
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "己", "branch": "巳"},
            "day": {"stem": "丙", "branch": "午"},
            "hour": {"stem": "丁", "branch": "卯"},
        }
    }
    tensor: dict = {
        "deity_energy_axes": _full_axes(5.0),
        "vector": {"wood": 2.0, "fire": 2.0, "earth": 2.0, "metal": 2.0, "water": 2.0},
        "meta": {},
    }
    settings = {"L1_STEM_FUSION_ENABLE": 1.0, "STEM_FUSION_VECTOR_LEAK_RATIO": 0.2}
    apply_op_stem_fusion(physics_tensor=tensor, metadata=md, settings=settings)
    sf = (tensor.get("meta") or {}).get("stem_fusion_v1") or {}
    assert sf.get("has_transform") is True
    assert any(c.get("mode") == "transformed" for c in (sf.get("cases") or []))
    assert "normalized" in tensor
