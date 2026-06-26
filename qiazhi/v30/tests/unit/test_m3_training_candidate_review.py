from __future__ import annotations

from pathlib import Path

from v30.validation import build_m3_core_spine_snapshot, build_m3_training_candidate_review, run_synthetic_tier


def test_m3_training_candidate_review_is_ready_and_review_only(tmp_path: Path) -> None:
    snapshot = build_m3_core_spine_snapshot(include_518k_sample=True, sample_limit=8)
    training = run_synthetic_tier("training_pipeline").model_dump(mode="json")
    review = build_m3_training_candidate_review(
        m3_snapshot=snapshot,
        training_pipeline=training,
        artifact_dir=tmp_path,
    )
    decision = review["decision"]
    summary = review["candidate_summary"]

    assert review["version"] == "v30.m3_training_candidate_review.v1"
    assert review["status"] == "completed"
    assert decision["decision_status"] == "m3_g3_training_candidate_review_ready"
    assert decision["ready_for_training_review"] is True
    assert decision["ready_for_pointer_promotion"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["fixed_bazi_verdict_allowed"] is False
    assert summary["candidate_count"] >= 8
    assert summary["forbidden_scope_hits"] == {}
    assert Path(str(review["artifact_uri"])).exists()


def test_m3_training_candidate_review_required_candidate_types_and_boundaries() -> None:
    snapshot = build_m3_core_spine_snapshot(include_518k_sample=True, sample_limit=8)
    training = run_synthetic_tier("training_pipeline").model_dump(mode="json")
    review = build_m3_training_candidate_review(m3_snapshot=snapshot, training_pipeline=training)
    candidate_types = {row["candidate_type"] for row in review["candidates"]}

    assert {
        "source_coverage_weight_candidate",
        "rule_path_priority_candidate",
        "domain_rule_depth_candidate",
        "counterevidence_trace_candidate",
        "dynamic_path_priority_candidate",
        "question_strategy_candidate",
        "training_distribution_candidate",
        "distribution_518k_candidate",
    }.issubset(candidate_types)
    for candidate in review["candidates"]:
        assert candidate["requires_operator_review"] is True
        assert candidate["auto_apply_allowed"] is False
        assert candidate["policy_pointer_promotion_allowed"] is False
        assert candidate["chart_fact_mutation_allowed"] is False
        assert candidate["fixed_bazi_verdict_allowed"] is False
        assert "four_pillars" not in candidate["allowed_training_scope"]
        assert "fixed_useful_god_verdict" not in candidate["allowed_training_scope"]


def test_m3_training_candidate_review_records_training_and_518k_sources() -> None:
    snapshot = build_m3_core_spine_snapshot(include_518k_sample=True, sample_limit=8)
    training = run_synthetic_tier("training_pipeline").model_dump(mode="json")
    review = build_m3_training_candidate_review(m3_snapshot=snapshot, training_pipeline=training)
    source = review["source_summary"]
    checks = {row["check_id"]: row for row in review["checks"]}

    assert source["m3_calibration_version"] == "v30.m3_source_governed_calibration.v1"
    assert source["training_pipeline_passed"] is True
    assert source["validation_518k"]["included"] is True
    assert source["validation_518k"]["case_count"] == 8
    assert checks["training_pipeline_passed"]["passed"] is True
    assert checks["sample_518k_distribution_present"]["passed"] is True
    assert review["next_mainline_selection"]["next_task"] == "M3-G4 Source Extraction Queue Operationalization"
