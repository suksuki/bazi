from __future__ import annotations

import subprocess
import sys

from v30.validation.release_boundary_finalization import build_release_boundary_finalization


def test_release_boundary_finalization_marks_internal_candidate_ready_without_full_pytest() -> None:
    result = build_release_boundary_finalization(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 13)],
        },
        release_candidate_gate_review={
            "version": "v30.release_candidate_gate_review.v1",
            "decision": {
                "decision_status": "standard_gate_passed",
                "release_boundary_ready": True,
                "policy_promotion_allowed": False,
            },
        },
    )

    assert result["version"] == "v30.release_boundary_finalization.v1"
    assert result["decision"]["decision_status"] == "internal_release_candidate_finalized"
    assert result["decision"]["internal_release_candidate_finalized"] is True
    assert result["decision"]["external_release_ready"] is False
    assert result["decision"]["full_pytest_required_before_external_release"] is True
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "R13"
    assert result["next_mainline_selection"]["title"] == "External Release Dry Run And Full Pytest Decision"


def test_release_boundary_finalization_external_ready_requires_full_pytest_pass() -> None:
    result = build_release_boundary_finalization(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 13)],
        },
        release_candidate_gate_review={
            "version": "v30.release_candidate_gate_review.v1",
            "decision": {
                "decision_status": "standard_gate_passed",
                "release_boundary_ready": True,
                "policy_promotion_allowed": False,
            },
        },
        full_pytest_result={"status": "passed"},
    )

    assert result["decision"]["internal_release_candidate_finalized"] is True
    assert result["decision"]["external_release_ready"] is True
    assert result["decision"]["full_pytest_run_recorded"] is True


def test_release_boundary_finalization_blocks_failed_full_pytest() -> None:
    result = build_release_boundary_finalization(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 13)],
        },
        release_candidate_gate_review={
            "version": "v30.release_candidate_gate_review.v1",
            "decision": {
                "decision_status": "standard_gate_passed",
                "release_boundary_ready": True,
                "policy_promotion_allowed": False,
            },
        },
        full_pytest_result={"status": "failed"},
    )

    assert result["decision"]["internal_release_candidate_finalized"] is False
    assert "full_pytest_not_passed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["title"] == "Release Boundary Evidence Gap Closure"


def test_release_boundary_finalization_script_runs_standard_gate() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_release_boundary_finalization.py",
            "--sample-limit",
            "2",
            "--shard-id",
            "7",
            "--shard-limit",
            "3",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.release_boundary_finalization.v1: internal_release_candidate_finalized" in result.stdout
    assert "internal_release_candidate_finalized=True" in result.stdout
    assert "external_release_ready=False" in result.stdout
    assert "next=R13 External Release Dry Run And Full Pytest Decision" in result.stdout
