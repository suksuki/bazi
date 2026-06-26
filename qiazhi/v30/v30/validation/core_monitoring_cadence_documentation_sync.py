from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.core_monitoring_cadence_baseline import (
    CORE_MONITORING_CADENCE_BASELINE_VERSION,
    run_core_monitoring_cadence_baseline,
)


CORE_MONITORING_CADENCE_DOCUMENTATION_SYNC_VERSION = "v30.core_monitoring_cadence_documentation_sync.v1"

REQUIRED_SYNC_DOCUMENTS = [
    "docs/V30_POST_SEAL_MAINLINE_TASK_PLAN.md",
    "docs/V30_CORE_MODULE_FINAL_COMPLETION_MAINLINE.md",
    "docs/V30_CORE_BAZI_EIGHT_MODULE_PLAN.md",
    "docs/V30_MAINLINE_COMPLETION_PLAN.md",
    "docs/V30_MASTER_MAINLINE_PLAN.md",
    "docs/V30_MODULE_REVIEW.md",
    "docs/V30_TRAINING_ARCHITECTURE.md",
    "docs/V30_TEST_ARCHITECTURE.md",
    "docs/V30_SYNTHETIC_VALIDATION.md",
    "docs/V30_518K_VALIDATION_PLAN.md",
]


def run_core_monitoring_cadence_documentation_sync(*, sample_limit: int = 8) -> dict[str, Any]:
    cadence_baseline = run_core_monitoring_cadence_baseline(sample_limit=sample_limit)
    return build_core_monitoring_cadence_documentation_sync(
        core_monitoring_cadence_baseline=cadence_baseline,
        synced_documents=REQUIRED_SYNC_DOCUMENTS,
    )


def build_core_monitoring_cadence_documentation_sync(
    *,
    core_monitoring_cadence_baseline: Mapping[str, Any],
    synced_documents: Sequence[str] | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    cadence_summary = _cadence_summary(core_monitoring_cadence_baseline)
    synced = sorted({str(path) for path in synced_documents or []})
    sync_summary = _sync_summary(synced)
    decision = _decision(cadence_summary=cadence_summary, sync_summary=sync_summary)
    return {
        "version": CORE_MONITORING_CADENCE_DOCUMENTATION_SYNC_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["documentation_sync_ready"] else "blocked",
        "decision": decision,
        "cadence_summary": cadence_summary,
        "documentation_sync_summary": sync_summary,
        "synced_documents": synced,
        "documentation_policy": {
            "source_of_truth": "v30.core_monitoring_cadence_baseline.v1",
            "default_cadence": "on_new_calibration_evidence_only",
            "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "future_review_entrypoint": "P5 Core Calibration Queue Review",
            "full_pytest_default": False,
            "full_518k_default": False,
            "pointer_promotion_default": False,
            "chart_fact_mutation_default": False,
            "boundary": "p8_syncs_cadence_docs_without_runtime_mutation",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p8_documentation_sync_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p8_syncs_core_monitoring_cadence_docs_without_full_pytest",
    }


def _cadence_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    cadence = payload.get("cadence_rules", {})
    cadence = cadence if isinstance(cadence, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "cadence_baseline_ready": bool(decision.get("cadence_baseline_ready")),
        "current_cycle_closed": bool(decision.get("current_cycle_closed")),
        "future_monitoring_ready": bool(decision.get("future_monitoring_ready")),
        "default_cadence": str(cadence.get("default_cadence") or ""),
        "new_evidence_entrypoint": str(cadence.get("new_evidence_entrypoint") or ""),
        "queued_evidence_review": str(cadence.get("queued_evidence_review") or ""),
        "default_heavy_validation_allowed": bool(decision.get("default_heavy_validation_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _sync_summary(synced_documents: Sequence[str]) -> dict[str, Any]:
    synced_set = set(synced_documents)
    missing = [path for path in REQUIRED_SYNC_DOCUMENTS if path not in synced_set]
    extra = [path for path in synced_documents if path not in set(REQUIRED_SYNC_DOCUMENTS)]
    return {
        "required_document_count": len(REQUIRED_SYNC_DOCUMENTS),
        "synced_document_count": len(synced_set.intersection(REQUIRED_SYNC_DOCUMENTS)),
        "missing_documents": missing,
        "extra_documents": extra,
        "all_required_documents_synced": not missing,
    }


def _decision(*, cadence_summary: Mapping[str, Any], sync_summary: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if cadence_summary["source_version"] != CORE_MONITORING_CADENCE_BASELINE_VERSION:
        blockers.append("p7_cadence_baseline_missing")
    if not cadence_summary["cadence_baseline_ready"]:
        blockers.append("p7_cadence_baseline_not_ready")
    if cadence_summary["default_cadence"] != "on_new_calibration_evidence_only":
        blockers.append("p7_cadence_not_new_evidence_only")
    if cadence_summary["new_evidence_entrypoint"] != "P4 Focused Core Calibration Evidence Queue":
        blockers.append("p7_future_evidence_entrypoint_mismatch")
    if cadence_summary["queued_evidence_review"] != "P5 Core Calibration Queue Review":
        blockers.append("p7_future_review_entrypoint_mismatch")
    if cadence_summary["default_heavy_validation_allowed"]:
        blockers.append("p7_allows_default_heavy_validation")
    if cadence_summary["full_pytest_required"] or cadence_summary["full_518k_required"]:
        blockers.append("p7_requested_heavy_validation")
    if cadence_summary["policy_pointer_promotion_allowed"] or cadence_summary["pointer_write_performed"]:
        blockers.append("p7_pointer_boundary_violation")
    if cadence_summary["chart_fact_mutation_allowed"]:
        blockers.append("p7_chart_fact_mutation_boundary_violation")
    if not sync_summary["all_required_documents_synced"]:
        blockers.append("required_cadence_docs_missing")
    ready = not blockers
    return {
        "documentation_sync_ready": ready,
        "decision_status": "core_monitoring_cadence_documentation_sync_ready" if ready else "core_monitoring_cadence_documentation_sync_blocked",
        "synced_document_count": sync_summary["synced_document_count"],
        "required_document_count": sync_summary["required_document_count"],
        "current_cycle_closed": bool(cadence_summary["current_cycle_closed"] and ready),
        "future_monitoring_ready": bool(cadence_summary["future_monitoring_ready"] and ready),
        "default_heavy_validation_allowed": False,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P7 cadence baseline is synchronized across the controlling docs."
            if ready
            else "Cadence documentation sync cannot complete until P7 baseline and required docs are aligned."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["documentation_sync_ready"]:
        return {
            "task_id": "P9",
            "title": "Core Monitoring Steady State",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "keep cadence in steady state",
                "route future evidence through P4/P5",
                "keep full pytest and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P8-FR",
        "title": "Core Monitoring Cadence Documentation Sync Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect missing cadence docs",
            "align docs to P7 cadence baseline",
            "do not reopen frozen M1-M8 globally",
        ],
    }
