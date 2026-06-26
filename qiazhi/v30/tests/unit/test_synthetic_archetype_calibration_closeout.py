from __future__ import annotations

from v30.validation.synthetic_archetype_calibration_closeout import (
    SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION,
    build_synthetic_archetype_calibration_closeout,
    run_synthetic_archetype_calibration_closeout,
)
from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
)
from v30.validation.synthetic_archetype_tier_registration import SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
from v30.validation.synthetic_archetype_training_signal_review import (
    SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION,
)


def test_syn_cal4_closeout_ready() -> None:
    result = run_synthetic_archetype_calibration_closeout()

    assert result["version"] == SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION
    assert result["status"] == "completed"
    decision = result["decision"]
    assert decision["decision_status"] == "syn_cal4_synthetic_archetype_calibration_closed"
    assert decision["synthetic_archetype_calibration_closed"] is True
    assert decision["passed_closeout_check_count"] == decision["closeout_check_count"]
    assert decision["training_signal_count"] == 4
    assert decision["queued_item_count"] == 0
    assert decision["auto_apply_training_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["full_pytest_required"] is False
    assert decision["full_518k_required"] is False

    frozen = result["frozen_evidence"]
    assert frozen["syn_cal1_archetype_calibration"]["ready"] is True
    assert frozen["syn_cal2_tier_registration"]["ready"] is True
    assert frozen["syn_cal3_training_signal_review"]["ready"] is True
    assert result["routine_cadence"]["calibration_queue_policy"]["review_only"] is True
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S0"


def test_syn_cal4_blocks_if_syn_cal3_not_ready() -> None:
    payload = _training_signal_review_payload(ready=False)
    result = build_synthetic_archetype_calibration_closeout(training_signal_review=payload)

    assert result["status"] == "blocked"
    decision = result["decision"]
    assert decision["decision_status"] == "syn_cal4_synthetic_archetype_calibration_blocked"
    assert "syn_cal3_training_signals_frozen_ready" in decision["failed_closeout_check_ids"]
    assert decision["full_pytest_required"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL4-FR"


def _training_signal_review_payload(*, ready: bool = True) -> dict:
    signals = [
        {
            "signal_id": "v30.training_signal.synthetic_archetype_m3_rule_claim_coverage",
            "target_modules": ["M3"],
            "review_only": True,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.synthetic_archetype_m5_ranked_candidate_alignment",
            "target_modules": ["M5"],
            "review_only": True,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.synthetic_archetype_m6_practical_claim_specificity",
            "target_modules": ["M6"],
            "review_only": True,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
        },
        {
            "signal_id": "v30.training_signal.synthetic_archetype_review_boundary_safety",
            "target_modules": ["M3", "M5", "M6"],
            "review_only": True,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "external_release_allowed": False,
        },
    ]
    return {
        "version": SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_archetype_training_signal_review_ready": ready,
            "decision_status": "syn_cal3_training_signal_review_ready" if ready else "syn_cal3_training_signal_review_blocked",
            "check_count": 6,
            "passed_check_count": 6 if ready else 5,
            "training_signal_count": 4,
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
            "tier_registration": {
                "version": SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
                "ready": True,
                "targeted_tier": "synthetic_archetype_rule_claim",
                "routine_targeted_gate": True,
                "included_in_synthetic_all": False,
            },
            "archetype_calibration": {
                "version": SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
                "ready": True,
                "case_count": 4,
                "passed_case_count": 4,
            },
            "case_summary": {
                "case_count": 4,
                "passed_case_count": 4,
                "failed_case_count": 0,
                "pass_ratio": 1.0,
            },
        },
        "training_signals": signals,
        "calibration_queue_items": [],
    }
