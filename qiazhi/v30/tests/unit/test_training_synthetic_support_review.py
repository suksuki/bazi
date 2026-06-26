from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_training_synthetic_support_review,
    run_training_synthetic_support_review,
)


REQUIRED_SIGNAL_IDS = [
    "v30.training_signal.krp_unit_coverage",
    "v30.training_signal.m3_core_spine_coverage",
    "v30.training_signal.birth_chart_conversion_boundary",
    "v30.training_signal.ten_god_energy_fusion",
    "v30.training_signal.ranked_decision_fusion",
    "v30.training_signal.practical_reading_quality",
    "v30.training_signal.api_projection_contract",
    "v30.training_signal.interaction_loop_quality",
    "v30.training_signal.question_model_signal_personalization",
    "v30.training_signal.real_case_calibration_pack",
    "v30.training_signal.bazi_llm_output_acceptance_quality",
]


def _llm(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.llm_bazi_expression_support_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "llm_bazi_expression_support_ready" if ready else "llm_bazi_expression_support_blocked",
            "llm_bazi_expression_support_ready": ready,
            "bazi_llm_acceptance_case_count": 5,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
    }


def _training(*, blocked: bool = False, chart_fact_tuning: bool = False) -> dict[str, object]:
    signals = [
        {
            "signal_id": signal_id,
            "domain": domain,
            "payload": {
                "can_tune_chart_facts": chart_fact_tuning if signal_id == REQUIRED_SIGNAL_IDS[0] else False,
                "chart_fact_mutation_allowed_count": 1 if chart_fact_tuning and signal_id == REQUIRED_SIGNAL_IDS[0] else 0,
            },
        }
        for signal_id, domain in zip(
            REQUIRED_SIGNAL_IDS,
            [
                "policy_tuning",
                "m3_core_spine",
                "core_calculation",
                "ten_god_energy",
                "ranked_decision",
                "practical_reading",
                "presentation",
                "question_intelligence",
                "question_intelligence",
                "real_case_calibration",
                "llm",
            ],
        )
    ]
    signals.extend(
        {
            "signal_id": f"v30.training_signal.extra_{idx}",
            "domain": f"extra_domain_{idx}",
            "payload": {"can_tune_chart_facts": False, "chart_fact_mutation_allowed_count": 0},
        }
        for idx in range(25)
    )
    return {
        "suite_id": "v30.synthetic.training_pipeline",
        "passed": not blocked,
        "case_count": 91,
        "passed_count": 91 if not blocked else 90,
        "failed_count": 0 if not blocked else 1,
        "training_signals": signals,
    }


def _manifest(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.synthetic_coverage_manifest.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "bt6_synthetic_coverage_manifest_ready" if ready else "bt6_synthetic_coverage_manifest_blocked",
            "synthetic_coverage_manifest_ready": ready,
            "synthetic_completion": 99 if ready else 90,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "summary": {
            "implemented_tier_count": 22,
            "implemented_case_count": 120,
            "major_node_only_tiers": ["all"],
        },
    }


def _sample(*, blocked: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "run_id": "v30.518k.sample.test",
        "mode": "sample",
        "case_count": 8,
        "promotion_signal": "eligible" if ready else "blocked",
        "failure_clusters": [] if ready else [{"cluster": "missing_interaction_state"}],
        "artifact_record_id": "v30.518k.artifact.test",
        "artifact_search_backend": "json_fallback",
        "artifact_searchable": True,
        "coverage_metrics": {
            "question_recommendation_coverage": 8,
            "model_signal_summary_coverage": 8,
            "interaction_state_coverage": 8,
            "visible_internal_next_question_split_count": 8,
            "calibration_probe_user_visible_count": 0 if ready else 1,
        },
        "drift_metrics": {
            "unsupported_question_rate": 0.0,
            "missing_model_signal_summary_rate": 0.0,
            "missing_interaction_state_rate": 0.0,
            "calibration_probe_user_visible_rate": 0.0,
        },
    }


def test_training_synthetic_support_review_ready(tmp_path: Path) -> None:
    result = build_training_synthetic_support_review(
        llm_support=_llm(),
        training_pipeline=_training(),
        synthetic_manifest=_manifest(),
        sample_518k=_sample(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.training_synthetic_support_review.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "training_synthetic_support_ready"
    assert decision["training_signal_count"] >= 30
    assert result["next_mainline_selection"]["next_task"] == "Core Chain Steady-State Summary"
    assert Path(str(result["artifact_uri"])).exists()


def test_training_support_review_blocks_missing_llm_or_training_tier() -> None:
    llm_result = build_training_synthetic_support_review(
        llm_support=_llm(blocked=True),
        training_pipeline=_training(),
        synthetic_manifest=_manifest(),
        sample_518k=_sample(),
    )
    training_result = build_training_synthetic_support_review(
        llm_support=_llm(),
        training_pipeline=_training(blocked=True),
        synthetic_manifest=_manifest(),
        sample_518k=_sample(),
    )

    assert "llm_support_ready_before_training_review" in llm_result["decision"]["failed_closeout_check_ids"]
    assert "training_pipeline_synthetic_ready" in training_result["decision"]["failed_closeout_check_ids"]


def test_training_support_review_blocks_chart_fact_tuning_or_manifest_gap() -> None:
    tuning_result = build_training_synthetic_support_review(
        llm_support=_llm(),
        training_pipeline=_training(chart_fact_tuning=True),
        synthetic_manifest=_manifest(),
        sample_518k=_sample(),
    )
    manifest_result = build_training_synthetic_support_review(
        llm_support=_llm(),
        training_pipeline=_training(),
        synthetic_manifest=_manifest(blocked=True),
        sample_518k=_sample(),
    )

    assert "training_cannot_tune_chart_facts" in tuning_result["decision"]["failed_closeout_check_ids"]
    assert "synthetic_manifest_ready_and_heavy_tiers_explicit" in manifest_result["decision"]["failed_closeout_check_ids"]


def test_training_support_review_blocks_518k_sample_gap() -> None:
    result = build_training_synthetic_support_review(
        llm_support=_llm(),
        training_pipeline=_training(),
        synthetic_manifest=_manifest(),
        sample_518k=_sample(blocked=True),
    )

    assert result["status"] == "blocked"
    assert "518k_sample_distribution_ready" in result["decision"]["failed_closeout_check_ids"]


def test_training_synthetic_support_review_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_training_synthetic_support_review(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "training_synthetic_support_ready"
    assert result["decision"]["training_pipeline_case_count"] >= 90
    assert result["decision"]["sample_518k_case_count"] == 8
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
