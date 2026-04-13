"""L2 pattern_detector_v2：on_physics_complete 路径与调试日志。"""
from __future__ import annotations

import pytest

from app.logic.patterns.l2_summary import sanitize_pattern_headline_zh
from app.plugins.classical.pattern_detector_v2 import run_pattern_detector_v2


def test_sanitize_pattern_headline_bans_pingchang_ju() -> None:
    assert sanitize_pattern_headline_zh("平常局") == "常规格"
    assert "正官格" in sanitize_pattern_headline_zh("正官格 (亲和度 100.0%)")


def test_run_pattern_detector_v2_writes_meta_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
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
        "meta": {"month_branch": "午", "active_structures": []},
    }
    out = run_pattern_detector_v2(physics_tensor=tensor, metadata={})
    assert isinstance(out, dict)
    meta = tensor.get("meta") or {}
    assert isinstance(meta, dict)
    assert meta.get("pattern_thresholds_engine") == "universal_manifest_v1"
    assert isinstance(meta.get("pattern_thresholds"), list)
    assert len(meta["pattern_thresholds"]) >= 1
    summary = meta.get("l2_pattern_result_summary_v1")
    assert isinstance(summary, str) and summary.strip()
    assert "亲和度" in summary
    assert meta.get("hit_pattern_name") == summary
    assert meta.get("l2_pattern_engine") == "MANIFEST_V5.8_STRICT"
    assert any("DEBUG: L2 Pattern Engine collision completed" in r.message for r in caplog.records)
