from __future__ import annotations

import subprocess
import sys

from v30.validation.external_release_blocked_status import build_external_release_blocked_status


def _full_pytest_decision() -> dict[str, object]:
    return {
        "version": "v30.external_release_full_pytest_decision.v1",
        "status": "completed",
        "decision": {
            "decision_status": "external_release_full_pytest_deferred",
            "external_release_ready": False,
            "external_release_blocked": True,
            "full_pytest_deferred": True,
        },
        "full_pytest_execution_summary": {"status": "deferred"},
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_external_release_blocked_status_records_expected_blockers() -> None:
    result = build_external_release_blocked_status(
        external_release_full_pytest_decision=_full_pytest_decision(),
    )

    assert result["version"] == "v30.external_release_blocked_status.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "external_release_blocked_pending_full_pytest"
    assert result["decision"]["external_release_ready"] is False
    assert result["decision"]["external_release_blocked"] is True
    assert result["policy_boundary"]["external_release_allowed"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert {row["blocker_id"] for row in result["release_blockers"]} == {
        "full_pytest_deferred",
        "manual_release_approval_missing",
        "manual_policy_pointer_promotion_missing",
    }
    assert result["next_mainline_selection"]["task_id"] == "R16"


def test_external_release_blocked_status_blocks_if_release_is_ready() -> None:
    payload = _full_pytest_decision()
    payload["decision"] = {
        "external_release_ready": True,
        "external_release_blocked": False,
        "full_pytest_deferred": False,
    }
    result = build_external_release_blocked_status(external_release_full_pytest_decision=payload)

    assert result["status"] == "blocked"
    assert "external_release_not_blocked" in result["decision"]["blockers"]
    assert "full_pytest_not_deferred" in result["decision"]["blockers"]
    assert "external_release_unexpectedly_ready" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "R15"


def test_external_release_blocked_status_script_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_external_release_blocked_status.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.external_release_blocked_status.v1: external_release_blocked_pending_full_pytest" in result.stdout
    assert "- external_release_blocked: True" in result.stdout
    assert "- pointer_promotion_allowed: False" in result.stdout
