from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_heavy_validation_decision import (
    DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION,
    build_dialogue_heavy_validation_decision,
    run_dialogue_heavy_validation_decision,
)


DIALOGUE_HEAVY_VALIDATION_DECISION_VALIDATION_VERSION = "v30.dialogue_heavy_validation_decision_validation.v1"


def run_dialogue_heavy_validation_decision_validation(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc6-dialogue-heavy-validation-decision",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    decision = run_dialogue_heavy_validation_decision(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=run_id,
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_heavy_validation_decision_validation(decision_result=decision)


def build_dialogue_heavy_validation_decision_validation(
    *,
    decision_result: Mapping[str, Any],
) -> dict[str, object]:
    result = dict(decision_result)
    decision = _mapping(result.get("decision"))
    boundary = _mapping(result.get("policy_boundary"))
    readiness = _mapping(result.get("readiness_summary"))
    checks = [
        _check(
            "decision_completed",
            result.get("version") == DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION
            and result.get("status") == "completed",
            {"decision_version": result.get("version"), "decision_status": result.get("status")},
        ),
        _check(
            "heavy_validation_recommended_without_execution",
            decision.get("heavy_validation_recommended") is True
            and decision.get("runs_triggered") is False,
            {
                "heavy_validation_recommended": decision.get("heavy_validation_recommended"),
                "recommended_gate_ids": decision.get("recommended_gate_ids"),
                "runs_triggered": decision.get("runs_triggered"),
            },
        ),
        _check(
            "operator_authorization_still_required",
            boundary.get("operator_authorization_required_before_execution") is True
            and boundary.get("heavy_validation_execution_allowed") is False,
            {
                "operator_authorization_required_before_execution": boundary.get("operator_authorization_required_before_execution"),
                "heavy_validation_execution_allowed": boundary.get("heavy_validation_execution_allowed"),
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
        _check(
            "readiness_uses_operator_pack_evidence",
            readiness.get("ready_for_recommended_heavy_gates") is True
            and int(readiness.get("dtc4_case_count") or 0) >= 4,
            {
                "ready_for_recommended_heavy_gates": readiness.get("ready_for_recommended_heavy_gates"),
                "dtc4_case_count": readiness.get("dtc4_case_count"),
                "dtc4_pass_ratio": readiness.get("dtc4_pass_ratio"),
            },
        ),
    ]
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_HEAVY_VALIDATION_DECISION_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "decision_result": result,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_decision_ready": ready,
            "decision_status": "dtc6_dialogue_heavy_validation_decision_ready"
            if ready else "dtc6_dialogue_heavy_validation_decision_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "heavy_validation_recommended": bool(decision.get("heavy_validation_recommended")),
            "recommended_gate_ids": list(decision.get("recommended_gate_ids") or []),
            "runs_triggered": False,
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
        "boundary": "dialogue_heavy_validation_decision_validation_is_read_only_and_does_not_execute_gates",
    }


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
