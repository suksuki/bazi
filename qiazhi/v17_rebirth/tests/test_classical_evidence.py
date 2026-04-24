from __future__ import annotations

from v17_rebirth.backend.logic.L2_structure_patterns.classical_evidence import (
    branch_main_god,
    dominant_element_from_ten_gods,
    element_structure_evidence,
    is_followable_weak_body,
    yangren_blade_context,
    zaqi_evidence,
)


def test_yangren_evidence_requires_daymaster_specific_blade_branch() -> None:
    tensor = {
        "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "luck_pillar": "己亥",
        "flow_pillar": "戊申",
    }

    context = yangren_blade_context(tensor)

    assert context["daymaster"] == "乙"
    assert context["blade_branch"] == "寅"
    assert context["has_natal_blade"] is False
    assert context["runtime_blade_scopes"] == []


def test_dominant_element_maps_ten_gods_relative_to_daymaster() -> None:
    scores = {"比肩": 38.0, "劫财": 20.0, "偏印": 8.0}

    element, top_score, second_score = dominant_element_from_ten_gods(scores, daymaster="庚")

    assert element == "金"
    assert top_score == 58.0
    assert second_score == 8.0


def test_zaqi_evidence_needs_hidden_and_visible_same_god_family() -> None:
    hidden_without_visible = zaqi_evidence(
        {
            "four_pillars": {"year": "甲子", "month": "己丑", "day": "乙午", "hour": "壬申"},
        },
        {"七杀"},
    )
    with_visible = zaqi_evidence(
        {
            "four_pillars": {"year": "甲子", "month": "辛丑", "day": "乙午", "hour": "辛酉"},
        },
        {"七杀"},
    )

    assert hidden_without_visible["has_hidden"] is True
    assert hidden_without_visible["has_visible"] is False
    assert with_visible["has_hidden"] is True
    assert with_visible["has_visible"] is True


def test_specialized_element_evidence_exposes_month_and_branch_structure() -> None:
    evidence = element_structure_evidence(
        {
            "four_pillars": {"year": "甲寅", "month": "乙卯", "day": "甲辰", "hour": "乙亥"},
        },
        "木",
    )

    assert evidence["month_supports_element"] is True
    assert len(evidence["strong_branch_hits"]) >= 2


def test_followable_weak_body_rejects_self_rooted_chart() -> None:
    ok, evidence = is_followable_weak_body(
        {
            "four_pillars": {"year": "甲寅", "month": "乙卯", "day": "甲辰", "hour": "戊辰"},
        },
        {"正财": 24.0, "偏财": 12.0, "比肩": 9.0, "劫财": 2.0, "正印": 8.0},
        max_support=18.0,
    )

    assert ok is False
    assert evidence["root_weight"] > 0.0
    assert evidence["self_support_score"] > evidence["self_support_limit"]


def test_branch_main_god_uses_hidden_main_qi_for_target_god() -> None:
    assert branch_main_god("壬", "子") == "劫财"
    assert branch_main_god("乙", "寅") == "劫财"
