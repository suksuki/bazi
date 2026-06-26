from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.release_boundary_finalization import RELEASE_BOUNDARY_FINALIZATION_VERSION
from v30.validation.targeted_calibration_closeout import (
    TARGETED_CALIBRATION_CLOSEOUT_VERSION,
    run_targeted_calibration_closeout,
)


MAINLINE_SELECTION_VERSION = "v30.mainline_selection.v1"


def run_mainline_selection(*, sample_limit: int = 8) -> dict[str, Any]:
    closeout = run_targeted_calibration_closeout(sample_limit=sample_limit)
    return build_mainline_selection(
        targeted_calibration_closeout=closeout,
        release_boundary_finalization=_default_release_boundary_finalization(),
    )


def build_mainline_selection(
    *,
    targeted_calibration_closeout: Mapping[str, Any],
    release_boundary_finalization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_at = datetime.now(timezone.utc)
    closeout_summary = _closeout_summary(targeted_calibration_closeout)
    release_boundary_finalization = release_boundary_finalization or _default_release_boundary_finalization()
    release_summary = _release_summary(release_boundary_finalization)
    decision = _decision(closeout_summary=closeout_summary, release_summary=release_summary)
    return {
        "version": MAINLINE_SELECTION_VERSION,
        "selected_at": selected_at.isoformat(),
        "status": "ready_for_next_mainline" if decision["mainline_selection_ready"] else "mainline_selection_blocked",
        "decision": decision,
        "core_completion_state": {
            "m1_m8_current_scope_complete": True,
            "m1_m8_reopen_allowed": False,
            "deterministic_chart_fact_mutation_allowed": False,
            "boundary": "m0_does_not_reopen_core_modules_or_mutate_chart_facts",
        },
        "targeted_calibration_summary": closeout_summary,
        "release_boundary_summary": release_summary,
        "next_mainline_selection": _next_selection(decision),
        "deferred_tracks": _deferred_tracks(),
        "verification_policy": {
            "full_pytest_default": False,
            "full_pytest_required_before_external_release": True,
            "full_518k_default": False,
            "targeted_tests_default": True,
            "boundary": "m0_selects_next_track_without_running_full_pytest_by_default",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "mainline_selection_is_read_only_and_does_not_promote_policy",
        },
        "boundary": "m0_selects_next_mainline_after_f6_without_mutating_policy_or_chart_facts",
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


def _closeout_summary(closeout: Mapping[str, Any]) -> dict[str, Any]:
    decision = closeout.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    monitoring = closeout.get("monitoring_baseline", {})
    monitoring = monitoring if isinstance(monitoring, dict) else {}
    policy = closeout.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    pointer = closeout.get("pointer_decision_summary", {})
    pointer = pointer if isinstance(pointer, dict) else {}
    return {
        "version": str(closeout.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "closeout_ready": bool(decision.get("closeout_ready")),
        "targeted_calibration_track_closed": bool(decision.get("targeted_calibration_track_closed")),
        "monitoring_check_count": int(monitoring.get("check_count", 0) or 0),
        "pointer_write_performed": bool(pointer.get("pointer_write_performed")),
        "changed_pointer_count": int(pointer.get("changed_pointer_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
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
        "full_pytest_required_before_external_release": bool(
            decision.get("full_pytest_required_before_external_release")
        ),
        "full_518k_required_before_external_release": bool(decision.get("full_518k_required_before_external_release")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
    }


def _decision(*, closeout_summary: Mapping[str, Any], release_summary: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if closeout_summary.get("version") != TARGETED_CALIBRATION_CLOSEOUT_VERSION:
        blockers.append("f6_closeout_version_missing")
    if not closeout_summary.get("closeout_ready"):
        blockers.append("f6_closeout_not_ready")
    if not closeout_summary.get("targeted_calibration_track_closed"):
        blockers.append("targeted_calibration_track_not_closed")
    if int(closeout_summary.get("monitoring_check_count", 0) or 0) < 4:
        blockers.append("targeted_monitoring_baseline_incomplete")
    if closeout_summary.get("pointer_write_performed") or int(closeout_summary.get("changed_pointer_count", 0) or 0):
        blockers.append("unexpected_pointer_write")
    if closeout_summary.get("policy_pointer_promotion_allowed"):
        blockers.append("unexpected_policy_promotion_allowed")
    if closeout_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_allowed")
    if not release_summary.get("internal_release_candidate_finalized"):
        blockers.append("release_boundary_not_finalized")
    if release_summary.get("policy_pointer_promotion_allowed"):
        blockers.append("release_boundary_allows_pointer_promotion")

    ready = not blockers
    return {
        "mainline_selection_ready": ready,
        "decision_status": "r13_external_release_dry_run_selected" if ready else "m0_mainline_selection_blocked",
        "selected_task_id": "R13" if ready else "M0",
        "selected_track": "external_release_boundary" if ready else "mainline_selection_gap_closure",
        "full_pytest_run_now": False,
        "full_pytest_required_before_external_release": True,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "F6 closed targeted calibration with no promotion and R12 finalized the internal release candidate; "
            "the next evidence-backed mainline is R13 external release dry run/full pytest decision."
            if ready
            else "M0 needs the listed blockers closed before selecting a new mainline."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["mainline_selection_ready"]:
        return {
            "task_id": "R13",
            "title": "External Release Dry Run And Full Pytest Decision",
            "selected_track": "external_release_boundary",
            "scope": [
                "run or explicitly defer full pytest for external release",
                "review policy pointer promotion as a manual operator action",
                "keep full 518K separate unless external production release requires it",
                "keep M1-M8 sealed unless targeted monitoring exposes a concrete regression",
            ],
            "explicit_non_goals": [
                "no speculative M1-M8 reopening",
                "no background policy pointer promotion",
                "no full pytest by default",
                "no full 518K by default",
                "no UI expansion under release-boundary work",
            ],
        }
    return {
        "task_id": "M0",
        "title": "Mainline Selection Gap Closure",
        "selected_track": "mainline_selection_gap_closure",
        "scope": [
            "restore F6 closeout evidence",
            "confirm release-boundary finalization evidence",
            "rerun M0 mainline selection",
        ],
        "explicit_non_goals": [
            "no pointer promotion while M0 is blocked",
            "no deterministic chart fact mutation",
        ],
    }


def _deferred_tracks() -> list[dict[str, Any]]:
    return [
        {
            "track": "policy_pointer_promotion",
            "reason": "F6 closed with no promotion; promotion requires a separate explicit operator write track.",
        },
        {
            "track": "core_module_reopen",
            "reason": "M1-M8 are current-scope complete; reopen only after concrete targeted validation failure.",
        },
        {
            "track": "full_518k",
            "reason": "Full 518K is reserved for explicit production release boundary, not routine mainline selection.",
        },
        {
            "track": "ui_expansion",
            "reason": "UI remains concise; release-boundary work should not expand product surface.",
        },
    ]
