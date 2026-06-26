from __future__ import annotations

from v20.interaction.question_dag import (
    build_question_nodes,
    default_choice_options,
    infer_question_stage,
    question_dag_manifest,
    role_default_dag_path,
)


def test_v20_question_dag_manifest_declares_role_paths_and_guardrails() -> None:
    manifest = question_dag_manifest()

    assert manifest["version"] == "v20.question_dag_manifest.v1"
    assert manifest["role_paths"]["guest"] == ("entry", "focus", "advice", "closure")
    assert manifest["role_paths"]["user"] == ("entry", "focus", "structure", "timing", "advice", "closure")
    assert manifest["role_paths"]["analyst"] == ("structure", "review", "timing", "closure")
    assert manifest["role_paths"]["admin"] == ("observe", "review", "closure")
    assert manifest["runtime_mutation"] is False
    assert "NO_RULE_TRUTH_MUTATION" in manifest["guardrails"]


def test_v20_question_dag_builds_role_specific_nodes_from_runtime_questions() -> None:
    questions = [
        {"question_key": "q_income_stability", "question_id": "qid-wealth", "domain": "wealth", "title": "财运怎么看？"},
        {"question_key": "q_branch_relation_detail", "question_id": "qid-branch", "domain": "branch", "title": "地支关系？"},
    ]

    user_nodes = build_question_nodes(questions, role_key="user")
    analyst_nodes = build_question_nodes(questions, role_key="analyst")
    admin_nodes = build_question_nodes(questions, role_key="admin")

    assert user_nodes[0].stage == "focus"
    assert user_nodes[0].answer_mode == "llm"
    assert user_nodes[0].visibility == "public_guided"
    assert analyst_nodes[1].stage == "review"
    assert analyst_nodes[1].learning_signal == "calibration_signal"
    assert admin_nodes[0].stage == "observe"
    assert admin_nodes[0].visibility == "system_observation"
    assert user_nodes[0].next_question_rules[0].next_stage == "structure"


def test_v20_question_dag_stage_inference_keeps_guest_simple_and_admin_observational() -> None:
    assert infer_question_stage({"domain": "wealth", "role_view_level": "entry"}, role_key="guest") == "entry"
    assert infer_question_stage({"domain": "time"}, role_key="user") == "timing"
    assert infer_question_stage({"domain": "pattern"}, role_key="analyst") == "review"
    assert infer_question_stage({"domain": "wealth"}, role_key="admin") == "observe"


def test_v20_question_dag_choice_options_are_structured_and_non_freeform() -> None:
    entry = default_choice_options("entry", role_key="user")
    review = default_choice_options("review", role_key="analyst")
    observe = default_choice_options("observe", role_key="admin")

    assert [row.option_key for row in entry] == ["career", "wealth", "relationship"]
    assert {row.learning_signal for row in review} == {"calibration_signal"}
    assert {row.next_stage for row in observe} <= set(role_default_dag_path("admin"))
