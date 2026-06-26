from __future__ import annotations

from v30.validation.core_calibration_observation_summary import build_core_calibration_observation_summary


def _p1_payload(*, failed: bool = False) -> dict[str, object]:
    checks = [
        {
            "check_id": "m1_m8_frozen_scope",
            "decision_status": "ready_for_targeted_calibration_iteration",
            "expected_status": "ready_for_targeted_calibration_iteration",
            "passed": True,
        },
        {
            "check_id": "targeted_candidate_review",
            "decision_status": "ready_for_validation_gate_review",
            "expected_status": "ready_for_validation_gate_review",
            "passed": True,
        },
        {
            "check_id": "targeted_validation_gate",
            "decision_status": "ready_for_policy_pointer_review" if not failed else "blocked",
            "expected_status": "ready_for_policy_pointer_review",
            "passed": not failed,
        },
        {
            "check_id": "pointer_decision_no_write",
            "decision_status": "pointer_promotion_deferred",
            "expected_status": "pointer_promotion_deferred",
            "passed": True,
        },
    ]
    return {
        "version": "v30.lightweight_core_monitoring_checks.v1",
        "status": "completed" if not failed else "blocked",
        "decision": {
            "decision_status": "lightweight_core_monitoring_checks_passed" if not failed else "lightweight_core_monitoring_checks_blocked",
            "monitoring_checks_completed": not failed,
            "regression_detected": failed,
            "failed_check_ids": ["targeted_validation_gate"] if failed else [],
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "check_summary": {
            "required_check_count": 4,
            "executed_check_count": 4,
            "passed_check_count": 3 if failed else 4,
            "failed_check_count": 1 if failed else 0,
            "missing_check_ids": [],
        },
        "checks": checks,
        "policy_boundary": {"pointer_write_allowed": False},
        "next_mainline_selection": {"task_id": "P2"},
    }


def test_core_calibration_observation_summary_ready() -> None:
    result = build_core_calibration_observation_summary(lightweight_monitoring_checks=_p1_payload())

    assert result["version"] == "v30.core_calibration_observation_summary.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_calibration_observation_summary_ready"
    assert result["decision"]["stable_observation_count"] == 4
    assert result["decision"]["focused_module_fix_required"] is False
    assert result["decision"]["full_pytest_required"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P3"
    assert result["boundary"] == "p2_summarizes_core_calibration_observations_without_full_pytest"


def test_core_calibration_observation_summary_blocks_failed_p1_check() -> None:
    result = build_core_calibration_observation_summary(lightweight_monitoring_checks=_p1_payload(failed=True))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_calibration_observation_summary_blocked"
    assert result["decision"]["regression_detected"] is True
    assert result["decision"]["focused_module_fix_required"] is True
    assert result["decision"]["needs_review_check_ids"] == ["targeted_validation_gate"]
    assert "p1_failed_checks_present" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "P2-FR"
