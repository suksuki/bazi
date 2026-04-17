"""V8.2：格局插件在 on_physics_complete 上白名单常驻。"""
from __future__ import annotations

from app.core.plugins.registry import PluginRegistry


def test_pattern_detector_v2_runs_on_physics_complete_even_if_not_in_enabled_list():
    reg = PluginRegistry()
    ctx = {
        "physics_tensor": {
            "deity_scores": {
                "比肩": 10.0,
                "劫财": 10.0,
                "食神": 8.0,
                "伤官": 8.0,
                "偏财": 9.0,
                "正财": 9.0,
                "七杀": 9.0,
                "正官": 9.0,
                "偏印": 9.0,
                "正印": 9.0,
            },
            "meta": {"month_branch": "午", "active_structures": []},
        },
        "metadata": {"pillars": {"month": {"branch": "午"}, "day": {"stem": "甲"}}},
        "blind_school_features": {},
        "is_preview": False,
        "dry_run": False,
    }
    out = reg.run_hook(hook="on_physics_complete", enabled_plugins=["classical.blind_school.v1"], context=ctx)
    assert "classical.pattern_detector.v2" in out
    assert out["classical.pattern_detector.v2"].get("ok") is True
