"""V12 M2：PSV 引擎单测（1990-06-14 正官格 + seek_stability，无 LLM）。"""

from __future__ import annotations

import copy

from app.logic.brain.config import PSVRuntimeConfig, load_psv_runtime_config
from app.logic.brain.psv_engine import PSVEngine, PSVSymbol
from app.services.helpers.metadata_projector_v12 import MetadataProjectorV12
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def _tri_from_sample() -> object:
    return MetadataProjectorV12().project(_sample_bundle_1990_06_14_zhengguan())


def _default_cfg() -> PSVRuntimeConfig:
    return load_psv_runtime_config(None)


def test_psv_detects_robber_wealth_penetrance_negative() -> None:
    """比劫/财星比 > 0.3：财星轴必须为负向（监军可据此拒稿「财运亨通」类叙事）。"""
    tri = _tri_from_sample()
    psv = PSVEngine(_default_cfg()).build(tri)
    wealth = [s for s in psv if s.axis == "WEALTH"]
    assert wealth, "expected WEALTH axis PSV"
    w = wealth[0]
    assert w.polarity in ("STRONG_NEGATIVE", "MILD_NEGATIVE"), w.polarity
    assert w.strength >= 0.35
    assert any("rule:psv.robber_wealth_pierce_ratio" in e for e in w.evidence)


def test_psv_officer_positive_under_stability_intention_and_zhengguan() -> None:
    """正官格 + 避险意志：官杀主轴应为正向加强，与财富损耗方向可并存（不同 axis）。"""
    tri = _tri_from_sample()
    psv = PSVEngine(_default_cfg()).build(tri)
    officer = [s for s in psv if s.axis == "OFFICER"]
    assert officer, "expected OFFICER axis for GOV_PATTERN mock"
    o = officer[0]
    assert o.polarity in ("STRONG_POSITIVE", "MILD_POSITIVE"), o.polarity
    assert o.strength >= 0.85
    assert any("pattern_id=GOV_PATTERN" in e for e in o.evidence)
    assert any("seek_stability" in e for e in o.evidence) or tri.arbiter_bias.user_intention_id == "seek_stability"


def test_psv_symbols_are_deterministic_and_serializable() -> None:
    tri = _tri_from_sample()
    cfg = _default_cfg()
    a = PSVEngine(cfg).build(tri)
    b = PSVEngine(cfg).build(tri)
    assert [s.model_dump() for s in a] == [s.model_dump() for s in b]
    for s in a:
        assert isinstance(s, PSVSymbol)
        assert s.fingerprint


def test_psv_wealth_loss_direction_unchanged_under_seek_wealth_intention() -> None:
    """换为求财意志：比劫夺财物理比不变，财星轴仍为负向（损耗方向不因叙事意志翻转）。"""
    bundle = copy.deepcopy(_sample_bundle_1990_06_14_zhengguan())
    bundle["user_intention"] = "seek_wealth"
    bundle["physics_tensor"]["meta"]["intention_context"]["active_intention"] = "seek_wealth"

    tri = MetadataProjectorV12().project(bundle)
    psv = {s.axis: s for s in PSVEngine(_default_cfg()).build(tri)}
    assert psv["WEALTH"].polarity in ("STRONG_NEGATIVE", "MILD_NEGATIVE")


def test_psv_robber_pierce_threshold_dynamic_no_negative_wealth() -> None:
    """提高 robber_wealth_pierce_threshold 后，夺财规则不再触发，财星负向消失（参数接管）。"""
    tri = _tri_from_sample()
    cfg = PSVRuntimeConfig(robber_wealth_pierce_threshold=0.9)
    psv = PSVEngine(cfg).build(tri)
    wealth_neg = [
        s
        for s in psv
        if s.axis == "WEALTH"
        and s.polarity in ("STRONG_NEGATIVE", "MILD_NEGATIVE")
        and any("rule:psv.robber_wealth_pierce_ratio" in e for e in s.evidence)
    ]
    assert not wealth_neg


def test_psv_from_tri_merges_arbiter_psv_runtime_overrides() -> None:
    """metadata.psv_runtime_overrides → ArbiterBias → from_tri 与显式配置等价。"""
    bundle = copy.deepcopy(_sample_bundle_1990_06_14_zhengguan())
    bundle["metadata"]["psv_runtime_overrides"] = {"robber_wealth_pierce_threshold": 0.9}
    tri = MetadataProjectorV12().project(bundle)
    explicit = PSVEngine(PSVRuntimeConfig(robber_wealth_pierce_threshold=0.9)).build(tri)
    from_tri = PSVEngine.from_tri(tri).build(tri)
    assert [s.model_dump() for s in explicit] == [s.model_dump() for s in from_tri]
