from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def _sanhe_targets(pt):
    facts = collect_all_spec_facts(pt)
    return [f for f in facts if str(f.plugin_id or "") == "l1.physics.op_branch_sanhe"]


def test_sanhe_metal_cluster_projects_into_officer_and_kill() -> None:
    pt = {
        "four_pillars": {"year": "丁巳", "month": "乙酉", "day": "乙丑", "hour": "乙巳"},
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {"正官": 15.0, "七杀": 11.0, "伤官": 34.0, "食神": 18.0, "比肩": 14.0},
        "ten_gods_runtime": {"正官": 15.0, "七杀": 11.0, "伤官": 34.0, "食神": 18.0, "比肩": 14.0},
        "ten_gods_absolute": {"正官": 15.0, "七杀": 11.0, "伤官": 34.0, "食神": 18.0, "比肩": 14.0},
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["luck", "month"], "origin_type": "luck_background"}],
                "liu_he": [],
                "san_he": [{"group": ["巳", "酉", "丑"], "pillars": ["year", "month", "day"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }
    facts = _sanhe_targets(pt)
    by_target = {str(f.meta.get("target_god") or ""): f for f in facts if isinstance(f.meta, dict)}
    assert "正官" in by_target
    assert "七杀" in by_target
    assert float(by_target["七杀"].meta.get("projection_share", 0.0) or 0.0) > 0.0
    assert float(by_target["正官"].meta.get("projection_share", 0.0) or 0.0) > 0.0


def test_sanhe_non_metal_groups_project_beyond_single_target() -> None:
    cases = [
        {
            "four_pillars": {"year": "癸亥", "month": "乙卯", "day": "庚未", "hour": "甲亥"},
            "luck_pillar": "乙酉",
            "flow_pillar": "丁巳",
            "ten_gods_absolute": {"偏财": 18.0, "正财": 14.0, "比肩": 10.0},
            "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [], "san_he": [{"group": ["亥", "卯", "未"], "pillars": ["year", "month", "day"], "origin_type": "natal"}], "ban_he": [], "sanxing": []}},
        },
        {
            "four_pillars": {"year": "壬申", "month": "戊子", "day": "庚辰", "hour": "壬申"},
            "luck_pillar": "癸亥",
            "flow_pillar": "丙午",
            "ten_gods_absolute": {"食神": 17.0, "伤官": 13.0, "偏印": 9.0},
            "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [], "san_he": [{"group": ["申", "子", "辰"], "pillars": ["year", "month", "day"], "origin_type": "natal"}], "ban_he": [], "sanxing": []}},
        },
    ]
    for pt in cases:
        pt["ten_gods_base_l0"] = dict(pt["ten_gods_absolute"])
        pt["ten_gods_runtime"] = dict(pt["ten_gods_absolute"])
        facts = _sanhe_targets(pt)
        assert facts
        total_share = sum(float((f.meta or {}).get("projection_share", 0.0) or 0.0) for f in facts)
        assert abs(total_share - 1.0) < 0.02
