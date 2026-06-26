from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.external_release_full_pytest_decision import (
    EXTERNAL_RELEASE_FULL_PYTEST_DECISION_VERSION,
    run_external_release_full_pytest_decision,
)


EXTERNAL_RELEASE_BLOCKED_STATUS_VERSION = "v30.external_release_blocked_status.v1"


def run_external_release_blocked_status(*, sample_limit: int = 8) -> dict[str, Any]:
    full_pytest_decision = run_external_release_full_pytest_decision(
        sample_limit=sample_limit,
        full_pytest_decision="defer",
    )
    return build_external_release_blocked_status(
        external_release_full_pytest_decision=full_pytest_decision,
    )


def build_external_release_blocked_status(
    *,
    external_release_full_pytest_decision: Mapping[str, Any],
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    pytest_summary = _pytest_decision_summary(external_release_full_pytest_decision)
    decision = _decision(pytest_summary)
    return {
        "version": EXTERNAL_RELEASE_BLOCKED_STATUS_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["blocked_status_recorded"] else "blocked",
        "decision": decision,
        "external_release_full_pytest_summary": pytest_summary,
        "release_blockers": _release_blockers(decision),
        "unblock_requirements": {
            "full_pytest_pass_required": True,
            "manual_external_release_approval_required": True,
            "manual_policy_pointer_promotion_required": True,
            "full_518k_required_by_default": False,
            "boundary": "r15_unblock_requires_explicit_release_evidence_not_background_work",
        },
        "policy_boundary": {
            "external_release_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "r15_blocked_status_does_not_release_or_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "r15_records_external_release_blocked_pending_full_pytest",
    }


def _pytest_decision_summary(full_pytest_decision: Mapping[str, Any]) -> dict[str, Any]:
    decision = full_pytest_decision.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    policy = full_pytest_decision.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    execution = full_pytest_decision.get("full_pytest_execution_summary", {})
    execution = execution if isinstance(execution, dict) else {}
    return {
        "version": str(full_pytest_decision.get("version") or ""),
        "status": str(full_pytest_decision.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "external_release_blocked": bool(decision.get("external_release_blocked")),
        "full_pytest_deferred": bool(decision.get("full_pytest_deferred")),
        "full_pytest_status": str(execution.get("status") or ""),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "pointer_write_allowed": bool(policy.get("pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _decision(pytest_summary: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if pytest_summary.get("version") != EXTERNAL_RELEASE_FULL_PYTEST_DECISION_VERSION:
        blockers.append("r14_full_pytest_decision_missing")
    if not pytest_summary.get("external_release_blocked"):
        blockers.append("external_release_not_blocked")
    if not pytest_summary.get("full_pytest_deferred"):
        blockers.append("full_pytest_not_deferred")
    if pytest_summary.get("external_release_ready"):
        blockers.append("external_release_unexpectedly_ready")
    if pytest_summary.get("policy_pointer_promotion_allowed") or pytest_summary.get("pointer_write_allowed"):
        blockers.append("unexpected_policy_pointer_permission")
    if pytest_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_permission")

    recorded = not blockers
    return {
        "blocked_status_recorded": recorded,
        "external_release_ready": False,
        "external_release_blocked": recorded,
        "full_pytest_deferred": bool(pytest_summary.get("full_pytest_deferred")),
        "full_pytest_required_before_external_release": True,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "external_release_blocked_pending_full_pytest" if recorded else "external_release_blocked_status_invalid",
        "blockers": blockers,
        "rationale": (
            "External release remains correctly blocked because full pytest is deferred; no policy pointers changed."
            if recorded
            else "External release blocked status needs the listed blockers resolved before it can be recorded."
        ),
    }


def _release_blockers(decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not decision["blocked_status_recorded"]:
        return [
            {
                "blocker_id": blocker,
                "status": "open",
                "required_action": "restore valid R14 full-pytest defer evidence before release-boundary review",
            }
            for blocker in decision["blockers"]
        ]
    return [
        {
            "blocker_id": "full_pytest_deferred",
            "status": "open",
            "required_action": "explicitly run full pytest and record passed evidence before external release",
        },
        {
            "blocker_id": "manual_release_approval_missing",
            "status": "open",
            "required_action": "record operator approval after full pytest passes",
        },
        {
            "blocker_id": "manual_policy_pointer_promotion_missing",
            "status": "open",
            "required_action": "keep pointer promotion separate from release approval unless explicitly requested",
        },
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["blocked_status_recorded"]:
        return {
            "task_id": "R16",
            "title": "Post-Release-Boundary Pause Or Full Pytest Authorization",
            "selected_track": "external_release_boundary",
            "scope": [
                "pause external release until full pytest is explicitly authorized",
                "keep targeted development on separate module/calibration tracks",
                "do not promote policy pointers while external release is blocked",
            ],
        }
    return {
        "task_id": "R15",
        "title": "External Release Blocked Status Gap Closure",
        "selected_track": "external_release_boundary",
        "scope": [
            "restore R14 defer evidence",
            "rerun blocked-status review",
            "do not approve release or promote policy while blocked",
        ],
    }
