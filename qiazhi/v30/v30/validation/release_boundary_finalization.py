from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


RELEASE_BOUNDARY_FINALIZATION_VERSION = "v30.release_boundary_finalization.v1"


def build_release_boundary_finalization(
    *,
    post_seal_status_review: dict[str, Any],
    release_candidate_gate_review: dict[str, Any],
    full_pytest_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    post_seal_status_review = post_seal_status_review if isinstance(post_seal_status_review, dict) else {}
    release_candidate_gate_review = (
        release_candidate_gate_review if isinstance(release_candidate_gate_review, dict) else {}
    )
    full_pytest_result = full_pytest_result if isinstance(full_pytest_result, dict) else {}
    completed = post_seal_status_review.get("completed_post_seal_tasks", [])
    completed_task_count = len(completed) if isinstance(completed, list) else 0
    core_summary = post_seal_status_review.get("core_module_summary", {})
    core_summary = core_summary if isinstance(core_summary, dict) else {}
    gate_decision = release_candidate_gate_review.get("decision", {})
    gate_decision = gate_decision if isinstance(gate_decision, dict) else {}
    decision = _decision(
        completed_task_count=completed_task_count,
        core_phase_sealed_count=int(core_summary.get("phase_sealed_count", 0) or 0),
        release_boundary_ready=bool(gate_decision.get("release_boundary_ready")),
        gate_policy_promotion_allowed=bool(gate_decision.get("policy_promotion_allowed")),
        full_pytest_result=full_pytest_result,
    )
    return {
        "version": RELEASE_BOUNDARY_FINALIZATION_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "decision": decision,
        "evidence_bundle_summary": {
            "post_seal_status_review_version": str(post_seal_status_review.get("version") or ""),
            "release_candidate_gate_review_version": str(release_candidate_gate_review.get("version") or ""),
            "completed_post_seal_task_count": completed_task_count,
            "core_phase_sealed_count": int(core_summary.get("phase_sealed_count", 0) or 0),
            "release_candidate_gate_status": str(gate_decision.get("decision_status") or ""),
            "release_boundary_ready": bool(gate_decision.get("release_boundary_ready")),
        },
        "external_release_requirements": {
            "full_pytest_required": True,
            "full_518k_required": False,
            "manual_policy_pointer_promotion_required": True,
            "live_provider_required": False,
            "boundary": "external_release_requires_explicit_operator_gate_not_background_task",
        },
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "r12_finalization_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "release_boundary_finalization_reviews_evidence_without_mutating_runtime_or_policy_pointers",
    }


def _decision(
    *,
    completed_task_count: int,
    core_phase_sealed_count: int,
    release_boundary_ready: bool,
    gate_policy_promotion_allowed: bool,
    full_pytest_result: dict[str, Any],
) -> dict[str, Any]:
    blockers = []
    if completed_task_count < 12:
        blockers.append("post_seal_tasks_before_r12_incomplete")
    if core_phase_sealed_count < 8:
        blockers.append("core_modules_not_phase_sealed")
    if not release_boundary_ready:
        blockers.append("release_candidate_gate_not_boundary_ready")
    if gate_policy_promotion_allowed:
        blockers.append("unexpected_policy_promotion_allowed_before_manual_boundary")
    full_pytest_status = str(full_pytest_result.get("status") or "")
    if full_pytest_status and full_pytest_status != "passed":
        blockers.append("full_pytest_not_passed")
    internal_ready = not blockers
    external_ready = internal_ready and full_pytest_status == "passed"
    return {
        "internal_release_candidate_finalized": internal_ready,
        "external_release_ready": external_ready,
        "full_pytest_run_recorded": bool(full_pytest_status),
        "full_pytest_required_before_external_release": True,
        "full_518k_required_before_external_release": False,
        "policy_pointer_promotion_allowed": False,
        "decision_status": "internal_release_candidate_finalized" if internal_ready else "release_boundary_blocked",
        "blockers": blockers,
        "rationale": (
            "R1-R12 evidence is sufficient to finalize the internal release candidate; external release still requires an explicit full pytest gate and manual policy-promotion decision."
            if internal_ready
            else "Release-boundary finalization needs the listed blockers closed before declaring an internal release candidate."
        ),
    }


def _next_selection(decision: dict[str, Any]) -> dict[str, Any]:
    if decision["internal_release_candidate_finalized"]:
        return {
            "task_id": "R13",
            "title": "External Release Dry Run And Full Pytest Decision",
            "selected_track": "external_release_boundary",
            "scope": [
                "run or explicitly defer full pytest for external release",
                "review policy pointer promotion as a manual operator action",
                "keep full 518K separate unless external production release requires it",
            ],
        }
    return {
        "task_id": "R13",
        "title": "Release Boundary Evidence Gap Closure",
        "selected_track": "release_readiness",
        "scope": [
            "close finalization blockers",
            "rerun release boundary finalization",
            "do not promote policy pointers while blocked",
        ],
    }
