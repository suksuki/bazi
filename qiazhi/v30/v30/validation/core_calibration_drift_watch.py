from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.core_calibration_observation_summary import (
    CORE_CALIBRATION_OBSERVATION_SUMMARY_VERSION,
    run_core_calibration_observation_summary,
)


CORE_CALIBRATION_DRIFT_WATCH_VERSION = "v30.core_calibration_drift_watch.v1"

DRIFT_ROUTE_MAP = {
    "m1_m8_frozen_scope": {
        "module_targets": ["M1", "M2", "M7"],
        "routing_scope": "deterministic_fact_or_core_freeze_boundary_review",
    },
    "targeted_candidate_review": {
        "module_targets": ["M3", "M4", "M5"],
        "routing_scope": "candidate_policy_and_evidence_spine_review",
    },
    "targeted_validation_gate": {
        "module_targets": ["M4", "M5", "M7"],
        "routing_scope": "synthetic_real_case_or_518k_sample_validation_review",
    },
    "pointer_decision_no_write": {
        "module_targets": ["M8"],
        "routing_scope": "policy_pointer_boundary_and_projection_governance_review",
    },
}


def run_core_calibration_drift_watch(*, sample_limit: int = 8) -> dict[str, Any]:
    observation_summary = run_core_calibration_observation_summary(sample_limit=sample_limit)
    return build_core_calibration_drift_watch(core_calibration_observation_summary=observation_summary)


def build_core_calibration_drift_watch(
    *,
    core_calibration_observation_summary: Mapping[str, Any],
    calibration_evidence: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    summary = _observation_summary(core_calibration_observation_summary)
    evidence_rows = [_normalize_evidence(row) for row in calibration_evidence or []]
    drift_routes = _drift_routes(summary=summary, evidence_rows=evidence_rows)
    decision = _decision(summary=summary, evidence_rows=evidence_rows, drift_routes=drift_routes)
    return {
        "version": CORE_CALIBRATION_DRIFT_WATCH_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["drift_watch_ready"] else "blocked",
        "decision": decision,
        "observation_summary": summary,
        "drift_watch_policy": {
            "cadence": "on_new_calibration_evidence_only",
            "default_heavy_validation": False,
            "full_pytest_trigger": "explicit_release_or_full_freeze_decision_only",
            "full_518k_trigger": "explicit_pointer_or_distribution_drift_review_only",
            "chart_fact_mutation_allowed": False,
            "training_mutation_scope": [
                "candidate_weights",
                "question_strategy",
                "rule_weights",
                "expression_candidates",
            ],
            "boundary": "p3_watches_drift_without_running_default_heavy_gates",
        },
        "calibration_evidence": evidence_rows,
        "drift_routes": drift_routes,
        "route_matrix": _route_matrix(),
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": decision["focused_module_fix_required"],
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p3_routes_drift_to_focused_modules_without_reopening_all_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p3_drift_watch_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p3_establishes_core_calibration_drift_watch_without_full_pytest",
    }


def _observation_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    monitoring = payload.get("monitoring_evidence_summary", {})
    monitoring = monitoring if isinstance(monitoring, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "observation_summary_ready": bool(decision.get("observation_summary_ready")),
        "stable_observation_count": int(decision.get("stable_observation_count", 0) or 0),
        "needs_review_observation_count": int(decision.get("needs_review_observation_count", 0) or 0),
        "needs_review_check_ids": decision.get("needs_review_check_ids", []) if isinstance(decision.get("needs_review_check_ids"), list) else [],
        "regression_detected": bool(decision.get("regression_detected")),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "p1_passed_check_count": int(monitoring.get("passed_check_count", 0) or 0),
        "p1_required_check_count": int(monitoring.get("required_check_count", 0) or 0),
    }


def _normalize_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    check_id = str(row.get("check_id") or "")
    status = str(row.get("status") or row.get("evidence_status") or "stable")
    severity = str(row.get("severity") or ("review" if status != "stable" else "none"))
    return {
        "evidence_id": str(row.get("evidence_id") or f"p3_evidence_{check_id or 'unknown'}"),
        "check_id": check_id,
        "status": status,
        "severity": severity,
        "source": str(row.get("source") or "manual_or_future_calibration_evidence"),
        "summary": str(row.get("summary") or ""),
        "chart_fact_mutation_allowed": bool(row.get("chart_fact_mutation_allowed", False)),
        "pointer_write_requested": bool(row.get("pointer_write_requested", False)),
    }


def _drift_routes(*, summary: Mapping[str, Any], evidence_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    route_check_ids = set(str(check_id) for check_id in summary.get("needs_review_check_ids", []))
    for row in evidence_rows:
        if row["status"] != "stable" or row["severity"] not in {"none", "info"}:
            route_check_ids.add(row["check_id"])
    routes = []
    for check_id in sorted(route_check_ids):
        route = DRIFT_ROUTE_MAP.get(check_id, {"module_targets": ["M7"], "routing_scope": "unmapped_calibration_evidence_review"})
        routes.append(
            {
                "check_id": check_id,
                "module_targets": route["module_targets"],
                "routing_scope": route["routing_scope"],
                "routing_action": "focused_module_fix_review",
                "reopen_all_core_modules": False,
            }
        )
    return routes


def _decision(
    *,
    summary: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
    drift_routes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    if summary["source_version"] != CORE_CALIBRATION_OBSERVATION_SUMMARY_VERSION:
        blockers.append("p2_observation_summary_missing")
    if not summary["observation_summary_ready"]:
        blockers.append("p2_observation_summary_not_ready")
    if summary["regression_detected"]:
        blockers.append("p2_regression_detected")
    if summary["focused_module_fix_required"]:
        blockers.append("p2_focused_module_fix_required")
    if summary["full_pytest_required"] or summary["full_518k_required"]:
        blockers.append("p2_requested_heavy_validation")
    if summary["policy_pointer_promotion_allowed"] or summary["pointer_write_performed"]:
        blockers.append("p2_pointer_boundary_violation")
    if summary["chart_fact_mutation_allowed"]:
        blockers.append("p2_chart_fact_mutation_boundary_violation")
    if any(row["chart_fact_mutation_allowed"] for row in evidence_rows):
        blockers.append("calibration_evidence_requests_chart_fact_mutation")
    if any(row["pointer_write_requested"] for row in evidence_rows):
        blockers.append("calibration_evidence_requests_pointer_write")
    drift_detected = bool(drift_routes)
    ready = not blockers and not drift_detected
    return {
        "drift_watch_ready": ready,
        "decision_status": "core_calibration_drift_watch_ready" if ready else "core_calibration_drift_watch_blocked",
        "drift_detected": drift_detected,
        "drift_route_count": len(drift_routes),
        "focused_module_fix_required": drift_detected,
        "continue_lightweight_watch": ready,
        "new_evidence_count": len(evidence_rows),
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P2 observations are stable and no new drift evidence exists; keep lightweight drift watch active."
            if ready
            else "Calibration drift or boundary pressure exists; route only concrete evidence to focused module review."
        ),
    }


def _route_matrix() -> list[dict[str, Any]]:
    return [
        {"check_id": check_id, **route}
        for check_id, route in sorted(DRIFT_ROUTE_MAP.items())
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["drift_watch_ready"]:
        return {
            "task_id": "P4",
            "title": "Focused Core Calibration Evidence Queue",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "collect only new calibration evidence",
                "batch evidence by M1-M8 module target",
                "keep heavy validation and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P3-FR",
        "title": "Core Calibration Drift Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect concrete drift routes",
            "open focused module fixes only for routed evidence",
            "do not reopen frozen M1-M8 globally",
        ],
    }
