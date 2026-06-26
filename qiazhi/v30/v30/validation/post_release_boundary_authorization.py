from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from v30.validation.external_release_blocked_status import (
    EXTERNAL_RELEASE_BLOCKED_STATUS_VERSION,
    run_external_release_blocked_status,
)


POST_RELEASE_BOUNDARY_AUTHORIZATION_VERSION = "v30.post_release_boundary_authorization.v1"
AuthorizationDecision = Literal["pause", "authorize_full_pytest"]


def run_post_release_boundary_authorization(
    *,
    sample_limit: int = 8,
    authorization_decision: AuthorizationDecision = "pause",
) -> dict[str, Any]:
    blocked_status = run_external_release_blocked_status(sample_limit=sample_limit)
    return build_post_release_boundary_authorization(
        external_release_blocked_status=blocked_status,
        authorization_decision=authorization_decision,
    )


def build_post_release_boundary_authorization(
    *,
    external_release_blocked_status: Mapping[str, Any],
    authorization_decision: AuthorizationDecision = "pause",
) -> dict[str, Any]:
    decided_at = datetime.now(timezone.utc)
    blocked_summary = _blocked_status_summary(external_release_blocked_status)
    authorization = _authorization_summary(authorization_decision)
    decision = _decision(blocked_summary=blocked_summary, authorization=authorization)
    return {
        "version": POST_RELEASE_BOUNDARY_AUTHORIZATION_VERSION,
        "decided_at": decided_at.isoformat(),
        "status": "completed" if decision["authorization_recorded"] else "blocked",
        "decision": decision,
        "external_release_blocked_summary": blocked_summary,
        "authorization_summary": authorization,
        "release_boundary_state": {
            "external_release_allowed": False,
            "external_release_ready": False,
            "release_boundary_paused": decision["release_boundary_paused"],
            "full_pytest_authorized": decision["full_pytest_authorized"],
            "boundary": "r16_keeps_release_boundary_explicit",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "r16_authorization_does_not_release_or_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "r16_records_pause_or_full_pytest_authorization_without_running_full_pytest",
    }


def _blocked_status_summary(blocked_status: Mapping[str, Any]) -> dict[str, Any]:
    decision = blocked_status.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    policy = blocked_status.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    release_blockers = blocked_status.get("release_blockers", [])
    return {
        "version": str(blocked_status.get("version") or ""),
        "status": str(blocked_status.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "external_release_blocked": bool(decision.get("external_release_blocked")),
        "full_pytest_deferred": bool(decision.get("full_pytest_deferred")),
        "release_blocker_count": len(release_blockers) if isinstance(release_blockers, list) else 0,
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "pointer_write_allowed": bool(policy.get("pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _authorization_summary(authorization_decision: AuthorizationDecision) -> dict[str, Any]:
    return {
        "operator_decision": authorization_decision,
        "pause_release_boundary": authorization_decision == "pause",
        "authorize_full_pytest": authorization_decision == "authorize_full_pytest",
        "full_pytest_run_triggered": False,
        "boundary": "authorization_records_intent_but_does_not_execute_full_pytest",
    }


def _decision(
    *,
    blocked_summary: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if blocked_summary.get("version") != EXTERNAL_RELEASE_BLOCKED_STATUS_VERSION:
        blockers.append("r15_blocked_status_missing")
    if not blocked_summary.get("external_release_blocked"):
        blockers.append("external_release_not_blocked")
    if blocked_summary.get("external_release_ready"):
        blockers.append("external_release_unexpectedly_ready")
    if blocked_summary.get("policy_pointer_promotion_allowed") or blocked_summary.get("pointer_write_allowed"):
        blockers.append("unexpected_policy_pointer_permission")
    if blocked_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_permission")

    recorded = not blockers
    full_pytest_authorized = recorded and bool(authorization.get("authorize_full_pytest"))
    paused = recorded and bool(authorization.get("pause_release_boundary"))
    status = (
        "full_pytest_authorized_pending_execution"
        if full_pytest_authorized
        else "release_boundary_paused_pending_full_pytest_authorization"
        if paused
        else "release_boundary_authorization_blocked"
    )
    return {
        "authorization_recorded": recorded,
        "release_boundary_paused": paused,
        "full_pytest_authorized": full_pytest_authorized,
        "full_pytest_run_triggered": False,
        "external_release_ready": False,
        "external_release_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": status,
        "blockers": blockers,
        "rationale": (
            "Release-boundary work is paused; full pytest remains deferred and external release stays blocked."
            if paused
            else "Full pytest is authorized but not executed by this review; execution must run in a separate explicit step."
            if full_pytest_authorized
            else "R16 needs the listed blockers closed before recording release-boundary authorization."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["full_pytest_authorized"]:
        return {
            "task_id": "R17",
            "title": "Execute Full Pytest Release Gate",
            "selected_track": "external_release_boundary",
            "scope": [
                "run full pytest explicitly",
                "record pass or fail evidence",
                "keep policy pointer promotion separate from release execution",
            ],
        }
    if decision["release_boundary_paused"]:
        return {
            "task_id": "M0",
            "title": "Mainline Selection After Release Boundary Pause",
            "selected_track": "mainline_selection",
            "scope": [
                "return to non-release mainline selection",
                "keep external release blocked until full pytest is authorized",
                "keep policy pointer promotion disabled",
            ],
        }
    return {
        "task_id": "R16",
        "title": "Post-Release-Boundary Authorization Gap Closure",
        "selected_track": "external_release_boundary",
        "scope": [
            "restore R15 blocked-status evidence",
            "rerun authorization review",
            "do not release or promote policy while blocked",
        ],
    }
