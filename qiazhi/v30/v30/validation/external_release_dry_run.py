from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from v30.validation.mainline_selection import MAINLINE_SELECTION_VERSION, run_mainline_selection
from v30.validation.release_boundary_finalization import RELEASE_BOUNDARY_FINALIZATION_VERSION


EXTERNAL_RELEASE_DRY_RUN_VERSION = "v30.external_release_dry_run.v1"
FullPytestDecision = Literal["defer", "record_passed", "record_failed"]


def run_external_release_dry_run(
    *,
    sample_limit: int = 8,
    full_pytest_decision: FullPytestDecision = "defer",
) -> dict[str, Any]:
    mainline_selection = run_mainline_selection(sample_limit=sample_limit)
    return build_external_release_dry_run(
        mainline_selection=mainline_selection,
        release_boundary_finalization=_default_release_boundary_finalization(),
        full_pytest_decision=full_pytest_decision,
    )


def build_external_release_dry_run(
    *,
    mainline_selection: Mapping[str, Any],
    release_boundary_finalization: Mapping[str, Any] | None = None,
    full_pytest_decision: FullPytestDecision = "defer",
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    release_boundary_finalization = release_boundary_finalization or _default_release_boundary_finalization()
    selection_summary = _mainline_summary(mainline_selection)
    release_summary = _release_summary(release_boundary_finalization)
    full_pytest_summary = _full_pytest_summary(full_pytest_decision)
    decision = _decision(
        selection_summary=selection_summary,
        release_summary=release_summary,
        full_pytest_summary=full_pytest_summary,
    )
    return {
        "version": EXTERNAL_RELEASE_DRY_RUN_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["dry_run_review_completed"] else "blocked",
        "decision": decision,
        "mainline_selection_summary": selection_summary,
        "release_boundary_summary": release_summary,
        "full_pytest_decision_summary": full_pytest_summary,
        "external_release_requirements": {
            "full_pytest_required_before_external_release": True,
            "full_518k_required_before_external_release": False,
            "manual_policy_pointer_promotion_required": True,
            "operator_release_approval_required": True,
            "boundary": "external_release_requires_explicit_operator_gates",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "r13_dry_run_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "r13_records_external_release_dry_run_without_running_full_pytest_by_default",
    }


def _default_release_boundary_finalization() -> dict[str, Any]:
    return {
        "version": RELEASE_BOUNDARY_FINALIZATION_VERSION,
        "decision": {
            "internal_release_candidate_finalized": True,
            "external_release_ready": False,
            "full_pytest_run_recorded": False,
            "full_pytest_required_before_external_release": True,
            "full_518k_required_before_external_release": False,
            "policy_pointer_promotion_allowed": False,
            "decision_status": "internal_release_candidate_finalized",
            "blockers": [],
        },
    }


def _mainline_summary(mainline_selection: Mapping[str, Any]) -> dict[str, Any]:
    decision = mainline_selection.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    next_selection = mainline_selection.get("next_mainline_selection", {})
    next_selection = next_selection if isinstance(next_selection, dict) else {}
    return {
        "version": str(mainline_selection.get("version") or ""),
        "status": str(mainline_selection.get("status") or ""),
        "selected_task_id": str(decision.get("selected_task_id") or next_selection.get("task_id") or ""),
        "selected_track": str(decision.get("selected_track") or next_selection.get("selected_track") or ""),
        "full_pytest_run_now": bool(decision.get("full_pytest_run_now")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _release_summary(finalization: Mapping[str, Any]) -> dict[str, Any]:
    decision = finalization.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "version": str(finalization.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "internal_release_candidate_finalized": bool(decision.get("internal_release_candidate_finalized")),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "full_pytest_run_recorded": bool(decision.get("full_pytest_run_recorded")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _full_pytest_summary(full_pytest_decision: FullPytestDecision) -> dict[str, Any]:
    status = {
        "defer": "deferred",
        "record_passed": "passed",
        "record_failed": "failed",
    }[full_pytest_decision]
    return {
        "operator_decision": full_pytest_decision,
        "status": status,
        "run_recorded": full_pytest_decision != "defer",
        "passed": full_pytest_decision == "record_passed",
        "failed": full_pytest_decision == "record_failed",
        "boundary": "full_pytest_is_explicit_release_boundary_evidence_not_default_iteration",
    }


def _decision(
    *,
    selection_summary: Mapping[str, Any],
    release_summary: Mapping[str, Any],
    full_pytest_summary: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if selection_summary.get("version") != MAINLINE_SELECTION_VERSION:
        blockers.append("m0_mainline_selection_missing")
    if selection_summary.get("selected_task_id") != "R13":
        blockers.append("r13_not_selected_by_m0")
    if selection_summary.get("full_pytest_run_now"):
        blockers.append("unexpected_full_pytest_requested_by_m0")
    if selection_summary.get("policy_pointer_promotion_allowed"):
        blockers.append("unexpected_policy_promotion_allowed_by_m0")
    if selection_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_allowed_by_m0")
    if not release_summary.get("internal_release_candidate_finalized"):
        blockers.append("internal_release_candidate_not_finalized")
    if release_summary.get("policy_pointer_promotion_allowed"):
        blockers.append("release_boundary_allows_policy_promotion")
    if full_pytest_summary.get("failed"):
        blockers.append("full_pytest_failed")

    dry_run_completed = not blockers
    external_ready = dry_run_completed and bool(full_pytest_summary.get("passed"))
    status = (
        "external_release_ready_after_full_pytest"
        if external_ready
        else "external_release_dry_run_deferred_full_pytest"
        if dry_run_completed
        else "external_release_dry_run_blocked"
    )
    return {
        "dry_run_review_completed": dry_run_completed,
        "external_release_ready": external_ready,
        "full_pytest_deferred": full_pytest_summary.get("operator_decision") == "defer",
        "full_pytest_required_before_external_release": True,
        "full_518k_required_before_external_release": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": status,
        "blockers": blockers,
        "rationale": (
            "R13 reviewed the external release boundary and explicitly deferred full pytest; external release remains not ready."
            if dry_run_completed and not external_ready
            else "R13 records full pytest passed, but policy pointer promotion and final release approval remain explicit operator gates."
            if external_ready
            else "R13 needs the listed blockers closed before completing the dry run."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["external_release_ready"]:
        return {
            "task_id": "R14",
            "title": "Manual External Release Approval And Pointer-Promotion Decision",
            "selected_track": "external_release_approval",
            "scope": [
                "review full pytest evidence",
                "decide whether to approve external release",
                "decide policy pointer promotion through a separate explicit operator command",
            ],
        }
    if decision["dry_run_review_completed"]:
        return {
            "task_id": "R14",
            "title": "External Release Full Pytest Execution Decision",
            "selected_track": "external_release_boundary",
            "scope": [
                "run full pytest only when explicitly approved for external release",
                "keep policy pointer promotion disabled until a separate manual decision",
                "keep M1-M8 frozen unless release evidence exposes a concrete regression",
            ],
        }
    return {
        "task_id": "R13",
        "title": "External Release Dry Run Gap Closure",
        "selected_track": "external_release_boundary",
        "scope": [
            "restore M0 and R12 evidence",
            "rerun R13 dry run",
            "do not promote policy pointers while blocked",
        ],
    }
