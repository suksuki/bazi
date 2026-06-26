from __future__ import annotations

from v30.validation.core_calibration_drift_watch import build_core_calibration_drift_watch


def _p2_payload(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_calibration_observation_summary.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_calibration_observation_summary_ready" if not blocked else "core_calibration_observation_summary_blocked",
            "observation_summary_ready": not blocked,
            "stable_observation_count": 4 if not blocked else 3,
            "needs_review_observation_count": 0 if not blocked else 1,
            "needs_review_check_ids": [] if not blocked else ["targeted_validation_gate"],
            "regression_detected": blocked,
            "focused_module_fix_required": blocked,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "monitoring_evidence_summary": {
            "passed_check_count": 4 if not blocked else 3,
            "required_check_count": 4,
        },
    }


def test_core_calibration_drift_watch_ready_without_new_evidence() -> None:
    result = build_core_calibration_drift_watch(
        core_calibration_observation_summary=_p2_payload(),
        calibration_evidence=[],
    )

    assert result["version"] == "v30.core_calibration_drift_watch.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_calibration_drift_watch_ready"
    assert result["decision"]["drift_detected"] is False
    assert result["decision"]["focused_module_fix_required"] is False
    assert result["drift_watch_policy"]["cadence"] == "on_new_calibration_evidence_only"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P4"
    assert result["boundary"] == "p3_establishes_core_calibration_drift_watch_without_full_pytest"


def test_core_calibration_drift_watch_routes_new_drift_evidence() -> None:
    result = build_core_calibration_drift_watch(
        core_calibration_observation_summary=_p2_payload(),
        calibration_evidence=[
            {
                "evidence_id": "sample_drift",
                "check_id": "targeted_validation_gate",
                "status": "drift",
                "severity": "review",
            }
        ],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_calibration_drift_watch_blocked"
    assert result["decision"]["drift_detected"] is True
    assert result["decision"]["focused_module_fix_required"] is True
    assert result["drift_routes"][0]["check_id"] == "targeted_validation_gate"
    assert result["drift_routes"][0]["module_targets"] == ["M4", "M5", "M7"]
    assert result["drift_routes"][0]["reopen_all_core_modules"] is False
    assert result["next_mainline_selection"]["task_id"] == "P3-FR"


def test_core_calibration_drift_watch_blocks_pointer_write_pressure() -> None:
    result = build_core_calibration_drift_watch(
        core_calibration_observation_summary=_p2_payload(),
        calibration_evidence=[
            {
                "check_id": "pointer_decision_no_write",
                "status": "stable",
                "severity": "none",
                "pointer_write_requested": True,
            }
        ],
    )

    assert result["status"] == "blocked"
    assert "calibration_evidence_requests_pointer_write" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
