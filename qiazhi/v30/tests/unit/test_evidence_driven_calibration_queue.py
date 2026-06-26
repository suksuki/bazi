from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_evidence_driven_calibration_queue,
    run_evidence_driven_calibration_queue,
)


def _core(*, blocked: bool = False, heavy: bool = False) -> dict[str, object]:
    ready = not blocked
    return {
        "version": "v30.core_chain_steady_state_summary.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "core_chain_steady_state_ready" if ready else "core_chain_steady_state_blocked",
            "core_chain_steady_state_ready": ready,
            "module_count": 13,
            "passed_check_count": 5 if ready else 4,
            "check_count": 5,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
            "synthetic_all_required": heavy,
            "full_pytest_required": heavy,
            "full_518k_required": heavy,
            "live_llm_required": heavy,
        },
    }


def _queue(*, blocked: bool = False, candidates: bool = False) -> dict[str, object]:
    ready = not blocked
    module_reviews = []
    if candidates:
        module_reviews = [
            {
                "module_target": "M5",
                "queued_item_count": 1,
                "evidence_ids": ["e1"],
                "review_status": "focused_fix_candidate",
                "fix_execution_allowed": False,
                "reopen_all_core_modules": False,
                "chart_fact_mutation_allowed": False,
                "pointer_write_allowed": False,
            }
        ]
    return {
        "version": "v30.core_calibration_queue_review.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": (
                "core_calibration_queue_review_has_focused_candidates"
                if candidates
                else "core_calibration_queue_review_ready"
            ),
            "queue_review_ready": ready,
            "reviewed_module_count": len(module_reviews),
            "focused_fix_candidate_count": len(module_reviews),
            "focused_module_fix_required": candidates,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "module_reviews": module_reviews,
    }


def test_evidence_driven_calibration_queue_ready(tmp_path: Path) -> None:
    result = build_evidence_driven_calibration_queue(
        core_chain_steady_state=_core(),
        core_calibration_queue_review=_queue(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.evidence_driven_calibration_queue.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "evidence_driven_calibration_queue_ready"
    assert decision["focused_fix_candidate_count"] == 0
    assert result["next_mainline_selection"]["next_task"] == "Await New Calibration Evidence"
    assert Path(str(result["artifact_uri"])).exists()


def test_evidence_driven_calibration_queue_reports_focused_candidates() -> None:
    result = build_evidence_driven_calibration_queue(
        core_chain_steady_state=_core(),
        core_calibration_queue_review=_queue(candidates=True),
    )

    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "evidence_driven_calibration_queue_has_candidates"
    assert result["decision"]["focused_module_fix_required"] is True
    assert result["next_mainline_selection"]["next_task"] == "Focused Calibration Fix Plan"


def test_evidence_driven_calibration_queue_blocks_core_or_queue_gap() -> None:
    core_result = build_evidence_driven_calibration_queue(
        core_chain_steady_state=_core(blocked=True),
        core_calibration_queue_review=_queue(),
    )
    queue_result = build_evidence_driven_calibration_queue(
        core_chain_steady_state=_core(),
        core_calibration_queue_review=_queue(blocked=True),
    )

    assert "core_chain_steady_before_evidence_queue" in core_result["decision"]["failed_check_ids"]
    assert "queue_review_ready" in queue_result["decision"]["failed_check_ids"]


def test_evidence_driven_calibration_queue_blocks_heavy_default_gate() -> None:
    result = build_evidence_driven_calibration_queue(
        core_chain_steady_state=_core(heavy=True),
        core_calibration_queue_review=_queue(),
    )

    assert result["status"] == "blocked"
    assert "no_default_heavy_or_live_gate" in result["decision"]["failed_check_ids"]
    assert result["policy_boundary"]["full_pytest_required"] is False


def test_evidence_driven_calibration_queue_runner_passes_targeted_gates(tmp_path: Path) -> None:
    result = run_evidence_driven_calibration_queue(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "evidence_driven_calibration_queue_ready"
    assert result["decision"]["focused_fix_candidate_count"] == 0
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
