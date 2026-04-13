"""V7.0 架构血缘：manifest 空则仪表盘数据链不得从隐性旧路径补数。"""
from __future__ import annotations

from app.logic.patterns.engine import UniversalPatternEngine
from app.services.orchestrator_service import build_physics_update_payload


def test_empty_manifest_engine_returns_no_rows():
    eng = UniversalPatternEngine(manifest={})
    rows = eng.evaluate({"deity_scores": {"比肩": 0.5, "劫财": 0.5}}, {})
    assert rows == []


def test_physics_payload_pattern_thresholds_empty_without_strict_meta():
    tensor = {
        "deity_scores": {"比肩": 1.0},
        "meta": {
            "pattern_thresholds_engine": "universal_manifest_v1",
            "pattern_thresholds": [],
        },
    }
    pl = build_physics_update_payload(tensor, {})
    assert pl["pattern_thresholds"] == []
    assert pl["pattern_thresholds_status"] == "EMPTY_NO_DATA"


def test_physics_payload_rejects_non_strict_rows():
    tensor = {
        "deity_scores": {"比肩": 1.0},
        "meta": {
            "pattern_thresholds_engine": "universal_manifest_v1",
            "pattern_thresholds": [
                {"name": "假行", "progress": 0.9, "engine_v": "LEGACY_CENTROID"},
            ],
        },
    }
    pl = build_physics_update_payload(tensor, {})
    assert pl["pattern_thresholds"] == []
    assert pl["pattern_thresholds_status"] == "EMPTY_NO_DATA"


def test_physics_payload_accepts_strict_manifest_rows():
    tensor = {
        "deity_scores": {"比肩": 1.0},
        "meta": {
            "pattern_thresholds_engine": "universal_manifest_v1",
            "pattern_thresholds": [
                {
                    "name": "专旺·比劫",
                    "progress": 0.42,
                    "engine_v": "MANIFEST_V5.8_STRICT",
                },
            ],
        },
    }
    pl = build_physics_update_payload(tensor, {})
    assert len(pl["pattern_thresholds"]) == 1
    assert pl["pattern_thresholds_status"] == "OK"
