from __future__ import annotations

from v30.validation.focused_core_calibration_evidence_queue import build_focused_core_calibration_evidence_queue


def _p3_payload(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_calibration_drift_watch.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_calibration_drift_watch_ready" if not blocked else "core_calibration_drift_watch_blocked",
            "drift_watch_ready": not blocked,
            "drift_detected": blocked,
            "drift_route_count": 0 if not blocked else 1,
            "focused_module_fix_required": blocked,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def test_focused_core_calibration_evidence_queue_ready_without_evidence() -> None:
    result = build_focused_core_calibration_evidence_queue(
        core_calibration_drift_watch=_p3_payload(),
        calibration_evidence=[],
    )

    assert result["version"] == "v30.focused_core_calibration_evidence_queue.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "focused_core_calibration_evidence_queue_ready"
    assert result["decision"]["queued_evidence_count"] == 0
    assert result["decision"]["queue_item_count"] == 0
    assert result["decision"]["focused_module_fix_required"] is False
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P5"
    assert result["boundary"] == "p4_builds_focused_core_calibration_evidence_queue_without_full_pytest"


def test_focused_core_calibration_evidence_queue_batches_by_module_target() -> None:
    result = build_focused_core_calibration_evidence_queue(
        core_calibration_drift_watch=_p3_payload(),
        calibration_evidence=[
            {
                "evidence_id": "validation_drift",
                "check_id": "targeted_validation_gate",
                "status": "queued",
                "severity": "review",
            }
        ],
    )

    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "focused_core_calibration_evidence_queued"
    assert result["decision"]["queued_evidence_count"] == 1
    assert result["decision"]["queue_item_count"] == 3
    assert result["decision"]["module_queue_count"] == 3
    assert [row["module_target"] for row in result["module_queues"]] == ["M4", "M5", "M7"]
    assert all(row["reopen_all_core_modules"] is False for row in result["queue_items"])
    assert result["decision"]["focused_module_fix_required"] is True


def test_focused_core_calibration_evidence_queue_blocks_mutation_pressure() -> None:
    result = build_focused_core_calibration_evidence_queue(
        core_calibration_drift_watch=_p3_payload(),
        calibration_evidence=[
            {
                "evidence_id": "bad_fact_request",
                "check_id": "m1_m8_frozen_scope",
                "chart_fact_mutation_requested": True,
            }
        ],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "focused_core_calibration_evidence_queue_blocked"
    assert "calibration_evidence_requests_chart_fact_mutation" in result["decision"]["blockers"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P4-FR"
