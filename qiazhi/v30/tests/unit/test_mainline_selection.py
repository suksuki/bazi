from __future__ import annotations

import subprocess
import sys

from v30.validation.mainline_selection import build_mainline_selection


def _ready_closeout() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_closeout.v1",
        "decision": {
            "closeout_ready": True,
            "targeted_calibration_track_closed": True,
            "decision_status": "targeted_calibration_closed_with_no_promotion",
        },
        "monitoring_baseline": {"check_count": 4},
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "pointer_decision_summary": {
            "pointer_write_performed": False,
            "changed_pointer_count": 0,
        },
    }


def _ready_release_boundary() -> dict[str, object]:
    return {
        "version": "v30.release_boundary_finalization.v1",
        "decision": {
            "internal_release_candidate_finalized": True,
            "external_release_ready": False,
            "full_pytest_run_recorded": False,
            "full_pytest_required_before_external_release": True,
            "full_518k_required_before_external_release": False,
            "policy_pointer_promotion_allowed": False,
            "decision_status": "internal_release_candidate_finalized",
        },
    }


def test_mainline_selection_selects_r13_after_f6_closeout() -> None:
    result = build_mainline_selection(
        targeted_calibration_closeout=_ready_closeout(),
        release_boundary_finalization=_ready_release_boundary(),
    )

    assert result["version"] == "v30.mainline_selection.v1"
    assert result["status"] == "ready_for_next_mainline"
    assert result["decision"]["decision_status"] == "r13_external_release_dry_run_selected"
    assert result["decision"]["selected_task_id"] == "R13"
    assert result["decision"]["full_pytest_run_now"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["core_completion_state"]["m1_m8_reopen_allowed"] is False
    assert result["next_mainline_selection"]["selected_track"] == "external_release_boundary"
    assert "no full pytest by default" in result["next_mainline_selection"]["explicit_non_goals"]


def test_mainline_selection_blocks_when_f6_not_closed() -> None:
    closeout = _ready_closeout()
    closeout["decision"] = {"closeout_ready": False}

    result = build_mainline_selection(
        targeted_calibration_closeout=closeout,
        release_boundary_finalization=_ready_release_boundary(),
    )

    assert result["status"] == "mainline_selection_blocked"
    assert result["next_mainline_selection"]["task_id"] == "M0"
    assert "f6_closeout_not_ready" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False


def test_mainline_selection_script_runs_small_closeout_gate() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_mainline_selection.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.mainline_selection.v1: r13_external_release_dry_run_selected" in result.stdout
    assert "- next: R13 External Release Dry Run And Full Pytest Decision" in result.stdout
    assert "- full_pytest_run_now: False" in result.stdout
