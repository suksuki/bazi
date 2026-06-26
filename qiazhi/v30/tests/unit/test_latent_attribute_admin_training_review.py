from __future__ import annotations

from v30.validation.latent_attribute_admin_training_review import (
    LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION,
    FORBIDDEN_LATENT_TRAINING_SCOPE,
    run_latent_attribute_admin_training_review,
)


def test_latent_attribute_admin_training_review_is_ready_and_review_only(tmp_path) -> None:
    result = run_latent_attribute_admin_training_review(
        review_id="unit-hf-r26",
        artifact_dir=tmp_path,
    )

    assert result["version"] == LATENT_ATTRIBUTE_ADMIN_TRAINING_REVIEW_VERSION
    assert result["decision"]["review_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["decision"]["candidate_count"] == 3
    assert result["candidate_summary"]["auto_apply_allowed_count"] == 0
    assert result["candidate_summary"]["pointer_promotion_allowed_count"] == 0
    assert result["candidate_summary"]["chart_fact_mutation_allowed_count"] == 0
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["artifact_uri"]

    target_domains = {row["target_domain"] for row in result["candidates"]}
    assert target_domains == {
        "latent_attribute_inference",
        "question_strategy",
        "individualized_projection",
    }
    for row in result["candidates"]:
        assert row["requires_operator_review"] is True
        assert row["auto_apply_allowed"] is False
        assert row["policy_pointer_promotion_allowed"] is False
        assert row["chart_fact_mutation_allowed"] is False
        assert FORBIDDEN_LATENT_TRAINING_SCOPE <= set(row["forbidden_training_scope"])
        assert row["source_signal_id"] == "v30.training_signal.latent_bazi_attribute_alignment"


def test_latent_attribute_admin_training_review_blocks_bad_boundaries() -> None:
    from v30.validation.latent_attribute_admin_training_review import build_latent_attribute_admin_training_review

    result = build_latent_attribute_admin_training_review(
        observability={"version": "v30.latent_policy_observability_readiness.v1", "decision": {"readiness_ready": True}},
        latent_divergence_suite={"suite_id": "latent", "passed": True, "passed_count": 2, "case_count": 2},
        training_signals=[],
        review_id="unit-hf-r26-blocked",
    )

    assert result["decision"]["review_ready"] is False
    assert "latent_training_signal_available" in result["decision"]["failed_check_ids"]
