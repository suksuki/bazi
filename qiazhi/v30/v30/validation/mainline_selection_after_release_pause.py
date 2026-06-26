from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.post_release_boundary_authorization import (
    POST_RELEASE_BOUNDARY_AUTHORIZATION_VERSION,
    run_post_release_boundary_authorization,
)


MAINLINE_SELECTION_AFTER_RELEASE_PAUSE_VERSION = "v30.mainline_selection_after_release_pause.v1"


def run_mainline_selection_after_release_pause(*, sample_limit: int = 8) -> dict[str, Any]:
    authorization = run_post_release_boundary_authorization(
        sample_limit=sample_limit,
        authorization_decision="pause",
    )
    return build_mainline_selection_after_release_pause(
        post_release_boundary_authorization=authorization,
    )


def build_mainline_selection_after_release_pause(
    *,
    post_release_boundary_authorization: Mapping[str, Any],
) -> dict[str, Any]:
    selected_at = datetime.now(timezone.utc)
    pause_summary = _pause_summary(post_release_boundary_authorization)
    decision = _decision(pause_summary)
    return {
        "version": MAINLINE_SELECTION_AFTER_RELEASE_PAUSE_VERSION,
        "selected_at": selected_at.isoformat(),
        "status": "ready_for_next_mainline" if decision["mainline_selection_ready"] else "mainline_selection_blocked",
        "decision": decision,
        "release_boundary_summary": pause_summary,
        "selected_non_release_mainline": _selected_mainline(decision),
        "deferred_tracks": _deferred_tracks(),
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "core_module_reopen_allowed": False,
            "boundary": "m0_after_release_pause_does_not_release_or_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m0_after_release_pause_selects_non_release_mainline",
    }


def _pause_summary(authorization: Mapping[str, Any]) -> dict[str, Any]:
    decision = authorization.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    release_state = authorization.get("release_boundary_state", {})
    release_state = release_state if isinstance(release_state, dict) else {}
    policy = authorization.get("policy_boundary", {})
    policy = policy if isinstance(policy, dict) else {}
    return {
        "version": str(authorization.get("version") or ""),
        "status": str(authorization.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "release_boundary_paused": bool(decision.get("release_boundary_paused")),
        "full_pytest_authorized": bool(decision.get("full_pytest_authorized")),
        "full_pytest_run_triggered": bool(decision.get("full_pytest_run_triggered")),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "external_release_allowed": bool(release_state.get("external_release_allowed")),
        "policy_pointer_promotion_allowed": bool(policy.get("policy_pointer_promotion_allowed")),
        "pointer_write_allowed": bool(policy.get("pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(policy.get("chart_fact_mutation_allowed")),
    }


def _decision(pause_summary: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if pause_summary.get("version") != POST_RELEASE_BOUNDARY_AUTHORIZATION_VERSION:
        blockers.append("r16_authorization_missing")
    if not pause_summary.get("release_boundary_paused"):
        blockers.append("release_boundary_not_paused")
    if pause_summary.get("full_pytest_authorized") or pause_summary.get("full_pytest_run_triggered"):
        blockers.append("full_pytest_not_paused")
    if pause_summary.get("external_release_ready") or pause_summary.get("external_release_allowed"):
        blockers.append("external_release_not_blocked")
    if pause_summary.get("policy_pointer_promotion_allowed") or pause_summary.get("pointer_write_allowed"):
        blockers.append("unexpected_policy_pointer_permission")
    if pause_summary.get("chart_fact_mutation_allowed"):
        blockers.append("unexpected_chart_fact_mutation_permission")

    ready = not blockers
    return {
        "mainline_selection_ready": ready,
        "decision_status": "core_monitoring_and_calibration_loop_selected" if ready else "mainline_selection_after_release_pause_blocked",
        "selected_task_id": "P0",
        "selected_track": "core_monitoring_and_calibration",
        "external_release_ready": False,
        "release_boundary_paused": bool(pause_summary.get("release_boundary_paused")),
        "full_pytest_authorized": False,
        "full_pytest_run_triggered": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": blockers,
        "rationale": (
            "Release-boundary work is paused; select a non-release core monitoring/calibration loop as the next mainline."
            if ready
            else "Mainline selection after release pause needs the listed blockers closed before selecting non-release work."
        ),
    }


def _selected_mainline(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": "P0",
        "title": "Core Module Monitoring And Calibration Loop",
        "selected_track": "core_monitoring_and_calibration",
        "scope": [
            "run lightweight monitoring checks against frozen M1-M8",
            "review targeted calibration signals without pointer promotion",
            "route concrete regressions to focused module fixes",
            "keep UI, full pytest, full 518K, and external release out of default iteration",
        ],
        "ready": bool(decision["mainline_selection_ready"]),
    }


def _deferred_tracks() -> list[dict[str, Any]]:
    return [
        {
            "track": "external_release",
            "reason": "release-boundary work is paused until full pytest is explicitly authorized",
        },
        {
            "track": "policy_pointer_promotion",
            "reason": "pointer promotion remains a separate manual operator command",
        },
        {
            "track": "ui_expansion",
            "reason": "UI remains concise while core monitoring/calibration continues",
        },
        {
            "track": "full_518k",
            "reason": "full 518K remains reserved for explicit production release boundary",
        },
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["mainline_selection_ready"]:
        return {
            "task_id": "P0",
            "title": "Core Module Monitoring And Calibration Loop",
            "selected_track": "core_monitoring_and_calibration",
            "scope": [
                "run F6 monitoring checks as the baseline",
                "review synthetic and real-case calibration drift",
                "do not reopen M1-M8 without a concrete targeted failure",
            ],
        }
    return {
        "task_id": "M0",
        "title": "Release-Pause Mainline Selection Gap Closure",
        "selected_track": "mainline_selection",
        "scope": [
            "restore R16 pause evidence",
            "rerun mainline selection after release pause",
            "keep release and pointer promotion disabled while blocked",
        ],
    }
