from __future__ import annotations

from v30.validation import run_synthetic_canonical_steady_state
from v30.validation.synthetic_canonical_steady_state import (
    SYNTHETIC_CANONICAL_STEADY_STATE_VERSION,
    build_synthetic_canonical_steady_state,
)


def test_scal_s3_synthetic_canonical_steady_state_ready() -> None:
    result = run_synthetic_canonical_steady_state()

    assert result["version"] == SYNTHETIC_CANONICAL_STEADY_STATE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "scal_s3_synthetic_canonical_steady_state_ready"
    assert result["decision"]["routine_gate_ready"] is True
    assert result["decision"]["case_count"] >= 16
    assert result["decision"]["covered_family_count"] == 10
    assert result["routine_gate"]["gate_status"] == "frozen_targeted_gate"
    assert "before release-boundary validation" in result["routine_gate"]["required_trigger_events"]
    assert result["failure_routing"]["operator_review_required_before_tuning"] is True
    assert result["policy_boundary"]["uses_real_person_truth"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["full_518k_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "SCAL-S3-WAIT"


def test_scal_s3_blocks_missing_s2_pack_decision() -> None:
    result = build_synthetic_canonical_steady_state(
        canonical_pack_decision={
            "version": "v30.synthetic_canonical_pack_decision.v1",
            "status": "blocked",
            "decision": {
                "synthetic_canonical_pack_decision_ready": False,
                "decision_status": "scal_s2_expanded_canonical_pack_blocked",
                "case_count": 6,
                "covered_family_count": 1,
                "missing_families": {"mixed_officer_killing": "官杀混杂"},
            },
            "expansion_summary": {
                "case_count": 6,
                "covered_family_count": 1,
                "covered_families": {"weak_body_many_wealth": "财多身弱"},
                "missing_families": {"mixed_officer_killing": "官杀混杂"},
            },
            "policy_boundary": {
                "uses_real_person_truth": False,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
            },
        }
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "scal_s3_synthetic_canonical_steady_state_blocked"
    assert "scal_s2_pack_decision_ready" in result["decision"]["failed_check_ids"]
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["full_518k_required"] is False
