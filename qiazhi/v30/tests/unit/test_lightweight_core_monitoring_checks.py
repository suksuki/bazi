from __future__ import annotations

import subprocess
import sys

from v30.validation.lightweight_core_monitoring_checks import build_lightweight_core_monitoring_checks


def _loop() -> dict[str, object]:
    return {
        "version": "v30.core_monitoring_loop.v1",
        "status": "completed",
        "decision": {
            "decision_status": "core_monitoring_loop_ready",
            "monitoring_loop_ready": True,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "monitoring_baseline_summary": {"check_count": 4, "required_check_count": 4},
    }


def _checks() -> list[dict[str, object]]:
    return [
        {
            "check_id": "m1_m8_frozen_scope",
            "decision_status": "ready_for_targeted_calibration_iteration",
            "expected_status": "ready_for_targeted_calibration_iteration",
        },
        {
            "check_id": "targeted_candidate_review",
            "decision_status": "ready_for_validation_gate_review",
            "expected_status": "ready_for_validation_gate_review",
        },
        {
            "check_id": "targeted_validation_gate",
            "decision_status": "ready_for_policy_pointer_review",
            "expected_status": "ready_for_policy_pointer_review",
        },
        {
            "check_id": "pointer_decision_no_write",
            "decision_status": "pointer_promotion_deferred",
            "expected_status": "pointer_promotion_deferred",
        },
    ]


def test_lightweight_core_monitoring_checks_pass() -> None:
    result = build_lightweight_core_monitoring_checks(core_monitoring_loop=_loop(), check_results=_checks())

    assert result["version"] == "v30.lightweight_core_monitoring_checks.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "lightweight_core_monitoring_checks_passed"
    assert result["decision"]["regression_detected"] is False
    assert result["check_summary"]["passed_check_count"] == 4
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "P2"


def test_lightweight_core_monitoring_checks_block_failed_check() -> None:
    checks = _checks()
    checks[2]["decision_status"] = "targeted_validation_gate_blocked"

    result = build_lightweight_core_monitoring_checks(core_monitoring_loop=_loop(), check_results=checks)

    assert result["status"] == "blocked"
    assert result["decision"]["regression_detected"] is True
    assert result["decision"]["failed_check_ids"] == ["targeted_validation_gate"]
    assert "monitoring_checks_failed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "P1"


def test_lightweight_core_monitoring_checks_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_lightweight_core_monitoring_checks.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.lightweight_core_monitoring_checks.v1: lightweight_core_monitoring_checks_passed" in result.stdout
    assert "- checks: 4/4" in result.stdout
