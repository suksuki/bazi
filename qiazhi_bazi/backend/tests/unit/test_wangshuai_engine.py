from app.plugins.wangshuai.wangshuai_engine import evaluate_wangshuai


def test_wangshuai_three_channel_audit_has_skill_ids():
    trace = {
        "比肩": {
            "base_energy": {
                "contribution_sources": [
                    {"source": "month.stem:乙", "contribution_energy": 10.0},
                    {"source": "day.branch:酉", "contribution_energy": 5.0},
                    {"source": "year.stem:丁", "contribution_energy": 3.0},
                ]
            }
        },
        "劫财": {"base_energy": {"contribution_sources": []}},
        "正印": {"base_energy": {"contribution_sources": []}},
        "偏印": {"base_energy": {"contribution_sources": []}},
    }
    axes = {
        "比肩": {"absolute_energy": 8.0, "relative_percentage": 40.0},
        "劫财": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "正印": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "偏印": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "食神": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "伤官": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "正财": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "偏财": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "正官": {"absolute_energy": 1.0, "relative_percentage": 5.0},
        "七杀": {"absolute_energy": 1.0, "relative_percentage": 5.0},
    }
    pt = {"deity_trace_details": trace, "deity_energy_axes": axes}
    out = evaluate_wangshuai(physics_tensor=pt, metadata={})
    ids = {x["payload"]["skill_id"] for x in out["audit_items"]}
    assert ids == {"ws_season", "ws_root", "ws_support"}
    assert out["wangshuai_axes"]["ws_season_raw"] == 10.0
    assert out["wangshuai_axes"]["ws_root_raw"] == 5.0
    assert out["wangshuai_axes"]["ws_support_raw"] == 3.0
