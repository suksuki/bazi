from __future__ import annotations

CORE_CASES = {
    "useful_god_candidate_gate": {
        "reading_id": "fixture-useful-god",
        "year": "甲子",
        "month": "戊辰",
        "day": "甲午",
        "hour": "辛酉",
        "expect": {
            "day_master": "甲",
            "day_master_element": "wood",
            "domains": {"chart", "element", "ten_god", "branch_relation", "time_context", "useful_god"},
        },
    },
    "explicit_time_layers": {
        "reading_id": "fixture-time-layers",
        "year": "甲子",
        "month": "乙丑",
        "day": "丙寅",
        "hour": "丁卯",
        "luck_pillar": "庚午",
        "flow_year_pillar": "辛未",
        "expect": {
            "day_master": "丙",
            "day_master_element": "fire",
            "time_status": "ready",
            "time_layers": ["luck", "flow_year"],
        },
    },
    "three_harmony_water": {
        "reading_id": "fixture-three-harmony",
        "year": "甲申",
        "month": "乙子",
        "day": "丙辰",
        "hour": "丁卯",
        "expect": {
            "relation_type": "three_harmony",
            "relation_element": "water",
        },
    },
}
