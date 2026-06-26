from __future__ import annotations

from v30.validation.synthetic_typical_answer_calibration_closeout import (
    SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION,
    build_synthetic_typical_answer_calibration_closeout,
    run_synthetic_typical_answer_calibration_closeout,
)
from v30.validation.synthetic_typical_answer_training_signal_review import (
    SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
)
from v30.validation.synthetic_typical_bazi_answer_calibration import SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION


def test_core_cal_s3_closeout_ready() -> None:
    result = run_synthetic_typical_answer_calibration_closeout()

    assert result["version"] == SYNTHETIC_TYPICAL_ANSWER_CALIBRATION_CLOSEOUT_VERSION
    assert result["status"] == "completed"
    decision = result["decision"]
    assert decision["decision_status"] == "core_cal_s3_synthetic_typical_answer_calibration_closed"
    assert decision["synthetic_typical_answer_calibration_closed"] is True
    assert decision["passed_closeout_check_count"] == decision["closeout_check_count"]
    assert decision["training_signal_count"] == 5
    assert decision["queued_item_count"] == 0
    assert decision["auto_apply_training_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["full_pytest_required"] is False
    assert decision["full_518k_required"] is False

    frozen = result["frozen_evidence"]
    assert frozen["core_cal_s1_typical_answer_calibration"]["ready"] is True
    assert frozen["core_cal_s2_training_signal_review"]["ready"] is True
    assert frozen["synthetic_typical_bazi_answer_tier"]["passed"] is True
    assert result["routine_cadence"]["calibration_queue_policy"]["review_only"] is True
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S4"


def test_core_cal_s3_blocks_if_s2_not_ready() -> None:
    result = build_synthetic_typical_answer_calibration_closeout(
        training_signal_review=_training_signal_review_payload(ready=False)
    )

    assert result["status"] == "blocked"
    decision = result["decision"]
    assert decision["decision_status"] == "core_cal_s3_synthetic_typical_answer_calibration_blocked"
    assert "core_cal_s2_training_signals_frozen_ready" in decision["failed_closeout_check_ids"]
    assert decision["full_pytest_required"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S3-FR"


def _training_signal_review_payload(*, ready: bool = True) -> dict:
    signals = [
        _signal("v30.training_signal.synthetic_typical_answer_m3_guidance_sanitization", ["M3"]),
        _signal("v30.training_signal.synthetic_typical_answer_m6_domain_mechanism_specificity", ["M6"]),
        _signal("v30.training_signal.synthetic_typical_answer_llm_expression_boundary", ["LLM"]),
        _signal("v30.training_signal.synthetic_typical_answer_interaction_answer_alignment", ["interaction"]),
        _signal("v30.training_signal.synthetic_typical_answer_review_boundary_safety", ["M3", "M6", "LLM", "interaction"]),
    ]
    return {
        "version": SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_typical_answer_training_signal_review_ready": ready,
            "decision_status": "core_cal_s2_training_signal_review_ready"
            if ready
            else "core_cal_s2_training_signal_review_blocked",
            "check_count": 6,
            "passed_check_count": 6 if ready else 5,
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
        "upstream_summary": {
            "typical_answer_calibration": {
                "version": SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
                "ready": True,
                "case_count": 5,
                "passed_case_count": 5,
                "failed_case_count": 0,
            },
            "synthetic_tier": {
                "suite_id": "v30.synthetic.synthetic_typical_bazi_answer",
                "passed": True,
                "case_count": 3,
            },
            "case_summary": {
                "case_count": 5,
                "passed_case_count": 5,
                "failed_case_count": 0,
                "pass_ratio": 1.0,
            },
        },
        "training_signals": signals,
        "calibration_queue_items": [],
    }


def _signal(signal_id: str, target_modules: list[str]) -> dict:
    return {
        "signal_id": signal_id,
        "target_modules": target_modules,
        "review_only": True,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "external_release_allowed": False,
    }
