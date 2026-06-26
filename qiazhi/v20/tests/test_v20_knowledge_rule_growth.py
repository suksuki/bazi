from __future__ import annotations

from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.rule_library import build_knowledge_rule_library
from v20.validation.rule_synthetic import RULE_SYNTHETIC_CASES


def test_v20_next_wave_knowledge_units_bind_rules_questions_guidance_and_counterexamples() -> None:
    units = {unit.knowledge_id: unit for unit in default_knowledge_units()}
    expected = {
        "v20.ten_god.position_layer_boundary",
        "v20.branch.arbitration.clash_combine_seen_together",
        "v20.pattern.false_following_counterexample",
        "v20.time.fuyin_fanyin_storage_boundary",
        "v20.palace.application.spouse_career_hour_boundary",
    }

    assert expected <= set(units)
    for knowledge_id in expected:
        unit = units[knowledge_id]
        assert unit.rule_atoms
        assert unit.portrait_mappings
        assert unit.question_mappings
        assert unit.answer_guidance
        assert unit.counterexamples
        assert "direct_rule_truth" in unit.forbidden_usage


def test_v20_next_wave_knowledge_units_enter_rule_library_and_synthetic_cases() -> None:
    library = build_knowledge_rule_library()
    source_ids = {row["source_knowledge_id"] for row in library["definitions"]}
    case_ids = {case.case_id for case in RULE_SYNTHETIC_CASES}

    assert {
        "v20.ten_god.position_layer_boundary",
        "v20.branch.arbitration.clash_combine_seen_together",
        "v20.pattern.false_following_counterexample",
        "v20.time.fuyin_fanyin_storage_boundary",
        "v20.palace.application.spouse_career_hour_boundary",
    } <= source_ids
    assert {
        "v20.rule.synthetic.ten_god_position_layer_boundary",
        "v20.rule.synthetic.branch_arbitration_clash_combine_boundary",
        "v20.rule.synthetic.pattern_false_following_counterexample",
        "v20.rule.synthetic.time_fuyin_fanyin_storage_boundary",
        "v20.rule.synthetic.palace_application_detail_boundary",
    } <= case_ids
