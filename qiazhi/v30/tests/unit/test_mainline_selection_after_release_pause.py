from __future__ import annotations

import subprocess
import sys

from v30.validation.mainline_selection_after_release_pause import build_mainline_selection_after_release_pause


def _authorization() -> dict[str, object]:
    return {
        "version": "v30.post_release_boundary_authorization.v1",
        "status": "completed",
        "decision": {
            "decision_status": "release_boundary_paused_pending_full_pytest_authorization",
            "release_boundary_paused": True,
            "full_pytest_authorized": False,
            "full_pytest_run_triggered": False,
            "external_release_ready": False,
        },
        "release_boundary_state": {"external_release_allowed": False},
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_mainline_selection_after_release_pause_selects_core_monitoring() -> None:
    result = build_mainline_selection_after_release_pause(post_release_boundary_authorization=_authorization())

    assert result["version"] == "v30.mainline_selection_after_release_pause.v1"
    assert result["status"] == "ready_for_next_mainline"
    assert result["decision"]["decision_status"] == "core_monitoring_and_calibration_loop_selected"
    assert result["decision"]["selected_task_id"] == "P0"
    assert result["selected_non_release_mainline"]["title"] == "Core Module Monitoring And Calibration Loop"
    assert result["policy_boundary"]["external_release_allowed"] is False
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "P0"


def test_mainline_selection_after_release_pause_blocks_when_full_pytest_authorized() -> None:
    payload = _authorization()
    payload["decision"] = {
        "release_boundary_paused": False,
        "full_pytest_authorized": True,
        "full_pytest_run_triggered": False,
        "external_release_ready": False,
    }
    result = build_mainline_selection_after_release_pause(post_release_boundary_authorization=payload)

    assert result["status"] == "mainline_selection_blocked"
    assert "release_boundary_not_paused" in result["decision"]["blockers"]
    assert "full_pytest_not_paused" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "M0"


def test_mainline_selection_after_release_pause_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_mainline_selection_after_release_pause.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.mainline_selection_after_release_pause.v1: core_monitoring_and_calibration_loop_selected" in result.stdout
    assert "- next: P0 Core Module Monitoring And Calibration Loop" in result.stdout
