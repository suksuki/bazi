from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.core_calibration_queue_review import (
    CORE_CALIBRATION_QUEUE_REVIEW_VERSION,
    run_core_calibration_queue_review,
)


CORE_CALIBRATION_WATCH_CLOSEOUT_VERSION = "v30.core_calibration_watch_closeout.v1"


def run_core_calibration_watch_closeout(*, sample_limit: int = 8) -> dict[str, Any]:
    queue_review = run_core_calibration_queue_review(sample_limit=sample_limit)
    return build_core_calibration_watch_closeout(core_calibration_queue_review=queue_review)


def build_core_calibration_watch_closeout(
    *,
    core_calibration_queue_review: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    review_summary = _review_summary(core_calibration_queue_review)
    closeout_checks = _closeout_checks(review_summary)
    decision = _decision(review_summary=review_summary, closeout_checks=closeout_checks)
    return {
        "version": CORE_CALIBRATION_WATCH_CLOSEOUT_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["watch_closeout_ready"] else "blocked",
        "decision": decision,
        "queue_review_summary": review_summary,
        "closeout_checks": closeout_checks,
        "watch_cycle_summary": {
            "cycle_id": "P0-P6 Core Monitoring And Calibration Watch",
            "completed_steps": ["P0", "P1", "P2", "P3", "P4", "P5", "P6"],
            "current_cycle_closed": decision["watch_closeout_ready"],
            "future_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "future_review_entrypoint": "P5 Core Calibration Queue Review",
            "boundary": "p6_closes_current_cycle_but_keeps_future_evidence_path_open",
        },
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": decision["focused_module_fix_required"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p6_closes_watch_without_reopening_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p6_watch_closeout_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p6_closes_core_calibration_watch_without_full_pytest",
    }


def _review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "queue_review_ready": bool(decision.get("queue_review_ready")),
        "reviewed_module_count": int(decision.get("reviewed_module_count", 0) or 0),
        "focused_fix_candidate_count": int(decision.get("focused_fix_candidate_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "continue_lightweight_watch": bool(decision.get("continue_lightweight_watch")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _closeout_checks(review_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "p5_queue_review_ready",
            "passed": review_summary["source_version"] == CORE_CALIBRATION_QUEUE_REVIEW_VERSION and review_summary["queue_review_ready"],
            "expected": "v30.core_calibration_queue_review.v1 ready",
        },
        {
            "check_id": "no_focused_fix_candidate",
            "passed": review_summary["focused_fix_candidate_count"] == 0 and not review_summary["focused_module_fix_required"],
            "expected": "focused_fix_candidate_count=0",
        },
        {
            "check_id": "no_heavy_validation_requested",
            "passed": not review_summary["full_pytest_required"] and not review_summary["full_518k_required"],
            "expected": "full_pytest=false and full_518k=false",
        },
        {
            "check_id": "no_pointer_or_chart_fact_mutation",
            "passed": (
                not review_summary["policy_pointer_promotion_allowed"]
                and not review_summary["pointer_write_performed"]
                and not review_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "no pointer write, no pointer promotion, no chart fact mutation",
        },
    ]


def _decision(*, review_summary: Mapping[str, Any], closeout_checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row["check_id"] for row in closeout_checks if not row["passed"]]
    blockers: list[str] = []
    if review_summary["source_version"] != CORE_CALIBRATION_QUEUE_REVIEW_VERSION:
        blockers.append("p5_queue_review_missing")
    if not review_summary["queue_review_ready"]:
        blockers.append("p5_queue_review_not_ready")
    if review_summary["focused_fix_candidate_count"] or review_summary["focused_module_fix_required"]:
        blockers.append("p5_focused_fix_candidates_present")
    if review_summary["full_pytest_required"] or review_summary["full_518k_required"]:
        blockers.append("p5_requested_heavy_validation")
    if review_summary["policy_pointer_promotion_allowed"] or review_summary["pointer_write_performed"]:
        blockers.append("p5_pointer_boundary_violation")
    if review_summary["chart_fact_mutation_allowed"]:
        blockers.append("p5_chart_fact_mutation_boundary_violation")
    if failed:
        blockers.append("closeout_checks_failed")
    ready = not blockers
    return {
        "watch_closeout_ready": ready,
        "decision_status": "core_calibration_watch_closeout_ready" if ready else "core_calibration_watch_closeout_blocked",
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": sum(1 for row in closeout_checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "focused_module_fix_required": False,
        "current_cycle_closed": ready,
        "future_monitoring_ready": ready,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P5 reviewed an empty queue; close the current watch cycle and keep the future evidence path open."
            if ready
            else "Current watch cycle cannot close until queue review blockers or focused candidates are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["watch_closeout_ready"]:
        return {
            "task_id": "P7",
            "title": "Core Monitoring Cadence Baseline",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "document the ongoing lightweight cadence",
                "reuse P4/P5 when future evidence appears",
                "keep heavy validation and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P6-FR",
        "title": "Core Calibration Watch Closeout Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect failed closeout checks",
            "resolve focused candidates before closeout",
            "do not reopen frozen M1-M8 globally",
        ],
    }
