from __future__ import annotations

import subprocess
import sys

from v30.validation.core_monitoring_loop import build_core_monitoring_loop


def _selection() -> dict[str, object]:
    return {
        "version": "v30.mainline_selection_after_release_pause.v1",
        "status": "ready_for_next_mainline",
        "decision": {
            "decision_status": "core_monitoring_and_calibration_loop_selected",
            "selected_task_id": "P0",
            "selected_track": "core_monitoring_and_calibration",
            "external_release_ready": False,
            "full_pytest_authorized": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _closeout() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_closeout.v1",
        "decision": {
            "decision_status": "targeted_calibration_closed_with_no_promotion",
            "closeout_ready": True,
            "targeted_calibration_track_closed": True,
        },
        "pointer_decision_summary": {"pointer_write_performed": False},
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "monitoring_baseline": {
            "check_count": 4,
            "full_pytest_required": False,
            "full_518k_required": False,
            "checks": [
                {"check_id": "m1_m8_frozen_scope"},
                {"check_id": "targeted_candidate_review"},
                {"check_id": "targeted_validation_gate"},
                {"check_id": "pointer_decision_no_write"},
            ],
        },
    }


def test_core_monitoring_loop_ready() -> None:
    result = build_core_monitoring_loop(
        mainline_selection_after_release_pause=_selection(),
        targeted_calibration_closeout=_closeout(),
    )

    assert result["version"] == "v30.core_monitoring_loop.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_monitoring_loop_ready"
    assert result["decision"]["regression_detected"] is False
    assert result["decision"]["core_module_reopen_recommended"] is False
    assert result["monitoring_baseline_summary"]["check_count"] == 4
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "P1"


def test_core_monitoring_loop_blocks_missing_monitoring_check() -> None:
    closeout = _closeout()
    closeout["monitoring_baseline"] = {
        "check_count": 3,
        "checks": [
            {"check_id": "m1_m8_frozen_scope"},
            {"check_id": "targeted_candidate_review"},
            {"check_id": "pointer_decision_no_write"},
        ],
    }

    result = build_core_monitoring_loop(
        mainline_selection_after_release_pause=_selection(),
        targeted_calibration_closeout=closeout,
    )

    assert result["status"] == "blocked"
    assert "monitoring_check_count_low" in result["decision"]["blockers"]
    assert "monitoring_required_checks_missing" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "P0"


def test_core_monitoring_loop_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_core_monitoring_loop.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.core_monitoring_loop.v1: core_monitoring_loop_ready" in result.stdout
    assert "- monitoring_checks: 4/4" in result.stdout
