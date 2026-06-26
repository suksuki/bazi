from __future__ import annotations

from v30.hidden_factor import HiddenFactorCalibration, build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime


def test_runtime_starts_with_default_latent_bazi_attributes() -> None:
    runtime = create_smoke_runtime("latent-attr-default", day_master="庚", day_master_element="metal")
    attrs = runtime.question_plan.policy_effect["latent_bazi_attributes"]
    summary = runtime.question_plan.policy_effect["latent_bazi_attributes_summary"]

    assert attrs["version"] == "v30.latent_bazi_attributes.v1"
    assert attrs["status"] == "default"
    assert attrs["reading_id"] == runtime.reading_id
    assert attrs["context_id"] == runtime.chart_context.context_id
    assert attrs["chart_signature"]["day_master"] == "庚"
    assert attrs["chart_fact_mutation_allowed"] is False
    assert attrs["global_attributes"]["luck_index"]["value"] == 0.5
    assert attrs["global_attributes"]["stability_index"]["value"] == 0.5
    assert attrs["ten_god_modifiers"]["authority"]["multiplier"] == 1.0
    assert attrs["domain_biases"]["career_bias"]["value"] == 0.5
    assert attrs["calculation_modifiers"]["individualization_ready"] is False
    assert summary["active_global_attributes"] == []
    assert summary["active_ten_god_modifiers"] == []


def test_structured_feedback_reverse_infers_calculation_ready_latent_attributes() -> None:
    runtime = create_smoke_runtime("latent-attr-career", day_master="庚", day_master_element="metal")
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
            "feedback_id": "latent-attr-career:feedback:career-pressure",
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
    attrs = final_runtime.question_plan.policy_effect["latent_bazi_attributes"]
    summary = final_runtime.question_plan.policy_effect["latent_bazi_attributes_summary"]
    modifiers = attrs["calculation_modifiers"]

    assert attrs["status"] == "inferred"
    assert attrs["source_profile_id"] == "latent-attr-career:latent_bazi_profile"
    assert attrs["global_attributes"]["resource_index"]["value"] > 0.5
    assert attrs["global_attributes"]["risk_index"]["value"] > 0.5
    assert attrs["ten_god_modifiers"]["authority"]["multiplier"] > 1.0
    assert attrs["ten_god_modifiers"]["resource"]["multiplier"] > 1.0
    assert attrs["domain_biases"]["career_bias"]["value"] > 0.5
    assert attrs["stability_thresholds"]["event_trigger_sensitivity"]["value"] > 0.5
    assert modifiers["individualization_ready"] is True
    assert modifiers["family_energy_multipliers"]["authority"] == attrs["ten_god_modifiers"]["authority"]["multiplier"]
    assert modifiers["domain_path_multipliers"]["career"] > 1.0
    assert attrs["inference_trace"][0]["state_tag"] == "career_pressure"
    assert attrs["chart_fact_mutation_allowed"] is False
    assert "resource_index" in summary["active_global_attributes"]
    assert "authority" in summary["active_ten_god_modifiers"]
    assert "career_bias" in summary["active_domain_biases"]
