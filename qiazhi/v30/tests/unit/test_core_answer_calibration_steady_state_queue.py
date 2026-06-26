from __future__ import annotations

from pathlib import Path

from v30.validation.core_answer_calibration_steady_state_queue import (
    CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
    build_core_answer_calibration_steady_state_queue,
)
from v30.validation.synthetic_typical_answer_calibration_closeout import (
    SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
)


def test_core_cal_s4_answer_calibration_queue_ready_waiting(tmp_path: Path) -> None:
    result = build_core_answer_calibration_steady_state_queue(
        typical_answer_closeout=_closeout(),
        answer_quality_evidence=[],
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION
    assert result["status"] == "completed"
    assert decision["decision_status"] == "core_cal_s4_answer_calibration_steady_state_queue_ready"
    assert decision["core_answer_calibration_steady_state_queue_ready"] is True
    assert decision["waiting_for_new_answer_quality_evidence"] is True
    assert decision["focused_answer_fix_candidate_count"] == 0
    assert decision["core_module_reopen_by_default"] is False
    assert decision["full_pytest_required"] is False
    assert decision["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-WAIT"
    assert Path(str(result["artifact_uri"])).exists()


def test_core_cal_s4_routes_answer_quality_evidence_to_review_queue() -> None:
    result = build_core_answer_calibration_steady_state_queue(
        typical_answer_closeout=_closeout(),
        answer_quality_evidence=[
            {
                "evidence_id": "aq.review_001",
                "source_id": "answer_quality_delta_review",
                "severity": "review",
                "target_modules": ["M6_answer_expression", "llm_prompt"],
                "issue_type": "generic_answer_regression",
                "summary": "Answer drifted toward generic wording.",
            }
        ],
    )
    decision = result["decision"]

    assert result["status"] == "completed"
    assert decision["waiting_for_new_answer_quality_evidence"] is False
    assert decision["focused_answer_fix_candidate_count"] == 1
    assert decision["focused_answer_fix_required"] is True
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S4-FIX"
    queue_item = result["calibration_queue_items"][0]
    assert queue_item["target_modules"] == ["LLM", "M6"]
    assert queue_item["review_only"] is True
    assert queue_item["chart_fact_mutation_allowed"] is False
    assert queue_item["policy_pointer_promotion_allowed"] is False


def test_core_cal_s4_blocks_without_s3_closeout() -> None:
    result = build_core_answer_calibration_steady_state_queue(
        typical_answer_closeout=_closeout(closed=False),
        answer_quality_evidence=[],
    )

    assert result["status"] == "blocked"
    assert "core_cal_s3_typical_answer_closeout_ready" in result["decision"]["failed_check_ids"]
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S4-FR"
    assert result["policy_boundary"]["full_pytest_required"] is False


def _closeout(*, closed: bool = True) -> dict[str, object]:
    return {
        "version": SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
        "status": "completed" if closed else "blocked",
        "decision": {
            "decision_status": (
                "core_cal_s3_synthetic_typical_answer_calibration_closed"
                if closed
                else "core_cal_s3_synthetic_typical_answer_calibration_blocked"
            ),
            "synthetic_typical_answer_calibration_closed": closed,
            "closeout_check_count": 6,
            "passed_closeout_check_count": 6 if closed else 5,
            "training_signal_count": 5,
            "queued_item_count": 0,
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "routine_cadence": {
            "routine_targeted_commands": [
                "python3 scripts/run_synthetic_typical_bazi_answer_calibration.py",
                "python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer",
                "python3 scripts/run_synthetic_typical_answer_training_signal_review.py",
                "python3 scripts/run_synthetic_typical_answer_calibration_closeout.py",
            ],
        },
    }
