from __future__ import annotations

import subprocess
import sys

from v30.validation.release_candidate_gate_review import build_release_candidate_gate_review


def test_release_candidate_gate_review_marks_standard_gate_ready() -> None:
    result = build_release_candidate_gate_review(
        release_gate_result={
            "run_id": "standard",
            "mode": "standard",
            "status": "passed",
            "promotion_signal": "eligible",
            "checks": [
                {"check_id": "runtime_smoke", "status": "passed"},
                {"check_id": "production_api_smoke", "status": "passed"},
                {"check_id": "llm_live_smoke", "status": "passed"},
                {"check_id": "post_seal_contracts", "status": "passed"},
                {"check_id": "synthetic_all", "status": "passed"},
                {"check_id": "518k_sample", "status": "passed"},
                {"check_id": "518k_shard", "status": "passed"},
            ],
            "artifact_review": {
                "version": "v30.release_artifact_review.v1",
                "status": "ready",
                "check_count": 7,
                "missing_sections": [],
                "promotion_review": {"failed_checks": []},
                "corpus_518k_summary": {
                    "sample": {"case_count": 8, "artifact_record_id": "sample-artifact"},
                    "shard": {"case_count": 16, "artifact_record_id": "shard-artifact"},
                    "artifact_record_ids": ["sample-artifact", "shard-artifact"],
                },
            },
        }
    )

    assert result["version"] == "v30.release_candidate_gate_review.v1"
    assert result["decision"]["decision_status"] == "standard_gate_passed"
    assert result["decision"]["release_boundary_ready"] is True
    assert result["decision"]["policy_promotion_allowed"] is False
    assert result["corpus_518k_summary"]["sample_case_count"] == 8
    assert result["corpus_518k_summary"]["shard_case_count"] == 16
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "R12"
    assert result["next_mainline_selection"]["title"] == "Release Boundary Finalization Review"


def test_release_candidate_gate_review_blocks_non_standard_gate() -> None:
    result = build_release_candidate_gate_review(
        release_gate_result={
            "run_id": "quick",
            "mode": "quick",
            "status": "passed",
            "promotion_signal": "eligible",
            "checks": [{"check_id": "runtime_smoke", "status": "passed"}],
            "artifact_review": {"status": "ready"},
        }
    )

    assert result["decision"]["release_boundary_ready"] is False
    assert "release_gate_mode_not_standard" in result["decision"]["blockers"]
    assert any(
        blocker.startswith("required_standard_checks_missing:")
        for blocker in result["decision"]["blockers"]
    )
    assert result["next_mainline_selection"]["title"] == "Standard Gate Evidence Gap Closure"


def test_release_candidate_gate_review_script_runs_small_standard_gate() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_release_candidate_gate_review.py",
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
    assert "v30.release_candidate_gate_review.v1: standard_gate_passed" in result.stdout
    assert "release_boundary_ready=True" in result.stdout
    assert "next=R12 Release Boundary Finalization Review" in result.stdout
