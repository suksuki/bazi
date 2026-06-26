from __future__ import annotations

from v30.validation.real_bazi_diagnosis_steady_state import (
    REAL_BAZI_DIAGNOSIS_STEADY_STATE_VERSION,
    build_real_bazi_diagnosis_steady_state,
    run_real_bazi_diagnosis_steady_state,
)


def test_rbd_s113_steady_state_ready() -> None:
    result = run_real_bazi_diagnosis_steady_state(real_case_limit=8, sample_518k_limit=8)

    assert result["version"] == REAL_BAZI_DIAGNOSIS_STEADY_STATE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rbd_s113_steady_state_ready"
    assert result["decision"]["rbd_mainline_closed_for_current_scope"] is True
    assert result["decision"]["routine_replay_ready"] is True
    assert result["decision"]["training_signal_count"] >= 4
    assert result["decision"]["queued_item_count"] >= 1
    assert result["policy_boundary"]["rbd_mainline_closed_for_current_scope"] is True
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["full_518k_required"] is False
    assert result["rbd_module_summary"]["completed_stage_count"] >= 12
    assert set(result["rbd_module_summary"]["supported_domains"]) == {
        "career",
        "wealth",
        "relationship",
        "health",
        "timing",
    }
    assert result["routine_cadence"]["calibration_review_required_before_tuning"] is True
    assert result["next_mainline_selection"]["task_id"] == "RBD-S1-WAIT"


def test_rbd_s113_blocks_missing_s112_queue() -> None:
    result = build_real_bazi_diagnosis_steady_state(
        training_calibration_queue={
            "version": "v30.real_bazi_training_calibration_queue.v1",
            "status": "blocked",
            "decision": {
                "training_calibration_queue_ready": False,
                "decision_status": "rbd_s112_training_calibration_queue_blocked",
                "training_signal_count": 0,
                "queued_item_count": 0,
            },
            "training_signals": [],
            "calibration_queue_items": [],
            "policy_boundary": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
            },
            "upstream_summary": {
                "decision": {"distribution_replay_ready": False},
                "real_case_summary": {"ready_ratio": 0.0, "replay_case_count": 0},
                "sample_518k_summary": {"ready_ratio": 0.0, "replay_case_count": 0},
            },
        }
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rbd_s113_steady_state_blocked"
    assert "rbd_s112_training_queue_ready" in result["decision"]["failed_closeout_check_ids"]
    assert result["policy_boundary"]["full_518k_required"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
