from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.mainline_selection_after_release_pause import (
    MAINLINE_SELECTION_AFTER_RELEASE_PAUSE_VERSION,
    run_mainline_selection_after_release_pause,
)
from v30.validation.targeted_calibration_closeout import (
    TARGETED_CALIBRATION_CLOSEOUT_VERSION,
    run_targeted_calibration_closeout,
)


CORE_MONITORING_LOOP_VERSION = "v30.core_monitoring_loop.v1"


def run_core_monitoring_loop(*, sample_limit: int = 8) -> dict[str, Any]:
    selection = run_mainline_selection_after_release_pause(sample_limit=sample_limit)
    closeout = run_targeted_calibration_closeout(sample_limit=sample_limit)
    return build_core_monitoring_loop(
        mainline_selection_after_release_pause=selection,
        targeted_calibration_closeout=closeout,
    )


def build_core_monitoring_loop(
    *,
    mainline_selection_after_release_pause: Mapping[str, Any],
    targeted_calibration_closeout: Mapping[str, Any],
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    selection_summary = _selection_summary(mainline_selection_after_release_pause)
    closeout_summary = _closeout_summary(targeted_calibration_closeout)
    monitoring = _monitoring_summary(targeted_calibration_closeout)
    decision = _decision(
        selection_summary=selection_summary,
        closeout_summary=closeout_summary,
        monitoring=monitoring,
    )
    return {
        "version": CORE_MONITORING_LOOP_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["monitoring_loop_ready"] else "blocked",
        "decision": decision,
        "mainline_selection_summary": selection_summary,
        "targeted_calibration_closeout_summary": closeout_summary,
        "monitoring_baseline_summary": monitoring,
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p0_monitors_frozen_core_without_reopening_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p0_monitoring_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p0_core_monitoring_loop_records_lightweight_monitoring_without_full_pytest",
    }


def _selection_summary(selection: Mapping[str, Any]) -> dict[str, Any]:
    decision = selection.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    selected = selection.get("selected_non_release_mainline", {})
    selected = selected if isinstance(selected, dict) else {}
    return {
        "version": str(selection.get("version") or ""),
        "status": str(selection.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "selected_task_id": str(decision.get("selected_task_id") or selected.get("task_id") or ""),
        "selected_track": str(decision.get("selected_track") or selected.get("selected_track") or ""),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "full_pytest_authorized": bool(decision.get("full_pytest_authorized")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _closeout_summary(closeout: Mapping[str, Any]) -> dict[str, Any]:
    decision = closeout.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    policy = closeout.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    pointer = closeout.get("pointer_decision_summary", {})
    pointer = pointer if isinstance(pointer, dict) else {}
    return {
        "version": str(closeout.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "closeout_ready": bool(decision.get("closeout_ready")),
        "targeted_calibration_track_closed": bool(decision.get("targeted_calibration_track_closed")),
        "pointer_write_performed": bool(pointer.get("pointer_write_performed")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _monitoring_summary(closeout: Mapping[str, Any]) -> dict[str, Any]:
    baseline = closeout.get("monitoring_baseline", {})
    baseline = baseline if isinstance(baseline, dict) else {}
    checks = baseline.get("checks", [])
    checks = checks if isinstance(checks, list) else []
    check_ids = [str(row.get("check_id") or "") for row in checks if isinstance(row, dict)]
    required = {
        "m1_m8_frozen_scope",
        "targeted_candidate_review",
        "targeted_validation_gate",
        "pointer_decision_no_write",
    }
    missing = sorted(required.difference(check_ids))
    return {
        "check_count": int(baseline.get("check_count", len(checks)) or 0),
        "check_ids": check_ids,
        "required_check_count": len(required),
        "missing_required_checks": missing,
        "full_pytest_required": bool(baseline.get("full_pytest_required")),
        "full_518k_required": bool(baseline.get("full_518k_required")),
        "boundary": str(baseline.get("boundary") or ""),
    }


def _decision(
    *,
    selection_summary: Mapping[str, Any],
    closeout_summary: Mapping[str, Any],
    monitoring: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if selection_summary.get("version") != MAINLINE_SELECTION_AFTER_RELEASE_PAUSE_VERSION:
        blockers.append("m0_after_release_pause_selection_missing")
    if selection_summary.get("selected_task_id") != "P0":
        blockers.append("p0_not_selected")
    if selection_summary.get("external_release_ready") or selection_summary.get("full_pytest_authorized"):
        blockers.append("release_boundary_not_paused")
    if selection_summary.get("policy_pointer_promotion_allowed") or selection_summary.get("chart_fact_mutation_allowed"):
        blockers.append("selection_boundary_allows_mutation")
    if closeout_summary.get("version") != TARGETED_CALIBRATION_CLOSEOUT_VERSION:
        blockers.append("f6_closeout_missing")
    if not closeout_summary.get("closeout_ready") or not closeout_summary.get("targeted_calibration_track_closed"):
        blockers.append("targeted_calibration_not_closed")
    if closeout_summary.get("pointer_write_performed") or closeout_summary.get("policy_pointer_promotion_allowed"):
        blockers.append("unexpected_pointer_permission")
    if closeout_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation")
    if int(monitoring.get("check_count", 0) or 0) < int(monitoring.get("required_check_count", 4) or 4):
        blockers.append("monitoring_check_count_low")
    if monitoring.get("missing_required_checks"):
        blockers.append("monitoring_required_checks_missing")
    if monitoring.get("full_pytest_required") or monitoring.get("full_518k_required"):
        blockers.append("monitoring_requires_heavy_gate")

    ready = not blockers
    return {
        "monitoring_loop_ready": ready,
        "decision_status": "core_monitoring_loop_ready" if ready else "core_monitoring_loop_blocked",
        "regression_detected": False,
        "core_module_reopen_recommended": False,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "Core monitoring loop is ready; use lightweight F6 monitoring checks and route only concrete failures to module fixes."
            if ready
            else "Core monitoring loop needs the listed blockers closed before it can be used as the active non-release mainline."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["monitoring_loop_ready"]:
        return {
            "task_id": "P1",
            "title": "Execute Lightweight Core Monitoring Checks",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "run the four F6 monitoring commands",
                "record pass/blocker status",
                "route concrete failures to focused module fixes",
            ],
        }
    return {
        "task_id": "P0",
        "title": "Core Monitoring Loop Gap Closure",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "restore M0-after-pause and F6 evidence",
            "rerun core monitoring loop review",
            "do not reopen modules while blocked",
        ],
    }
