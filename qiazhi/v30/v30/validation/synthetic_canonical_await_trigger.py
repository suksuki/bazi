from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_canonical_steady_state import (
    SYNTHETIC_CANONICAL_STEADY_STATE_VERSION,
    run_synthetic_canonical_steady_state,
)


SYNTHETIC_CANONICAL_AWAIT_TRIGGER_VERSION = "v30.synthetic_canonical_await_trigger.v1"

KNOWN_TRIGGER_IDS = {
    "rbd_change",
    "m3_change",
    "m5_change",
    "iq_change",
    "release_boundary",
}


def run_synthetic_canonical_await_trigger(
    *,
    active_triggers: list[str] | None = None,
) -> dict[str, Any]:
    steady_state = run_synthetic_canonical_steady_state()
    return build_synthetic_canonical_await_trigger(
        synthetic_canonical_steady_state=steady_state,
        active_triggers=active_triggers or [],
    )


def build_synthetic_canonical_await_trigger(
    *,
    synthetic_canonical_steady_state: Mapping[str, Any],
    active_triggers: list[str] | None = None,
) -> dict[str, Any]:
    recorded_at = datetime.now(timezone.utc)
    steady_summary = _steady_summary(synthetic_canonical_steady_state)
    trigger_summary = _trigger_summary(active_triggers or [])
    checks = _checks(steady_summary, trigger_summary)
    decision = _decision(checks, steady_summary, trigger_summary)
    return {
        "version": SYNTHETIC_CANONICAL_AWAIT_TRIGGER_VERSION,
        "recorded_at": recorded_at.isoformat(),
        "status": "completed" if decision["synthetic_canonical_await_trigger_ready"] else "blocked",
        "task": {
            "task_id": "SCAL-S3-WAIT",
            "title": "Synthetic Canonical Calibration Await Trigger",
            "scope": "record_wait_state_for_frozen_synthetic_canonical_gate_and_route_known_triggers",
        },
        "decision": decision,
        "steady_state_summary": steady_summary,
        "trigger_summary": trigger_summary,
        "wait_policy": {
            "current_state": "SCAL-S3-WAIT Synthetic Canonical Calibration Await Trigger",
            "default_action": "wait_without_reopening_modules_when_no_trigger_is_active",
            "trigger_entrypoint": "SCAL-S3 frozen routine gate",
            "trigger_command": "python3 scripts/run_synthetic_canonical_steady_state.py",
            "known_triggers": sorted(KNOWN_TRIGGER_IDS),
            "core_module_reopen_by_default": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "scal_s3_wait_records_trigger_state_without_running_heavy_gates_or_mutating_runtime",
        },
        "routine_cadence": {
            "routine_command": "python3 scripts/run_synthetic_canonical_await_trigger.py",
            "gate_command": "python3 scripts/run_synthetic_canonical_steady_state.py",
            "canonical_tier_command": "python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration",
            "major_node_commands_explicit_only": [
                "python3 scripts/run_synthetic_validation.py --tier all",
                "pytest -q",
                "python3 scripts/run_518k_validation.py --mode full --confirm-full",
            ],
        },
        "policy_boundary": {
            "uses_real_person_truth": False,
            "full_pytest_run_allowed_by_default": False,
            "synthetic_all_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "scal_s3_wait_is_a_status_artifact_not_new_calibration_or_release",
    }


def _steady_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    policy = _mapping(payload.get("policy_boundary"))
    routine_gate = _mapping(payload.get("routine_gate"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "synthetic_canonical_steady_state_ready": bool(decision.get("synthetic_canonical_steady_state_ready")),
        "routine_gate_ready": bool(decision.get("routine_gate_ready")),
        "case_count": int(decision.get("case_count", 0) or routine_gate.get("case_count", 0) or 0),
        "covered_family_count": int(decision.get("covered_family_count", 0) or routine_gate.get("family_count", 0) or 0),
        "gate_status": str(routine_gate.get("gate_status") or ""),
        "full_pytest_required": bool(policy.get("full_pytest_required")),
        "synthetic_all_required": bool(policy.get("synthetic_all_required")),
        "full_518k_required": bool(policy.get("full_518k_required")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
        "auto_apply_training_allowed": bool(policy.get("auto_apply_training_allowed")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
    }


def _trigger_summary(active_triggers: list[str]) -> dict[str, Any]:
    normalized = sorted({str(item) for item in active_triggers if str(item)})
    unknown = sorted(set(normalized) - KNOWN_TRIGGER_IDS)
    known_active = sorted(set(normalized) & KNOWN_TRIGGER_IDS)
    return {
        "active_trigger_ids": known_active,
        "unknown_trigger_ids": unknown,
        "active_trigger_count": len(known_active),
        "trigger_required": bool(known_active),
        "known_trigger_ids": sorted(KNOWN_TRIGGER_IDS),
    }


def _checks(steady_summary: Mapping[str, Any], trigger_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "scal_s3_steady_state_ready",
            "passed": (
                steady_summary["version"] == SYNTHETIC_CANONICAL_STEADY_STATE_VERSION
                and steady_summary["synthetic_canonical_steady_state_ready"]
                and steady_summary["routine_gate_ready"]
                and steady_summary["gate_status"] == "frozen_targeted_gate"
            ),
            "observed": steady_summary,
        },
        {
            "check_id": "canonical_gate_has_expected_coverage",
            "passed": int(steady_summary.get("case_count", 0) or 0) >= 16
            and int(steady_summary.get("covered_family_count", 0) or 0) >= 10,
            "observed": {
                "case_count": steady_summary.get("case_count"),
                "covered_family_count": steady_summary.get("covered_family_count"),
            },
        },
        {
            "check_id": "trigger_ids_are_known",
            "passed": not trigger_summary.get("unknown_trigger_ids"),
            "observed": trigger_summary,
        },
        {
            "check_id": "no_heavy_pointer_or_fact_mutation",
            "passed": (
                steady_summary.get("full_pytest_required") is False
                and steady_summary.get("synthetic_all_required") is False
                and steady_summary.get("full_518k_required") is False
                and steady_summary.get("chart_fact_mutation_allowed") is False
                and steady_summary.get("auto_apply_training_allowed") is False
                and steady_summary.get("policy_pointer_promotion_allowed") is False
            ),
            "observed": steady_summary,
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    steady_summary: Mapping[str, Any],
    trigger_summary: Mapping[str, Any],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    trigger_required = bool(trigger_summary.get("trigger_required"))
    return {
        "synthetic_canonical_await_trigger_ready": ready,
        "decision_status": "scal_s3_await_trigger_ready" if ready else "scal_s3_await_trigger_blocked",
        "waiting_for_synthetic_canonical_trigger": ready and not trigger_required,
        "synthetic_canonical_gate_run_required": ready and trigger_required,
        "active_trigger_ids": list(trigger_summary.get("active_trigger_ids", [])),
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "case_count": int(steady_summary.get("case_count", 0) or 0),
        "covered_family_count": int(steady_summary.get("covered_family_count", 0) or 0),
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "chart_fact_mutation_allowed": False,
        "auto_apply_training_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "blockers": ["synthetic_canonical_await_trigger_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("synthetic_canonical_gate_run_required"):
        return {
            "next_task": "Run Synthetic Canonical Gate",
            "reason": "Known trigger is active; re-run SCAL-S3 frozen routine gate.",
            "command": "python3 scripts/run_synthetic_canonical_steady_state.py",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    if decision.get("waiting_for_synthetic_canonical_trigger"):
        return {
            "next_task": "Await Synthetic Canonical Trigger",
            "reason": "No RBD/M3/M5/IQ/release-boundary trigger is active.",
            "command": "python3 scripts/run_synthetic_canonical_await_trigger.py",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "SCAL-S3-WAIT Remediation",
        "reason": "Repair failed wait-state checks before resuming trigger wait.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
