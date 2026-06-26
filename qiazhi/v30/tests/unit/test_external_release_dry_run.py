from __future__ import annotations

import subprocess
import sys

from v30.validation.external_release_dry_run import build_external_release_dry_run


def _mainline_selection() -> dict[str, object]:
    return {
        "version": "v30.mainline_selection.v1",
        "status": "ready_for_next_mainline",
        "decision": {
            "selected_task_id": "R13",
            "selected_track": "external_release_boundary",
            "full_pytest_run_now": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _release_boundary() -> dict[str, object]:
    return {
        "version": "v30.release_boundary_finalization.v1",
        "decision": {
            "internal_release_candidate_finalized": True,
            "external_release_ready": False,
            "full_pytest_run_recorded": False,
            "policy_pointer_promotion_allowed": False,
            "decision_status": "internal_release_candidate_finalized",
        },
    }


def test_external_release_dry_run_defers_full_pytest_by_default() -> None:
    result = build_external_release_dry_run(
        mainline_selection=_mainline_selection(),
        release_boundary_finalization=_release_boundary(),
        full_pytest_decision="defer",
    )

    assert result["version"] == "v30.external_release_dry_run.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "external_release_dry_run_deferred_full_pytest"
    assert result["decision"]["external_release_ready"] is False
    assert result["decision"]["full_pytest_deferred"] is True
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "R14"


def test_external_release_dry_run_can_record_passed_full_pytest_without_promoting_policy() -> None:
    result = build_external_release_dry_run(
        mainline_selection=_mainline_selection(),
        release_boundary_finalization=_release_boundary(),
        full_pytest_decision="record_passed",
    )

    assert result["decision"]["decision_status"] == "external_release_ready_after_full_pytest"
    assert result["decision"]["external_release_ready"] is True
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["title"] == "Manual External Release Approval And Pointer-Promotion Decision"


def test_external_release_dry_run_blocks_failed_full_pytest() -> None:
    result = build_external_release_dry_run(
        mainline_selection=_mainline_selection(),
        release_boundary_finalization=_release_boundary(),
        full_pytest_decision="record_failed",
    )

    assert result["status"] == "blocked"
    assert "full_pytest_failed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "R13"


def test_external_release_dry_run_script_defers_full_pytest() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_external_release_dry_run.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.external_release_dry_run.v1: external_release_dry_run_deferred_full_pytest" in result.stdout
    assert "- external_release_ready: False" in result.stdout
    assert "- full_pytest_deferred: True" in result.stdout
