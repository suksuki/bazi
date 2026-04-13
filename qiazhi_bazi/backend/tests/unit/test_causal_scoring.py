"""因果评分单测。"""
from __future__ import annotations

from typing import Any, Dict

from app.logic.causal_scoring import calculate_decision_score


def _tensor(
    *,
    deity: Dict[str, float],
    entropy: float | None = None,
    critical_blob: str | None = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if entropy is not None:
        meta["global_entropy"] = float(entropy)
    if critical_blob:
        meta["preview_pattern_alert"] = critical_blob
    return {"deity_scores": dict(deity), "meta": meta}


def test_calculate_decision_score_follower_progress_and_entropy():
    """manifest 从财路径：财星抬升且比劫始终低于红线 → FOLLOW_WEALTH progress 上升；熵降。"""
    before = _tensor(
        deity={
            "比肩": 0.02,
            "劫财": 0.02,
            "食神": 0.08,
            "伤官": 0.08,
            "偏财": 0.22,
            "正财": 0.22,
            "七杀": 0.1,
            "正官": 0.1,
            "偏印": 0.04,
            "正印": 0.04,
        },
        entropy=0.62,
    )
    after = _tensor(
        deity={
            "比肩": 0.02,
            "劫财": 0.02,
            "食神": 0.07,
            "伤官": 0.07,
            "偏财": 0.3,
            "正财": 0.3,
            "七杀": 0.085,
            "正官": 0.085,
            "偏印": 0.04,
            "正印": 0.04,
        },
        entropy=0.38,
    )
    out = calculate_decision_score(before, after)
    assert out["total_score"] > 0.35
    assert out["components"]["pattern_boost"] > 0.2
    assert out["components"]["entropy_reduction"] > 0.4


def test_calculate_decision_score_risk_avoidance():
    before = _tensor(
        deity={"比肩": 0.2, "劫财": 0.2, "食神": 0.1, "伤官": 0.1, "偏财": 0.1, "正财": 0.1, "七杀": 0.05, "正官": 0.05, "偏印": 0.05, "正印": 0.05},
        critical_blob="玫瑰色预警 [CRITICAL] 测试",
    )
    after = _tensor(
        deity={"比肩": 0.2, "劫财": 0.2, "食神": 0.1, "伤官": 0.1, "偏财": 0.1, "正财": 0.1, "七杀": 0.05, "正官": 0.05, "偏印": 0.05, "正印": 0.05},
        critical_blob="稳态",
    )
    out = calculate_decision_score(before, after)
    assert out["components"]["risk_avoidance"] > 0.0
    assert out["raw"]["risk_hits_before"] >= out["raw"]["risk_hits_after"]
