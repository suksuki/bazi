"""L0 通根共振与柱位加权（无 DB 时回退 physics_rules 常量）。"""
from __future__ import annotations

from app.core.bazi.engine import blend_position_weights_l0, get_root_resonance
from app.core.bazi.l0_manager import L0PluginManager


def setup_function() -> None:
    L0PluginManager.reset_instance_for_tests()


def test_get_root_resonance_boosts_when_hidden_present() -> None:
    r0 = get_root_resonance("甲", ["寅", "子"], {"L0_ROOT_BOOST_FACTOR": 1.0})
    r1 = get_root_resonance("甲", ["寅", "子"], {"L0_ROOT_BOOST_FACTOR": 1.2})
    assert r1 > r0
    assert 0.55 <= r0 <= 2.0


def test_blend_position_weights_l0_ratio() -> None:
    base = {"year": 0.2, "month": 0.45, "day": 0.25, "hour": 0.1}
    hi = blend_position_weights_l0(base, {"L0_YM_DH_WEIGHT_RATIO": 1.5})
    lo = blend_position_weights_l0(base, {"L0_YM_DH_WEIGHT_RATIO": 0.75})
    assert hi["year"] + hi["month"] > lo["year"] + lo["month"]
