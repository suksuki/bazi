from __future__ import annotations

from copy import deepcopy

from v30.hidden_factor import HiddenFactorCalibration, build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime


def test_default_individualized_projection_is_diagnostic_and_neutral() -> None:
    runtime = create_smoke_runtime("latent-projection-default", day_master="庚", day_master_element="metal")
    projection = runtime.question_plan.policy_effect["latent_bazi_individualized_projection"]
    summary = runtime.question_plan.policy_effect["latent_bazi_individualized_projection_summary"]

    assert projection["version"] == "v30.latent_bazi_individualized_model_projection.v1"
    assert projection["status"] == "default"
    assert projection["individualization_ready"] is False
    assert projection["chart_fact_mutation_allowed"] is False
    assert projection["base_ten_god_energy_mutation_allowed"] is False
    assert projection["ranked_decision_mutation_allowed"] is False
    assert summary["individualization_ready"] is False
    assert summary["adjusted_domain_count"] == 0


def test_latent_attributes_create_projection_without_mutating_base_models() -> None:
    runtime = create_smoke_runtime("latent-projection-career", day_master="庚", day_master_element="metal")
    base_ten_god_energy = deepcopy(runtime.question_plan.policy_effect["ten_god_energy_model"])
    base_summary = deepcopy(runtime.question_plan.policy_effect["ten_god_energy_summary"])
    base_ranked = deepcopy(runtime.question_plan.policy_effect["ranked_decisions"])
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
            "feedback_id": "latent-projection-career:feedback:career-pressure",
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
    projection = final_runtime.question_plan.policy_effect["latent_bazi_individualized_projection"]
    summary = final_runtime.question_plan.policy_effect["latent_bazi_individualized_projection_summary"]

    assert final_runtime.question_plan.policy_effect["ten_god_energy_model"] == base_ten_god_energy
    assert final_runtime.question_plan.policy_effect["ten_god_energy_summary"] == base_summary
    assert final_runtime.question_plan.policy_effect["ranked_decisions"] == base_ranked
    assert projection["status"] == "inferred"
    assert projection["individualization_ready"] is True
    authority = next(row for row in projection["family_energy_projection"] if row["family"] == "authority")
    resource = next(row for row in projection["family_energy_projection"] if row["family"] == "resource")
    career = next(row for row in projection["domain_path_projection"] if row["domain"] == "career")
    assert authority["latent_multiplier"] > 1.0
    assert resource["latent_multiplier"] > 1.0
    assert career["adjusted_path_score"] > career["base_path_score"]
    assert projection["ranked_decision_projection"]
    assert projection["chart_fact_mutation_allowed"] is False
    assert projection["base_ten_god_energy_mutation_allowed"] is False
    assert projection["ranked_decision_mutation_allowed"] is False
    assert "authority" in summary["adjusted_families"]
    assert "career" in summary["adjusted_domains"]
