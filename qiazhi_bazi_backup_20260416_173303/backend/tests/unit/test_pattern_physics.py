from __future__ import annotations

from app.logic.pattern_physics import (
    benchmark_pattern_proximity_ms,
    calculate_pattern_proximity,
    pattern_thresholds_for_sse,
)
from app.logic.patterns.engine import UniversalPatternEngine, _iter_specs, load_pattern_manifest


def _manifest_pattern_row_count() -> int:
    m = load_pattern_manifest()
    return len(_iter_specs(m))


def test_calculate_pattern_proximity_sorted_and_bounded():
    tensor = {
        "deity_scores": {
            "比肩": 0.02,
            "劫财": 0.02,
            "食神": 0.05,
            "伤官": 0.05,
            "偏财": 0.35,
            "正财": 0.35,
            "七杀": 0.05,
            "正官": 0.05,
            "偏印": 0.03,
            "正印": 0.03,
        }
    }
    rows = calculate_pattern_proximity(tensor)
    assert len(rows) == _manifest_pattern_row_count()
    for r in rows:
        assert 0.0 <= float(r["progress"]) <= 1.0
        assert 0.0 <= float(r["stability"]) <= 1.0
    assert rows[0]["progress"] >= rows[-1]["progress"]


def test_pattern_thresholds_for_sse_shape():
    tensor = {"deity_scores": {"比肩": 1.0}}
    out = pattern_thresholds_for_sse(tensor)
    assert isinstance(out, list)
    assert out and all(
        set(x.keys()) == {"name", "progress", "stability", "temporal_volatility"} for x in out
    )


def test_temporal_volatility_clash_on_wealth_lowers_cong_cai_stability():
    """弃命从财倾向（比劫·印低于红线）+ 流年冲财：从财格 affinity 仍可观，stability 因波动被拉低。"""
    tensor = {
        "deity_scores": {
            "比肩": 0.02,
            "劫财": 0.02,
            "食神": 0.075,
            "伤官": 0.075,
            "偏财": 0.26,
            "正财": 0.26,
            "七杀": 0.095,
            "正官": 0.095,
            "偏印": 0.04,
            "正印": 0.04,
        }
    }
    metadata = {
        "conflict_matrix": {
            "points": [
                {
                    "kind": "clash",
                    "detail": "流年与日支相冲，财星根气受损",
                    "positions": ["liunian", "day_pillar"],
                }
            ]
        }
    }
    base = calculate_pattern_proximity(tensor, None)
    hit = calculate_pattern_proximity(tensor, metadata)
    cong_b = next(r for r in base if r.get("pattern_id") == "FOLLOW_WEALTH")
    cong_h = next(r for r in hit if r.get("pattern_id") == "FOLLOW_WEALTH")
    assert float(cong_h["progress"]) > 0.35
    assert float(cong_h["temporal_volatility"]) > float(cong_b["temporal_volatility"]) + 0.05
    assert float(cong_h["stability"]) < float(cong_b["stability"]) - 0.02


def test_benchmark_single_call_under_50ms():
    tensor = {
        "deity_scores": {k: 0.1 for k in ("比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印")}
    }
    ms = benchmark_pattern_proximity_ms(tensor, iterations=500)
    assert ms < 50.0, f"expected <50ms per call, got {ms:.3f}ms"


def test_empty_manifest_evaluate_returns_empty():
    eng = UniversalPatternEngine(manifest={})
    assert eng.evaluate({"deity_scores": {"比肩": 1.0}}, {}) == []
