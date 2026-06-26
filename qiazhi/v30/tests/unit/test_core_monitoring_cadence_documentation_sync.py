from __future__ import annotations

from v30.validation.core_monitoring_cadence_documentation_sync import (
    REQUIRED_SYNC_DOCUMENTS,
    build_core_monitoring_cadence_documentation_sync,
)


def _p7_payload(*, blocked: bool = False, heavy: bool = False) -> dict[str, object]:
    return {
        "version": "v30.core_monitoring_cadence_baseline.v1",
        "status": "completed" if not blocked else "blocked",
        "decision": {
            "decision_status": "core_monitoring_cadence_baseline_ready" if not blocked else "core_monitoring_cadence_baseline_blocked",
            "cadence_baseline_ready": not blocked,
            "current_cycle_closed": not blocked,
            "future_monitoring_ready": not blocked,
            "default_heavy_validation_allowed": heavy,
            "focused_module_fix_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_performed": False,
            "chart_fact_mutation_allowed": False,
        },
        "cadence_rules": {
            "default_cadence": "on_new_calibration_evidence_only",
            "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "queued_evidence_review": "P5 Core Calibration Queue Review",
        },
    }


def test_core_monitoring_cadence_documentation_sync_ready() -> None:
    result = build_core_monitoring_cadence_documentation_sync(
        core_monitoring_cadence_baseline=_p7_payload(),
        synced_documents=REQUIRED_SYNC_DOCUMENTS,
    )

    assert result["version"] == "v30.core_monitoring_cadence_documentation_sync.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "core_monitoring_cadence_documentation_sync_ready"
    assert result["decision"]["synced_document_count"] == len(REQUIRED_SYNC_DOCUMENTS)
    assert result["documentation_policy"]["default_cadence"] == "on_new_calibration_evidence_only"
    assert result["policy_boundary"]["full_pytest_run_allowed_by_default"] is False
    assert result["policy_boundary"]["pointer_write_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "P9"
    assert result["boundary"] == "p8_syncs_core_monitoring_cadence_docs_without_full_pytest"


def test_core_monitoring_cadence_documentation_sync_blocks_missing_doc() -> None:
    result = build_core_monitoring_cadence_documentation_sync(
        core_monitoring_cadence_baseline=_p7_payload(),
        synced_documents=REQUIRED_SYNC_DOCUMENTS[:-1],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "core_monitoring_cadence_documentation_sync_blocked"
    assert "required_cadence_docs_missing" in result["decision"]["blockers"]
    assert result["documentation_sync_summary"]["missing_documents"] == [REQUIRED_SYNC_DOCUMENTS[-1]]
    assert result["next_mainline_selection"]["task_id"] == "P8-FR"


def test_core_monitoring_cadence_documentation_sync_blocks_heavy_baseline() -> None:
    result = build_core_monitoring_cadence_documentation_sync(
        core_monitoring_cadence_baseline=_p7_payload(heavy=True),
        synced_documents=REQUIRED_SYNC_DOCUMENTS,
    )

    assert result["status"] == "blocked"
    assert "p7_allows_default_heavy_validation" in result["decision"]["blockers"]
    assert result["decision"]["full_pytest_required"] is False
