from __future__ import annotations

import subprocess
import sys

from v30.validation.post_release_boundary_authorization import build_post_release_boundary_authorization


def _blocked_status() -> dict[str, object]:
    return {
        "version": "v30.external_release_blocked_status.v1",
        "status": "completed",
        "decision": {
            "decision_status": "external_release_blocked_pending_full_pytest",
            "external_release_ready": False,
            "external_release_blocked": True,
            "full_pytest_deferred": True,
        },
        "release_blockers": [{"blocker_id": "full_pytest_deferred"}],
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_post_release_boundary_authorization_pauses_by_default() -> None:
    result = build_post_release_boundary_authorization(
        external_release_blocked_status=_blocked_status(),
        authorization_decision="pause",
    )

    assert result["version"] == "v30.post_release_boundary_authorization.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "release_boundary_paused_pending_full_pytest_authorization"
    assert result["decision"]["release_boundary_paused"] is True
    assert result["decision"]["full_pytest_authorized"] is False
    assert result["decision"]["full_pytest_run_triggered"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "M0"


def test_post_release_boundary_authorization_can_authorize_without_running_full_pytest() -> None:
    result = build_post_release_boundary_authorization(
        external_release_blocked_status=_blocked_status(),
        authorization_decision="authorize_full_pytest",
    )

    assert result["decision"]["decision_status"] == "full_pytest_authorized_pending_execution"
    assert result["decision"]["full_pytest_authorized"] is True
    assert result["decision"]["full_pytest_run_triggered"] is False
    assert result["next_mainline_selection"]["task_id"] == "R17"


def test_post_release_boundary_authorization_blocks_if_release_not_blocked() -> None:
    payload = _blocked_status()
    payload["decision"] = {"external_release_ready": True, "external_release_blocked": False}

    result = build_post_release_boundary_authorization(
        external_release_blocked_status=payload,
        authorization_decision="pause",
    )

    assert result["status"] == "blocked"
    assert "external_release_not_blocked" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "R16"


def test_post_release_boundary_authorization_script_pauses() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_post_release_boundary_authorization.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.post_release_boundary_authorization.v1: release_boundary_paused_pending_full_pytest_authorization" in result.stdout
    assert "- release_boundary_paused: True" in result.stdout
    assert "- full_pytest_run_triggered: False" in result.stdout
