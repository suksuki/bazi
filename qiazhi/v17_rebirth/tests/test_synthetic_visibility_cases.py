from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import calc_deity_scores
from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts


def _sanhe_projection(four_pillars, luck_pillar, flow_pillar):
    scores, _top, _total, _meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender="male",
    )
    pt = {
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "ten_gods_absolute": dict(scores),
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
                "liu_po": [],
                "liu_he": [],
                "san_he": [{"group": ["巳", "酉", "丑"], "pillars": ["year", "month", "day"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }
    facts = [
        f for f in collect_all_spec_facts(pt)
        if str(f.plugin_id or "") == "l1.physics.op_branch_sanhe"
    ]
    return {
        str((f.meta or {}).get("target_god") or ""): float((f.meta or {}).get("projection_share") or 0.0)
        for f in facts
    }


def _sanhe_facts(four_pillars, luck_pillar, flow_pillar, sanhe_row):
    scores, _top, _total, _meta = calc_deity_scores(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        gender="male",
    )
    pt = {
        "four_pillars": four_pillars,
        "luck_pillar": luck_pillar,
        "flow_pillar": flow_pillar,
        "ten_gods_base_l0": dict(scores),
        "ten_gods_runtime": dict(scores),
        "ten_gods_absolute": dict(scores),
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [],
                "liu_po": [],
                "liu_he": [],
                "san_he": [sanhe_row],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }
    return [
        f for f in collect_all_spec_facts(pt)
        if str(f.plugin_id or "") == "l1.physics.op_branch_sanhe"
    ]


def test_floating_peer_weaker_than_rooted_peer() -> None:
    floating_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        gender="male",
    )
    rooted_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "丁卯", "month": "乙卯", "day": "乙未", "hour": "乙亥"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        gender="male",
    )
    assert float(floating_scores.get("比肩", 0.0)) < float(rooted_scores.get("比肩", 0.0))


def test_visible_geng_biases_sanhe_toward_officer() -> None:
    four = {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"}
    with_geng = _sanhe_projection(four, "庚子", "丙午")
    without_geng = _sanhe_projection(four, "辛亥", "丙午")
    assert with_geng.get("正官", 0.0) > without_geng.get("正官", 0.0)
    assert without_geng.get("正官", 0.0) < without_geng.get("七杀", 0.0)


def test_weak_residual_root_does_not_equate_full_root() -> None:
    weak_root_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="辛丑",
        flow_pillar="乙未",
        gender="male",
    )
    strong_root_scores, _, _, _ = calc_deity_scores(
        four_pillars={"year": "丁卯", "month": "乙卯", "day": "乙未", "hour": "乙亥"},
        luck_pillar="辛丑",
        flow_pillar="乙未",
        gender="male",
    )
    assert float(weak_root_scores.get("比肩", 0.0)) < float(strong_root_scores.get("比肩", 0.0))


def test_duplicate_sanhe_support_boosts_officer_kill_cluster() -> None:
    four = {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"}
    simple = _sanhe_facts(
        four,
        "辛亥",
        "丙午",
        {"group": ["巳", "酉", "丑"], "pillars": ["year", "day", "hour"], "matched_branches": ["巳", "丑", "酉"], "origin_type": "natal"},
    )
    duplicated = _sanhe_facts(
        four,
        "辛丑",
        "乙未",
        {"group": ["巳", "酉", "丑"], "pillars": ["year", "month", "day", "hour", "luck"], "matched_branches": ["巳", "巳", "丑", "酉", "丑"], "duplicate_count": 2, "pivot_factor": 1.0, "origin_type": "natal"},
    )
    simple_peak = max(float((f.meta or {}).get("impact_ratio") or 0.0) for f in simple)
    duplicated_peak = max(float((f.meta or {}).get("impact_ratio") or 0.0) for f in duplicated)
    assert duplicated_peak > simple_peak


def test_pure_qisha_luck_and_duplicate_sanhe_push_qisha_to_top() -> None:
    scores, _top, _total, meta = calc_deity_scores(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="辛丑",
        flow_pillar="乙未",
        gender="male",
    )

    assert float(scores.get("七杀", 0.0)) > float(scores.get("伤官", 0.0))
    assert float(scores.get("七杀", 0.0)) > float(scores.get("比肩", 0.0))
    bonuses = meta.get("structural_bonuses") or []
    assert bonuses
    top_bonus = bonuses[0]
    assert float((top_bonus.get("projection") or {}).get("七杀", 0.0)) > float((top_bonus.get("projection") or {}).get("正官", 0.0))
