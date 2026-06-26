from __future__ import annotations

import subprocess
import sys

from v30.validation.release_candidate_review import build_release_candidate_review


def test_release_candidate_review_recommends_standard_gate_with_evidence() -> None:
    result = build_release_candidate_review(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 10)],
            "next_mainline_selection": {"task_id": "R10"},
        },
        release_gate_result={
            "run_id": "quick",
            "mode": "quick",
            "status": "passed",
            "promotion_signal": "eligible",
            "checks": [{"check_id": "runtime_smoke", "status": "passed"}],
            "artifact_review": {"version": "v30.release_artifact_review.v1"},
        },
        replay_search={
            "version": "v30.production_replay_search.v1",
            "searchable": True,
            "summary": {
                "row_count": 25,
                "calibration_ready_count": 25,
                "privacy_guard_pass_count": 25,
            },
        },
    )

    assert result["version"] == "v30.release_candidate_review.v1"
    assert result["decision"]["decision_status"] == "ready_for_release_candidate_gate"
    assert result["decision"]["release_candidate_gate_recommended"] is True
    assert result["decision"]["real_production_row_ingestion_required_before_rc"] is False
    assert result["release_candidate_gate"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "R11"
    assert result["next_mainline_selection"]["title"] == "Standard Release-Candidate Gate"


def test_release_candidate_review_blocks_without_gate_evidence() -> None:
    result = build_release_candidate_review(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 10)],
        },
        replay_search={
            "version": "v30.production_replay_search.v1",
            "summary": {"row_count": 25, "calibration_ready_count": 25},
        },
    )

    assert result["decision"]["release_candidate_gate_recommended"] is False
    assert result["decision"]["real_production_row_ingestion_required_before_rc"] is False
    assert "release_gate_not_run_for_review" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["title"] == "Release Candidate Evidence Gap Closure"


def test_release_candidate_review_requires_replay_ingestion_only_for_low_coverage() -> None:
    result = build_release_candidate_review(
        post_seal_status_review={
            "version": "v30.post_seal_status_review.v1",
            "core_module_summary": {"phase_sealed_count": 8},
            "completed_post_seal_tasks": [{"task_id": f"R{idx}"} for idx in range(1, 11)],
        },
        release_gate_result={
            "run_id": "quick",
            "mode": "quick",
            "status": "passed",
            "promotion_signal": "eligible",
            "checks": [{"check_id": "runtime_smoke", "status": "passed"}],
        },
        replay_search={
            "version": "v30.production_replay_search.v1",
            "summary": {"row_count": 8, "calibration_ready_count": 8},
        },
    )

    assert result["decision"]["release_candidate_gate_recommended"] is False
    assert result["decision"]["real_production_row_ingestion_required_before_rc"] is True
    assert "replay_calibration_ready_coverage_low" in result["decision"]["blockers"]


def test_release_candidate_review_script_without_gate_is_read_only() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_release_candidate_review.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.release_candidate_review.v1" in result.stdout
    assert "rc_gate_recommended=False" in result.stdout
    assert "release_gate_not_run_for_review" in result.stdout
