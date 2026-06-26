from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from v30.policy.runtime_pointer import PolicyFamily, RuntimePointerStore
from v30.validation.targeted_calibration_pointer_review import (
    POINTER_REVIEW_FAMILIES,
    build_targeted_calibration_pointer_review,
    run_targeted_calibration_pointer_review,
)


TARGETED_CALIBRATION_POINTER_DECISION_VERSION = "v30.targeted_calibration_pointer_decision.v1"
OperatorDecision = Literal["defer", "request_promotion"]


def run_targeted_calibration_pointer_decision(
    *,
    operator_decision: OperatorDecision = "defer",
    sample_limit: int = 8,
    decision_id: str | None = None,
    store: RuntimePointerStore | None = None,
) -> dict[str, Any]:
    store = store or RuntimePointerStore()
    pointer_review = run_targeted_calibration_pointer_review(
        sample_limit=sample_limit,
        review_id=decision_id,
        store=store,
    )
    return build_targeted_calibration_pointer_decision(
        pointer_review=pointer_review,
        operator_decision=operator_decision,
        store=store,
        decision_id=decision_id,
    )


def build_targeted_calibration_pointer_decision(
    *,
    pointer_review: Mapping[str, Any],
    operator_decision: OperatorDecision = "defer",
    store: RuntimePointerStore | None = None,
    decision_id: str | None = None,
) -> dict[str, Any]:
    decided_at = datetime.now(timezone.utc)
    store = store or RuntimePointerStore()
    before_versions = _active_versions(store)
    review_summary = _pointer_review_summary(pointer_review)
    decision = _decision(review_summary=review_summary, operator_decision=operator_decision)
    after_versions = _active_versions(store)
    return {
        "version": TARGETED_CALIBRATION_POINTER_DECISION_VERSION,
        "decision_id": decision_id or f"v30.targeted_calibration.pointer_decision.{decided_at.strftime('%Y%m%d%H%M%S')}",
        "decided_at": decided_at.isoformat(),
        "status": "completed",
        "operator_decision": operator_decision,
        "decision": decision,
        "pointer_review_summary": review_summary,
        "pointer_state_before": before_versions,
        "pointer_state_after": after_versions,
        "pointer_write_summary": {
            "pointer_write_performed": False,
            "changed_pointer_count": sum(
                1 for family, before in before_versions.items()
                if after_versions.get(family) != before
            ),
            "automatic_pointer_write_allowed": False,
            "boundary": "f5_decision_records_operator_choice_without_pointer_write",
        },
        "operator_boundary": {
            "explicit_operator_decision_recorded": True,
            "operator_decision_required_for_future_promotion": True,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "f5_pointer_decision_is_explicit_and_does_not_mutate_runtime",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "targeted_calibration_pointer_decision_records_decision_without_mutating_policy_or_chart_facts",
    }


def _active_versions(store: RuntimePointerStore) -> dict[str, str]:
    rows: dict[str, str] = {}
    for family in POINTER_REVIEW_FAMILIES:
        rows[family] = store.load_pointer(family).active_artifact_id
    return rows


def _pointer_review_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    decision = review.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    pointer_diff = review.get("pointer_diff_summary", {})
    pointer_diff = pointer_diff if isinstance(pointer_diff, dict) else {}
    active = review.get("active_pointer_summary", {})
    active = active if isinstance(active, dict) else {}
    return {
        "version": str(review.get("version") or ""),
        "review_id": str(review.get("review_id") or ""),
        "pointer_review_ready": bool(decision.get("pointer_review_ready")),
        "decision_status": str(decision.get("decision_status") or ""),
        "would_change_count": int(pointer_diff.get("would_change_count", 0) or 0),
        "diff_count": int(pointer_diff.get("diff_count", 0) or 0),
        "candidate_families": active.get("candidate_families", []) if isinstance(active.get("candidate_families", []), list) else [],
    }


def _decision(*, review_summary: Mapping[str, Any], operator_decision: OperatorDecision) -> dict[str, Any]:
    blockers: list[str] = []
    if not review_summary.get("pointer_review_ready"):
        blockers.append("f4_pointer_review_not_ready")
    if int(review_summary.get("would_change_count", 0) or 0) <= 0:
        blockers.append("no_pointer_diff_ready")
    if operator_decision == "request_promotion":
        blockers.append("promotion_requires_separate_explicit_pointer_write_command")
    ready = not blockers
    if operator_decision == "defer" and ready:
        decision_status = "pointer_promotion_deferred"
        rationale = (
            "Operator decision recorded as defer; targeted calibration evidence remains available, "
            "but no active pointer was written."
        )
    elif operator_decision == "request_promotion":
        decision_status = "promotion_request_blocked_pending_explicit_write_command"
        rationale = (
            "Promotion request is noted, but F5 does not write pointers. A separate explicit pointer-write command "
            "is required before any runtime pointer can change."
        )
    else:
        decision_status = "pointer_decision_blocked"
        rationale = "Pointer decision needs the listed blockers closed before recording a clean decision."
    return {
        "pointer_decision_recorded": operator_decision == "defer" and ready,
        "operator_deferred_promotion": operator_decision == "defer" and ready,
        "promotion_request_recorded": operator_decision == "request_promotion",
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": decision_status,
        "blockers": blockers,
        "rationale": rationale,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["pointer_decision_recorded"]:
        return {
            "task_id": "F6",
            "title": "Targeted Calibration Closeout And Monitoring Baseline",
            "selected_track": "targeted_calibration",
            "scope": [
                "record that no pointer was promoted in F5",
                "keep F2/F3/F4 evidence available for a future explicit promotion request",
                "monitor frozen M1-M8 regression gates without reopening modules",
            ],
        }
    return {
        "task_id": "F5",
        "title": "Explicit Operator Pointer Decision Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "restore F4 pointer-review readiness",
            "separate promotion request from pointer-write execution",
            "do not write active pointers while blocked",
        ],
    }
