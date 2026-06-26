from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.core_monitoring_cadence_documentation_sync import (
    CORE_MONITORING_CADENCE_DOCUMENTATION_SYNC_VERSION,
    run_core_monitoring_cadence_documentation_sync,
)


CORE_MONITORING_STEADY_STATE_VERSION = "v30.core_monitoring_steady_state.v1"


def run_core_monitoring_steady_state(*, sample_limit: int = 8) -> dict[str, Any]:
    documentation_sync = run_core_monitoring_cadence_documentation_sync(sample_limit=sample_limit)
    return build_core_monitoring_steady_state(core_monitoring_cadence_documentation_sync=documentation_sync)


def build_core_monitoring_steady_state(
    *,
    core_monitoring_cadence_documentation_sync: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    sync_summary = _sync_summary(core_monitoring_cadence_documentation_sync)
    steady_state_checks = _steady_state_checks(sync_summary)
    decision = _decision(sync_summary=sync_summary, steady_state_checks=steady_state_checks)
    return {
        "version": CORE_MONITORING_STEADY_STATE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["steady_state_ready"] else "blocked",
        "decision": decision,
        "sync_summary": sync_summary,
        "steady_state_checks": steady_state_checks,
        "steady_state_policy": {
            "default_action": "wait_for_new_calibration_evidence",
            "no_new_evidence_action": "read_only_status_projection",
            "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "queued_evidence_review": "P5 Core Calibration Queue Review",
            "release_boundary_entrypoint": "explicit_release_or_full_freeze_decision_only",
            "pointer_boundary_entrypoint": "separate_explicit_operator_pointer_review_only",
            "full_pytest_default": False,
            "full_518k_default": False,
            "pointer_promotion_default": False,
            "chart_fact_mutation_default": False,
            "boundary": "p9_steady_state_waits_for_new_evidence_without_runtime_mutation",
        },
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": False,
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p9_keeps_core_modules_frozen_in_steady_state",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p9_steady_state_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p9_enters_core_monitoring_steady_state_without_full_pytest",
    }


def _sync_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    documentation = payload.get("documentation_policy", {})
    documentation = documentation if isinstance(documentation, dict) else {}
    sync = payload.get("documentation_sync_summary", {})
    sync = sync if isinstance(sync, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "documentation_sync_ready": bool(decision.get("documentation_sync_ready")),
        "synced_document_count": int(decision.get("synced_document_count", 0) or 0),
        "required_document_count": int(decision.get("required_document_count", 0) or 0),
        "missing_documents": sync.get("missing_documents", []) if isinstance(sync.get("missing_documents"), list) else [],
        "current_cycle_closed": bool(decision.get("current_cycle_closed")),
        "future_monitoring_ready": bool(decision.get("future_monitoring_ready")),
        "default_cadence": str(documentation.get("default_cadence") or ""),
        "future_evidence_entrypoint": str(documentation.get("future_evidence_entrypoint") or ""),
        "future_review_entrypoint": str(documentation.get("future_review_entrypoint") or ""),
        "default_heavy_validation_allowed": bool(decision.get("default_heavy_validation_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _steady_state_checks(sync_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "p8_documentation_sync_ready",
            "passed": (
                sync_summary["source_version"] == CORE_MONITORING_CADENCE_DOCUMENTATION_SYNC_VERSION
                and sync_summary["documentation_sync_ready"]
            ),
            "expected": "v30.core_monitoring_cadence_documentation_sync.v1 ready",
        },
        {
            "check_id": "required_docs_synced",
            "passed": (
                sync_summary["required_document_count"] > 0
                and sync_summary["synced_document_count"] == sync_summary["required_document_count"]
                and not sync_summary["missing_documents"]
            ),
            "expected": "all required cadence docs synced",
        },
        {
            "check_id": "cadence_routes_future_evidence",
            "passed": (
                sync_summary["default_cadence"] == "on_new_calibration_evidence_only"
                and sync_summary["future_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
                and sync_summary["future_review_entrypoint"] == "P5 Core Calibration Queue Review"
            ),
            "expected": "cadence routes future evidence through P4/P5",
        },
        {
            "check_id": "no_default_heavy_or_pointer_action",
            "passed": (
                not sync_summary["default_heavy_validation_allowed"]
                and not sync_summary["full_pytest_required"]
                and not sync_summary["full_518k_required"]
                and not sync_summary["policy_pointer_promotion_allowed"]
                and not sync_summary["pointer_write_performed"]
                and not sync_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "no default heavy validation, pointer, or chart-fact mutation",
        },
    ]


def _decision(*, sync_summary: Mapping[str, Any], steady_state_checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row["check_id"] for row in steady_state_checks if not row["passed"]]
    blockers: list[str] = []
    if sync_summary["source_version"] != CORE_MONITORING_CADENCE_DOCUMENTATION_SYNC_VERSION:
        blockers.append("p8_documentation_sync_missing")
    if not sync_summary["documentation_sync_ready"]:
        blockers.append("p8_documentation_sync_not_ready")
    if sync_summary["missing_documents"]:
        blockers.append("p8_required_docs_missing")
    if not sync_summary["future_monitoring_ready"]:
        blockers.append("p8_future_monitoring_not_ready")
    if sync_summary["default_heavy_validation_allowed"]:
        blockers.append("p8_allows_default_heavy_validation")
    if sync_summary["full_pytest_required"] or sync_summary["full_518k_required"]:
        blockers.append("p8_requested_heavy_validation")
    if sync_summary["policy_pointer_promotion_allowed"] or sync_summary["pointer_write_performed"]:
        blockers.append("p8_pointer_boundary_violation")
    if sync_summary["chart_fact_mutation_allowed"]:
        blockers.append("p8_chart_fact_mutation_boundary_violation")
    if failed:
        blockers.append("steady_state_checks_failed")
    ready = not blockers
    return {
        "steady_state_ready": ready,
        "decision_status": "core_monitoring_steady_state_ready" if ready else "core_monitoring_steady_state_blocked",
        "steady_state_check_count": len(steady_state_checks),
        "passed_steady_state_check_count": sum(1 for row in steady_state_checks if row["passed"]),
        "failed_steady_state_check_ids": failed,
        "current_cycle_closed": bool(sync_summary["current_cycle_closed"] and ready),
        "future_monitoring_ready": bool(sync_summary["future_monitoring_ready"] and ready),
        "waiting_for_new_evidence": ready,
        "focused_module_fix_required": False,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "Cadence is synchronized and the core monitoring track is in steady state."
            if ready
            else "Steady state cannot be entered until P8 sync and boundary blockers are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["steady_state_ready"]:
        return {
            "task_id": "S0",
            "title": "Steady State Await New Calibration Evidence",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "do not run more tasks without new evidence or explicit release request",
                "route future calibration evidence through P4/P5",
                "keep full pytest and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P9-FR",
        "title": "Core Monitoring Steady State Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect failed steady-state checks",
            "resolve cadence sync blockers",
            "do not reopen frozen M1-M8 globally",
        ],
    }
