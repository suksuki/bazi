from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.core_calibration_drift_watch import (
    CORE_CALIBRATION_DRIFT_WATCH_VERSION,
    DRIFT_ROUTE_MAP,
    run_core_calibration_drift_watch,
)


FOCUSED_CORE_CALIBRATION_EVIDENCE_QUEUE_VERSION = "v30.focused_core_calibration_evidence_queue.v1"


def run_focused_core_calibration_evidence_queue(*, sample_limit: int = 8) -> dict[str, Any]:
    drift_watch = run_core_calibration_drift_watch(sample_limit=sample_limit)
    return build_focused_core_calibration_evidence_queue(core_calibration_drift_watch=drift_watch)


def build_focused_core_calibration_evidence_queue(
    *,
    core_calibration_drift_watch: Mapping[str, Any],
    calibration_evidence: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    drift_summary = _drift_watch_summary(core_calibration_drift_watch)
    evidence_rows = [_normalize_evidence(row) for row in calibration_evidence or []]
    queue_items = _queue_items(evidence_rows)
    module_queues = _module_queues(queue_items)
    decision = _decision(drift_summary=drift_summary, evidence_rows=evidence_rows, queue_items=queue_items)
    return {
        "version": FOCUSED_CORE_CALIBRATION_EVIDENCE_QUEUE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["evidence_queue_ready"] else "blocked",
        "decision": decision,
        "drift_watch_summary": drift_summary,
        "queue_policy": {
            "queue_scope": "future_calibration_evidence_only",
            "batch_key": "m1_m8_module_target",
            "default_heavy_validation": False,
            "full_pytest_trigger": "explicit_release_or_full_freeze_decision_only",
            "full_518k_trigger": "explicit_pointer_or_distribution_drift_review_only",
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "p4_batches_evidence_without_mutating_core_facts_or_pointers",
        },
        "calibration_evidence": evidence_rows,
        "queue_items": queue_items,
        "module_queues": module_queues,
        "route_matrix": _route_matrix(),
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": decision["focused_module_fix_required"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p4_queues_focused_module_evidence_without_reopening_all_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p4_evidence_queue_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p4_builds_focused_core_calibration_evidence_queue_without_full_pytest",
    }


def _drift_watch_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "drift_watch_ready": bool(decision.get("drift_watch_ready")),
        "drift_detected": bool(decision.get("drift_detected")),
        "drift_route_count": int(decision.get("drift_route_count", 0) or 0),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _normalize_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    check_id = str(row.get("check_id") or "")
    route = DRIFT_ROUTE_MAP.get(check_id, {"module_targets": ["M7"], "routing_scope": "unmapped_calibration_evidence_review"})
    module_targets = row.get("module_targets")
    if not isinstance(module_targets, list) or not module_targets:
        module_targets = route["module_targets"]
    return {
        "evidence_id": str(row.get("evidence_id") or f"p4_evidence_{check_id or 'unknown'}"),
        "check_id": check_id,
        "status": str(row.get("status") or row.get("evidence_status") or "queued"),
        "severity": str(row.get("severity") or "review"),
        "source": str(row.get("source") or "manual_or_future_calibration_evidence"),
        "summary": str(row.get("summary") or ""),
        "module_targets": [str(module) for module in module_targets],
        "routing_scope": str(row.get("routing_scope") or route["routing_scope"]),
        "chart_fact_mutation_requested": bool(row.get("chart_fact_mutation_requested", row.get("chart_fact_mutation_allowed", False))),
        "pointer_write_requested": bool(row.get("pointer_write_requested", False)),
        "requires_full_pytest": bool(row.get("requires_full_pytest", False)),
        "requires_full_518k": bool(row.get("requires_full_518k", False)),
    }


def _queue_items(evidence_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in evidence_rows:
        for module in row["module_targets"]:
            items.append(
                {
                    "queue_item_id": f"{row['evidence_id']}::{module}",
                    "evidence_id": row["evidence_id"],
                    "module_target": module,
                    "check_id": row["check_id"],
                    "routing_scope": row["routing_scope"],
                    "severity": row["severity"],
                    "status": "queued_for_focused_review",
                    "reopen_all_core_modules": False,
                    "chart_fact_mutation_allowed": False,
                    "pointer_write_allowed": False,
                }
            )
    return items


def _module_queues(queue_items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in queue_items:
        grouped[str(item["module_target"])].append(item)
    return [
        {
            "module_target": module,
            "queued_item_count": len(items),
            "evidence_ids": sorted({str(item["evidence_id"]) for item in items}),
            "routing_scopes": sorted({str(item["routing_scope"]) for item in items}),
            "queue_status": "ready_for_focused_review",
        }
        for module, items in sorted(grouped.items())
    ]


def _decision(
    *,
    drift_summary: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
    queue_items: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    if drift_summary["source_version"] != CORE_CALIBRATION_DRIFT_WATCH_VERSION:
        blockers.append("p3_drift_watch_missing")
    if not drift_summary["drift_watch_ready"]:
        blockers.append("p3_drift_watch_not_ready")
    if drift_summary["drift_detected"] or drift_summary["focused_module_fix_required"]:
        blockers.append("p3_drift_watch_reports_existing_drift")
    if drift_summary["full_pytest_required"] or drift_summary["full_518k_required"]:
        blockers.append("p3_requested_heavy_validation")
    if drift_summary["policy_pointer_promotion_allowed"] or drift_summary["pointer_write_performed"]:
        blockers.append("p3_pointer_boundary_violation")
    if drift_summary["chart_fact_mutation_allowed"]:
        blockers.append("p3_chart_fact_mutation_boundary_violation")
    if any(row["chart_fact_mutation_requested"] for row in evidence_rows):
        blockers.append("calibration_evidence_requests_chart_fact_mutation")
    if any(row["pointer_write_requested"] for row in evidence_rows):
        blockers.append("calibration_evidence_requests_pointer_write")
    ready = not blockers
    queued_count = len(queue_items)
    return {
        "evidence_queue_ready": ready,
        "decision_status": (
            "focused_core_calibration_evidence_queue_ready"
            if ready and queued_count == 0
            else "focused_core_calibration_evidence_queued"
            if ready
            else "focused_core_calibration_evidence_queue_blocked"
        ),
        "queued_evidence_count": len(evidence_rows),
        "queue_item_count": queued_count,
        "module_queue_count": len({str(item["module_target"]) for item in queue_items}),
        "focused_module_fix_required": bool(queued_count),
        "continue_lightweight_watch": ready and queued_count == 0,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P3 drift watch is stable and no new evidence is queued; keep the queue open for future module-targeted evidence."
            if ready and queued_count == 0
            else "New calibration evidence is queued by module target for focused review without mutating core facts."
            if ready
            else "Evidence queue is blocked by upstream drift-watch status or prohibited mutation/pointer pressure."
        ),
    }


def _route_matrix() -> list[dict[str, Any]]:
    return [
        {"check_id": check_id, **route}
        for check_id, route in sorted(DRIFT_ROUTE_MAP.items())
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["evidence_queue_ready"]:
        return {
            "task_id": "P5",
            "title": "Core Calibration Queue Review",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "review queued evidence by module target",
                "open focused fixes only when evidence exists",
                "keep heavy validation and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P4-FR",
        "title": "Focused Core Calibration Evidence Queue Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect blocked evidence queue inputs",
            "remove mutation or pointer-write pressure",
            "do not reopen frozen M1-M8 globally",
        ],
    }
