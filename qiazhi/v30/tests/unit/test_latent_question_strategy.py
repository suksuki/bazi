from __future__ import annotations

from v30.hidden_factor import HiddenFactorCalibration, build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.interaction_constraints import answer_constraints_for_question, validate_structured_interaction_payload
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime


def test_latent_question_strategy_exists_without_forcing_primary_flow() -> None:
    runtime = create_smoke_runtime("latent-question-strategy-default", day_master="庚", day_master_element="metal")
    strategy = runtime.question_plan.policy_effect["latent_question_strategy"]
    hidden = next(row for row in runtime.question_plan.recommended_questions if row["topic"] == "hidden_factor")

    assert strategy["version"] == "v30.latent_question_need_strategy.v1"
    assert strategy["chart_fact_mutation_allowed"] is False
    assert strategy["skip_policy"]["continue_with_neutral_defaults"] is True
    assert hidden["latent_question_strategy"]["version"] == strategy["version"]
    assert hidden["latent_question_strategy"]["target_latent_attributes"]
    assert runtime.question_plan.recommended_questions[0]["question_id"] != "q_v30_hidden_factor_boundary_discovery"
    assert runtime.question_plan.policy_effect["interaction_state"]["visible_next_question_id"].startswith("q_v30_user_")


def test_inferred_latent_attributes_reduce_followup_need() -> None:
    runtime = create_smoke_runtime("latent-question-strategy-inferred", day_master="庚", day_master_element="metal")
    answered = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "2021 and 2024 repeated as career pressure.",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "strong",
                "recurrence": "repeated",
                "confidence": "certain",
            },
            "feedback_tags": ["career", "structured_hidden_factor"],
            "confidence": 0.86,
        },
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": "latent-question-strategy-inferred:feedback",
            "special_event_years": [2021, 2024],
            "repeated_states": ["career_pressure"],
            "feedback_status": "confirmed",
        },
    )
    state = build_hidden_factor_state(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        calibration=HiddenFactorCalibration.model_validate(answered.question_plan.policy_effect["hidden_factor_calibration"]),
        feedback=[feedback],
    )

    final_runtime = attach_hidden_factor_state(answered, state.model_dump(mode="json"))
    strategy = final_runtime.question_plan.policy_effect["latent_question_strategy"]
    hidden = next(row for row in final_runtime.question_plan.recommended_questions if row["topic"] == "hidden_factor")

    assert strategy["ask_now"] is False
    assert "latent_attributes_already_inferred" in strategy["reasons"]
    assert "latent_question_strategy:not_needed_now" in hidden["reasons"]
    assert final_runtime.question_plan.policy_effect["latent_bazi_attributes"]["status"] == "inferred"


def test_uncertain_or_skip_latent_answer_is_valid_but_does_not_update_attributes() -> None:
    constraints = answer_constraints_for_question(stage="dialogue_discovery", topic="hidden_factor")
    signal = validate_structured_interaction_payload(
        question_id="q_v30_hidden_factor_boundary_discovery",
        question_type="structured_hidden_factor",
        constraints=constraints,
        structured_payload={},
        selected_option="hidden_factor:default",
    )
    assert signal["valid"] is True
    assert signal["allowed_to_update_hidden_factor"] is False
    assert signal["latent_answer_status"] == "skipped_or_uncertain"

    runtime = create_smoke_runtime("latent-question-strategy-skip", day_master="庚", day_master_element="metal")
    updated = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "",
            "selected_option": "hidden_factor:default",
            "structured_payload": {},
            "confidence": 0.0,
            "feedback_tags": ["latent_skip"],
        },
    )
    strategy = updated.question_plan.policy_effect["latent_question_strategy"]

    assert updated.question_plan.policy_effect["latest_interaction_turn_signal"]["allowed_to_update_hidden_factor"] is False
    assert updated.question_plan.policy_effect["latent_bazi_attributes"]["status"] == "default"
    assert strategy["ask_now"] is False
    assert "user_recently_skipped_latent_question" in strategy["reasons"]
