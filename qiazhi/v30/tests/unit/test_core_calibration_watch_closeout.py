from __future__ import annotations

from v30.validation.core_calibration_watch_closeout import build_core_calibration_watch_closeout


def _p5_payload(*, blocked: bool = False, candidates: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_calibration_queue_review.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_calibration_queue_review_ready" if not candidates else "core_calibration_queue_review_has_focused_candidates",
            "queue_review_ready": not blocked,
            "reviewed_module_count": 2 if candidates else 0,
            "focused_fix_candidate_count": 2 if candidates else 0,
            "focused_module_fix_required": candidates,
            "continue_lightweight_watch": not candidates,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_core_calibration_watch_closeout_ready() -> None:
    result = build_core_calibration_watch_closeout(core_calibration_queue_review=_p5_payload())

    assert result["version"] == "v30.core_calibration_watch_closeout.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_calibration_watch_closeout_ready"
    assert result["decision"]["passed_closeout_check_count"] == 4
    assert result["decision"]["current_cycle_closed"] is True
    assert result["decision"]["future_monitoring_ready"] is True
    assert result["decision"]["focused_module_fix_required"] is False
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P7"
    assert result["boundary"] == "p6_closes_core_calibration_watch_without_full_pytest"


def test_core_calibration_watch_closeout_blocks_focused_candidates() -> None:
    result = build_core_calibration_watch_closeout(core_calibration_queue_review=_p5_payload(candidates=True))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_calibration_watch_closeout_blocked"
    assert "p5_focused_fix_candidates_present" in result["decision"]["blockers"]
    assert "closeout_checks_failed" in result["decision"]["blockers"]
    assert result["decision"]["failed_closeout_check_ids"] == ["no_focused_fix_candidate"]
    assert result["next_mainline_selection"]["task_id"] == "P6-FR"


def test_core_calibration_watch_closeout_blocks_upstream_failure() -> None:
    result = build_core_calibration_watch_closeout(core_calibration_queue_review=_p5_payload(blocked=True))

    assert result["status"] == "blocked"
    assert "p5_queue_review_not_ready" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
