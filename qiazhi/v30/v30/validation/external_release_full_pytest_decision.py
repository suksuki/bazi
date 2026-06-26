from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from v30.validation.external_release_dry_run import (
    EXTERNAL_RELEASE_DRY_RUN_VERSION,
    run_external_release_dry_run,
)


EXTERNAL_RELEASE_FULL_PYTEST_DECISION_VERSION = "v30.external_release_full_pytest_decision.v1"
FullPytestExecutionDecision = Literal["defer", "record_passed", "record_failed"]


def run_external_release_full_pytest_decision(
    *,
    sample_limit: int = 8,
    full_pytest_decision: FullPytestExecutionDecision = "defer",
) -> dict[str, Any]:
    dry_run = run_external_release_dry_run(
        sample_limit=sample_limit,
        full_pytest_decision="defer",
    )
    return build_external_release_full_pytest_decision(
        external_release_dry_run=dry_run,
        full_pytest_decision=full_pytest_decision,
    )


def build_external_release_full_pytest_decision(
    *,
    external_release_dry_run: Mapping[str, Any],
    full_pytest_decision: FullPytestExecutionDecision = "defer",
) -> dict[str, Any]:
    decided_at = datetime.now(timezone.utc)
    dry_run_summary = _dry_run_summary(external_release_dry_run)
    full_pytest_summary = _full_pytest_summary(full_pytest_decision)
    decision = _decision(dry_run_summary=dry_run_summary, full_pytest_summary=full_pytest_summary)
    return {
        "version": EXTERNAL_RELEASE_FULL_PYTEST_DECISION_VERSION,
        "decided_at": decided_at.isoformat(),
        "status": "completed" if decision["full_pytest_decision_recorded"] else "blocked",
        "decision": decision,
        "external_release_dry_run_summary": dry_run_summary,
        "full_pytest_execution_summary": full_pytest_summary,
        "external_release_requirements": {
            "full_pytest_required_before_external_release": True,
            "full_518k_required_before_external_release": False,
            "manual_policy_pointer_promotion_required": True,
            "operator_release_approval_required": True,
            "boundary": "r14_records_full_pytest_decision_without_running_it_implicitly",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "r14_does_not_promote_policy_or_mutate_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "r14_makes_full_pytest_execution_explicit_and_keeps_external_release_blocked_when_deferred",
    }


def _dry_run_summary(dry_run: Mapping[str, Any]) -> dict[str, Any]:
    decision = dry_run.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    policy = dry_run.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    return {
        "version": str(dry_run.get("version") or ""),
        "status": str(dry_run.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "dry_run_review_completed": bool(decision.get("dry_run_review_completed")),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "full_pytest_deferred": bool(decision.get("full_pytest_deferred")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "pointer_write_allowed": bool(policy.get("pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _full_pytest_summary(full_pytest_decision: FullPytestExecutionDecision) -> dict[str, Any]:
    status = {
        "defer": "deferred",
        "record_passed": "passed",
        "record_failed": "failed",
    }[full_pytest_decision]
    return {
        "operator_decision": full_pytest_decision,
        "status": status,
        "run_requested_by_r14": full_pytest_decision != "defer",
        "run_recorded": full_pytest_decision != "defer",
        "passed": full_pytest_decision == "record_passed",
        "failed": full_pytest_decision == "record_failed",
        "boundary": "full_pytest_must_be_run_outside_default_iteration_before_recording_pass_or_fail",
    }


def _decision(
    *,
    dry_run_summary: Mapping[str, Any],
    full_pytest_summary: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if dry_run_summary.get("version") != EXTERNAL_RELEASE_DRY_RUN_VERSION:
        blockers.append("r13_dry_run_missing")
    if not dry_run_summary.get("dry_run_review_completed"):
        blockers.append("r13_dry_run_not_completed")
    if dry_run_summary.get("policy_pointer_promotion_allowed") or dry_run_summary.get("pointer_write_allowed"):
        blockers.append("unexpected_policy_pointer_permission")
    if dry_run_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_permission")
    if full_pytest_summary.get("failed"):
        blockers.append("full_pytest_failed")

    recorded = not blockers
    external_ready = recorded and bool(full_pytest_summary.get("passed"))
    status = (
        "external_release_full_pytest_passed"
        if external_ready
        else "external_release_full_pytest_deferred"
        if recorded
        else "external_release_full_pytest_decision_blocked"
    )
    return {
        "full_pytest_decision_recorded": recorded,
        "external_release_ready": external_ready,
        "external_release_blocked": not external_ready,
        "full_pytest_deferred": full_pytest_summary.get("operator_decision") == "defer",
        "full_pytest_required_before_external_release": True,
        "full_518k_required_before_external_release": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": status,
        "blockers": blockers,
        "rationale": (
            "R14 explicitly deferred full pytest; external release remains blocked and policy pointers remain unchanged."
            if recorded and not external_ready
            else "R14 records full pytest passed; external release can move to manual approval, while pointer promotion remains separate."
            if external_ready
            else "R14 needs the listed blockers closed before recording the full pytest execution decision."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["external_release_ready"]:
        return {
            "task_id": "R15",
            "title": "Manual External Release Approval And Pointer-Promotion Decision",
            "selected_track": "external_release_approval",
            "scope": [
                "review recorded full pytest pass evidence",
                "decide external release approval explicitly",
                "decide policy pointer promotion through a separate manual operator command",
            ],
        }
    if decision["full_pytest_decision_recorded"]:
        return {
            "task_id": "R15",
            "title": "External Release Blocked Pending Full Pytest",
            "selected_track": "external_release_boundary",
            "scope": [
                "run full pytest only when explicitly approved",
                "keep external release blocked while full pytest is deferred",
                "keep policy pointer promotion disabled",
            ],
        }
    return {
        "task_id": "R14",
        "title": "External Release Full Pytest Decision Gap Closure",
        "selected_track": "external_release_boundary",
        "scope": [
            "restore R13 dry-run evidence",
            "rerun R14 full pytest decision",
            "do not promote policy pointers while blocked",
        ],
    }
