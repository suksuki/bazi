from __future__ import annotations

from pathlib import Path

from v30.validation.core_calibration_steady_state_queue import (
    CORE_CALIBRATION_STEADY_STATE_QUEUE_VERSION,
    build_core_calibration_steady_state_queue,
)
from v30.validation.synthetic_archetype_calibration_closeout import (
    SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION,
)


SOURCE_IDS = [
    "real_case_calibration",
    "business_acceptance",
    "518k_distribution",
    "training_signal_distribution",
    "llm_expression_acceptance",
    "question_chain_acceptance",
]


def test_core_calibration_s0_ready(tmp_path: Path) -> None:
    result = build_core_calibration_steady_state_queue(
        synthetic_archetype_closeout=_syn_cal4(),
        await_new_evidence_status=_await_status(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == CORE_CALIBRATION_STEADY_STATE_QUEUE_VERSION
    assert result["status"] == "completed"
    assert decision["decision_status"] == "core_calibration_s0_steady_state_queue_ready"
    assert decision["core_calibration_steady_state_queue_ready"] is True
    assert decision["waiting_for_new_calibration_evidence"] is True
    assert decision["focused_fix_candidate_count"] == 0
    assert decision["core_module_reopen_by_default"] is False
    assert decision["full_pytest_required"] is False
    assert decision["full_518k_required"] is False
    assert decision["auto_apply_training_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-WAIT"
    assert Path(str(result["artifact_uri"])).exists()


def test_core_calibration_s0_blocks_without_syn_cal4() -> None:
    result = build_core_calibration_steady_state_queue(
        synthetic_archetype_closeout=_syn_cal4(closed=False),
        await_new_evidence_status=_await_status(),
    )

    assert result["status"] == "blocked"
    assert "syn_cal4_archetype_closeout_ready" in result["decision"]["failed_check_ids"]
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S0-FR"
    assert result["policy_boundary"]["full_pytest_required"] is False


def test_core_calibration_s0_blocks_candidates_or_heavy_defaults() -> None:
    candidate_result = build_core_calibration_steady_state_queue(
        synthetic_archetype_closeout=_syn_cal4(),
        await_new_evidence_status=_await_status(candidates=1),
    )
    heavy_result = build_core_calibration_steady_state_queue(
        synthetic_archetype_closeout=_syn_cal4(),
        await_new_evidence_status=_await_status(heavy=True),
    )

    assert "await_new_evidence_state_ready" in candidate_result["decision"]["failed_check_ids"]
    assert "no_default_reopen_or_heavy_gate" in heavy_result["decision"]["failed_check_ids"]
    assert heavy_result["decision"]["full_pytest_required"] is False


def _syn_cal4(*, closed: bool = True) -> dict[str, object]:
    return {
        "version": SYNTHETIC_ARCHETYPE_CALIBRATION_CLOSEOUT_VERSION,
        "status": "completed" if closed else "blocked",
        "decision": {
            "decision_status": (
                "syn_cal4_synthetic_archetype_calibration_closed"
                if closed
                else "syn_cal4_synthetic_archetype_calibration_blocked"
            ),
            "synthetic_archetype_calibration_closed": closed,
            "closeout_check_count": 6,
            "passed_closeout_check_count": 6 if closed else 5,
            "training_signal_count": 4,
            "queued_item_count": 0,
            "external_release_allowed": False,
            "chart_fact_mutation_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "routine_cadence": {
            "routine_targeted_commands": [
                "python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim",
                "python3 scripts/run_synthetic_archetype_training_signal_review.py",
                "python3 scripts/run_synthetic_archetype_calibration_closeout.py",
            ],
        },
    }


def _await_status(*, candidates: int = 0, heavy: bool = False) -> dict[str, object]:
    ready = candidates == 0 and not heavy
    return {
        "version": "v30.await_new_calibration_evidence_status.v1",
        "status": "completed" if ready else "blocked",
        "decision": {
            "decision_status": "await_new_calibration_evidence_ready" if ready else "await_new_calibration_evidence_blocked",
            "await_new_evidence_ready": ready,
            "waiting_for_new_calibration_evidence": ready,
            "focused_fix_candidate_count": candidates,
            "focused_module_fix_required": candidates > 0,
            "core_module_reopen_by_default": False,
            "full_pytest_required": heavy,
            "synthetic_all_required": heavy,
            "full_518k_required": heavy,
            "live_llm_required": heavy,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "wait_policy": {
            "accepted_evidence_sources": SOURCE_IDS,
        },
    }
