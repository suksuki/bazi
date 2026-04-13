"""V10：WILL_PROXY 意志锚点须对同一格局的亲和度产生可测偏移。"""
from __future__ import annotations

from app.logic.patterns.engine import UniversalPatternEngine
from app.plugins.modern.will_proxy_v1 import build_pattern_affinity_multipliers, run_will_proxy_v1
from app.skills.energy_topology_skill import EnergyTopologySkill


def _wealth_affinity(rows: list) -> float:
    for r in rows:
        if isinstance(r, dict) and str(r.get("pattern_id") or "") == "WEALTH_PATTERN":
            return float(r.get("affinity_score") or 0.0)
    raise AssertionError("WEALTH_PATTERN row missing")


def test_will_proxy_skews_wealth_affinity_between_stability_and_wealth() -> None:
    """同一物理张量：求财抬财、避险压财，财星格亲和度须显著分化（GOV 在本夹中常触红线为 0，故用 WEALTH_PATTERN）。"""
    tensor = {
        "deity_scores": {"正印": 4.0, "偏印": 4.0, "食神": 30.0, "伤官": 30.0, "比肩": 6.0, "劫财": 6.0, "偏财": 6.0, "正财": 6.0, "七杀": 4.0, "正官": 4.0},
        "meta": {"month_branch": "午", "active_structures": []},
    }
    md: dict = {}
    eng = UniversalPatternEngine()

    rows_neutral = eng.evaluate(tensor, md)
    w0 = _wealth_affinity(rows_neutral)
    assert w0 > 0.05

    tensor_s = {**tensor, "meta": {**dict(tensor["meta"]), "intention_context": {}}}
    md_s = {"user_intention": "seek_stability"}
    run_will_proxy_v1(physics_tensor=tensor_s, metadata=md_s)
    assert "intention_context" in tensor_s["meta"]
    rows_s = eng.evaluate(tensor_s, md_s)
    w_s = _wealth_affinity(rows_s)

    tensor_w = {**tensor, "meta": {**dict(tensor["meta"]), "intention_context": {}}}
    md_w = {"user_intention": "seek_wealth"}
    run_will_proxy_v1(physics_tensor=tensor_w, metadata=md_w)
    rows_w = eng.evaluate(tensor_w, md_w)
    w_w = _wealth_affinity(rows_w)

    mult_s = build_pattern_affinity_multipliers("seek_stability")["WEALTH_PATTERN"]
    mult_w = build_pattern_affinity_multipliers("seek_wealth")["WEALTH_PATTERN"]
    assert mult_w > mult_s
    assert w_w > w_s + 1e-6
    assert w_w > w_s + 0.01


def test_pattern_row_includes_affinity_pre_will_when_intention_active() -> None:
    tensor = {
        "deity_scores": {"正印": 4.0, "偏印": 4.0, "食神": 30.0, "伤官": 30.0, "比肩": 6.0, "劫财": 6.0, "偏财": 6.0, "正财": 6.0, "七杀": 4.0, "正官": 4.0},
        "meta": {"month_branch": "午", "active_structures": []},
    }
    run_will_proxy_v1(physics_tensor=tensor, metadata={"user_intention": "seek_wealth"})
    eng = UniversalPatternEngine()
    rows = eng.evaluate(tensor, {"user_intention": "seek_wealth"})
    wealth = next(r for r in rows if r.get("pattern_id") == "WEALTH_PATTERN")
    assert "affinity_pre_will_proxy" in wealth
    assert float(wealth["affinity_score"]) > float(wealth["affinity_pre_will_proxy"]) + 1e-6


def test_evaluate_preserves_climate_field_under_intention() -> None:
    """V10.1：切换意志只改 L2/亲和与意志 meta，不应改写 physics_tensor.meta 中的调候块。"""
    cfc = {
        "month_branch": "午",
        "element_mods": {"wood": 1.0, "fire": 1.12, "earth": 1.0, "metal": 1.0, "water": 1.0},
    }
    tensor = {
        "deity_scores": {
            "正印": 4.0,
            "偏印": 4.0,
            "食神": 30.0,
            "伤官": 30.0,
            "比肩": 6.0,
            "劫财": 6.0,
            "偏财": 6.0,
            "正财": 6.0,
            "七杀": 4.0,
            "正官": 4.0,
        },
        "meta": {"month_branch": "午", "active_structures": [], "climate_field_correction_v1": cfc},
    }
    eng = UniversalPatternEngine()
    for md in ({"user_intention": "seek_stability"}, {"user_intention": "seek_wealth"}):
        t = {**tensor, "meta": {**dict(tensor["meta"]), "intention_context": {}}}
        run_will_proxy_v1(physics_tensor=t, metadata=md)
        rows = eng.evaluate(t, md)
        assert t["meta"]["climate_field_correction_v1"] == cfc
        assert rows


def test_topology_skill_emits_pre_will_energy_when_intention_context() -> None:
    pt = {
        "meta": {
            "intention_context": {
                "active_intention": "seek_wealth",
                "topology_node_will_inverse_factor": 1.06,
            }
        },
        "deity_energy_axes": {"正官": {"absolute_energy": 5.0}},
    }
    topo = EnergyTopologySkill.build_topology(metadata={"pillars": {}}, physics_tensor=pt)
    pres = [n.get("pre_will_energy") for n in topo["nodes"] if n.get("pre_will_energy") is not None]
    assert pres
    assert all(float(x) > 0 for x in pres)
