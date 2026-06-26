from __future__ import annotations

from v30.validation.core_evidence_closeout import (
    CORE_EVIDENCE_CLOSEOUT_VERSION,
    build_core_evidence_closeout,
    run_core_evidence_closeout,
)


def test_core_evidence_closeout_accepts_current_chain() -> None:
    result = run_core_evidence_closeout(reading_id="pytest-core-evidence-6")

    assert result["version"] == CORE_EVIDENCE_CLOSEOUT_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["core_evidence_closeout_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["closeout_summary"]["missing_task_ids"] == []
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S1"


def test_core_evidence_closeout_blocks_missing_chain_rows() -> None:
    result = build_core_evidence_closeout(
        reading_id="pytest-core-evidence-6-missing",
        evidence={
            "CORE-EVIDENCE-2": {
                "version": "v30.answer_quality_delta_review.v1",
                "status": "completed",
                "decision": {
                    "answer_quality_delta_ready": True,
                    "decision_status": "ready",
                    "passed_check_count": 1,
                    "check_count": 1,
                    "failed_check_ids": [],
                    "full_pytest_required": False,
                },
            }
        },
    )

    assert result["status"] == "blocked"
    assert result["decision"]["core_evidence_closeout_ready"] is False
    assert "core_evidence_task_coverage_incomplete" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "CORE-EVIDENCE-6A"
