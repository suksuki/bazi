from __future__ import annotations

import subprocess
import sys

from v30.validation.external_release_full_pytest_decision import build_external_release_full_pytest_decision


def _dry_run() -> dict[str, object]:
    return {
        "version": "v30.external_release_dry_run.v1",
        "status": "completed",
        "decision": {
            "decision_status": "external_release_dry_run_deferred_full_pytest",
            "dry_run_review_completed": True,
            "external_release_ready": False,
            "full_pytest_deferred": True,
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_external_release_full_pytest_decision_defers_by_default() -> None:
    result = build_external_release_full_pytest_decision(
        external_release_dry_run=_dry_run(),
        full_pytest_decision="defer",
    )

    assert result["version"] == "v30.external_release_full_pytest_decision.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "external_release_full_pytest_deferred"
    assert result["decision"]["external_release_ready"] is False
    assert result["decision"]["external_release_blocked"] is True
    assert result["decision"]["full_pytest_deferred"] is True
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "R15"


def test_external_release_full_pytest_decision_records_pass_without_pointer_promotion() -> None:
    result = build_external_release_full_pytest_decision(
        external_release_dry_run=_dry_run(),
        full_pytest_decision="record_passed",
    )

    assert result["decision"]["decision_status"] == "external_release_full_pytest_passed"
    assert result["decision"]["external_release_ready"] is True
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["title"] == "Manual External Release Approval And Pointer-Promotion Decision"


def test_external_release_full_pytest_decision_blocks_failed_full_pytest() -> None:
    result = build_external_release_full_pytest_decision(
        external_release_dry_run=_dry_run(),
        full_pytest_decision="record_failed",
    )

    assert result["status"] == "blocked"
    assert "full_pytest_failed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "R14"


def test_external_release_full_pytest_decision_script_defers() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_external_release_full_pytest_decision.py", "--sample-limit", "8"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.external_release_full_pytest_decision.v1: external_release_full_pytest_deferred" in result.stdout
    assert "- external_release_ready: False" in result.stdout
    assert "- full_pytest_deferred: True" in result.stdout
