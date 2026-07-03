from __future__ import annotations

from v30.validation import run_decision_centered_architecture_validation


def test_decision_centered_architecture_validation_accepts_current_spine() -> None:
    result = run_decision_centered_architecture_validation(reading_id="pytest-dca-validation")

    assert result["version"] == "v30.decision_centered_architecture_validation.v1"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["decision_status"] == "dca_10_architecture_validation_ready"
    assert result["decision"]["live_llm_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "DCA-12"
    assert all(row["passed"] is True for row in result["checks"])


def test_decision_centered_architecture_validation_covers_core_boundaries() -> None:
    result = run_decision_centered_architecture_validation(reading_id="pytest-dca-validation-boundaries")
    checks = {row["check_id"]: row for row in result["checks"]}

    assert checks["decision_engine_result_is_present_and_current"]["observed"]["verdict_count"] > 0
    assert checks["llm_context_reads_decision_verdicts_without_override"]["observed"]["fact_boundary"]["llm_can_override_decision_verdict"] is False
    assert checks["journey_compresses_material_without_default_llm_longform"]["observed"]["journey_step_ids"] == [
        "journey_chart_calibration",
        "journey_structure_useful_god",
        "journey_material_candidates",
        "journey_path_timing_domain",
        "journey_branch_calibration",
        "journey_decision_verdicts",
        "journey_final_expression",
    ]
    assert "decision.verdict" in checks["sidebar_memory_tracks_verdict_summary"]["observed"]["memory_ids"]
    assert checks["practitioner_branch_options_are_trainable_without_fact_mutation"]["observed"]["decision_option_count"] >= 1
    assert checks["decision_question_slot_drives_dialogue_without_becoming_step"]["observed"]["candidate_source"] == "decision_engine_next_question_slot"
    assert checks["feedback_recalculation_feeds_admin_training_projection"]["observed"]["feedback_applied"] is True
    assert checks["feedback_recalculation_feeds_admin_training_projection"]["observed"]["affected_verdict_ids"]
