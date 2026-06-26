from __future__ import annotations

from v30.validation.core_monitoring_cadence_baseline import build_core_monitoring_cadence_baseline


def _p6_payload(*, blocked: bool = False, heavy: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_calibration_watch_closeout.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_calibration_watch_closeout_ready" if not blocked else "core_calibration_watch_closeout_blocked",
            "watch_closeout_ready": not blocked,
            "closeout_check_count": 4,
            "passed_closeout_check_count": 4 if not blocked else 3,
            "current_cycle_closed": not blocked,
            "future_monitoring_ready": not blocked,
            "focused_module_fix_required": False,
            "full_pytest_required": heavy,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "watch_cycle_summary": {
            "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "future_review_entrypoint": "P5 Core Calibration Queue Review",
        },
    }


def test_core_monitoring_cadence_baseline_ready() -> None:
    result = build_core_monitoring_cadence_baseline(core_calibration_watch_closeout=_p6_payload())

    assert result["version"] == "v30.core_monitoring_cadence_baseline.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_monitoring_cadence_baseline_ready"
    assert result["decision"]["current_cycle_closed"] is True
    assert result["decision"]["future_monitoring_ready"] is True
    assert result["decision"]["default_heavy_validation_allowed"] is False
    assert result["cadence_rules"]["default_cadence"] == "on_new_calibration_evidence_only"
    assert result["trigger_matrix"][1]["entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P8"
    assert result["boundary"] == "p7_establishes_core_monitoring_cadence_without_full_pytest"


def test_core_monitoring_cadence_baseline_blocks_unclosed_cycle() -> None:
    result = build_core_monitoring_cadence_baseline(core_calibration_watch_closeout=_p6_payload(blocked=True))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_monitoring_cadence_baseline_blocked"
    assert "p6_watch_closeout_not_ready" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "P7-FR"


def test_core_monitoring_cadence_baseline_blocks_heavy_validation_pressure() -> None:
    result = build_core_monitoring_cadence_baseline(core_calibration_watch_closeout=_p6_payload(heavy=True))

    assert result["status"] == "blocked"
    assert "p6_requested_heavy_validation" in result["decision"]["blockers"]
    assert result["decision"]["full_pytest_required"] is False
