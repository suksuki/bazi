from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_heavy_validation_authorization import run_dialogue_heavy_validation_authorization


DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION = "v30.dialogue_heavy_validation_execution_plan.v1"


def run_dialogue_heavy_validation_execution_plan(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc8-dialogue-heavy-validation-execution-plan",
    persist_review: bool = True,
    authorization_decision: str = "authorize_recommended",
    settings: V30Settings | None = None,
) -> dict[str, object]:
    safe_decision = "defer_all" if authorization_decision == "defer_all" else "authorize_recommended"
    authorization = run_dialogue_heavy_validation_authorization(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc7",
        persist_review=persist_review,
        authorization_decision=safe_decision,
        settings=settings,
    )
    return build_dialogue_heavy_validation_execution_plan(
        authorization_result=authorization,
        run_id=run_id,
    )


def build_dialogue_heavy_validation_execution_plan(
    *,
    authorization_result: Mapping[str, Any],
    run_id: str = "dtc8-dialogue-heavy-validation-execution-plan",
) -> dict[str, object]:
    authorization = dict(authorization_result)
    auth_decision = _mapping(authorization.get("decision"))
    steps = _execution_steps(_list(authorization.get("authorization_matrix")))
    plan_summary = _plan_summary(authorization=authorization, steps=steps)
    checks = _checks(authorization=authorization, steps=steps, plan_summary=plan_summary)
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION,
        "run_id": run_id,
        "planned_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-8",
            "title": "Dialogue Heavy Validation Execution Plan",
            "scope": "build_explicit_execution_plan_for_authorized_dialogue_heavy_validation_gates_without_running_them",
        },
        "authorization_result": authorization,
        "plan_summary": plan_summary,
        "execution_steps": steps,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_execution_plan_ready": ready,
            "decision_status": "dtc8_dialogue_heavy_validation_execution_plan_ready"
            if ready else "dtc8_dialogue_heavy_validation_execution_plan_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "authorized_gate_ids": list(auth_decision.get("authorized_gate_ids") or []),
            "planned_step_count": len(steps),
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
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "ready_to_execute": False,
            "runs_triggered": False,
            "execution_started": False,
            "manual_execution_required": True,
            "policy_promotion_requires_separate_flow": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
                "automatic_heavy_validation_execution",
            ],
            "boundary": "dialogue_heavy_validation_execution_plan_lists_commands_without_starting_them",
        },
        "next_mainline_selection": {
            "task_id": "DTC-9" if ready and steps else "DTC-8-WAIT",
            "title": "Dialogue Heavy Validation Execution Runner" if ready and steps else "Await Authorized Heavy Validation Gates",
            "reason": "execution_plan_ready_for_explicit_runner"
            if ready and steps else "no_authorized_gates_to_plan",
        },
        "boundary": "dtc8_creates_execution_plan_not_execution_or_policy_release",
    }


def _execution_steps(authorization_matrix: Sequence[object]) -> list[dict[str, object]]:
    rows = [_mapping(row) for row in authorization_matrix]
    authorized = [
        row for row in rows
        if row.get("authorized_pending_execution") is True
    ]
    steps: list[dict[str, object]] = []
    for index, row in enumerate(authorized, start=1):
        gate_id = str(row.get("gate_id") or "")
        steps.append(
            {
                "step_id": f"dtc8.{gate_id}",
                "order": index,
                "gate_id": gate_id,
                "category": str(row.get("category") or ""),
                "command": str(row.get("command") or ""),
                "expected_artifact_family": _expected_artifact_family(gate_id),
                "timeout_seconds": _timeout_seconds(gate_id),
                "ready_to_execute": False,
                "run_triggered": False,
                "execution_started": False,
                "promotion_allowed_after_step": False,
                "requires_manual_runner": True,
                "boundary": "execution_step_is_planned_command_not_started_process",
            }
        )
    return steps


def _plan_summary(*, authorization: Mapping[str, Any], steps: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    auth_decision = _mapping(authorization.get("decision"))
    return {
        "version": "v30.dialogue_heavy_validation_execution_plan_summary.v1",
        "authorization_status": str(authorization.get("status") or ""),
        "authorization_decision_status": str(auth_decision.get("decision_status") or ""),
        "authorized_gate_count": int(auth_decision.get("authorized_gate_count") or len(auth_decision.get("authorized_gate_ids") or [])),
        "planned_step_count": len(steps),
        "planned_gate_ids": [str(row.get("gate_id") or "") for row in steps],
        "commands": [str(row.get("command") or "") for row in steps],
        "runs_triggered": False,
        "execution_started": False,
        "manual_execution_required": True,
        "boundary": "execution_plan_summary_records_commands_without_running_them",
    }


def _checks(
    *,
    authorization: Mapping[str, Any],
    steps: Sequence[Mapping[str, Any]],
    plan_summary: Mapping[str, Any],
) -> list[dict[str, object]]:
    auth_decision = _mapping(authorization.get("decision"))
    return [
        _check(
            "dtc7_authorization_ready",
            authorization.get("status") == "completed"
            and auth_decision.get("dialogue_heavy_validation_authorization_ready") is True,
            {
                "authorization_status": authorization.get("status"),
                "authorization_decision_status": auth_decision.get("decision_status"),
            },
        ),
        _check(
            "authorized_gates_have_plan_steps",
            int(plan_summary.get("authorized_gate_count") or 0) == len(steps)
            and len(steps) >= 1,
            {
                "authorized_gate_count": plan_summary.get("authorized_gate_count"),
                "planned_step_count": len(steps),
            },
        ),
        _check(
            "planned_steps_do_not_execute",
            all(row.get("run_triggered") is False for row in steps)
            and all(row.get("execution_started") is False for row in steps)
            and plan_summary.get("runs_triggered") is False,
            {
                "run_triggered_count": sum(1 for row in steps if row.get("run_triggered") is True),
                "execution_started_count": sum(1 for row in steps if row.get("execution_started") is True),
            },
        ),
        _check(
            "commands_are_explicit",
            all(str(row.get("command") or "") for row in steps),
            {"commands": plan_summary.get("commands")},
        ),
        _check(
            "release_and_pointer_remain_blocked",
            auth_decision.get("promotion_allowed") is False
            and auth_decision.get("policy_pointer_write_allowed") is False
            and auth_decision.get("chart_fact_mutation_allowed") is False,
            {
                "promotion_allowed": auth_decision.get("promotion_allowed"),
                "policy_pointer_write_allowed": auth_decision.get("policy_pointer_write_allowed"),
                "chart_fact_mutation_allowed": auth_decision.get("chart_fact_mutation_allowed"),
            },
        ),
    ]


def _expected_artifact_family(gate_id: str) -> str:
    if gate_id == "dialogue_518k_sample":
        return "518k_validation"
    if gate_id == "dialogue_synthetic_all":
        return "synthetic_validation"
    return "manual_validation"


def _timeout_seconds(gate_id: str) -> int:
    if gate_id == "dialogue_synthetic_all":
        return 1800
    if gate_id == "dialogue_518k_sample":
        return 900
    return 3600


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
