from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.core_monitoring_steady_state import (
    CORE_MONITORING_STEADY_STATE_VERSION,
    run_core_monitoring_steady_state,
)


CORE_MONITORING_S0_STATUS_VERSION = "v30.core_monitoring_s0_status.v1"


def run_core_monitoring_s0_status(*, sample_limit: int = 8) -> dict[str, Any]:
    steady_state = run_core_monitoring_steady_state(sample_limit=sample_limit)
    return build_core_monitoring_s0_status(core_monitoring_steady_state=steady_state)


def build_core_monitoring_s0_status(
    *,
    core_monitoring_steady_state: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    steady_summary = _steady_summary(core_monitoring_steady_state)
    status_checks = _status_checks(steady_summary)
    decision = _decision(steady_summary=steady_summary, status_checks=status_checks)
    return {
        "version": CORE_MONITORING_S0_STATUS_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["s0_status_ready"] else "blocked",
        "decision": decision,
        "steady_state_summary": steady_summary,
        "status_checks": status_checks,
        "s0_policy": {
            "current_state": "S0 Steady State Await New Calibration Evidence",
            "default_action": "do_not_start_new_core_monitoring_task",
            "allowed_default_action": "read_only_status_projection",
            "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "queued_evidence_review": "P5 Core Calibration Queue Review",
            "release_boundary_entrypoint": "explicit_release_or_full_freeze_decision_only",
            "pointer_boundary_entrypoint": "separate_explicit_operator_pointer_review_only",
            "full_pytest_default": False,
            "full_518k_default": False,
            "pointer_promotion_default": False,
            "chart_fact_mutation_default": False,
            "boundary": "s0_waits_for_new_evidence_without_runtime_mutation",
        },
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": False,
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "s0_keeps_core_modules_frozen_until_new_evidence",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "s0_status_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "s0_records_steady_state_without_full_pytest",
    }


def _steady_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    steady_policy = payload.get("steady_state_policy", {})
    steady_policy = steady_policy if isinstance(steady_policy, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "steady_state_ready": bool(decision.get("steady_state_ready")),
        "steady_state_check_count": int(decision.get("steady_state_check_count", 0) or 0),
        "passed_steady_state_check_count": int(decision.get("passed_steady_state_check_count", 0) or 0),
        "waiting_for_new_evidence": bool(decision.get("waiting_for_new_evidence")),
        "future_monitoring_ready": bool(decision.get("future_monitoring_ready")),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "new_evidence_entrypoint": str(steady_policy.get("new_evidence_entrypoint") or ""),
        "queued_evidence_review": str(steady_policy.get("queued_evidence_review") or ""),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _status_checks(steady_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "p9_steady_state_ready",
            "passed": steady_summary["source_version"] == CORE_MONITORING_STEADY_STATE_VERSION and steady_summary["steady_state_ready"],
            "expected": "v30.core_monitoring_steady_state.v1 ready",
        },
        {
            "check_id": "waiting_for_new_evidence",
            "passed": steady_summary["waiting_for_new_evidence"] and steady_summary["future_monitoring_ready"],
            "expected": "waiting_for_new_evidence=true and future_monitoring_ready=true",
        },
        {
            "check_id": "future_routes_preserved",
            "passed": (
                steady_summary["new_evidence_entrypoint"] == "P4 Focused Core Calibration Evidence Queue"
                and steady_summary["queued_evidence_review"] == "P5 Core Calibration Queue Review"
            ),
            "expected": "future evidence routes through P4/P5",
        },
        {
            "check_id": "no_default_heavy_pointer_or_fact_mutation",
            "passed": (
                not steady_summary["full_pytest_required"]
                and not steady_summary["full_518k_required"]
                and not steady_summary["policy_pointer_promotion_allowed"]
                and not steady_summary["pointer_write_performed"]
                and not steady_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "no default heavy validation, pointer action, or chart-fact mutation",
        },
    ]


def _decision(*, steady_summary: Mapping[str, Any], status_checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row["check_id"] for row in status_checks if not row["passed"]]
    blockers: list[str] = []
    if steady_summary["source_version"] != CORE_MONITORING_STEADY_STATE_VERSION:
        blockers.append("p9_steady_state_missing")
    if not steady_summary["steady_state_ready"]:
        blockers.append("p9_steady_state_not_ready")
    if not steady_summary["waiting_for_new_evidence"]:
        blockers.append("p9_not_waiting_for_new_evidence")
    if steady_summary["focused_module_fix_required"]:
        blockers.append("p9_focused_module_fix_required")
    if steady_summary["full_pytest_required"] or steady_summary["full_518k_required"]:
        blockers.append("p9_requested_heavy_validation")
    if steady_summary["policy_pointer_promotion_allowed"] or steady_summary["pointer_write_performed"]:
        blockers.append("p9_pointer_boundary_violation")
    if steady_summary["chart_fact_mutation_allowed"]:
        blockers.append("p9_chart_fact_mutation_boundary_violation")
    if failed:
        blockers.append("s0_status_checks_failed")
    ready = not blockers
    return {
        "s0_status_ready": ready,
        "decision_status": "core_monitoring_s0_status_ready" if ready else "core_monitoring_s0_status_blocked",
        "status_check_count": len(status_checks),
        "passed_status_check_count": sum(1 for row in status_checks if row["passed"]),
        "failed_status_check_ids": failed,
        "waiting_for_new_evidence": ready,
        "new_core_monitoring_task_allowed_by_default": False,
        "future_monitoring_ready": bool(steady_summary["future_monitoring_ready"] and ready),
        "focused_module_fix_required": False,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "S0 is ready; wait for new calibration evidence or an explicit release/pointer boundary request."
            if ready
            else "S0 cannot be recorded until P9 steady-state blockers are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["s0_status_ready"]:
        return {
            "task_id": "S0",
            "title": "Steady State Await New Calibration Evidence",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "no further default core-monitoring task",
                "route future calibration evidence through P4/P5",
                "keep full pytest and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "S0-FR",
        "title": "Steady State Status Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect S0 status blockers",
            "resolve steady-state readiness before waiting",
            "do not reopen frozen M1-M8 globally",
        ],
    }
