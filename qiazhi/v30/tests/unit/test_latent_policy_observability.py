from __future__ import annotations

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.latent_policy_observability import (
    LATENT_POLICY_OBSERVABILITY_VERSION,
    run_latent_policy_observability_readiness,
)


def test_admin_projection_exposes_latent_policy_observability_without_customer_leak() -> None:
    runtime = create_smoke_runtime(
        "unit-hf-r25-admin",
        policy_payload_overrides={
            "question_policy": _latent_policy_payload(),
            "rule_policy": _latent_policy_payload(),
        },
        active_policy_version_overrides={
            "question_policy": "question_policy.unit-hf-r25",
            "rule_policy": "rule_policy.unit-hf-r25",
        },
    )
    admin = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    user = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")

    observability = admin["diagnostics"]["latent_policy_observability"]
    assert observability["version"] == "v30.latent_policy_observability.v1"
    assert observability["status"] == "policy_active"
    assert observability["customer_visible"] is False
    assert observability["question_policy"]["source_signal_id"] == "v30.training_signal.latent_bazi_attribute_alignment"
    assert observability["rule_policy"]["source_signal_id"] == "v30.training_signal.latent_bazi_attribute_alignment"
    assert observability["influenced_question_count"] >= 1
    assert observability["training_boundary"]["can_tune_question_strategy"] is True
    assert observability["training_boundary"]["can_tune_chart_facts"] is False
    assert observability["training_boundary"]["chart_fact_mutation_allowed"] is False
    assert {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"} <= set(
        observability["training_boundary"]["blocked_training_routes"]
    )

    rendered_user = str(
        {
            "reading_surface": user["reading_surface"],
            "questions": user["questions"],
            "answer_panel": user["answer_panel"],
            "diagnostics": user["diagnostics"],
        }
    )
    assert "latent_policy_observability" not in rendered_user
    assert "latent_bazi_attribute_policy" not in rendered_user
    assert user["diagnostics"] == {}


def test_latent_policy_observability_readiness_passes() -> None:
    result = run_latent_policy_observability_readiness(reading_id="unit-hf-r25-readiness")

    assert result["version"] == LATENT_POLICY_OBSERVABILITY_VERSION
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "HF-R2.6"


def _latent_policy_payload() -> dict[str, object]:
    return {
        "weights": {
            "latent_bazi_attribute_policy": {
                "version": "v30.latent_bazi_attribute_policy.v1",
                "mode": "latent_personalization_candidate_not_chart_fact",
                "source_signal_id": "v30.training_signal.latent_bazi_attribute_alignment",
                "reverse_inference_weight": 1.08,
                "question_need_weight": 1.08,
                "individualized_projection_weight": 1.06,
                "domain_bias_weights": {"career_bias": 1.03, "wealth_bias": 1.03, "relationship_bias": 1.02},
                "ten_god_modifier_weights": {"authority": 1.03, "resource": 1.03, "wealth": 1.02},
                "global_attribute_weights": {"resource_index": 1.03, "risk_index": 1.02, "stability_index": 1.02},
                "blocked_training_routes": ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"],
                "can_tune_latent_inference": True,
                "can_tune_question_strategy": True,
                "can_tune_individualized_projection": True,
                "can_tune_chart_facts": False,
                "boundary": "latent_bazi_attribute_policy_trains_personalization_not_chart_facts",
            }
        }
    }
