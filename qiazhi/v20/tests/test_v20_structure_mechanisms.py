from __future__ import annotations

from v20.knowledge.structure_mechanisms import match_structure_path_mechanisms, structure_mechanism_units
from v20.knowledge.loader import default_knowledge_units


def test_v20_structure_mechanism_units_cover_core_dynamic_labels() -> None:
    labels = {unit.label for unit in structure_mechanism_units()}

    assert labels >= {
        "食神制杀",
        "伤官制杀",
        "输出制官杀",
        "食伤生财",
        "财生官/财滋杀",
        "官印/杀印相生",
        "印星承身",
        "比劫承身",
        "印制食伤",
        "比劫夺财",
        "财破印",
    }


def test_v20_structure_mechanisms_are_promoted_to_reviewed_knowledge_units() -> None:
    mechanism_labels = {unit.label for unit in structure_mechanism_units()}
    knowledge_units = [
        unit
        for unit in default_knowledge_units()
        if unit.knowledge_id.startswith("v20.structure.mechanism.")
    ]
    promoted_labels = {
        str(tag)
        for unit in knowledge_units
        for tag in unit.retrieval_tags
        if str(tag) in mechanism_labels
    }

    assert promoted_labels >= mechanism_labels
    assert all(unit.status == "reviewed" for unit in knowledge_units)
    assert all(unit.evidence_template and unit.boundary for unit in knowledge_units)
    assert all(unit.feature_hooks and unit.question_hooks for unit in knowledge_units)


def test_v20_structure_mechanism_matcher_prefers_specific_food_controls_killing() -> None:
    rows = match_structure_path_mechanisms(
        family_chain=("output", "authority", "resource", "day_master"),
        node_labels=("丁食神", "辛七杀", "癸偏印", "乙日主"),
        path_score=0.91,
    )

    assert rows[0]["label"] == "食神制杀"
    assert rows[0]["mechanism_source"] == "knowledge.structure_mechanisms"
    assert "日主承载" in rows[0]["boundary"]


def test_v20_structure_mechanism_matcher_covers_counterexample_paths() -> None:
    peer_wealth = match_structure_path_mechanisms(
        family_chain=("self", "wealth"),
        node_labels=("甲比肩", "戊偏财"),
        path_score=0.72,
    )
    wealth_resource = match_structure_path_mechanisms(
        family_chain=("wealth", "resource"),
        node_labels=("戊偏财", "癸正印"),
        path_score=0.68,
    )
    resource_output = match_structure_path_mechanisms(
        family_chain=("resource", "output", "wealth"),
        node_labels=("壬偏印", "丙食神", "戊偏财"),
        path_score=0.74,
    )

    assert peer_wealth[0]["label"] == "比劫夺财"
    assert wealth_resource[0]["label"] == "财破印"
    assert {row["label"] for row in resource_output} >= {"印制食伤", "食伤生财"}


def test_v20_structure_mechanism_matcher_covers_resource_support_self_path() -> None:
    rows = match_structure_path_mechanisms(
        family_chain=("resource", "self"),
        node_labels=("癸正印", "甲比肩"),
        path_score=0.72,
    )

    assert rows[0]["label"] == "印星承身"
    assert "承载" in rows[0]["boundary"]


def test_v20_structure_mechanism_matcher_covers_peer_support_day_master_path() -> None:
    rows = match_structure_path_mechanisms(
        family_chain=("self", "day_master"),
        node_labels=("壬劫财", "癸日主"),
        path_score=0.74,
    )

    assert rows[0]["label"] == "比劫承身"
    assert "同气力量" in rows[0]["boundary"]
