from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Literal

from v30.config import V30Settings
from v30.training.dialogue_heavy_validation_decision import run_dialogue_heavy_validation_decision


DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION = "v30.dialogue_heavy_validation_authorization.v1"
AuthorizationDecision = Literal["authorize_recommended", "defer_all"]


def run_dialogue_heavy_validation_authorization(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc7-dialogue-heavy-validation-authorization",
    persist_review: bool = True,
    authorization_decision: AuthorizationDecision = "authorize_recommended",
    settings: V30Settings | None = None,
) -> dict[str, object]:
    decision = run_dialogue_heavy_validation_decision(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc6",
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_heavy_validation_authorization(
        decision_result=decision,
        run_id=run_id,
        authorization_decision=authorization_decision,
    )


def build_dialogue_heavy_validation_authorization(
    *,
    decision_result: Mapping[str, Any],
    run_id: str = "dtc7-dialogue-heavy-validation-authorization",
    authorization_decision: AuthorizationDecision = "authorize_recommended",
) -> dict[str, object]:
    decision_result = dict(decision_result)
    decision = _mapping(decision_result.get("decision"))
    recommended_gate_ids = {str(row) for row in _list(decision.get("recommended_gate_ids"))}
    requested_gate_ids = recommended_gate_ids if authorization_decision == "authorize_recommended" else set()
    authorization_matrix = [
        _authorization_row(row, requested_gate_ids=requested_gate_ids, decision=decision)
        for row in _list(decision_result.get("gate_matrix"))
        if isinstance(row, Mapping)
    ]
    checks = _checks(
        decision_result=decision_result,
        decision=decision,
        authorization_decision=authorization_decision,
        authorization_matrix=authorization_matrix,
    )
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    authorized_gate_ids = [
        str(row["gate_id"])
        for row in authorization_matrix
        if row.get("authorized_pending_execution") is True
    ]
    return {
        "version": DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION,
        "run_id": run_id,
        "authorized_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-7",
            "title": "Dialogue Heavy Validation Authorization",
            "scope": "record_operator_authorization_for_recommended_dialogue_heavy_validation_gates_without_executing_them",
        },
        "decision_result": decision_result,
        "authorization_request": {
            "operator_decision": authorization_decision,
            "requested_gate_ids": sorted(requested_gate_ids),
            "runs_triggered": False,
            "boundary": "authorization_records_requested_gates_without_execution",
        },
        "authorization_matrix": authorization_matrix,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_authorization_ready": ready,
            "decision_status": "dtc7_dialogue_heavy_validation_authorization_ready"
            if ready else "dtc7_dialogue_heavy_validation_authorization_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "operator_decision": authorization_decision,
            "authorized_gate_ids": authorized_gate_ids,
            "authorized_gate_count": len(authorized_gate_ids),
            "deferred_gate_ids": [
                str(row["gate_id"])
                for row in authorization_matrix
                if row.get("authorized_pending_execution") is not True
            ],
            "runs_triggered": False,
            "execution_allowed_in_this_step": False,
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "runs_triggered": False,
            "heavy_validation_execution_allowed_in_this_step": False,
            "execution_requires_dtc8": True,
            "policy_promotion_requires_separate_flow": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
                "automatic_heavy_validation_execution",
            ],
            "boundary": "dialogue_heavy_validation_authorization_records_operator_intent_without_executing_gates",
        },
        "next_mainline_selection": {
            "task_id": "DTC-8" if ready and authorized_gate_ids else "DTC-7-WAIT",
            "title": "Dialogue Heavy Validation Execution Plan" if ready and authorized_gate_ids else "Await Dialogue Heavy Validation Authorization",
            "reason": "operator_authorized_recommended_gates_pending_separate_execution"
            if ready and authorized_gate_ids else "all_heavy_validation_gates_deferred",
        },
        "boundary": "dtc7_authorizes_next_execution_step_but_does_not_run_tests_or_release_policy",
    }


def _authorization_row(
    row: Mapping[str, Any],
    *,
    requested_gate_ids: set[str],
    decision: Mapping[str, Any],
) -> dict[str, object]:
    gate_id = str(row.get("gate_id") or "")
    recommended = row.get("recommended_pending_operator_execution") is True
    requested = gate_id in requested_gate_ids
    decision_ready = decision.get("dialogue_heavy_validation_decision_ready") is True
    authorized = requested and recommended and decision_ready
    deferred_reason = ""
    if not requested:
        deferred_reason = "not_requested_by_operator"
    elif not recommended:
        deferred_reason = "not_recommended_by_dtc6"
    elif not decision_ready:
        deferred_reason = "dtc6_decision_not_ready"
    return {
        "gate_id": gate_id,
        "category": str(row.get("category") or ""),
        "command": str(row.get("command") or ""),
        "recommended_by_dtc6": recommended,
        "requested_by_operator": requested,
        "authorized_pending_execution": authorized,
        "run_triggered": False,
        "promotion_allowed_after_gate": False,
        "deferred_reason": deferred_reason,
        "boundary": "authorization_row_never_executes_gate",
    }


def _checks(
    *,
    decision_result: Mapping[str, Any],
    decision: Mapping[str, Any],
    authorization_decision: AuthorizationDecision,
    authorization_matrix: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    authorized = [row for row in authorization_matrix if row.get("authorized_pending_execution") is True]
    return [
        _check(
            "dtc6_decision_ready",
            decision_result.get("status") == "completed"
            and decision.get("dialogue_heavy_validation_decision_ready") is True
            and decision.get("heavy_validation_recommended") is True,
            {
                "decision_status": decision.get("decision_status"),
                "heavy_validation_recommended": decision.get("heavy_validation_recommended"),
            },
        ),
        _check(
            "authorization_matrix_matches_operator_decision",
            (
                authorization_decision == "defer_all"
                and not authorized
            )
            or (
                authorization_decision == "authorize_recommended"
                and {row.get("gate_id") for row in authorized} == {"dialogue_synthetic_all", "dialogue_518k_sample"}
            ),
            {
                "operator_decision": authorization_decision,
                "authorized_gate_ids": [row.get("gate_id") for row in authorized],
            },
        ),
        _check(
            "authorization_does_not_execute_gates",
            all(row.get("run_triggered") is False for row in authorization_matrix),
            {
                "run_triggered_count": sum(1 for row in authorization_matrix if row.get("run_triggered") is True),
            },
        ),
        _check(
            "release_and_pointer_remain_blocked",
            decision.get("promotion_allowed") is False
            and decision.get("policy_pointer_write_allowed") is False
            and decision.get("chart_fact_mutation_allowed") is False,
            {
                "promotion_allowed": decision.get("promotion_allowed"),
                "policy_pointer_write_allowed": decision.get("policy_pointer_write_allowed"),
                "chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed"),
            },
        ),
    ]


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
