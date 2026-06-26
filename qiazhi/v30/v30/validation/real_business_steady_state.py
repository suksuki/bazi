from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.real_business_acceptance_closeout import run_real_business_acceptance_closeout


REAL_BUSINESS_STEADY_STATE_VERSION = "v30.real_business_steady_state.v1"


def run_real_business_steady_state() -> dict[str, Any]:
    closeout = run_real_business_acceptance_closeout()
    return build_real_business_steady_state(b6_acceptance_closeout=closeout)


def build_real_business_steady_state(*, b6_acceptance_closeout: Mapping[str, Any]) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    closeout_summary = _closeout_summary(b6_acceptance_closeout)
    steady_state_checks = _steady_state_checks(closeout_summary)
    decision = _decision(closeout_summary=closeout_summary, steady_state_checks=steady_state_checks)
    return {
        "version": REAL_BUSINESS_STEADY_STATE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["business_steady_state_ready"] else "blocked",
        "decision": decision,
        "b6_closeout_summary": closeout_summary,
        "steady_state_checks": steady_state_checks,
        "routine_business_gate": {
            "version": "v30.business_reading_steady_state_gate.v1",
            "default_gate": "B1-B5",
            "routine_command": "python3 scripts/run_real_business_api_contract_freeze.py",
            "closeout_command": "python3 scripts/run_real_business_acceptance_closeout.py",
            "customer_reading_path_required": True,
            "default_action": "serve_business_bazi_reading_with_frozen_gate",
            "business_track_auto_continue_allowed": False,
            "boundary": "s1_uses_b1_b5_as_routine_business_acceptance_gate",
        },
        "reopen_conditions": _reopen_conditions(),
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "business_track_auto_continue_allowed": False,
            "boundary": "s1_business_steady_state_is_read_only_without_release_or_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "s1_business_acceptance_steady_state_after_b6_closeout",
    }


def _closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    accepted_gate = payload.get("accepted_business_gate", {})
    accepted_gate = accepted_gate if isinstance(accepted_gate, Mapping) else {}
    policy = payload.get("policy_boundary", {})
    policy = policy if isinstance(policy, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "business_acceptance_closeout_ready": bool(decision.get("business_acceptance_closeout_ready")),
        "business_track_paused": bool(decision.get("business_track_paused")),
        "major_validation_requires_explicit_request": bool(
            decision.get("major_validation_requires_explicit_request")
        ),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "accepted_gate_version": str(accepted_gate.get("version") or ""),
        "accepted_gate_status": str(accepted_gate.get("gate_status") or ""),
        "required_tasks": [str(row) for row in accepted_gate.get("required_tasks", [])]
        if isinstance(accepted_gate.get("required_tasks"), list) else [],
        "default_validation_command": str(accepted_gate.get("default_validation_command") or ""),
        "major_validation_gate_explicit": bool(accepted_gate.get("major_validation_requires_explicit_request")),
        "full_pytest_default": bool(accepted_gate.get("full_pytest_default")),
        "full_518k_default": bool(accepted_gate.get("full_518k_default")),
        "external_release_default": bool(accepted_gate.get("external_release_default")),
        "policy_pointer_promotion_default": bool(accepted_gate.get("policy_pointer_promotion_default")),
        "gate_chart_fact_mutation_allowed": bool(accepted_gate.get("chart_fact_mutation_allowed")),
        "external_release_allowed": bool(policy.get("external_release_allowed")),
        "full_pytest_allowed_by_default": bool(policy.get("full_pytest_run_allowed_by_default")),
        "full_518k_allowed_by_default": bool(policy.get("full_518k_run_allowed_by_default")),
        "pointer_write_allowed": bool(policy.get("pointer_write_allowed")),
        "business_track_auto_continue_allowed": bool(policy.get("business_track_auto_continue_allowed")),
    }


def _steady_state_checks(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "b6_closeout_ready",
            "passed": (
                summary["version"] == "v30.real_business_acceptance_closeout.v1"
                and summary["business_acceptance_closeout_ready"]
                and summary["decision_status"] == "b6_business_acceptance_closed"
                and summary["business_track_paused"]
            ),
            "expected": "B6 closeout completed and business track paused",
        },
        {
            "check_id": "default_business_gate_recorded",
            "passed": (
                summary["accepted_gate_version"] == "v30.business_reading_acceptance_gate.v1"
                and summary["accepted_gate_status"] == "frozen_default_gate"
                and summary["required_tasks"] == ["B1", "B2", "B3", "B4", "B5"]
                and summary["default_validation_command"] == "python3 scripts/run_real_business_api_contract_freeze.py"
            ),
            "expected": "B1-B5 are the frozen default business gate",
        },
        {
            "check_id": "major_validation_explicit_only",
            "passed": (
                summary["major_validation_requires_explicit_request"]
                and summary["major_validation_gate_explicit"]
                and not summary["full_pytest_required"]
                and not summary["full_518k_required"]
                and not summary["full_pytest_default"]
                and not summary["full_518k_default"]
                and not summary["full_pytest_allowed_by_default"]
                and not summary["full_518k_allowed_by_default"]
            ),
            "expected": "full pytest and 518K remain explicit, not routine",
        },
        {
            "check_id": "no_release_pointer_or_chart_mutation",
            "passed": (
                not summary["external_release_ready"]
                and not summary["external_release_default"]
                and not summary["external_release_allowed"]
                and not summary["policy_pointer_promotion_allowed"]
                and not summary["policy_pointer_promotion_default"]
                and not summary["pointer_write_allowed"]
                and not summary["chart_fact_mutation_allowed"]
                and not summary["gate_chart_fact_mutation_allowed"]
            ),
            "expected": "S1 does not authorize release, pointer writes, or chart-fact mutation",
        },
        {
            "check_id": "business_track_no_auto_continue",
            "passed": not summary["business_track_auto_continue_allowed"],
            "expected": "no further B-track task starts by default",
        },
    ]


def _decision(
    *,
    closeout_summary: Mapping[str, Any],
    steady_state_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in steady_state_checks if not row.get("passed")]
    blockers: list[str] = []
    if closeout_summary["version"] != "v30.real_business_acceptance_closeout.v1":
        blockers.append("b6_closeout_missing")
    if not closeout_summary["business_acceptance_closeout_ready"]:
        blockers.append("b6_closeout_not_ready")
    if not closeout_summary["business_track_paused"]:
        blockers.append("business_track_not_paused")
    if closeout_summary["full_pytest_required"] or closeout_summary["full_518k_required"]:
        blockers.append("unexpected_heavy_validation_request")
    if closeout_summary["external_release_ready"] or closeout_summary["external_release_allowed"]:
        blockers.append("unexpected_external_release_pressure")
    if closeout_summary["policy_pointer_promotion_allowed"] or closeout_summary["pointer_write_allowed"]:
        blockers.append("unexpected_pointer_pressure")
    if closeout_summary["chart_fact_mutation_allowed"] or closeout_summary["gate_chart_fact_mutation_allowed"]:
        blockers.append("unexpected_chart_fact_mutation_pressure")
    if failed:
        blockers.append("business_steady_state_checks_failed")
    ready = not blockers
    return {
        "business_steady_state_ready": ready,
        "decision_status": "s1_business_acceptance_steady_state_ready"
        if ready else "s1_business_acceptance_steady_state_blocked",
        "steady_state_check_count": len(steady_state_checks),
        "passed_steady_state_check_count": sum(1 for row in steady_state_checks if row["passed"]),
        "failed_steady_state_check_ids": failed,
        "routine_business_gate_ready": ready,
        "business_track_paused": bool(closeout_summary["business_track_paused"] and ready),
        "waiting_for_new_business_evidence": ready,
        "major_validation_requires_explicit_request": True,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "Business Bazi reading acceptance is in steady state: use the frozen B1-B5 gate routinely and wait for explicit new evidence or release-boundary request."
            if ready
            else "S1 cannot enter steady state until B6 closeout and boundary blockers are resolved."
        ),
    }


def _reopen_conditions() -> list[dict[str, Any]]:
    return [
        {
            "condition": "new_real_business_failure",
            "route": "business_regression_candidate_review",
            "description": "a ready real-case customer reading fails B1-B5 acceptance",
        },
        {
            "condition": "api_contract_change_request",
            "route": "B5 Business Reading API Contract Freeze",
            "description": "new customer surface fields are additive and must preserve frozen required fields",
        },
        {
            "condition": "boundary_or_blocked_input_failure",
            "route": "B4 Business Reading Boundary And Blocked Input Regression",
            "description": "pending or blocked BirthInput projection becomes fake-ready or mutates chart facts",
        },
        {
            "condition": "explicit_major_validation_request",
            "route": "major_validation_or_release_boundary_track",
            "description": "full pytest, full 518K, external release, or pointer decision remains separate",
        },
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["business_steady_state_ready"]:
        return {
            "task_id": "S1-WAIT",
            "title": "Business Acceptance Steady State Await Evidence",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "serve routine business Bazi readings through the B1-B5 gate",
                "do not start another B-track task without new business evidence",
                "keep full pytest, full 518K, release, and pointer promotion explicit",
            ],
        }
    return {
        "task_id": "S1-FR",
        "title": "Business Acceptance Steady State Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "inspect failed S1 steady-state checks",
            "repair B6 closeout or frozen business gate blockers",
            "keep release and pointer promotion disabled while blocked",
        ],
    }
