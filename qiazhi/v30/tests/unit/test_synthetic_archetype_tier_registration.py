from __future__ import annotations

from v30.validation import SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES, run_synthetic_tier
from v30.validation.synthetic_archetype_tier_registration import (
    SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION,
    build_synthetic_archetype_tier_registration,
    run_synthetic_archetype_tier_registration,
)


def _tier(*, passed: bool = True) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.synthetic_archetype_rule_claim",
        "passed": passed,
        "case_count": len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES),
        "passed_count": len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES) if passed else len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES) - 1,
        "failed_count": 0 if passed else 1,
        "results": [
            {"case_id": case.case_id, "passed": passed or index > 0}
            for index, case in enumerate(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES)
        ],
    }


def _calibration(*, ready: bool = True, queue: bool = False) -> dict[str, object]:
    return {
        "version": "v30.synthetic_archetype_rule_claim_calibration.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "synthetic_archetype_calibration_ready": ready,
            "decision_status": "syn_cal1_archetype_rule_claim_calibration_ready" if ready else "blocked",
            "case_count": len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES),
            "passed_case_count": len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES) if ready else len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES) - 1,
            "failed_case_ids": [] if ready else ["failed-case"],
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "calibration_queue": [
            {
                "queue_item_id": "syn_cal1.calibration.failed-case",
                "case_id": "failed-case",
                "target_modules": ["M5"],
                "failed_check_ids": ["m5_strength_candidate_matches"],
                "review_only": True,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "boundary": "syn_cal1_queue_routes_archetype_gaps_to_review_not_auto_training",
            }
        ]
        if queue
        else [],
    }


def test_syn_cal2_registers_targeted_tier_and_queue_contract() -> None:
    result = build_synthetic_archetype_tier_registration(
        synthetic_tier=_tier(),
        archetype_calibration=_calibration(),
    )

    assert result["version"] == SYNTHETIC_ARCHETYPE_TIER_REGISTRATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "syn_cal2_tier_registration_ready"
    assert result["tier_contract"]["tier"] == "synthetic_archetype_rule_claim"
    assert result["tier_contract"]["routine_targeted_gate"] is True
    assert result["tier_contract"]["included_in_synthetic_all"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL3"


def test_syn_cal2_blocks_failed_tier_but_preserves_readonly_queue() -> None:
    result = build_synthetic_archetype_tier_registration(
        synthetic_tier=_tier(passed=False),
        archetype_calibration=_calibration(ready=False, queue=True),
    )

    assert result["status"] == "blocked"
    assert "synthetic_archetype_tier_passes_current_runtime" in result["decision"]["failed_check_ids"]
    assert result["calibration_queue_items"][0]["review_only"] is True
    assert result["calibration_queue_items"][0]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SYN-CAL2-FR"


def test_synthetic_archetype_rule_claim_tier_runs_through_synthetic_framework() -> None:
    result = run_synthetic_tier("synthetic_archetype_rule_claim")

    assert result.suite_id == "v30.synthetic.synthetic_archetype_rule_claim"
    assert result.case_count == len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES)
    assert result.passed


def test_syn_cal2_runner_passes_current_registration() -> None:
    result = run_synthetic_archetype_tier_registration()

    assert result["decision"]["decision_status"] == "syn_cal2_tier_registration_ready"
    assert result["tier_summary"]["case_count"] == len(SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES)
    assert result["decision"]["external_release_allowed"] is False
