"""UniversalPatternEngine：manifest 热加载与 exclusions 拦截。"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from app.logic.patterns.engine import UniversalPatternEngine, load_pattern_manifest


def _tensor_follow_child_case(*, seal_pct: float, output_pct: float, self_pct: float) -> dict:
    """十神百分比之和应为 100（与 physics 引擎一致）。"""
    rest = max(0.0, 100.0 - seal_pct - output_pct - self_pct)
    return {
        "deity_scores": {
            "正印": seal_pct * 0.55,
            "偏印": seal_pct * 0.45,
            "食神": output_pct * 0.5,
            "伤官": output_pct * 0.5,
            "比肩": self_pct * 0.5,
            "劫财": self_pct * 0.5,
            "偏财": rest * 0.2,
            "正财": rest * 0.2,
            "七杀": rest * 0.2,
            "正官": rest * 0.2,
        },
        "meta": {
            "month_branch": "午",
            "active_structures": [],
        },
    }


def test_manifest_threshold_change_no_process_restart(tmp_path: Path) -> None:
    """改 JSON 后新建引擎即读新阈值，无需重启解释器进程（下一轮 evaluate 生效）。"""
    src = Path(__file__).resolve().parents[2] / "app" / "logic" / "patterns" / "pattern_manifest.json"
    p1 = tmp_path / "m1.json"
    p2 = tmp_path / "m2.json"
    base = json.loads(src.read_text(encoding="utf-8"))
    sp = dict(base["SPECIAL_PATTERNS"]["FOLLOW_CHILD"])
    sp_lo = {**sp, "gating": {**dict(sp.get("gating") or {}), "min_energy": 0.2}}
    sp_hi = {**sp, "gating": {**dict(sp.get("gating") or {}), "min_energy": 0.92}}
    m1 = {**base, "SPECIAL_PATTERNS": {"FOLLOW_CHILD": sp_lo}}
    m2 = {**base, "SPECIAL_PATTERNS": {"FOLLOW_CHILD": sp_hi}}
    p1.write_text(json.dumps(m1, ensure_ascii=False), encoding="utf-8")
    p2.write_text(json.dumps(m2, ensure_ascii=False), encoding="utf-8")

    tensor = _tensor_follow_child_case(seal_pct=2.0, output_pct=62.0, self_pct=5.0)
    row_lo = next(r for r in UniversalPatternEngine(p1).evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")
    row_hi = next(r for r in UniversalPatternEngine(p2).evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")
    assert row_lo["exclusion_hit"] is False and row_hi["exclusion_hit"] is False
    assert row_lo["affinity_score"] > row_hi["affinity_score"] + 0.05

    hot = tmp_path / "hot.json"
    hot.write_text(json.dumps(m1, ensure_ascii=False), encoding="utf-8")
    a = next(r for r in UniversalPatternEngine(hot).evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")["affinity_score"]
    hot.write_text(json.dumps(m2, ensure_ascii=False), encoding="utf-8")
    b = next(r for r in UniversalPatternEngine(hot).evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")["affinity_score"]
    assert a > b + 0.05


def test_follow_child_exclusion_seal_axis_zeros_score() -> None:
    """从儿格：印星过重触发 Seal_Axis exclusions → affinity 归零。"""
    tensor = _tensor_follow_child_case(seal_pct=28.0, output_pct=55.0, self_pct=5.0)
    rows = UniversalPatternEngine().evaluate(tensor, {})
    fc = next(r for r in rows if r["pattern_id"] == "FOLLOW_CHILD")
    assert fc["exclusion_hit"] is True
    assert fc["affinity_score"] == pytest.approx(0.0, abs=1e-9)
    assert any("exclusion:Seal_Axis" in x for x in (fc.get("trace_logic") or []))


def test_follow_child_passes_without_seal_load() -> None:
    tensor = _tensor_follow_child_case(seal_pct=2.0, output_pct=70.0, self_pct=4.0)
    fc = next(r for r in UniversalPatternEngine().evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")
    assert fc["exclusion_hit"] is False
    assert fc["affinity_score"] > 0.2


def test_climate_field_correction_scales_output_axis_energy() -> None:
    """甲木日主：食伤轴属火；``element_mods.fire`` 抬高则主轴能量同比放大（乘子夹紧前）。"""
    tensor_base = _tensor_follow_child_case(seal_pct=2.0, output_pct=62.0, self_pct=5.0)
    md = {"pillars": {"day": {"stem": "甲"}}}
    row_base = next(r for r in UniversalPatternEngine().evaluate(tensor_base, md) if r["pattern_id"] == "FOLLOW_CHILD")
    tensor_hot = {
        **tensor_base,
        "meta": {
            **tensor_base["meta"],
            "climate_field_correction_v1": {
                "element_mods": {
                    "wood": 1.0,
                    "fire": 1.5,
                    "earth": 1.0,
                    "metal": 1.0,
                    "water": 1.0,
                },
            },
        },
    }
    row_hot = next(r for r in UniversalPatternEngine().evaluate(tensor_hot, md) if r["pattern_id"] == "FOLLOW_CHILD")
    assert row_hot["primary_axis_energy"] > row_base["primary_axis_energy"] + 1e-9
    assert row_hot["primary_axis_energy"] == pytest.approx(row_base["primary_axis_energy"] * 1.5, rel=1e-5)


def test_evaluate_trace_contains_codex_gating_exclusion_and_final_ranking() -> None:
    """V6.8：trace_logic 含 CODEX / GATING / EXCLUSION / FINAL_RANKING 节点。"""
    tensor = _tensor_follow_child_case(seal_pct=28.0, output_pct=55.0, self_pct=5.0)
    rows = UniversalPatternEngine().evaluate(tensor, {})
    fc = next(r for r in rows if r["pattern_id"] == "FOLLOW_CHILD")
    tl = list(fc.get("trace_logic") or [])
    assert any(str(x).startswith("[CODEX_LOAD]") for x in tl)
    assert any(str(x).startswith("[GATING_CHECK]") and "FOLLOW_CHILD" in str(x) for x in tl)
    assert any(str(x).startswith("[EXCLUSION_CHECK]") for x in tl)
    assert any(str(x).startswith("[FINAL_RANKING]") and "#1" in str(x) for x in tl)


def test_load_pattern_manifest_mapping() -> None:
    m = load_pattern_manifest({"ENGINE": {}, "AXIS_REGISTRY": {}, "STANDARD_OCTAD": {}, "SPECIAL_PATTERNS": {}})
    assert isinstance(m, dict)


def test_vibrant_wood_metal_exclusion_ultra_low_tolerance() -> None:
    """专旺曲直：官杀（Metal_Axis）>0.02 即红线归零。"""
    tensor = {
        "deity_scores": {
            "比肩": 22.0,
            "劫财": 20.0,
            "正印": 14.0,
            "偏印": 12.0,
            "食神": 6.0,
            "伤官": 6.0,
            "偏财": 5.0,
            "正财": 5.0,
            "七杀": 6.0,
            "正官": 4.0,
        },
        "meta": {"month_branch": "卯", "active_structures": []},
    }
    row = next(r for r in UniversalPatternEngine().evaluate(tensor, {}) if r["pattern_id"] == "VIBRANT_WOOD")
    assert row["exclusion_hit"] is True
    assert row["affinity_score"] == pytest.approx(0.0, abs=1e-9)
    assert any("Metal_Axis" in x for x in (row.get("trace_logic") or []))
    assert any("[拦截]" in x and "金气" in x for x in (row.get("trace_display_zh") or []))


def test_vibrant_wood_month_gate_custom_penalty() -> None:
    """曲直：month_gate_custom 仅寅卯辰为旺月支。"""
    hi = {
        "deity_scores": {
            "比肩": 24.0,
            "劫财": 22.0,
            "正印": 14.0,
            "偏印": 12.0,
            "食神": 6.0,
            "伤官": 6.0,
            "偏财": 5.0,
            "正财": 5.0,
            "七杀": 1.0,
            "正官": 1.0,
        },
        "meta": {"month_branch": "子", "active_structures": []},
    }
    ok = {
        **hi,
        "meta": {**hi["meta"], "month_branch": "寅"},
    }
    bad = next(r for r in UniversalPatternEngine().evaluate(hi, {}) if r["pattern_id"] == "VIBRANT_WOOD")
    good = next(r for r in UniversalPatternEngine().evaluate(ok, {}) if r["pattern_id"] == "VIBRANT_WOOD")
    assert not bad["exclusion_hit"] and not good["exclusion_hit"]
    assert good["affinity_score"] > bad["affinity_score"] + 0.05


def test_fake_follow_child_trace_display_zh() -> None:
    """假从儿：印重触发红线，trace_display_zh 含印星拦截语义。"""
    tensor = _tensor_follow_child_case(seal_pct=26.0, output_pct=56.0, self_pct=5.0)
    fc = next(r for r in UniversalPatternEngine().evaluate(tensor, {}) if r["pattern_id"] == "FOLLOW_CHILD")
    assert fc["exclusion_hit"] is True
    zh = " ".join(fc.get("trace_display_zh") or [])
    assert "印星" in zh


def _extreme_interference_tensor() -> dict:
    """五行偏枯 + 强食伤见官 + 多重结构标签，用于压测拦截与并发。"""
    return {
        "deity_scores": {
            "伤官": 36.0,
            "正官": 26.0,
            "七杀": 8.0,
            "食神": 6.0,
            "正印": 7.0,
            "偏印": 5.0,
            "比肩": 4.0,
            "劫财": 4.0,
            "偏财": 2.0,
            "正财": 2.0,
        },
        "meta": {
            "month_branch": "酉",
            "active_structures": ["FOOD_RESTRAIN_KILL", "SANHE_OUTPUT", "CLASH_YEAR_DAY", "BLADE_HINT"],
        },
    }


def test_extreme_tensor_manifest_intercept_and_concurrent_stress() -> None:
    """极端盘：manifest 内全部格局行可算；高并发预览式 evaluate 无异常（无全局缓存泄漏路径）。"""
    tensor = _extreme_interference_tensor()
    eng = UniversalPatternEngine()
    rows = eng.evaluate(tensor, {})
    assert len(rows) >= 8
    hits = sum(1 for r in rows if r.get("exclusion_hit"))
    assert hits >= 1, "极端盘应至少触发一条 exclusion 红线"
    assert hits / max(len(rows), 1) >= 0.15, "极端盘应对多格局触发红线（拦截率显著）"

    def _once(_: int) -> int:
        return len(UniversalPatternEngine().evaluate(tensor, {}))

    with ThreadPoolExecutor(max_workers=16) as pool:
        futs = [pool.submit(_once, i) for i in range(64)]
        lens = [f.result() for f in as_completed(futs)]
    assert all(n == len(rows) for n in lens)

    for _ in range(200):
        UniversalPatternEngine().evaluate(tensor, {})
