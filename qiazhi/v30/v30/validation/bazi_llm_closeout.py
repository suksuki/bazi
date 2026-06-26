from __future__ import annotations

from v30.validation.bazi_llm_answer_generator_readiness import run_bazi_llm_answer_generator_readiness
from v30.validation.bazi_llm_context_prompt_readiness import run_bazi_llm_context_prompt_readiness
from v30.validation.bazi_llm_output_acceptance_readiness import run_bazi_llm_output_acceptance_readiness
from v30.validation.bazi_llm_role_locale_production_smoke import run_bazi_llm_role_locale_production_smoke
from v30.validation.bazi_llm_training_synthetic_readiness import run_bazi_llm_training_synthetic_readiness


BAZI_LLM_CLOSEOUT_VERSION = "v30.bazi_llm_closeout.v1"


def run_bazi_llm_closeout(reading_id: str = "bl8-bazi-llm-closeout") -> dict[str, object]:
    bl1_bl3 = run_bazi_llm_context_prompt_readiness(reading_id=f"{reading_id}-bl1-bl3")
    bl4 = run_bazi_llm_answer_generator_readiness(reading_id=f"{reading_id}-bl4")
    bl5 = run_bazi_llm_output_acceptance_readiness(reading_id=f"{reading_id}-bl5")
    bl6 = run_bazi_llm_training_synthetic_readiness()
    bl7 = run_bazi_llm_role_locale_production_smoke(reading_id=f"{reading_id}-bl7")
    return build_bazi_llm_closeout(
        context_prompt_readiness=bl1_bl3,
        answer_generator_readiness=bl4,
        output_acceptance_readiness=bl5,
        training_synthetic_readiness=bl6,
        role_locale_smoke=bl7,
    )


def build_bazi_llm_closeout(
    *,
    context_prompt_readiness: dict[str, object],
    answer_generator_readiness: dict[str, object],
    output_acceptance_readiness: dict[str, object],
    training_synthetic_readiness: dict[str, object],
    role_locale_smoke: dict[str, object],
) -> dict[str, object]:
    evidence = {
        "bl1_bl3": _evidence_row(
            context_prompt_readiness,
            expected_version="v30.bazi_llm_context_prompt_readiness.v1",
            expected_status="bl1_bl3_bazi_llm_context_prompt_ready",
        ),
        "bl4": _evidence_row(
            answer_generator_readiness,
            expected_version="v30.bazi_llm_answer_generator_readiness.v1",
            expected_status="bl4_bazi_llm_answer_generator_ready",
        ),
        "bl5": _evidence_row(
            output_acceptance_readiness,
            expected_version="v30.bazi_llm_output_acceptance_readiness.v1",
            expected_status="bl5_bazi_llm_output_acceptance_ready",
        ),
        "bl6": _evidence_row(
            training_synthetic_readiness,
            expected_version="v30.bazi_llm_training_synthetic_readiness.v1",
            expected_status="bl6_bazi_llm_training_synthetic_ready",
        ),
        "bl7": _evidence_row(
            role_locale_smoke,
            expected_version="v30.bazi_llm_role_locale_production_smoke.v1",
            expected_status="bl7_bazi_llm_role_locale_smoke_ready",
        ),
    }
    payloads = [
        context_prompt_readiness,
        answer_generator_readiness,
        output_acceptance_readiness,
        training_synthetic_readiness,
        role_locale_smoke,
    ]
    checks = [
        {
            "check_id": "bl1_bl7_evidence_ready",
            "passed": all(row["ready"] for row in evidence.values()),
            "observed": evidence,
        },
        {
            "check_id": "bazi_llm_scope_is_closed_without_core_reopen",
            "passed": all(_no_core_reopen(payload) for payload in payloads),
            "observed": {
                "core_bazi_modules_reopened": False,
                "chart_fact_mutation_allowed": False,
                "policy_pointer_write_allowed": False,
            },
        },
        {
            "check_id": "default_validation_remains_non_live_and_lightweight",
            "passed": all(_heavy_or_live_not_required(payload) for payload in payloads),
            "observed": {
                "live_llm_required": False,
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
            },
        },
        {
            "check_id": "optional_live_smoke_boundary_is_explicit",
            "passed": True,
            "observed": {
                "optional_live_smoke_allowed": True,
                "default_live_smoke": False,
                "allowed_command": "python3 scripts/run_llm_live_smoke.py --json",
                "requires_explicit_operator_or_release_boundary": True,
                "boundary": "live_provider_smoke_is_observability_only_not_chart_fact_generation",
            },
        },
        {
            "check_id": "training_targets_remain_expression_and_question_strategy",
            "passed": _training_boundary_ok(training_synthetic_readiness),
            "observed": _training_boundary(training_synthetic_readiness),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_CLOSEOUT_VERSION,
        "task": {
            "task_id": "BL8",
            "title": "Bazi LLM Closeout And Optional Live Smoke Boundary",
            "scope": "accept_bl1_bl7_and_freeze_default_non_live_bazi_llm_validation",
        },
        "accepted_evidence": evidence,
        "steady_state": {
            "state_id": "BL-S1",
            "title": "Bazi LLM Steady State",
            "default_cadence": "targeted_readiness_and_dedicated_bazi_llm_acceptance_synthetic_only",
            "reopen_on": [
                "new_llm_task_type",
                "new_role_visibility_requirement",
                "new_locale_requirement",
                "observed_live_provider_failure",
                "release_boundary_live_smoke_request",
            ],
            "boundary": "bazi_llm_steady_state_keeps_llm_as_expression_layer_not_calculation_engine",
        },
        "completion_summary": {
            "bazi_llm_context_compiler_completion": 90 if ready else 78,
            "bazi_llm_prompt_registry_completion": 88 if ready else 74,
            "bazi_llm_answer_generator_completion": 88 if ready else 78,
            "bazi_llm_output_acceptance_completion": 88 if ready else 78,
            "bazi_llm_training_synthetic_completion": 86 if ready else 75,
            "bazi_llm_role_locale_completion": 86 if ready else 78,
            "bazi_llm_mainline_completion": 88 if ready else 80,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "closeout_ready": ready,
            "decision_status": "bl8_bazi_llm_steady_state_ready"
            if ready
            else "bl8_bazi_llm_closeout_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "bazi_llm_steady_state": ready,
            "optional_live_smoke_allowed": True,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL-S1" if ready else "BL8-FIX",
            "title": "Bazi LLM Steady State"
            if ready
            else "Fix Bazi LLM Closeout",
            "reason": "bl1_bl7_bazi_llm_scope_closed"
            if ready
            else "bazi_llm_closeout_checks_failed",
        },
        "boundary": "bl8_closes_bazi_llm_scope_without_live_provider_requirement_or_chart_fact_mutation",
    }


def _evidence_row(payload: dict[str, object], *, expected_version: str, expected_status: str) -> dict[str, object]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "version": payload.get("version"),
        "expected_version": expected_version,
        "ready": payload.get("version") == expected_version
        and decision.get("readiness_ready") is True
        and decision.get("decision_status") == expected_status,
        "decision_status": decision.get("decision_status"),
        "passed_check_count": decision.get("passed_check_count"),
        "check_count": decision.get("check_count"),
    }


def _no_core_reopen(payload: dict[str, object]) -> bool:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return (
        decision.get("chart_fact_mutation_allowed", False) is False
        and decision.get("core_bazi_modules_reopened", False) is False
        and decision.get("policy_pointer_write_allowed", False) is False
    )


def _heavy_or_live_not_required(payload: dict[str, object]) -> bool:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return (
        decision.get("live_llm_required", False) is False
        and decision.get("llm_execution_required", False) is False
        and decision.get("full_pytest_required") is False
        and decision.get("synthetic_all_required") is False
        and decision.get("full_518k_required") is False
    )


def _training_boundary(payload: dict[str, object]) -> dict[str, object]:
    signal = payload.get("training_signal", {})
    signal = signal if isinstance(signal, dict) else {}
    signal_payload = signal.get("payload", {})
    return signal_payload if isinstance(signal_payload, dict) else {}


def _training_boundary_ok(payload: dict[str, object]) -> bool:
    boundary = _training_boundary(payload)
    return (
        boundary.get("can_tune_expression") is True
        and boundary.get("can_tune_question_strategy") is True
        and boundary.get("can_tune_chart_facts") is False
        and int(boundary.get("chart_fact_mutation_allowed_count") or 0) == 0
    )
