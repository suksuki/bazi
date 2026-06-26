from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.core_calibration_watch_closeout import (
    CORE_CALIBRATION_WATCH_CLOSEOUT_VERSION,
    run_core_calibration_watch_closeout,
)


CORE_MONITORING_CADENCE_BASELINE_VERSION = "v30.core_monitoring_cadence_baseline.v1"


def run_core_monitoring_cadence_baseline(*, sample_limit: int = 8) -> dict[str, Any]:
    closeout = run_core_calibration_watch_closeout(sample_limit=sample_limit)
    return build_core_monitoring_cadence_baseline(core_calibration_watch_closeout=closeout)


def build_core_monitoring_cadence_baseline(
    *,
    core_calibration_watch_closeout: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    closeout_summary = _closeout_summary(core_calibration_watch_closeout)
    cadence_rules = _cadence_rules()
    decision = _decision(closeout_summary=closeout_summary)
    return {
        "version": CORE_MONITORING_CADENCE_BASELINE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["cadence_baseline_ready"] else "blocked",
        "decision": decision,
        "closeout_summary": closeout_summary,
        "cadence_rules": cadence_rules,
        "trigger_matrix": _trigger_matrix(),
        "core_module_scope": {
            "m1_m8_frozen": True,
            "core_module_reopen_allowed": False,
            "focused_module_fix_required": False,
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "p7_documents_cadence_without_reopening_core_modules",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "p7_cadence_baseline_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "p7_establishes_core_monitoring_cadence_without_full_pytest",
    }


def _closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    cycle = payload.get("watch_cycle_summary", {})
    cycle = cycle if isinstance(cycle, dict) else {}
    return {
        "source_version": str(payload.get("version") or ""),
        "source_status": str(payload.get("status") or ""),
        "source_decision_status": str(decision.get("decision_status") or ""),
        "watch_closeout_ready": bool(decision.get("watch_closeout_ready")),
        "closeout_check_count": int(decision.get("closeout_check_count", 0) or 0),
        "passed_closeout_check_count": int(decision.get("passed_closeout_check_count", 0) or 0),
        "current_cycle_closed": bool(decision.get("current_cycle_closed")),
        "future_monitoring_ready": bool(decision.get("future_monitoring_ready")),
        "focused_module_fix_required": bool(decision.get("focused_module_fix_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "future_evidence_entrypoint": str(cycle.get("future_evidence_entrypoint") or "P4 Focused Core Calibration Evidence Queue"),
        "future_review_entrypoint": str(cycle.get("future_review_entrypoint") or "P5 Core Calibration Queue Review"),
    }


def _cadence_rules() -> dict[str, Any]:
    return {
        "default_cadence": "on_new_calibration_evidence_only",
        "routine_check": "read_only_status_projection",
        "new_evidence_entrypoint": "P4 Focused Core Calibration Evidence Queue",
        "queued_evidence_review": "P5 Core Calibration Queue Review",
        "watch_closeout": "P6 Core Calibration Watch Closeout",
        "full_pytest_trigger": "explicit_release_or_full_freeze_decision_only",
        "full_518k_trigger": "explicit_pointer_or_distribution_drift_review_only",
        "policy_pointer_trigger": "separate_explicit_operator_pointer_review_only",
        "chart_fact_mutation_trigger": "never_from_training_or_calibration_feedback",
        "boundary": "p7_cadence_uses_lightweight_monitoring_until_explicit_release_boundary",
    }


def _trigger_matrix() -> list[dict[str, Any]]:
    return [
        {
            "trigger": "no_new_evidence",
            "action": "keep_lightweight_watch_ready",
            "entrypoint": "read_only_status_projection",
            "full_pytest_allowed": False,
            "full_518k_allowed": False,
            "pointer_write_allowed": False,
        },
        {
            "trigger": "new_calibration_evidence",
            "action": "queue_by_module_target",
            "entrypoint": "P4 Focused Core Calibration Evidence Queue",
            "full_pytest_allowed": False,
            "full_518k_allowed": False,
            "pointer_write_allowed": False,
        },
        {
            "trigger": "queued_module_evidence",
            "action": "review_focused_candidates",
            "entrypoint": "P5 Core Calibration Queue Review",
            "full_pytest_allowed": False,
            "full_518k_allowed": False,
            "pointer_write_allowed": False,
        },
        {
            "trigger": "explicit_release_or_full_freeze_decision",
            "action": "run_release_scoped_heavy_validation",
            "entrypoint": "release_boundary_track",
            "full_pytest_allowed": True,
            "full_518k_allowed": False,
            "pointer_write_allowed": False,
        },
        {
            "trigger": "explicit_pointer_or_distribution_drift_review",
            "action": "run_pointer_scoped_distribution_validation",
            "entrypoint": "pointer_review_track",
            "full_pytest_allowed": False,
            "full_518k_allowed": True,
            "pointer_write_allowed": False,
        },
    ]


def _decision(*, closeout_summary: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if closeout_summary["source_version"] != CORE_CALIBRATION_WATCH_CLOSEOUT_VERSION:
        blockers.append("p6_watch_closeout_missing")
    if not closeout_summary["watch_closeout_ready"]:
        blockers.append("p6_watch_closeout_not_ready")
    if not closeout_summary["current_cycle_closed"]:
        blockers.append("p6_current_cycle_not_closed")
    if not closeout_summary["future_monitoring_ready"]:
        blockers.append("p6_future_monitoring_not_ready")
    if closeout_summary["focused_module_fix_required"]:
        blockers.append("p6_focused_module_fix_required")
    if closeout_summary["full_pytest_required"] or closeout_summary["full_518k_required"]:
        blockers.append("p6_requested_heavy_validation")
    if closeout_summary["policy_pointer_promotion_allowed"] or closeout_summary["pointer_write_performed"]:
        blockers.append("p6_pointer_boundary_violation")
    if closeout_summary["chart_fact_mutation_allowed"]:
        blockers.append("p6_chart_fact_mutation_boundary_violation")
    ready = not blockers
    return {
        "cadence_baseline_ready": ready,
        "decision_status": "core_monitoring_cadence_baseline_ready" if ready else "core_monitoring_cadence_baseline_blocked",
        "current_cycle_closed": bool(closeout_summary["current_cycle_closed"] and ready),
        "future_monitoring_ready": bool(closeout_summary["future_monitoring_ready"] and ready),
        "default_heavy_validation_allowed": False,
        "focused_module_fix_required": False,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "P6 closeout is complete; use lightweight monitoring until new evidence or an explicit release boundary appears."
            if ready
            else "Cadence baseline cannot be established until P6 closeout blockers are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["cadence_baseline_ready"]:
        return {
            "task_id": "P8",
            "title": "Core Monitoring Cadence Documentation Sync",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "sync cadence baseline across module and test docs",
                "keep future evidence routed through P4/P5",
                "keep heavy validation and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "P7-FR",
        "title": "Core Monitoring Cadence Baseline Failure Review",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "inspect P6 closeout blockers",
            "resolve monitoring readiness before cadence baseline",
            "do not reopen frozen M1-M8 globally",
        ],
    }
