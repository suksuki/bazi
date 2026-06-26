from __future__ import annotations

from v30.validation.core_monitoring_s0_status import build_core_monitoring_s0_status


def _p9_payload(*, blocked: bool = False, waiting: bool = True, pointer: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_monitoring_steady_state.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_monitoring_steady_state_ready" if not blocked else "core_monitoring_steady_state_blocked",
            "steady_state_ready": not blocked,
            "steady_state_check_count": 4,
            "passed_steady_state_check_count": 4 if not blocked else 3,
            "waiting_for_new_evidence": waiting,
            "future_monitoring_ready": not blocked,
            "focused_module_fix_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": pointer,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "steady_state_policy": {
            "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "queued_evidence_review": "P5 Core Calibration Queue Review",
        },
    }


def test_core_monitoring_s0_status_ready() -> None:
    result = build_core_monitoring_s0_status(core_monitoring_steady_state=_p9_payload())

    assert result["version"] == "v30.core_monitoring_s0_status.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_monitoring_s0_status_ready"
    assert result["decision"]["passed_status_check_count"] == 4
    assert result["decision"]["waiting_for_new_evidence"] is True
    assert result["decision"]["new_core_monitoring_task_allowed_by_default"] is False
    assert result["s0_policy"]["default_action"] == "do_not_start_new_core_monitoring_task"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["next_mainline_selection"]["task_id"] == "S0"
    assert result["boundary"] == "s0_records_steady_state_without_full_pytest"


def test_core_monitoring_s0_status_blocks_not_waiting() -> None:
    result = build_core_monitoring_s0_status(core_monitoring_steady_state=_p9_payload(waiting=False))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_monitoring_s0_status_blocked"
    assert "p9_not_waiting_for_new_evidence" in result["decision"]["blockers"]
    assert "s0_status_checks_failed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "S0-FR"


def test_core_monitoring_s0_status_blocks_pointer_pressure() -> None:
    result = build_core_monitoring_s0_status(core_monitoring_steady_state=_p9_payload(pointer=True))

    assert result["status"] == "blocked"
    assert "p9_pointer_boundary_violation" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
