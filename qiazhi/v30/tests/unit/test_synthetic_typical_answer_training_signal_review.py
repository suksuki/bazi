from __future__ import annotations

from v30.validation.synthetic_typical_answer_training_signal_review import (
    SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION,
    build_synthetic_typical_answer_training_signal_review,
    run_synthetic_typical_answer_training_signal_review,
)
from v30.validation.synthetic_typical_bazi_answer_calibration import SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION


def test_core_cal_s2_training_signal_review_ready() -> None:
    result = run_synthetic_typical_answer_training_signal_review()

    assert result["version"] == SYNTHETIC_TYPICAL_ANSWER_TRAINING_SIGNAL_REVIEW_VERSION
    assert result["status"] == "completed"
    decision = result["decision"]
    assert decision["decision_status"] == "core_cal_s2_training_signal_review_ready"
    assert decision["training_signal_count"] == 5
    assert decision["queued_item_count"] == 0
    assert decision["auto_apply_training_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S3"

    signal_ids = {signal["signal_id"] for signal in result["training_signals"]}
    assert {
        "v30.training_signal.synthetic_typical_answer_m3_guidance_sanitization",
        "v30.training_signal.synthetic_typical_answer_m6_domain_mechanism_specificity",
        "v30.training_signal.synthetic_typical_answer_llm_expression_boundary",
        "v30.training_signal.synthetic_typical_answer_interaction_answer_alignment",
        "v30.training_signal.synthetic_typical_answer_review_boundary_safety",
    } <= signal_ids
    for signal in result["training_signals"]:
        assert set(signal["target_modules"]) <= {"M3", "M6", "LLM", "interaction"}
        assert signal["review_only"] is True
        assert signal["chart_fact_mutation_allowed"] is False
        assert signal["auto_apply_training_allowed"] is False
        assert signal["policy_pointer_promotion_allowed"] is False
        assert signal["external_release_allowed"] is False


def test_core_cal_s2_blocks_if_s1_calibration_not_ready() -> None:
    result = build_synthetic_typical_answer_training_signal_review(
        typical_answer_calibration=_calibration_payload(ready=False),
        synthetic_tier=_tier_payload(),
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_cal_s2_training_signal_review_blocked"
    assert "core_cal_s1_typical_answer_calibration_ready" in result["decision"]["failed_check_ids"]
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S2-FR"


def test_core_cal_s2_blocks_if_synthetic_tier_not_passing() -> None:
    result = build_synthetic_typical_answer_training_signal_review(
        typical_answer_calibration=_calibration_payload(),
        synthetic_tier=_tier_payload(passed=False),
    )

    assert result["status"] == "blocked"
    assert "synthetic_typical_bazi_answer_tier_passed" in result["decision"]["failed_check_ids"]
    assert result["decision"]["queued_item_count"] == 1
    queue_item = result["calibration_queue_items"][0]
    assert queue_item["issue_type"] == "synthetic_typical_answer_tier_failure"
    assert queue_item["chart_fact_mutation_allowed"] is False
    assert queue_item["policy_pointer_promotion_allowed"] is False


def _calibration_payload(*, ready: bool = True) -> dict:
    checks = {
        "answer_present": True,
        "answer_mentions_day_master_or_chart": True,
        "domain_tokens_covered": True,
        "mechanism_tokens_covered": True,
        "boundary_language_present": True,
        "evidence_trace_present": True,
        "no_internal_or_english_leak": True,
        "answer_boundary_non_mutating": True,
    }
    return {
        "version": SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_typical_answer_calibration_ready": ready,
            "decision_status": "core_cal_s1_synthetic_typical_answer_calibration_ready"
            if ready
            else "core_cal_s1_synthetic_typical_answer_calibration_blocked",
            "case_count": 5,
            "passed_case_count": 5 if ready else 4,
            "failed_case_count": 0 if ready else 1,
            "failed_case_ids": [] if ready else ["mock.failed"],
            "failed_check_ids": [] if ready else ["domain_tokens_covered"],
        },
        "case_reviews": [
            {
                "case_id": f"core_cal_s1.mock_{index}",
                "question_id": f"q_mock_{index}",
                "passed": True,
                "failed_check_ids": [],
                "checks": checks,
                "calibration_target_modules": [],
            }
            for index in range(5)
        ],
        "calibration_queue": []
        if ready
        else [
            {
                "case_id": "mock.failed",
                "target_modules": ["M6_answer_expression"],
                "failed_check_ids": ["domain_tokens_covered"],
            }
        ],
    }


def _tier_payload(*, passed: bool = True) -> dict:
    return {
        "suite_id": "v30.synthetic.synthetic_typical_bazi_answer",
        "passed": passed,
        "case_count": 3,
        "passed_count": 3 if passed else 2,
        "failed_count": 0 if passed else 1,
    }
