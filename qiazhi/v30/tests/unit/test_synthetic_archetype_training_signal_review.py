from __future__ import annotations

from v30.validation.synthetic_archetype_rule_claim_calibration import (
    SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
)
from v30.validation.synthetic_archetype_tier_registration import SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
from v30.validation.synthetic_archetype_training_signal_review import (
    SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION,
    build_synthetic_archetype_training_signal_review,
    run_synthetic_archetype_training_signal_review,
)


def test_syn_cal3_training_signal_review_ready() -> None:
    result = run_synthetic_archetype_training_signal_review()

    assert result["version"] == SYNTHETIC_ARCHETYPE_TRAINING_SIGNAL_REVIEW_VERSION
    assert result["status"] == "completed"
    decision = result["decision"]
    assert decision["decision_status"] == "syn_cal3_training_signal_review_ready"
    assert decision["training_signal_count"] == 4
    assert decision["queued_item_count"] == 0
    assert decision["auto_apply_training_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL4"

    signal_ids = {signal["signal_id"] for signal in result["training_signals"]}
    assert {
        "v30.training_signal.synthetic_archetype_m3_rule_claim_coverage",
        "v30.training_signal.synthetic_archetype_m5_ranked_candidate_alignment",
        "v30.training_signal.synthetic_archetype_m6_practical_claim_specificity",
        "v30.training_signal.synthetic_archetype_review_boundary_safety",
    } <= signal_ids
    for signal in result["training_signals"]:
        assert set(signal["target_modules"]) <= {"M3", "M5", "M6"}
        assert signal["review_only"] is True
        assert signal["chart_fact_mutation_allowed"] is False
        assert signal["auto_apply_training_allowed"] is False
        assert signal["policy_pointer_promotion_allowed"] is False
        assert signal["external_release_allowed"] is False


def test_syn_cal3_blocks_if_tier_registration_not_ready() -> None:
    result = build_synthetic_archetype_training_signal_review(
        tier_registration=_tier_registration_payload(ready=False),
        archetype_calibration=_archetype_calibration_payload(),
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "syn_cal3_training_signal_review_blocked"
    assert "syn_cal2_tier_registration_ready" in result["decision"]["failed_check_ids"]
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL3-FR"


def _tier_registration_payload(*, ready: bool = True) -> dict:
    return {
        "version": SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_archetype_tier_registration_ready": ready,
            "decision_status": "syn_cal2_tier_registration_ready" if ready else "syn_cal2_tier_registration_blocked",
            "check_count": 6,
            "passed_check_count": 6 if ready else 5,
            "calibration_queue_item_count": 0,
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "tier_contract": {
            "tier": "synthetic_archetype_rule_claim",
            "routine_targeted_gate": ready,
            "included_in_synthetic_all": False,
        },
        "calibration_queue_items": [],
    }


def _archetype_calibration_payload() -> dict:
    checks = {
        "m3_claim_domains_cover_archetype": True,
        "m3_dynamic_mechanisms_cover_archetype": True,
        "m5_strength_candidate_matches": True,
        "m5_useful_god_candidate_matches": True,
        "m5_candidate_scores_present": True,
        "m6_domain_claims_present": True,
        "m6_summaries_are_bazi_specific": True,
    }
    return {
        "version": SYNTHETIC_ARCHETYPE_RULE_CLAIM_CALIBRATION_VERSION,
        "status": "completed",
        "decision": {
            "synthetic_archetype_calibration_ready": True,
            "decision_status": "syn_cal1_archetype_rule_claim_calibration_ready",
            "case_count": 4,
            "passed_case_count": 4,
            "failed_case_ids": [],
            "failed_check_ids": [],
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "case_reviews": [
            {
                "case_id": f"syn_cal1.mock_{index}",
                "passed": True,
                "failed_check_ids": [],
                "checks": checks,
                "calibration_target_modules": [],
                "observed": {
                    "claim_domain_counts": {"wealth": 1, "career": 1, "relationship": 1},
                    "mechanism_counts": {"官印相生": 1, "财官印制化": 1},
                },
            }
            for index in range(4)
        ],
    }
