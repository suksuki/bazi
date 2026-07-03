from __future__ import annotations

from copy import deepcopy

from v30.brain.text_options import (
    OPTION_SET_VERSION,
    PRACTITIONER_SELECTION_VERSION,
    TEXT_OPTION_PROJECTION_VERSION,
    TEXT_SEMANTIC_UNIT_VERSION,
    build_practitioner_selection,
    build_response_option_set_for_question,
    build_text_option_projection_from_stage_points,
    extract_text_semantic_units,
    role_visible_option_sets,
)
from v30.presentation import build_presentation_model
from v30.presentation.thinking import build_thinking_projection
from v30.runtime import attach_question_outcome, create_smoke_runtime


def test_text_option_extractor_turns_useful_god_text_into_option_set() -> None:
    extraction = extract_text_semantic_units(
        "用神候选先看土与火，土负责承接，火负责温煦，但火过旺会加重燥性。",
        source_type="stage_point",
        source_id="stage.useful_god.001",
        stage_id="useful_god_arbitration",
        bazi_terms=["用神", "取用"],
        evidence_refs=["useful_god.candidate.earth", "useful_god.candidate.fire"],
    )

    assert extraction["semantic_units"]
    first = extraction["semantic_units"][0]
    assert first["version"] == TEXT_SEMANTIC_UNIT_VERSION
    assert first["unit_type"] == "alternative"
    assert {"土", "火"} <= set(first["normalized_terms"])
    assert first["boundary"] == "text_semantic_unit_is_extracted_from_text_not_new_chart_fact"

    projection = build_text_option_projection_from_stage_points(
        [
            {
                "point_id": "stage.useful_god.001",
                "stage_id": "useful_god_arbitration",
                "text": "用神候选先看土与火，土负责承接，火负责温煦，但火过旺会加重燥性。",
                "bazi_terms": ["用神", "土", "火"],
                "evidence_refs": ["useful_god.candidate.earth", "useful_god.candidate.fire"],
            }
        ],
        stage_id="useful_god_arbitration",
    )

    assert projection["version"] == TEXT_OPTION_PROJECTION_VERSION
    assert projection["option_sets"]
    option_set = projection["option_sets"][0]
    assert option_set["version"] == OPTION_SET_VERSION
    assert option_set["topic"] == "useful_god"
    assert option_set["selection_mode"] == "rank_one_or_more"
    assert option_set["visibility"]["user"] == "hidden"
    assert option_set["visibility"]["practitioner"] == "interactive"
    assert {"earth", "fire"} <= {row["option_id"] for row in option_set["options"]}
    assert option_set["boundary"] == "option_set_changes_interpretation_weight_not_chart_fact"


def test_branch_option_hints_are_practitioner_selectable_and_user_read_only() -> None:
    projection = build_text_option_projection_from_stage_points(
        [
            {
                "point_id": "stage.useful_god.branch.001",
                "stage_id": "useful_god_arbitration",
                "kind": "branch",
                "text": "用神取向有土为主与火为辅两条分支，当前土的承接路径权重更高。",
                "bazi_terms": ["用神", "土", "火"],
                "evidence_refs": ["useful_god.candidate.earth", "useful_god.candidate.fire"],
                "branch_probability": 0.72,
                "option_hints": [
                    {
                        "label": "土为主",
                        "value": "earth_primary",
                        "probability": 0.72,
                        "meaning": "以承接官杀压力为优先",
                    },
                    {
                        "label": "火为辅",
                        "value": "fire_secondary",
                        "probability": 0.54,
                        "meaning": "以温煦和激活为辅助",
                    },
                ],
                "resolution_conditions": ["若火势过旺，火分支降权", "若土能承接财官，土分支升权"],
            }
        ],
        stage_id="useful_god_arbitration",
    )

    hinted = next(row for row in projection["option_sets"] if row["source_type"] == "stage_point_branch")

    assert hinted["topic"] == "useful_god"
    assert hinted["selection_mode"] == "rank_one_or_more"
    assert hinted["visibility"]["user"] == "hidden"
    assert hinted["visibility"]["practitioner"] == "interactive"
    assert hinted["visibility"]["admin"] == "interactive"
    assert {"earth_primary", "fire_secondary"} <= {row["value"] for row in hinted["options"]}
    assert hinted["display"]["role_projection"]["user"] == "read_only_primary_branch"
    assert hinted["boundary"] == "branch_option_set_is_practitioner_calibration_not_customer_choice"
    assert role_visible_option_sets([hinted], role_key="user") == []
    assert role_visible_option_sets([hinted], role_key="practitioner")[0]["role_visibility"] == "interactive"
    assert role_visible_option_sets([hinted], role_key="admin")[0]["role_visibility"] == "interactive"


def test_thinking_projection_attaches_text_options_to_stage_points() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-toi-thinking", locale="zh")
    projection = build_thinking_projection(runtime)
    useful_step = next(step for step in projection["steps"] if step["step_id"] == "useful_god_arbitration")

    point_set = useful_step["stage_point_set"]
    assert point_set["text_option_projection"]["version"] == TEXT_OPTION_PROJECTION_VERSION
    assert "option_sets" in point_set
    assert "semantic_units" in point_set
    assert point_set["text_option_projection"]["training_signal"]["trainable"] is True
    assert set(point_set["text_option_projection"]["training_signal"]["blocked_targets"]) >= {
        "chart_facts",
        "calendar_conversion",
        "four_pillars",
    }
    assert all("option_set_ids" in point for point in useful_step["stage_points"])


def test_current_dialogue_turn_exposes_response_option_set_without_extra_questions() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-toi-dialogue", locale="zh")
    payload = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")

    turn = payload["reading_surface"]["current_dialogue_turn"]
    assert turn["version"] == "v30.current_dialogue_turn.v1"
    assert turn["ui_policy"]["max_visible_questions"] == 1
    assert turn["response_option_set"]["version"] == OPTION_SET_VERSION
    assert turn["response_option_set"]["visibility"]["user"] == "interactive"
    assert turn["response_option_set"]["boundary"] == "dialogue_response_option_set_records_user_background_without_mutating_chart_facts"
    assert len(turn["visible_option_sets"]) == 1
    assert payload["reading_surface"]["next_question"]["response_option_set"]["option_set_id"] == turn["response_option_set"]["option_set_id"]


def test_current_dialogue_turn_requires_central_brain_ask_decision() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-dialogue-central-gate", locale="zh")
    policy_effect = deepcopy(runtime.question_plan.policy_effect)
    central = policy_effect["central_reading_state"]
    central["brain_decision_trace"] = {
        **central.get("brain_decision_trace", {}),
        "selected_action": "continue_next_stage",
    }
    central["value_of_information_policy"] = {
        **central.get("value_of_information_policy", {}),
        "selected_action": "continue_next_stage",
        "question_value": 1.0,
        "information_gain": 1.0,
    }
    central["next_action"] = {
        **central.get("next_action", {}),
        "action": "continue_next_stage",
    }
    patched_plan = runtime.question_plan.model_copy(update={"policy_effect": policy_effect})
    patched = runtime.model_copy(update={"question_plan": patched_plan})

    payload = build_presentation_model(patched, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    turn = payload["reading_surface"]["current_dialogue_turn"]

    assert turn["action"] == "continue"
    assert turn["question"] == {}
    assert turn["decision_basis"]["relevance_passed"] is False
    assert turn["decision_basis"]["relevance_reason"] == "central_brain_did_not_select_dialogue"


def test_current_dialogue_turn_does_not_fallback_to_graph_or_first_question() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-dialogue-no-legacy-fallback", locale="zh")
    policy_effect = deepcopy(runtime.question_plan.policy_effect)
    central = policy_effect["central_reading_state"]
    central["dialogue_plan"] = {
        **central.get("dialogue_plan", {}),
        "current_question_id": "",
    }
    central["brain_decision_trace"] = {
        **central.get("brain_decision_trace", {}),
        "selected_action": "ask_stage_question",
    }
    central["next_action"] = {
        **central.get("next_action", {}),
        "action": "ask_stage_question",
    }
    assert policy_effect["question_dialogue_graph"]["next_question_id"]
    assert runtime.question_plan.recommended_questions
    patched_plan = runtime.question_plan.model_copy(update={"policy_effect": policy_effect})
    patched = runtime.model_copy(update={"question_plan": patched_plan})

    payload = build_presentation_model(patched, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    surface = payload["reading_surface"]
    turn = surface["current_dialogue_turn"]

    assert surface["next_question"] == {}
    assert surface["next_question_id"] == ""
    assert turn["action"] == "stop"
    assert turn["question"] == {}
    assert turn["decision_basis"]["relevance_reason"] == "missing_question"


def test_initial_answer_panel_is_not_user_feedback_until_question_answered() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-dialogue-not-self-answer", locale="zh")
    payload = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")

    answer = payload["answer_panel"]
    turn = payload["reading_surface"]["current_dialogue_turn"]

    assert answer["question_id"] == turn["question"]["question_id"]
    assert answer["user_submitted"] is False
    assert answer["question_stage_id"] == turn["stage_id"]
    assert answer["question_label"] == turn["question"]["label"]

    answered = attach_question_outcome(
        runtime,
        answer["question_id"],
        {
            "answer": "用户选择了这个问题，并补充了现实背景。",
            "outcome_status": "answered",
            "selected_option": "career:pressure",
            "confidence": 0.74,
            "feedback_tags": ["pytest"],
        },
    )
    answered_payload = build_presentation_model(answered, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")

    assert answered_payload["answer_panel"]["user_submitted"] is True
    assert answered_payload["answer_panel"]["question_stage_id"]
    assert answered_payload["answer_panel"]["question_label"]


def test_practitioner_selection_updates_weights_not_chart_facts() -> None:
    option_set = build_response_option_set_for_question(
        {
            "question_id": "q-test",
            "topic": "decision",
            "label": "这个八字最需要注意的决策盲点是什么？",
            "options": [
                {"option_id": "risk", "label": "先看风险"},
                {"option_id": "action", "label": "先看行动建议"},
            ],
        },
        stage_id="domain_synthesis",
        role_key="practitioner",
    )
    selection = build_practitioner_selection(
        option_set,
        action="rank",
        selected_option_ids=["risk", "action"],
        ranked_option_ids=["risk", "action"],
        note="先看风险，再给行动建议。",
        confidence=0.82,
    )

    assert selection["version"] == PRACTITIONER_SELECTION_VERSION
    assert selection["action"] == "rank"
    assert "stage_point.display_priority" in selection["effect_targets"]
    assert "four_pillars" in selection["forbidden_effect_targets"]
    assert "calendar_conversion" in selection["forbidden_effect_targets"]
    assert selection["boundary"] == "practitioner_selection_updates_belief_and_weight_not_chart_facts"
