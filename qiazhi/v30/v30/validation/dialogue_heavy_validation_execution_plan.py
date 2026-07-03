from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_heavy_validation_execution_plan import (
    DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION,
    build_dialogue_heavy_validation_execution_plan,
    run_dialogue_heavy_validation_execution_plan,
)


DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VALIDATION_VERSION = "v30.dialogue_heavy_validation_execution_plan_validation.v1"


def run_dialogue_heavy_validation_execution_plan_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc8-dialogue-heavy-validation-execution-plan",
    persist_review: bool = True,
    authorization_decision: str = "authorize_recommended",
    settings: V30Settings | None = None,
) -> dict[str, object]:
    plan = run_dialogue_heavy_validation_execution_plan(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        authorization_decision=authorization_decision,
        settings=settings,
    )
    return build_dialogue_heavy_validation_execution_plan_validation(plan_result=plan)


def build_dialogue_heavy_validation_execution_plan_validation(
    *,
    plan_result: Mapping[str, Any],
) -> dict[str, object]:
    plan = dict(plan_result)
    decision = _mapping(plan.get("decision"))
    boundary = _mapping(plan.get("policy_boundary"))
    checks = [
        _check(
            "plan_completed",
            plan.get("version") == DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION
            and plan.get("status") == "completed",
            {"plan_version": plan.get("version"), "plan_status": plan.get("status")},
        ),
        _check(
            "steps_planned_without_execution",
            int(decision.get("planned_step_count") or 0) >= 1
            and decision.get("runs_triggered") is False
            and decision.get("execution_started") is False,
            {
                "planned_step_count": decision.get("planned_step_count"),
                "runs_triggered": decision.get("runs_triggered"),
                "execution_started": decision.get("execution_started"),
            },
        ),
        _check(
            "manual_execution_required",
            boundary.get("manual_execution_required") is True
            and boundary.get("ready_to_execute") is False,
            {
                "manual_execution_required": boundary.get("manual_execution_required"),
                "ready_to_execute": boundary.get("ready_to_execute"),
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
        "version": DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "plan_result": plan,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_execution_plan_ready": ready,
            "decision_status": "dtc8_dialogue_heavy_validation_execution_plan_ready"
            if ready else "dtc8_dialogue_heavy_validation_execution_plan_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "planned_step_count": int(decision.get("planned_step_count") or 0),
            "ready_to_execute": False,
            "runs_triggered": False,
            "execution_started": False,
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": plan.get("next_mainline_selection", {}),
        "policy_boundary": boundary,
        "boundary": "dialogue_heavy_validation_execution_plan_validation_is_read_only_and_does_not_start_processes",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
