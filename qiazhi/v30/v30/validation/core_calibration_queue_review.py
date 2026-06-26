from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.focused_core_calibration_evidence_queue import (
    FOCUSED_CORE_CALIBRATION_EVIDENCE_QUEUE_VERSION,
    run_focused_core_calibration_evidence_queue,
)


CORE_CALIBRATION_QUEUE_REVIEW_VERSION = "v30.core_calibration_queue_review.v1"


def run_core_calibration_queue_review(*, sample_limit: int = 8) -> dict[str, Any]:
    evidence_queue = run_focused_core_calibration_evidence_queue(sample_limit=sample_limit)
    return build_core_calibration_queue_review(focused_core_calibration_evidence_queue=evidence_queue)


def build_core_calibration_queue_review(
    *,
    focused_core_calibration_evidence_queue: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    queue_summary = _queue_summary(focused_core_calibration_evidence_queue)
    queue_items = _queue_items(focused_core_calibration_evidence_queue)
    module_reviews = _module_reviews(queue_items)
    decision = _decision(queue_summary=queue_summary, module_reviews=module_reviews)
    return {
        "version": CORE_CALIBRATION_QUEUE_REVIEW_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["queue_review_ready"] else "blocked",
        "decision": decision,
        "queue_summary": queue_summary,
        "module_reviews": module_reviews,
        "review_policy": {
            "review_scope": "queued_calibration_evidence_only",
            "fix_execution_allowed": False,
            "default_heavy_validation": False,
            "full_pytest_trigger": "explicit_release_or_full_freeze_decision_only",
            "full_518k_trigger": "explicit_pointer_or_distribution_drift_review_only",
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "p5_reviews_queue_without_executing_fixes_or_promoting_policy",
        },
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": decision["focused_module_fix_required"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p5_reviews_focused_queue_without_reopening_all_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p5_queue_review_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p5_reviews_core_calibration_queue_without_full_pytest",
    }


def _queue_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "evidence_queue_ready": bool(decision.get("evidence_queue_ready")),
        "queued_evidence_count": int(decision.get("queued_evidence_count", 0) or 0),
        "queue_item_count": int(decision.get("queue_item_count", 0) or 0),
        "module_queue_count": int(decision.get("module_queue_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _queue_items(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("queue_items", [])
    rows = rows if isinstance(rows, list) else []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "queue_item_id": str(row.get("queue_item_id") or ""),
                "evidence_id": str(row.get("evidence_id") or ""),
                "module_target": str(row.get("module_target") or "M7"),
                "check_id": str(row.get("check_id") or ""),
                "routing_scope": str(row.get("routing_scope") or ""),
                "severity": str(row.get("severity") or "review"),
                "status": str(row.get("status") or "queued_for_focused_review"),
                "reopen_all_core_modules": bool(row.get("reopen_all_core_modules")),
                "chart_fact_mutation_allowed": bool(row.get("chart_fact_mutation_allowed")),
                "pointer_write_allowed": bool(row.get("pointer_write_allowed")),
            }
        )
    return normalized


def _module_reviews(queue_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in queue_items:
        grouped[item["module_target"]].append(item)
    reviews: list[dict[str, Any]] = []
    for module, items in sorted(grouped.items()):
        severity_rank = {"none": 0, "info": 1, "review": 2, "warning": 3, "critical": 4}
        max_severity = max((item["severity"] for item in items), key=lambda value: severity_rank.get(value, 2))
        reviews.append(
            {
                "module_target": module,
                "queued_item_count": len(items),
                "evidence_ids": sorted({item["evidence_id"] for item in items}),
                "check_ids": sorted({item["check_id"] for item in items}),
                "max_severity": max_severity,
                "review_status": "focused_fix_candidate",
                "recommended_action": "open_focused_module_fix_plan",
                "fix_execution_allowed": False,
                "reopen_all_core_modules": False,
                "chart_fact_mutation_allowed": False,
                "pointer_write_allowed": False,
            }
        )
    return reviews


def _decision(*, queue_summary: Mapping[str, Any], module_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if queue_summary["source_version"] != FOCUSED_CORE_CALIBRATION_EVIDENCE_QUEUE_VERSION:
        blockers.append("p4_evidence_queue_missing")
    if not queue_summary["evidence_queue_ready"]:
        blockers.append("p4_evidence_queue_not_ready")
    if queue_summary["full_pytest_required"] or queue_summary["full_518k_required"]:
        blockers.append("p4_requested_heavy_validation")
    if queue_summary["policy_pointer_promotion_allowed"] or queue_summary["pointer_write_performed"]:
        blockers.append("p4_pointer_boundary_violation")
    if queue_summary["chart_fact_mutation_allowed"]:
        blockers.append("p4_chart_fact_mutation_boundary_violation")
    if any(row["reopen_all_core_modules"] for row in module_reviews):
        blockers.append("module_review_requests_global_reopen")
    ready = not blockers
    return {
        "queue_review_ready": ready,
        "decision_status": (
            "core_calibration_queue_review_ready"
            if ready and not module_reviews
            else "core_calibration_queue_review_has_focused_candidates"
            if ready
            else "core_calibration_queue_review_blocked"
        ),
        "reviewed_module_count": len(module_reviews),
        "focused_fix_candidate_count": len(module_reviews),
        "focused_module_fix_required": bool(module_reviews),
        "continue_lightweight_watch": ready and not module_reviews,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P4 evidence queue is ready and empty; no focused module fix is required."
            if ready and not module_reviews
            else "Queued evidence has focused module candidates; prepare fix plans without executing changes."
            if ready
            else "Queue review is blocked by upstream queue status or prohibited heavy/pointer/chart-fact boundary pressure."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["queue_review_ready"]:
        return {
            "task_id": "P6",
            "title": "Core Calibration Watch Closeout",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "close the current empty queue review cycle",
                "keep monitoring ready for future evidence",
                "keep heavy validation and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P5-FR",
        "title": "Core Calibration Queue Review Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect blocked queue review inputs",
            "remove heavy validation or pointer pressure",
            "do not reopen frozen M1-M8 globally",
        ],
    }
