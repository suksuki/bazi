from __future__ import annotations

from v30.training.dialogue_calibration_loop import (
    DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION,
    run_dialogue_training_calibration_loop,
)
from v30.validation.dialogue_training_calibration_loop import (
    DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION,
    run_dialogue_training_calibration_validation,
)


def test_dialogue_training_calibration_loop_builds_review_only_candidates() -> None:
    result = run_dialogue_training_calibration_loop(run_id="pytest-dtc1-loop")

    assert result["version"] == DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["dialogue_training_calibration_ready"] is True
    assert result["decision"]["policy_candidate_count"] >= 1
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["decision"]["policy_pointer_write_allowed"] is False
    assert result["sample_summary"]["sample_count"] >= 1
    assert result["sample_summary"]["macro_domains"]
    assert result["quality_summary"]["average_answer_quality"] > 0
    assert all(candidate["requires_operator_review"] is True for candidate in result["policy_candidates"])
    assert all(candidate["auto_apply_allowed"] is False for candidate in result["policy_candidates"])
    assert all(candidate["chart_fact_mutation_allowed"] is False for candidate in result["policy_candidates"])
    assert any(sample["semantic_training_slots"] for sample in result["training_samples"])


def test_dialogue_training_calibration_validation_is_read_only_ready() -> None:
    result = run_dialogue_training_calibration_validation(run_id="pytest-dtc1-validation")

    assert result["version"] == DIALOGUE_TRAINING_CALIBRATION_VALIDATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "dtc1_dialogue_training_calibration_ready"
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["decision"]["policy_pointer_write_allowed"] is False
    assert result["decision"]["auto_apply_training_allowed"] is False
    assert {row["check_id"] for row in result["checks"]} == {
        "loop_completed",
        "samples_and_candidates_ready",
        "quality_is_measured",
        "policy_boundary_is_safe",
        "loop_checks_passed",
    }
