from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


def _rows(pt):
    return [f for f in collect_all_spec_facts(pt) if str(f.plugin_id or "") in {
        "l1.physics.op_stem_fusion",
        "l1.physics.op_branch_liuhe",
        "l1.physics.op_branch_liuhai",
        "l1.physics.op_branch_liupo",
    }]


def test_stem_fusion_transform_scores_above_stuck() -> None:
    base = {
        "four_pillars": {"year": "辛酉", "month": "乙酉", "day": "乙丑", "hour": "庚申"},
        "luck_pillar": "庚辰",
        "flow_pillar": "辛巳",
        "ten_gods_absolute": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
        "ten_gods_base_l0": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
        "ten_gods_runtime": {"正官": 22.0, "七杀": 17.0, "比肩": 14.0},
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    stuck = dict(base)
    stuck["meta"] = dict(base["meta"])
    stuck["meta"]["stem_fusion_v1"] = {"cases": [{"pillars": ["month", "luck"], "stems": ["乙", "庚"], "mode": "stuck", "hua_element": "metal", "month_stem_supports": False, "branch_hua_ratio": 0.1667}]}
    transformed = dict(base)
    transformed["meta"] = dict(base["meta"])
    transformed["meta"]["stem_fusion_v1"] = {"cases": [{"pillars": ["month", "luck"], "stems": ["乙", "庚"], "mode": "transformed", "hua_element": "metal", "month_stem_supports": False, "branch_hua_ratio": 0.52}]}

    stuck_fact = next(f for f in _rows(stuck) if str(f.plugin_id or "") == "l1.physics.op_stem_fusion")
    transformed_facts = [f for f in _rows(transformed) if str(f.plugin_id or "") == "l1.physics.op_stem_fusion"]
    transformed_fact = transformed_facts[0]
    transformed_targets = {str(f.meta.get("target_god") or "") for f in transformed_facts}

    assert float(transformed_fact.meta.get("match_ratio", 0.0) or 0.0) > float(stuck_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert transformed_fact.meta.get("condition_state") == "formed"
    assert stuck_fact.meta.get("condition_state") == "stuck"
    assert "化气神" not in transformed_targets
    assert {"正官", "七杀"} <= transformed_targets


def test_liuhai_stronger_than_liupo_on_balanced_cases() -> None:
    common_scores = {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0}
    liuhai_pt = {
        "four_pillars": {"year": "甲子", "month": "乙未", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "month"], "origin_type": "natal"}], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liupo_pt = {
        "four_pillars": {"year": "甲子", "month": "乙酉", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "month"], "origin_type": "natal"}], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    hai_fact = next(f for f in _rows(liuhai_pt) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhai")
    po_fact = next(f for f in _rows(liupo_pt) if str(f.plugin_id or "") == "l1.physics.op_branch_liupo")
    assert float(hai_fact.meta.get("match_ratio", 0.0) or 0.0) > float(po_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert all(str(f.plugin_id or "") != "l1.physics.op_branch_liuhai" for f in _rows(liupo_pt))


def test_liuhe_supported_emits_positive_impact() -> None:
    pt = {
        "four_pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己巳",
        "ten_gods_absolute": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
        "ten_gods_base_l0": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
        "ten_gods_runtime": {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0},
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "month"], "origin_type": "natal"}], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    fact = next(f for f in _rows(pt) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhe")
    assert float(fact.meta.get("impact_ratio", 0.0) or 0.0) > 0.0
    assert fact.meta.get("condition_state") == "supported"


def test_luck_background_relations_score_above_flow_trigger() -> None:
    common_scores = {"正官": 18.0, "七杀": 11.0, "食神": 14.0, "偏财": 12.0}

    liuhe_luck = {
        "four_pillars": {"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
        "luck_pillar": "己丑",
        "flow_pillar": "庚午",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "luck"], "origin_type": "luck_background"}], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liuhe_flow = {
        "four_pillars": {"year": "甲子", "month": "丙寅", "day": "丁卯", "hour": "戊辰"},
        "luck_pillar": "己未",
        "flow_pillar": "庚丑",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [], "liu_he": [{"pair": ["子", "丑"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liuhai_luck = {
        "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊未",
        "flow_pillar": "己巳",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "luck"], "origin_type": "luck_background"}], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liuhai_flow = {
        "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己未",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [{"pair": ["子", "未"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}], "liu_po": [], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liupo_luck = {
        "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊酉",
        "flow_pillar": "己巳",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "luck"], "origin_type": "luck_background"}], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }
    liupo_flow = {
        "four_pillars": {"year": "甲子", "month": "乙卯", "day": "丙寅", "hour": "丁卯"},
        "luck_pillar": "戊辰",
        "flow_pillar": "己酉",
        "ten_gods_absolute": dict(common_scores),
        "ten_gods_base_l0": dict(common_scores),
        "ten_gods_runtime": dict(common_scores),
        "meta": {"interaction_v2": {"liu_chong": [], "liu_hai": [], "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "flow"], "origin_type": "flow_trigger"}], "liu_he": [], "san_he": [], "ban_he": [], "sanxing": []}},
    }

    liuhe_luck_fact = next(f for f in _rows(liuhe_luck) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhe")
    liuhe_flow_fact = next(f for f in _rows(liuhe_flow) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhe")
    liuhai_luck_fact = next(f for f in _rows(liuhai_luck) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhai")
    liuhai_flow_fact = next(f for f in _rows(liuhai_flow) if str(f.plugin_id or "") == "l1.physics.op_branch_liuhai")
    liupo_luck_fact = next(f for f in _rows(liupo_luck) if str(f.plugin_id or "") == "l1.physics.op_branch_liupo")
    liupo_flow_fact = next(f for f in _rows(liupo_flow) if str(f.plugin_id or "") == "l1.physics.op_branch_liupo")

    assert float(liuhe_luck_fact.meta.get("match_ratio", 0.0) or 0.0) > float(liuhe_flow_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert float(liuhai_luck_fact.meta.get("match_ratio", 0.0) or 0.0) > float(liuhai_flow_fact.meta.get("match_ratio", 0.0) or 0.0)
    assert float(liupo_luck_fact.meta.get("match_ratio", 0.0) or 0.0) > float(liupo_flow_fact.meta.get("match_ratio", 0.0) or 0.0)
