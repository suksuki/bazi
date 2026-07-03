from __future__ import annotations

from v30.runtime import attach_question_outcome, create_smoke_runtime


def test_runtime_exposes_question_dialogue_graph() -> None:
    runtime = create_smoke_runtime("v30-question-dialogue-graph-test")
    graph = runtime.question_plan.policy_effect["question_dialogue_graph"]
    interaction_state = runtime.question_plan.policy_effect["interaction_state"]
    assert graph["next_question_id"] == runtime.question_plan.recommended_questions[0]["question_id"]
    assert graph["internal_next_question_id"] == "q_v30_time_context_boundary"
    assert graph["followup_reason"] == "highest_ranked_unanswered_question"
    assert interaction_state["interaction_stage"] == "initial_question_selection"
    assert interaction_state["visible_next_question_id"] == "q_v30_user_relationship_pattern"
    assert interaction_state["internal_next_question_id"] == graph["next_question_id"]
    top_visible = next(
        row for row in runtime.question_plan.recommended_questions
        if row["question_id"] == interaction_state["visible_next_question_id"]
    )
    assert any(
        str(reason).startswith("model_signal_question_focus:")
        for reason in top_visible["reasons"]
    )
    assert len(graph["nodes"]) == len(runtime.question_plan.recommended_questions)
    assert len(graph["edges"]) >= 2
    assert "time_context_first_blocks_unbound_timing_claims" in graph["policy_notes"]


def test_calibrated_hidden_factor_adds_followup_edges() -> None:
    runtime = create_smoke_runtime(
        "v30-question-dialogue-graph-calibrated-test",
        hidden_factor_user_calibrated=True,
    )
    graph = runtime.question_plan.policy_effect["question_dialogue_graph"]
    relations = {edge["relation"] for edge in graph["edges"]}
    assert "calibrated_hidden_factor_can_condition_followup" in relations


def test_question_outcome_recomputes_graph_and_followup_reasons() -> None:
    runtime = create_smoke_runtime("v30-question-outcome-test")
    rehydrated = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "2021 and 2024 repeated as career pressure years.",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "approximate",
            },
            "confidence": 0.82,
            "feedback_tags": ["career", "hidden_factor_followup"],
        },
    )
    outcomes = rehydrated.question_plan.session_state["question_outcomes"]
    graph = rehydrated.question_plan.policy_effect["question_dialogue_graph"]
    interaction_state = rehydrated.question_plan.policy_effect["interaction_state"]
    answered = next(
        row for row in rehydrated.question_plan.recommended_questions
        if row["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    )
    assert outcomes[0]["boundary"] == "question_outcome_feedback_not_chart_fact"
    assert outcomes[0]["topic"] == "hidden_factor"
    assert outcomes[0]["selected_option"] == "domain:career"
    assert "question_dialogue_outcome_consumed" in graph["policy_notes"]
    assert "question_outcome_topic:hidden_factor" in graph["policy_notes"]
    assert "structured_option_selected:domain:career" in graph["policy_notes"]
    assert graph["next_question_id"] == "q_v30_user_career_direction"
    assert graph["internal_next_question_id"] == "q_v30_user_career_direction"
    assert graph["followup_reason"].startswith("selected_domain:career:")
    assert interaction_state["version"] == "v30.interaction_state.v1"
    assert interaction_state["interaction_stage"] == "followup_question_selection"
    assert interaction_state["selected_domain"] == "career"
    assert interaction_state["answered_question_ids"] == ["q_v30_hidden_factor_boundary_discovery"]
    assert interaction_state["selected_option_ids"] == ["domain:career"]
    assert interaction_state["visible_next_question_id"] == "q_v30_user_career_direction"
    assert interaction_state["internal_next_question_id"] == "q_v30_user_career_direction"
    assert interaction_state["boundary"] == "interaction_state_guides_followup_not_chart_fact"
    assert "question_outcome_answered" in answered["reasons"]
    assert rehydrated.question_plan.session_state["known_user_signals"]["selected_options"] == ["domain:career"]
    assert rehydrated.chart_context == runtime.chart_context
    assert rehydrated.feature_evidence == runtime.feature_evidence


def test_question_answer_stays_bound_to_clicked_question_when_followup_changes() -> None:
    runtime = create_smoke_runtime("v30-question-answer-stage-boundary")
    answered_question_id = "q_v30_hidden_factor_boundary_discovery"

    rehydrated = attach_question_outcome(
        runtime,
        answered_question_id,
        {
            "answer": "2024 repeated as career pressure.",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "approximate",
            },
            "confidence": 0.8,
            "feedback_tags": ["career"],
        },
    )

    assert rehydrated.question_plan.policy_effect["interaction_state"]["visible_next_question_id"] == "q_v30_user_career_direction"
    assert rehydrated.answer_context is not None
    assert rehydrated.answer_result is not None
    assert rehydrated.answer_context.selected_question_anchor.question_id == answered_question_id
    assert rehydrated.answer_result.question_id == answered_question_id
