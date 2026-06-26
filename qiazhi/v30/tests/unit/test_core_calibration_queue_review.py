from __future__ import annotations

from v30.validation.core_calibration_queue_review import build_core_calibration_queue_review


def _p4_payload(*, blocked: bool = False, queued: bool = False) -> dict[str, object]:
    queue_items = []
    if queued:
        queue_items = [
            {
                "queue_item_id": "e1::M4",
                "evidence_id": "e1",
                "module_target": "M4",
                "check_id": "targeted_validation_gate",
                "routing_scope": "synthetic_real_case_or_518k_sample_validation_review",
                "severity": "review",
                "status": "queued_for_focused_review",
                "reopen_all_core_modules": False,
                "chart_fact_mutation_allowed": False,
                "pointer_write_allowed": False,
            },
            {
                "queue_item_id": "e1::M5",
                "evidence_id": "e1",
                "module_target": "M5",
                "check_id": "targeted_validation_gate",
                "routing_scope": "synthetic_real_case_or_518k_sample_validation_review",
                "severity": "review",
                "status": "queued_for_focused_review",
                "reopen_all_core_modules": False,
                "chart_fact_mutation_allowed": False,
                "pointer_write_allowed": False,
            },
        ]
    return {
        "version": "v30.focused_core_calibration_evidence_queue.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "focused_core_calibration_evidence_queue_ready" if not queued else "focused_core_calibration_evidence_queued",
            "evidence_queue_ready": not blocked,
            "queued_evidence_count": 1 if queued else 0,
            "queue_item_count": len(queue_items),
            "module_queue_count": 2 if queued else 0,
            "focused_module_fix_required": queued,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "queue_items": queue_items,
    }


def test_core_calibration_queue_review_ready_for_empty_queue() -> None:
    result = build_core_calibration_queue_review(focused_core_calibration_evidence_queue=_p4_payload())

    assert result["version"] == "v30.core_calibration_queue_review.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_calibration_queue_review_ready"
    assert result["decision"]["reviewed_module_count"] == 0
    assert result["decision"]["focused_module_fix_required"] is False
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P6"
    assert result["boundary"] == "p5_reviews_core_calibration_queue_without_full_pytest"


def test_core_calibration_queue_review_reports_focused_candidates() -> None:
    result = build_core_calibration_queue_review(focused_core_calibration_evidence_queue=_p4_payload(queued=True))

    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_calibration_queue_review_has_focused_candidates"
    assert result["decision"]["reviewed_module_count"] == 2
    assert result["decision"]["focused_fix_candidate_count"] == 2
    assert result["decision"]["focused_module_fix_required"] is True
    assert [row["module_target"] for row in result["module_reviews"]] == ["M4", "M5"]
    assert all(row["fix_execution_allowed"] is False for row in result["module_reviews"])
    assert all(row["reopen_all_core_modules"] is False for row in result["module_reviews"])


def test_core_calibration_queue_review_blocks_upstream_queue_failure() -> None:
    result = build_core_calibration_queue_review(focused_core_calibration_evidence_queue=_p4_payload(blocked=True))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_calibration_queue_review_blocked"
    assert "p4_evidence_queue_not_ready" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P5-FR"
