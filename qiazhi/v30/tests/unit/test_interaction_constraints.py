from __future__ import annotations

from v30.interaction_constraints import (
    ANSWER_CONSTRAINTS_VERSION,
    answer_constraints_for_question,
    hidden_factor_feedback_payload_from_turn_signal,
    validate_structured_interaction_payload,
)
from v30.presentation import build_presentation_model
from v30.runtime import attach_question_outcome, create_smoke_runtime


def test_hidden_factor_constraints_require_whitelisted_structured_payload() -> None:
    constraints = answer_constraints_for_question(stage="dialogue_discovery", topic="hidden_factor")

    assert constraints["version"] == ANSWER_CONSTRAINTS_VERSION
    assert constraints["constraint_type"] == "structured_hidden_factor"
    assert "state_tags" in constraints["required_fields"]
    assert "recurrence" in constraints["required_fields"]
    assert constraints["free_note_policy"] == "store_as_note_only"
    assert constraints["chart_fact_mutation_allowed"] is False

    signal = validate_structured_interaction_payload(
        question_id="q_v30_hidden_factor_boundary_discovery",
        question_type="structured_hidden_factor",
        constraints=constraints,
        structured_payload={
            "years": [2021, "2024"],
            "state_tags": ["career_pressure", "credential_pressure"],
            "intensity": "medium",
            "recurrence": "repeated",
            "confidence": "approximate",
            "selected_domain": "career",
        },
        free_note="当时换岗并准备证书",
        selected_option="domain:career",
    )

    assert signal["valid"] is True
    assert signal["allowed_to_update_hidden_factor"] is True
    assert signal["allowed_to_update_chart_facts"] is False
    assert signal["structured_payload"]["years"] == [2021, 2024]
    assert signal["structured_payload"]["state_tags"] == ["career_pressure", "credential_pressure"]
    assert {"hidden_factor", "selected_domain", "free_note_note_only"} <= set(signal["absorbed_signals"])


def test_free_text_or_unknown_tags_do_not_update_hidden_factor() -> None:
    constraints = answer_constraints_for_question(stage="dialogue_discovery", topic="hidden_factor")
    signal = validate_structured_interaction_payload(
        question_id="q_v30_hidden_factor_boundary_discovery",
        question_type="structured_hidden_factor",
        constraints=constraints,
        structured_payload={
            "years": [1888, "not-a-year"],
            "state_tags": ["anything_i_want"],
        },
        free_note="我感觉很多事情都不顺，这段自由文本不能进权重。",
        selected_option="",
    )

    assert signal["valid"] is False
    assert signal["allowed_to_update_hidden_factor"] is False
    assert signal["allowed_to_update_chart_facts"] is False
    assert "hidden_factor" not in signal["absorbed_signals"]
    assert hidden_factor_feedback_payload_from_turn_signal(signal, feedback_id="blocked") == {}
    rejected = set(signal["rejected_signals"])
    assert "years:year_out_of_range" in rejected
    assert "years:invalid_year" in rejected
    assert "state_tags:unknown_state_tag" in rejected


def test_runtime_records_interaction_brain_result_without_mutating_chart_facts() -> None:
    runtime = create_smoke_runtime("uib-2-runtime")
    original_chart_context = runtime.chart_context
    updated = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "2021 和 2024 都有事业压力。",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "certain",
            },
            "confidence": 0.82,
        },
    )

    result = updated.question_plan.policy_effect["interaction_brain_result"]
    outcome = updated.question_plan.session_state["question_outcomes"][0]
    assert result["version"] == "v30.unified_interaction_brain_result.v1"
    assert result["component_role"] == "structured_feedback_adapter"
    assert result["customer_decision_owner"] == "central_reading_state.brain_decision_trace"
    assert result["can_select_next_question"] is False
    assert result["can_generate_public_conclusion"] is False
    assert result["valid"] is True
    assert result["allowed_to_update_hidden_factor"] is True
    assert result["hidden_factor_feedback_payload"]["source"] == "unified_interaction_brain_structured_payload"
    assert result["hidden_factor_feedback_saved"] is False
    assert result["chart_fact_mutation_allowed"] is False
    assert outcome["interaction_turn_signal"]["structured_payload"]["state_tags"] == ["career_pressure"]
    assert updated.chart_context == original_chart_context


def test_invalid_structured_answer_retries_same_visible_question() -> None:
    runtime = create_smoke_runtime("uib-5-invalid-retry")
    updated = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "我只写自由文本，不选择结构化状态。",
            "outcome_status": "answered",
            "selected_option": "",
            "structured_payload": {},
            "confidence": 0.6,
        },
    )

    state = updated.question_plan.policy_effect["interaction_state"]
    hidden = next(
        row
        for row in updated.question_plan.recommended_questions
        if row["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    )
    outcome = updated.question_plan.session_state["question_outcomes"][0]

    assert outcome["constraint_valid"] is False
    assert state["invalid_retry_question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert state["visible_next_question_id"] == "q_v30_hidden_factor_boundary_discovery"
    assert "invalid_input_retry_required" in hidden["reasons"]
    assert "question_outcome_answered_suppressed" not in hidden["reasons"]
    assert updated.chart_context == runtime.chart_context


def test_presentation_projects_answer_constraints_for_next_question() -> None:
    runtime = create_smoke_runtime("uib-2-presentation")
    payload = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")

    hidden_question = next(row for row in payload["questions"] if row["topic"] == "hidden_factor")
    constraints = hidden_question["answer_constraints"]
    assert constraints["version"] == ANSWER_CONSTRAINTS_VERSION
    assert constraints["constraint_type"] == "structured_hidden_factor"
    assert constraints["allowed_state_tags"]
    assert constraints["invalid_input_action"] == "ask_user_to_reselect"
