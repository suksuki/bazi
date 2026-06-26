from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.lightweight_core_monitoring_checks import (
    LIGHTWEIGHT_CORE_MONITORING_CHECKS_VERSION,
    run_lightweight_core_monitoring_checks,
)


CORE_CALIBRATION_OBSERVATION_SUMMARY_VERSION = "v30.core_calibration_observation_summary.v1"


def run_core_calibration_observation_summary(*, sample_limit: int = 8) -> dict[str, Any]:
    monitoring_checks = run_lightweight_core_monitoring_checks(sample_limit=sample_limit)
    return build_core_calibration_observation_summary(lightweight_monitoring_checks=monitoring_checks)


def build_core_calibration_observation_summary(
    *,
    lightweight_monitoring_checks: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    monitoring_summary = _monitoring_summary(lightweight_monitoring_checks)
    observations = _observations(lightweight_monitoring_checks)
    decision = _decision(monitoring_summary=monitoring_summary, observations=observations)
    return {
        "version": CORE_CALIBRATION_OBSERVATION_SUMMARY_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["observation_summary_ready"] else "blocked",
        "decision": decision,
        "monitoring_evidence_summary": monitoring_summary,
        "observations": observations,
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "core_module_reopen_recommended": decision["focused_module_fix_required"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p2_observes_core_calibration_without_reopening_frozen_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p2_observation_summary_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p2_summarizes_core_calibration_observations_without_full_pytest",
    }


def _monitoring_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    check_summary = payload.get("check_summary", {})
    check_summary = check_summary if isinstance(check_summary, dict) else {}
    policy_boundary = payload.get("policy_boundary", {})
    policy_boundary = policy_boundary if isinstance(policy_boundary, dict) else {}
    next_selection = payload.get("next_mainline_selection", {})
    next_selection = next_selection if isinstance(next_selection, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "monitoring_checks_completed": bool(decision.get("monitoring_checks_completed")),
        "regression_detected": bool(decision.get("regression_detected")),
        "failed_check_ids": decision.get("failed_check_ids", []) if isinstance(decision.get("failed_check_ids"), list) else [],
        "passed_check_count": int(check_summary.get("passed_check_count", 0) or 0),
        "required_check_count": int(check_summary.get("required_check_count", 0) or 0),
        "missing_check_ids": check_summary.get("missing_check_ids", []) if isinstance(check_summary.get("missing_check_ids"), list) else [],
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "policy_pointer_boundary_allows_write": bool(policy_boundary.get("pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "next_task_id_from_p1": str(next_selection.get("task_id") or ""),
    }


def _observations(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("checks", [])
    rows = rows if isinstance(rows, list) else []
    observations: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        check_id = str(row.get("check_id") or "")
        passed = bool(row.get("passed"))
        observations.append(
            {
                "observation_id": f"p2_observe_{check_id}" if check_id else "p2_observe_unknown_check",
                "check_id": check_id,
                "source_decision_status": str(row.get("decision_status") or ""),
                "expected_status": str(row.get("expected_status") or ""),
                "observation_status": "stable" if passed else "needs_review",
                "module_reopen_recommended": False,
                "action": (
                    "carry_forward_as_monitoring_baseline"
                    if passed
                    else "route_to_focused_failure_review_without_reopening_all_modules"
                ),
            }
        )
    return observations


def _decision(*, monitoring_summary: Mapping[str, Any], observations: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if monitoring_summary["source_version"] != LIGHTWEIGHT_CORE_MONITORING_CHECKS_VERSION:
        blockers.append("p1_lightweight_monitoring_checks_missing")
    if not monitoring_summary["monitoring_checks_completed"]:
        blockers.append("p1_monitoring_checks_not_completed")
    if monitoring_summary["regression_detected"]:
        blockers.append("p1_regression_detected")
    if monitoring_summary["failed_check_ids"]:
        blockers.append("p1_failed_checks_present")
    if monitoring_summary["missing_check_ids"]:
        blockers.append("p1_missing_checks_present")
    if monitoring_summary["pointer_write_performed"] or monitoring_summary["policy_pointer_promotion_allowed"]:
        blockers.append("p1_pointer_boundary_violation")
    if monitoring_summary["chart_fact_mutation_allowed"]:
        blockers.append("p1_chart_fact_mutation_boundary_violation")
    if monitoring_summary["full_pytest_required"] or monitoring_summary["full_518k_required"]:
        blockers.append("p1_requested_heavy_validation")
    if not observations:
        blockers.append("p1_observation_rows_missing")
    needs_review = [row["check_id"] for row in observations if row["observation_status"] != "stable"]
    if needs_review:
        blockers.append("p2_observations_need_review")
    ready = not blockers
    return {
        "observation_summary_ready": ready,
        "decision_status": "core_calibration_observation_summary_ready" if ready else "core_calibration_observation_summary_blocked",
        "stable_observation_count": sum(1 for row in observations if row["observation_status"] == "stable"),
        "needs_review_observation_count": len(needs_review),
        "needs_review_check_ids": needs_review,
        "regression_detected": bool(monitoring_summary["regression_detected"] or needs_review),
        "focused_module_fix_required": bool(needs_review),
        "continue_observation_cycle": ready,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P1 monitoring evidence is stable; continue with a lightweight calibration drift-watch cycle."
            if ready
            else "P1 monitoring evidence is incomplete or unstable; route only the failed checks to focused review."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["observation_summary_ready"]:
        return {
            "task_id": "P3",
            "title": "Core Calibration Drift Watch",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "repeat lightweight observation only when new calibration evidence exists",
                "route drift to focused module fixes instead of broad rewrites",
                "keep full pytest for explicit release or full-freeze decisions",
            ],
        }
    return {
        "task_id": "P2-FR",
        "title": "Core Calibration Observation Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect blocked observation rows",
            "route concrete failures to focused module fixes",
            "do not reopen frozen M1-M8 without check-level evidence",
        ],
    }
