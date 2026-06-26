from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


RELEASE_CANDIDATE_REVIEW_VERSION = "v30.release_candidate_review.v1"


def build_release_candidate_review(
    *,
    post_seal_status_review: dict[str, Any],
    release_gate_result: dict[str, Any] | None = None,
    replay_search: dict[str, Any] | None = None,
) -> dict[str, Any]:
    release_gate_result = release_gate_result if isinstance(release_gate_result, dict) else {}
    replay_search = replay_search if isinstance(replay_search, dict) else {}
    gate_status = str(release_gate_result.get("status") or "")
    promotion_signal = str(release_gate_result.get("promotion_signal") or "")
    replay_summary = replay_search.get("summary", {}) if isinstance(replay_search.get("summary"), dict) else {}
    core_phase_sealed = (
        int(post_seal_status_review.get("core_module_summary", {}).get("phase_sealed_count", 0) or 0)
        if isinstance(post_seal_status_review.get("core_module_summary"), dict) else 0
    )
    completed_tasks = post_seal_status_review.get("completed_post_seal_tasks", [])
    completed_task_count = len(completed_tasks) if isinstance(completed_tasks, list) else 0
    replay_ready_count = int(replay_summary.get("calibration_ready_count", 0) or 0)
    decision = _decision(
        gate_status=gate_status,
        promotion_signal=promotion_signal,
        core_phase_sealed=core_phase_sealed,
        completed_task_count=completed_task_count,
        replay_ready_count=replay_ready_count,
    )
    return {
        "version": RELEASE_CANDIDATE_REVIEW_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "decision": decision,
        "post_seal_summary": {
            "status_review_version": str(post_seal_status_review.get("version") or ""),
            "core_phase_sealed_count": core_phase_sealed,
            "completed_task_count": completed_task_count,
            "next_mainline_before_review": (
                post_seal_status_review.get("next_mainline_selection", {})
                if isinstance(post_seal_status_review.get("next_mainline_selection"), dict) else {}
            ).get("task_id", ""),
        },
        "release_gate_summary": _release_gate_summary(release_gate_result),
        "replay_store_summary": {
            "search_version": str(replay_search.get("version") or ""),
            "searchable": bool(replay_search.get("searchable")),
            "row_count": int(replay_summary.get("row_count", 0) or 0),
            "calibration_ready_count": replay_ready_count,
            "hold_pending_count": int(replay_summary.get("hold_pending_count", 0) or 0),
            "blocked_count": int(replay_summary.get("blocked_count", 0) or 0),
            "privacy_guard_pass_count": int(replay_summary.get("privacy_guard_pass_count", 0) or 0),
        },
        "release_candidate_gate": {
            "recommended": decision["release_candidate_gate_recommended"],
            "minimum_command": "python3 scripts/run_release_gate.py --mode standard --sample-limit 8 --shard-id 7 --shard-limit 16",
            "full_pytest_required": False,
            "full_518k_required": False,
            "policy_pointer_promotion_allowed": False,
            "boundary": "release_candidate_review_recommends_gate_without_promoting_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "release_candidate_review_is_read_only_and_does_not_mutate_chart_facts_or_policy_pointers",
    }


def _decision(
    *,
    gate_status: str,
    promotion_signal: str,
    core_phase_sealed: int,
    completed_task_count: int,
    replay_ready_count: int,
) -> dict[str, Any]:
    blockers = []
    if core_phase_sealed < 8:
        blockers.append("core_modules_not_all_phase_sealed")
    if completed_task_count < 9:
        blockers.append("post_seal_tasks_incomplete")
    if replay_ready_count < 20:
        blockers.append("replay_calibration_ready_coverage_low")
    if gate_status and gate_status != "passed":
        blockers.append("release_gate_not_passed")
    if promotion_signal and promotion_signal != "eligible":
        blockers.append("release_gate_not_eligible")
    if not gate_status:
        blockers.append("release_gate_not_run_for_review")
    rc_ready = not blockers
    return {
        "release_candidate_gate_recommended": rc_ready,
        "real_production_row_ingestion_required_before_rc": "replay_calibration_ready_coverage_low" in blockers,
        "decision_status": "ready_for_release_candidate_gate" if rc_ready else "blocked_or_needs_gate_evidence",
        "blockers": blockers,
        "rationale": (
            "R1-R9 evidence is sufficient for a standard release-candidate gate; real production row ingestion can remain the next calibration expansion."
            if rc_ready
            else "Release-candidate readiness needs the listed evidence before moving past post-seal hardening."
        ),
    }


def _release_gate_summary(release_gate_result: dict[str, Any]) -> dict[str, Any]:
    checks = release_gate_result.get("checks", [])
    checks = checks if isinstance(checks, list) else []
    return {
        "run_id": str(release_gate_result.get("run_id") or ""),
        "mode": str(release_gate_result.get("mode") or ""),
        "status": str(release_gate_result.get("status") or ""),
        "promotion_signal": str(release_gate_result.get("promotion_signal") or ""),
        "check_count": len(checks),
        "check_statuses": {
            str(row.get("check_id") or ""): str(row.get("status") or "")
            for row in checks
            if isinstance(row, dict) and row.get("check_id")
        },
        "artifact_review_version": (
            release_gate_result.get("artifact_review", {})
            if isinstance(release_gate_result.get("artifact_review"), dict) else {}
        ).get("version", ""),
    }


def _next_selection(decision: dict[str, Any]) -> dict[str, Any]:
    if decision["release_candidate_gate_recommended"]:
        return {
            "task_id": "R11",
            "title": "Standard Release-Candidate Gate",
            "selected_track": "release_candidate_gate",
            "scope": [
                "run standard release gate with selected 518K shard",
                "record release-candidate artifact review",
                "do not promote policy pointers unless explicitly requested after gate evidence",
            ],
        }
    return {
        "task_id": "R11",
        "title": "Release Candidate Evidence Gap Closure",
        "selected_track": "release_readiness",
        "scope": [
            "close listed release-candidate blockers",
            "rerun quick release gate after fixes",
            "keep full pytest/full 518K reserved for release boundary",
        ],
    }
