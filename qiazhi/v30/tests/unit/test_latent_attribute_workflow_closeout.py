from __future__ import annotations

from v30.validation.latent_attribute_workflow_closeout import (
    LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION,
    build_latent_attribute_workflow_closeout,
    run_latent_attribute_workflow_closeout,
)


def test_latent_attribute_workflow_closeout_is_ready(tmp_path) -> None:
    result = run_latent_attribute_workflow_closeout(
        closeout_id="unit-hf-r28",
        artifact_dir=tmp_path,
    )

    assert result["version"] == LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION
    assert result["decision"]["closeout_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["workflow_summary"]["runtime_latent_attribute_update_validated"] is True
    assert result["workflow_summary"]["admin_review_is_read_only"] is True
    assert result["workflow_summary"]["customer_policy_internals_hidden"] is True
    assert {"latent_attribute_inference", "question_strategy", "individualized_projection"} <= set(
        result["workflow_summary"]["training_routes"]
    )
    assert {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"} <= set(
        result["workflow_summary"]["blocked_training_routes"]
    )
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "HF-S1"
    assert result["artifact_uri"]


def test_latent_attribute_workflow_closeout_blocks_missing_ui_review_panel() -> None:
    result = build_latent_attribute_workflow_closeout(
        observability={
            "version": "v30.latent_policy_observability_readiness.v1",
            "decision": {"readiness_ready": True},
            "checks": [{"check_id": "customer_projection_hides_latent_policy_observability", "passed": True}],
        },
        admin_training_review={
            "version": "v30.latent_attribute_admin_training_review.v1",
            "decision": {"review_ready": True, "candidate_count": 3},
            "candidate_summary": {
                "auto_apply_allowed_count": 0,
                "pointer_promotion_allowed_count": 0,
                "chart_fact_mutation_allowed_count": 0,
            },
            "policy_boundary": {
                "review_only": True,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "chart_fact_mutation_allowed": False,
            },
        },
        latent_divergence_suite={
            "suite_id": "v30.synthetic.latent_bazi_divergence",
            "passed": True,
            "passed_count": 2,
            "case_count": 2,
        },
        training_signals=[
            {
                "signal_id": "v30.training_signal.latent_bazi_attribute_alignment",
                "payload": {
                    "training_routes": ["latent_attribute_inference", "question_strategy", "individualized_projection"],
                    "blocked_training_routes": ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"],
                    "can_tune_chart_facts": False,
                    "chart_fact_mutation_allowed_count": 0,
                },
            }
        ],
        ui_source={
            "source_exists": True,
            "latent_review_endpoint_loaded": True,
            "latent_review_panel_present": False,
            "forbidden_apply_controls_present": False,
        },
        closeout_id="unit-hf-r28-blocked",
    )

    assert result["decision"]["closeout_ready"] is False
    assert "admin_training_ui_has_read_only_review_panel" in result["decision"]["failed_check_ids"]
