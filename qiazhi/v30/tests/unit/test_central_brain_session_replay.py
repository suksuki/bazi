from __future__ import annotations

from copy import deepcopy

from v30.hidden_factor import (
    HiddenFactorCalibration,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
)
from v30.presentation import build_presentation_model
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime
from v30.validation.central_brain_acceptance import run_central_brain_acceptance
from v30.validation.central_brain_session_replay import (
    CENTRAL_BRAIN_SESSION_REPLAY_VERSION,
    build_central_brain_session_replay,
    run_central_brain_session_replay,
)


def _builder_payloads() -> dict[str, object]:
    initial = create_smoke_runtime("unit-bt2-session")
    before = initial.chart_context.model_dump(mode="json")
    first_question_id = str(initial.question_plan.recommended_questions[0]["question_id"])
    first_visible_next = str(
        initial.question_plan.policy_effect["interaction_state"]["visible_next_question_id"]
    )
    answered = attach_question_outcome(
        initial,
        first_question_id,
        {
            "event_id": "unit-bt2-question-outcome",
            "answer": "先看事业。",
            "selected_option": "career",
            "confidence": 0.78,
            "feedback_tags": ["career"],
        },
    )
    second_question_id = str(answered.question_plan.recommended_questions[0]["question_id"])
    calibration = HiddenFactorCalibration.model_validate(
        answered.question_plan.policy_effect["hidden_factor_calibration"]
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": "unit-bt2-hidden-feedback",
            "special_event_years": [2020],
            "repeated_states": ["career_breakthrough"],
            "time_context_bindings": ["flow_year"],
            "feedback_status": "affirmed",
        },
    )
    hidden_state = build_hidden_factor_state(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        calibration=calibration,
        feedback=[feedback],
    )
    hidden_rehydrated = attach_hidden_factor_state(answered, hidden_state.model_dump(mode="json"))
    return {
        "bt1_acceptance": run_central_brain_acceptance(),
        "initial_runtime": initial.model_dump(mode="json"),
        "answered_runtime": answered.model_dump(mode="json"),
        "hidden_rehydrated_runtime": hidden_rehydrated.model_dump(mode="json"),
        "user_projection": build_presentation_model(hidden_rehydrated, role_key="user").model_dump(mode="json"),
        "practitioner_projection": build_presentation_model(
            hidden_rehydrated,
            role_key="practitioner",
        ).model_dump(mode="json"),
        "chart_fingerprint_before": before,
        "chart_fingerprint_after": hidden_rehydrated.chart_context.model_dump(mode="json"),
        "first_question_id": first_question_id,
        "second_question_id": second_question_id,
        "first_visible_next_question_id": first_visible_next,
        "final_visible_next_question_id": str(
            hidden_rehydrated.question_plan.policy_effect["interaction_state"]["visible_next_question_id"]
        ),
    }


def test_bt2_central_brain_session_replay_ready() -> None:
    result = run_central_brain_session_replay()

    assert result["version"] == CENTRAL_BRAIN_SESSION_REPLAY_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt2_central_brain_session_replay_ready"
    assert result["decision"]["central_brain_completion"] == 94
    assert result["decision"]["passed_replay_check_count"] == 6
    assert result["replay_summary"]["hidden_factor_state_status"] == "amplifier_candidate"
    assert result["replay_summary"]["user_diagnostics_hidden"] is True
    assert result["replay_summary"]["practitioner_central_brain_visible"] is True
    assert result["replay_summary"]["chart_fact_fingerprint_preserved"] is True
    assert result["next_mainline_selection"]["task_id"] == "BT3"


def test_bt2_blocks_chart_fact_mutation() -> None:
    payloads = _builder_payloads()
    after = deepcopy(payloads["chart_fingerprint_after"])
    after["day_master"] = "乙"  # type: ignore[index]
    payloads["chart_fingerprint_after"] = after

    result = build_central_brain_session_replay(**payloads)

    assert result["status"] == "blocked"
    assert "long_session_replay_read_only" in result["decision"]["failed_check_ids"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def test_bt2_blocks_customer_diagnostic_leak() -> None:
    payloads = _builder_payloads()
    user_projection = deepcopy(payloads["user_projection"])
    user_projection["diagnostics"] = {"central_brain": {"version": "leak"}}  # type: ignore[index]
    payloads["user_projection"] = user_projection

    result = build_central_brain_session_replay(**payloads)

    assert result["status"] == "blocked"
    assert "role_projection_split_preserved" in result["decision"]["failed_check_ids"]
