from __future__ import annotations

import subprocess
import sys

from v30.validation.brain_training_synthetic_closeout import build_brain_training_synthetic_closeout


def test_bt10_closeout_accepts_bt1_bt9_evidence() -> None:
    result = build_brain_training_synthetic_closeout(
        central_brain_synthetic={
            "suite_id": "v30.synthetic.central_brain",
            "passed": True,
            "case_count": 5,
            "passed_count": 5,
        },
        training_pipeline_synthetic={
            "suite_id": "v30.synthetic.training_pipeline",
            "passed": True,
            "case_count": 91,
            "passed_count": 91,
        },
        synthetic_coverage_manifest={
            "version": "v30.synthetic_coverage_manifest.v1",
            "decision": {
                "synthetic_coverage_manifest_ready": True,
                "decision_status": "bt6_synthetic_coverage_manifest_ready",
                "synthetic_completion": 99,
            },
            "next_mainline_selection": {"task_id": "BT9"},
        },
        readiness_518k_matrix={
            "version": "v30.518k_readiness_matrix.v1",
            "decision": {
                "readiness_matrix_ready": True,
                "decision_status": "bt9_518k_readiness_matrix_ready",
                "validation_518k_completion": 95,
                "full_518k_required": False,
            },
            "next_mainline_selection": {"task_id": "BT10"},
        },
    )

    assert result["version"] == "v30.brain_training_synthetic_closeout.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt10_support_systems_steady_state_ready"
    assert result["decision"]["support_systems_steady_state"] is True
    assert result["completion_summary"] == {
        "central_brain_completion": 100,
        "training_completion": 100,
        "synthetic_completion": 100,
        "validation_518k_completion": 95,
        "support_systems_current_scope_complete": True,
    }
    assert result["steady_state"]["state_id"] == "BT-S1"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["synthetic_all_run_allowed_by_default"] is False
    assert result["policy_boundary"]["full_518k_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT-S1"


def test_bt10_closeout_blocks_missing_518k_readiness() -> None:
    result = build_brain_training_synthetic_closeout(
        central_brain_synthetic={
            "suite_id": "v30.synthetic.central_brain",
            "passed": True,
            "case_count": 5,
            "passed_count": 5,
        },
        training_pipeline_synthetic={
            "suite_id": "v30.synthetic.training_pipeline",
            "passed": True,
            "case_count": 91,
            "passed_count": 91,
        },
        synthetic_coverage_manifest={
            "version": "v30.synthetic_coverage_manifest.v1",
            "decision": {"synthetic_coverage_manifest_ready": True, "synthetic_completion": 99},
        },
        readiness_518k_matrix={
            "version": "v30.518k_readiness_matrix.v1",
            "decision": {"readiness_matrix_ready": False, "validation_518k_completion": 85},
        },
    )

    assert result["status"] == "blocked"
    assert "518k_readiness_matrix_ready" in result["decision"]["failed_check_ids"]
    assert result["next_mainline_selection"]["task_id"] == "BT10-FR"


def test_bt10_closeout_script_runs_targeted_support_gates() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_brain_training_synthetic_closeout.py",
            "--sample-limit",
            "2",
            "--shard-limit",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "v30.brain_training_synthetic_closeout.v1: passed" in result.stdout
    assert "bt10_support_systems_steady_state_ready" in result.stdout
