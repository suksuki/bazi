from __future__ import annotations

from v30.hidden_factor import HiddenFactorCalibration, build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime


def test_structured_feedback_builds_chart_bound_latent_bazi_profile() -> None:
    runtime = create_smoke_runtime("latent-profile-reading", day_master="庚", day_master_element="metal")
    answered = attach_question_outcome(
        runtime,
        "q_v30_hidden_factor_boundary_discovery",
        {
            "answer": "2021 and 2024 repeated as career pressure.",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "certain",
            },
            "feedback_tags": ["career", "structured_hidden_factor"],
            "confidence": 0.82,
        },
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": "latent-profile-reading:feedback:career-pressure",
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
    profile = final_runtime.question_plan.policy_effect["latent_bazi_profile"]
    summary = final_runtime.question_plan.policy_effect["latent_bazi_profile_summary"]

    assert profile["version"] == "v30.latent_bazi_profile.v1"
    assert profile["reading_id"] == answered.reading_id
    assert profile["context_id"] == answered.chart_context.context_id
    assert profile["chart_signature"]["day_master"] == "庚"
    assert profile["chart_signature"]["natal_pillars"] == answered.chart_context.natal_pillars
    assert profile["chart_fact_mutation_allowed"] is False
    assert profile["dimensions"][0]["state_tag"] == "career_pressure"
    assert profile["dimensions"][0]["linked_domains"] == ["career", "useful_god"]
    assert "authority" in profile["dimensions"][0]["linked_ten_god_families"]
    assert profile["dimensions"][0]["years"] == [2021, 2024]
    assert profile["dimensions"][0]["recurrence"] == "repeated"
    assert profile["dimensions"][0]["intensity"] == "medium"
    assert profile["dimensions"][0]["confidence"] == "certain"
    assert profile["dimensions"][0]["linked_dynamic_path_ids"]
    assert profile["dimensions"][0]["linked_claim_ids"]
    assert profile["training_routes"] == [
        "latent_bazi_profile_calibration",
        "question_strategy_calibration",
        "real_bazi_diagnosis_calibration",
    ]
    assert summary["dimension_count"] == 1
    assert summary["active_state_tags"] == ["career_pressure"]
    assert summary["chart_fact_mutation_allowed"] is False
