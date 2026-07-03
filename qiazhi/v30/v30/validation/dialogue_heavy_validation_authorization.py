from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_heavy_validation_authorization import (
    DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION,
    AuthorizationDecision,
    build_dialogue_heavy_validation_authorization,
    run_dialogue_heavy_validation_authorization,
)


DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VALIDATION_VERSION = "v30.dialogue_heavy_validation_authorization_validation.v1"


def run_dialogue_heavy_validation_authorization_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc7-dialogue-heavy-validation-authorization",
    persist_review: bool = True,
    authorization_decision: AuthorizationDecision = "authorize_recommended",
    settings: V30Settings | None = None,
) -> dict[str, object]:
    authorization = run_dialogue_heavy_validation_authorization(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        authorization_decision=authorization_decision,
        settings=settings,
    )
    return build_dialogue_heavy_validation_authorization_validation(authorization_result=authorization)


def build_dialogue_heavy_validation_authorization_validation(
    *,
    authorization_result: Mapping[str, Any],
) -> dict[str, object]:
    result = dict(authorization_result)
    decision = _mapping(result.get("decision"))
    boundary = _mapping(result.get("policy_boundary"))
    checks = [
        _check(
            "authorization_completed",
            result.get("version") == DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION
            and result.get("status") == "completed",
            {"authorization_version": result.get("version"), "authorization_status": result.get("status")},
        ),
        _check(
            "recommended_gates_authorized_without_execution",
            set(decision.get("authorized_gate_ids") or []) == {"dialogue_synthetic_all", "dialogue_518k_sample"}
            and decision.get("runs_triggered") is False,
            {
                "authorized_gate_ids": decision.get("authorized_gate_ids"),
                "runs_triggered": decision.get("runs_triggered"),
            },
        ),
        _check(
            "execution_deferred_to_dtc8",
            decision.get("execution_allowed_in_this_step") is False
            and boundary.get("execution_requires_dtc8") is True,
            {
                "execution_allowed_in_this_step": decision.get("execution_allowed_in_this_step"),
                "execution_requires_dtc8": boundary.get("execution_requires_dtc8"),
            },
        ),
        _check(
            "promotion_and_chart_fact_boundary_safe",
            decision.get("promotion_allowed") is False
            and decision.get("policy_pointer_write_allowed") is False
            and decision.get("chart_fact_mutation_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False,
            {
                "promotion_allowed": decision.get("promotion_allowed"),
                "policy_pointer_write_allowed": decision.get("policy_pointer_write_allowed"),
                "chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed"),
                "policy_pointer_promotion_allowed": boundary.get("policy_pointer_promotion_allowed"),
            },
        ),
    ]
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "authorization_result": result,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_authorization_ready": ready,
            "decision_status": "dtc7_dialogue_heavy_validation_authorization_ready"
            if ready else "dtc7_dialogue_heavy_validation_authorization_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "authorized_gate_ids": list(decision.get("authorized_gate_ids") or []),
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
        "next_mainline_selection": result.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_heavy_validation_authorization_validation_is_read_only_and_does_not_execute_gates",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
