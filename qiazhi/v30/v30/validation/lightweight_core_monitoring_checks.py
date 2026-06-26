from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.core_monitoring_loop import CORE_MONITORING_LOOP_VERSION, run_core_monitoring_loop
from v30.validation.frozen_core_calibration_review import run_frozen_core_calibration_review
from v30.validation.targeted_calibration_candidate_review import run_targeted_calibration_candidate_review
from v30.validation.targeted_calibration_pointer_decision import run_targeted_calibration_pointer_decision
from v30.validation.targeted_calibration_validation_gate import run_targeted_calibration_validation_gate


LIGHTWEIGHT_CORE_MONITORING_CHECKS_VERSION = "v30.lightweight_core_monitoring_checks.v1"

EXPECTED_CHECKS = {
    "m1_m8_frozen_scope": "ready_for_targeted_calibration_iteration",
    "targeted_candidate_review": "ready_for_validation_gate_review",
    "targeted_validation_gate": "ready_for_policy_pointer_review",
    "pointer_decision_no_write": "pointer_promotion_deferred",
}


def run_lightweight_core_monitoring_checks(*, sample_limit: int = 8) -> dict[str, Any]:
    loop = run_core_monitoring_loop(sample_limit=sample_limit)
    check_results = [
        _check_result(
            "m1_m8_frozen_scope",
            run_frozen_core_calibration_review(),
            EXPECTED_CHECKS["m1_m8_frozen_scope"],
        ),
        _check_result(
            "targeted_candidate_review",
            run_targeted_calibration_candidate_review(),
            EXPECTED_CHECKS["targeted_candidate_review"],
        ),
        _check_result(
            "targeted_validation_gate",
            run_targeted_calibration_validation_gate(sample_limit=sample_limit),
            EXPECTED_CHECKS["targeted_validation_gate"],
        ),
        _check_result(
            "pointer_decision_no_write",
            run_targeted_calibration_pointer_decision(sample_limit=sample_limit, operator_decision="defer"),
            EXPECTED_CHECKS["pointer_decision_no_write"],
        ),
    ]
    return build_lightweight_core_monitoring_checks(
        core_monitoring_loop=loop,
        check_results=check_results,
    )


def build_lightweight_core_monitoring_checks(
    *,
    core_monitoring_loop: Mapping[str, Any],
    check_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    loop_summary = _loop_summary(core_monitoring_loop)
    rows = [_normalize_check(row) for row in check_results]
    decision = _decision(loop_summary=loop_summary, check_results=rows)
    return {
        "version": LIGHTWEIGHT_CORE_MONITORING_CHECKS_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["monitoring_checks_completed"] else "blocked",
        "decision": decision,
        "core_monitoring_loop_summary": loop_summary,
        "check_summary": {
            "required_check_count": len(EXPECTED_CHECKS),
            "executed_check_count": len(rows),
            "passed_check_count": sum(1 for row in rows if row["passed"]),
            "failed_check_count": sum(1 for row in rows if not row["passed"]),
            "missing_check_ids": sorted(set(EXPECTED_CHECKS).difference(row["check_id"] for row in rows)),
        },
        "checks": rows,
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "core_module_reopen_recommended": decision["core_module_reopen_recommended"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p1_executes_monitoring_without_reopening_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p1_monitoring_checks_are_read_only_and_do_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p1_executes_lightweight_core_monitoring_checks_without_full_pytest",
    }


def _check_result(check_id: str, payload: Mapping[str, Any], expected_status: str) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    status = str(decision.get("decision_status") or "")
    return {
        "check_id": check_id,
        "version": str(payload.get("version") or ""),
        "decision_status": status,
        "expected_status": expected_status,
        "passed": status == expected_status,
        "blockers": decision.get("blockers", []) if isinstance(decision.get("blockers"), list) else [],
    }


def _loop_summary(loop: Mapping[str, Any]) -> dict[str, Any]:
    decision = loop.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    monitoring = loop.get("monitoring_baseline_summary", {})
    monitoring = monitoring if isinstance(monitoring, dict) else {}
    return {
        "version": str(loop.get("version") or ""),
        "status": str(loop.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "monitoring_loop_ready": bool(decision.get("monitoring_loop_ready")),
        "check_count": int(monitoring.get("check_count", 0) or 0),
        "required_check_count": int(monitoring.get("required_check_count", len(EXPECTED_CHECKS)) or len(EXPECTED_CHECKS)),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _normalize_check(row: Mapping[str, Any]) -> dict[str, Any]:
    check_id = str(row.get("check_id") or "")
    expected = str(row.get("expected_status") or EXPECTED_CHECKS.get(check_id, ""))
    status = str(row.get("decision_status") or "")
    return {
        "check_id": check_id,
        "version": str(row.get("version") or ""),
        "decision_status": status,
        "expected_status": expected,
        "passed": bool(row.get("passed")) if "passed" in row else status == expected,
        "blockers": row.get("blockers", []) if isinstance(row.get("blockers"), list) else [],
    }


def _decision(*, loop_summary: Mapping[str, Any], check_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if loop_summary.get("version") != CORE_MONITORING_LOOP_VERSION:
        blockers.append("p0_core_monitoring_loop_missing")
    if not loop_summary.get("monitoring_loop_ready"):
        blockers.append("p0_core_monitoring_loop_not_ready")
    if loop_summary.get("policy_pointer_promotion_allowed") or loop_summary.get("chart_fact_mutation_allowed"):
        blockers.append("p0_boundary_allows_mutation")
    check_ids = {str(row.get("check_id") or "") for row in check_results}
    missing = sorted(set(EXPECTED_CHECKS).difference(check_ids))
    if missing:
        blockers.append("monitoring_checks_missing")
    failed = [row for row in check_results if not row.get("passed")]
    if failed:
        blockers.append("monitoring_checks_failed")
    ready = not blockers
    return {
        "monitoring_checks_completed": ready,
        "decision_status": "lightweight_core_monitoring_checks_passed" if ready else "lightweight_core_monitoring_checks_blocked",
        "regression_detected": bool(failed),
        "core_module_reopen_recommended": False,
        "failed_check_ids": [str(row.get("check_id") or "") for row in failed],
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "All lightweight core monitoring checks passed; keep M1-M8 frozen and continue calibration observation."
            if ready
            else "One or more lightweight monitoring checks failed or were missing; inspect failed check ids before reopening any module."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["monitoring_checks_completed"]:
        return {
            "task_id": "P2",
            "title": "Core Calibration Observation Summary",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "summarize monitoring pass evidence",
                "confirm no module reopen is needed",
                "prepare next targeted calibration observation cycle",
            ],
        }
    return {
        "task_id": "P1",
        "title": "Lightweight Core Monitoring Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect failed monitoring checks",
            "route concrete failures to focused module fixes",
            "do not reopen modules without check-level evidence",
        ],
    }
