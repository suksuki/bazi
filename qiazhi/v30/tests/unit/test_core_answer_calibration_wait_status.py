from __future__ import annotations

from pathlib import Path

from v30.validation.core_answer_calibration_steady_state_queue import (
    CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
)
from v30.validation.core_answer_calibration_wait_status import (
    CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION,
    build_core_answer_calibration_wait_status,
)


SOURCES = [
    "answer_quality_delta_review",
    "synthetic_typical_bazi_answer",
    "runtime_answer_integration",
    "business_answer_refresh",
    "llm_output_acceptance",
    "user_feedback_answer_quality",
]


def test_core_cal_wait_ready(tmp_path: Path) -> None:
    result = build_core_answer_calibration_wait_status(
        core_answer_calibration_queue=_queue(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == CORE_ANSWER_CALIBRATION_WAIT_STATUS_VERSION
    assert result["status"] == "completed"
    assert decision["decision_status"] == "core_cal_wait_answer_quality_evidence_wait_ready"
    assert decision["core_answer_calibration_wait_ready"] is True
    assert decision["waiting_for_new_answer_quality_evidence"] is True
    assert decision["focused_answer_fix_candidate_count"] == 0
    assert decision["full_pytest_required"] is False
    assert decision["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-WAIT"
    assert Path(str(result["artifact_uri"])).exists()


def test_core_cal_wait_blocks_when_queue_has_candidates() -> None:
    result = build_core_answer_calibration_wait_status(
        core_answer_calibration_queue=_queue(candidates=1, waiting=False),
    )

    assert result["status"] == "blocked"
    assert "waiting_without_current_candidates" in result["decision"]["failed_check_ids"]
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-WAIT-FR"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False


def test_core_cal_wait_blocks_heavy_or_mutation_defaults() -> None:
    result = build_core_answer_calibration_wait_status(
        core_answer_calibration_queue=_queue(heavy=True),
    )

    assert result["status"] == "blocked"
    assert "no_heavy_release_or_mutation_defaults" in result["decision"]["failed_check_ids"]
    assert result["decision"]["full_pytest_required"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False


def _queue(*, candidates: int = 0, waiting: bool = True, heavy: bool = False) -> dict[str, object]:
    ready = candidates == 0 and waiting and not heavy
    return {
        "version": CORE_ANSWER_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "core_cal_s4_answer_calibration_steady_state_queue_ready"
            if ready
            else "core_cal_s4_answer_calibration_steady_state_queue_blocked",
            "core_answer_calibration_steady_state_queue_ready": ready,
            "waiting_for_new_answer_quality_evidence": waiting,
            "focused_answer_fix_candidate_count": candidates,
            "focused_answer_fix_required": candidates > 0,
            "core_module_reopen_by_default": False,
            "full_pytest_required": heavy,
            "synthetic_all_required": heavy,
            "full_518k_required": heavy,
            "live_llm_required": heavy,
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": heavy,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
        },
        "queue_policy": {
            "accepted_evidence_source_ids": SOURCES,
            "allowed_target_modules": ["M3", "M6", "LLM", "interaction"],
        },
    }
