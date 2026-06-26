from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.policy.runtime_pointer import RuntimePointerStore
from v30.validation.targeted_calibration_pointer_decision import (
    build_targeted_calibration_pointer_decision,
    run_targeted_calibration_pointer_decision,
)


TARGETED_CALIBRATION_CLOSEOUT_VERSION = "v30.targeted_calibration_closeout.v1"


def run_targeted_calibration_closeout(
    *,
    sample_limit: int = 8,
    closeout_id: str | None = None,
    store: RuntimePointerStore | None = None,
) -> dict[str, Any]:
    store = store or RuntimePointerStore()
    pointer_decision = run_targeted_calibration_pointer_decision(
        operator_decision="defer",
        sample_limit=sample_limit,
        decision_id=closeout_id,
        store=store,
    )
    return build_targeted_calibration_closeout(
        pointer_decision=pointer_decision,
        store=store,
        closeout_id=closeout_id,
    )


def build_targeted_calibration_closeout(
    *,
    pointer_decision: Mapping[str, Any],
    store: RuntimePointerStore | None = None,
    closeout_id: str | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    store = store or RuntimePointerStore()
    pointer_summary = _pointer_decision_summary(pointer_decision)
    monitoring_checks = _monitoring_checks(pointer_summary)
    decision = _decision(pointer_summary=pointer_summary, monitoring_checks=monitoring_checks)
    return {
        "version": TARGETED_CALIBRATION_CLOSEOUT_VERSION,
        "closeout_id": closeout_id or f"v30.targeted_calibration.closeout.{closed_at.strftime('%Y%m%d%H%M%S')}",
        "closed_at": closed_at.isoformat(),
        "status": "completed",
        "decision": decision,
        "pointer_decision_summary": pointer_summary,
        "active_pointer_snapshot": _active_pointer_snapshot(store),
        "evidence_lineage": {
            "f1": "v30.frozen_core_calibration_review.v1",
            "f2": "v30.targeted_calibration_candidate_review.v1",
            "f3": "v30.targeted_calibration_validation_gate.v1",
            "f4": "v30.targeted_calibration_pointer_review.v1",
            "f5": "v30.targeted_calibration_pointer_decision.v1",
            "boundary": "evidence_lineage_is_retained_for_future_explicit_promotion_request",
        },
        "monitoring_baseline": {
            "check_count": len(monitoring_checks),
            "checks": monitoring_checks,
            "recommended_interval": "targeted_before_next_calibration_or_release_gate",
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "monitoring_baseline_is_lightweight_and_does_not_reopen_frozen_core",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "f6_closeout_records_no_promotion_and_no_core_reopen",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "targeted_calibration_closeout_records_monitoring_without_mutating_policy_or_chart_facts",
    }


def _pointer_decision_summary(pointer_decision: Mapping[str, Any]) -> dict[str, Any]:
    decision = pointer_decision.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    write = pointer_decision.get("pointer_write_summary", {})
    write = write if isinstance(write, dict) else {}
    return {
        "version": str(pointer_decision.get("version") or ""),
        "decision_id": str(pointer_decision.get("decision_id") or ""),
        "operator_decision": str(pointer_decision.get("operator_decision") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "pointer_decision_recorded": bool(decision.get("pointer_decision_recorded")),
        "operator_deferred_promotion": bool(decision.get("operator_deferred_promotion")),
        "pointer_write_performed": bool(write.get("pointer_write_performed")),
        "changed_pointer_count": int(write.get("changed_pointer_count", 0) or 0),
    }


def _active_pointer_snapshot(store: RuntimePointerStore) -> dict[str, str]:
    families = ("structure_policy", "rule_policy", "question_policy", "answer_policy")
    return store.active_versions(families)


def _monitoring_checks(pointer_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "m1_m8_frozen_scope",
            "command": "python3 scripts/run_frozen_core_calibration_review.py",
            "required_status": "ready_for_targeted_calibration_iteration",
            "purpose": "confirm frozen core calibration baseline remains ready",
        },
        {
            "check_id": "targeted_candidate_review",
            "command": "python3 scripts/run_targeted_calibration_candidate_review.py",
            "required_status": "ready_for_validation_gate_review",
            "purpose": "confirm candidate tracks remain complete without fact mutation",
        },
        {
            "check_id": "targeted_validation_gate",
            "command": "python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 8",
            "required_status": "ready_for_policy_pointer_review",
            "purpose": "confirm synthetic all and 518K sample remain clean under candidate overrides",
        },
        {
            "check_id": "pointer_decision_no_write",
            "command": "python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision defer",
            "required_status": "pointer_promotion_deferred",
            "purpose": "confirm defer decision keeps active pointers unchanged",
            "latest_pointer_write_performed": bool(pointer_summary.get("pointer_write_performed")),
        },
    ]


def _decision(*, pointer_summary: Mapping[str, Any], monitoring_checks: list[dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    if not pointer_summary.get("pointer_decision_recorded"):
        blockers.append("f5_pointer_decision_not_recorded")
    if not pointer_summary.get("operator_deferred_promotion"):
        blockers.append("pointer_promotion_not_deferred")
    if pointer_summary.get("pointer_write_performed"):
        blockers.append("unexpected_pointer_write")
    if int(pointer_summary.get("changed_pointer_count", 0) or 0) != 0:
        blockers.append("active_pointer_changed")
    if len(monitoring_checks) < 4:
        blockers.append("monitoring_check_count_low")
    ready = not blockers
    return {
        "closeout_ready": ready,
        "targeted_calibration_track_closed": ready,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "targeted_calibration_closed_with_no_promotion" if ready else "targeted_calibration_closeout_blocked",
        "blockers": blockers,
        "rationale": (
            "Targeted calibration is closed with promotion deferred; monitoring checks are defined and no active pointers changed."
            if ready
            else "Targeted calibration closeout needs the listed blockers closed before the track can be marked closed."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["closeout_ready"]:
        return {
            "task_id": "M0",
            "title": "Mainline Selection After Targeted Calibration Closeout",
            "selected_track": "mainline_selection",
            "scope": [
                "choose next mainline explicitly: product usability, release boundary, or new calibration cycle",
                "keep F1-F6 evidence available for future explicit pointer promotion",
                "keep frozen M1-M8 core sealed unless targeted monitoring exposes a regression",
            ],
        }
    return {
        "task_id": "F6",
        "title": "Targeted Calibration Closeout Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "restore F5 defer decision evidence",
            "prove no active pointer changed",
            "complete monitoring baseline",
        ],
    }
