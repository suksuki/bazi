from __future__ import annotations

import subprocess
import sys

from v30.validation import build_post_seal_status_review


def test_post_seal_status_review_selects_next_mainline_from_evidence() -> None:
    review = build_post_seal_status_review(
        release_artifact_review={
            "version": "v30.release_artifact_review.v1",
            "status": "ready",
            "check_count": 6,
            "admin_review_sections": ["synthetic_suite_summary", "518k_artifacts"],
            "artifact_index": [{"family": "518k_sample"}],
            "promotion_review": {"policy_promotion_allowed": False},
        }
    )

    assert review["version"] == "v30.post_seal_status_review.v1"
    assert review["status"] == "ready_for_next_mainline"
    assert review["core_module_summary"]["module_count"] == 8
    assert review["core_module_summary"]["phase_sealed_count"] == 8
    assert len(review["completed_post_seal_tasks"]) == 12
    assert review["release_evidence_summary"]["release_artifact_review_version"] == "v30.release_artifact_review.v1"
    assert review["release_evidence_summary"]["policy_promotion_allowed"] is False
    assert review["next_mainline_selection"]["task_id"] == "R13"
    assert review["next_mainline_selection"]["title"] == "External Release Dry Run And Full Pytest Decision"
    assert review["next_mainline_selection"]["selected_track"] == "external_release_boundary"
    assert "no M1-M8 speculative reopening" in review["next_mainline_selection"]["explicit_non_goals"]
    assert review["reopen_rules"]["core_modules_reopen_only_on_validation_failure"] is True
    assert review["reopen_rules"]["no_private_content_into_chart_facts"] is True


def test_post_seal_status_review_script_outputs_next_task() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_post_seal_status_review.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.post_seal_status_review.v1: ready_for_next_mainline" in result.stdout
    assert "core_phase_sealed=8/8" in result.stdout
    assert "next=R13 External Release Dry Run And Full Pytest Decision" in result.stdout
