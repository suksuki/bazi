from __future__ import annotations

from v30.validation.core_monitoring_steady_state import build_core_monitoring_steady_state


def _p8_payload(*, blocked: bool = False, missing_docs: bool = False, pointer: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_monitoring_cadence_documentation_sync.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_monitoring_cadence_documentation_sync_ready" if not blocked else "core_monitoring_cadence_documentation_sync_blocked",
            "documentation_sync_ready": not blocked,
            "synced_document_count": 9 if missing_docs else 10,
            "required_document_count": 10,
            "current_cycle_closed": not blocked,
            "future_monitoring_ready": not blocked,
            "default_heavy_validation_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": pointer,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "documentation_sync_summary": {
            "missing_documents": ["docs/V30_518K_VALIDATION_PLAN.md"] if missing_docs else [],
        },
        "documentation_policy": {
            "default_cadence": "on_new_calibration_evidence_only",
            "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "future_review_entrypoint": "P5 Core Calibration Queue Review",
        },
    }


def test_core_monitoring_steady_state_ready() -> None:
    result = build_core_monitoring_steady_state(core_monitoring_cadence_documentation_sync=_p8_payload())

    assert result["version"] == "v30.core_monitoring_steady_state.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_monitoring_steady_state_ready"
    assert result["decision"]["passed_steady_state_check_count"] == 4
    assert result["decision"]["waiting_for_new_evidence"] is True
    assert result["steady_state_policy"]["new_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "S0"
    assert result["boundary"] == "p9_enters_core_monitoring_steady_state_without_full_pytest"


def test_core_monitoring_steady_state_blocks_missing_docs() -> None:
    result = build_core_monitoring_steady_state(core_monitoring_cadence_documentation_sync=_p8_payload(missing_docs=True))

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_monitoring_steady_state_blocked"
    assert "p8_required_docs_missing" in result["decision"]["blockers"]
    assert "steady_state_checks_failed" in result["decision"]["blockers"]
    assert result["next_mainline_selection"]["task_id"] == "P9-FR"


def test_core_monitoring_steady_state_blocks_pointer_pressure() -> None:
    result = build_core_monitoring_steady_state(core_monitoring_cadence_documentation_sync=_p8_payload(pointer=True))

    assert result["status"] == "blocked"
    assert "p8_pointer_boundary_violation" in result["decision"]["blockers"]
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
