from __future__ import annotations

from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


BAZI_LLM_TRAINING_SYNTHETIC_READINESS_VERSION = "v30.bazi_llm_training_synthetic_readiness.v1"


def run_bazi_llm_training_synthetic_readiness() -> dict[str, object]:
    synthetic = run_synthetic_tier("bazi_llm_acceptance")
    signals = extract_training_signals(synthetic)
    bazi_signal = next(
        (
            signal for signal in signals
            if signal.signal_id == "v30.training_signal.bazi_llm_output_acceptance_quality"
        ),
        None,
    )
    return build_bazi_llm_training_synthetic_readiness(
        synthetic_result=synthetic.model_dump(mode="json"),
        training_signal=bazi_signal.model_dump(mode="json") if bazi_signal is not None else {},
    )


def build_bazi_llm_training_synthetic_readiness(
    *,
    synthetic_result: dict[str, object],
    training_signal: dict[str, object],
) -> dict[str, object]:
    payload = training_signal.get("payload", {}) if isinstance(training_signal, dict) else {}
    payload = payload if isinstance(payload, dict) else {}
    checks = [
        {
            "check_id": "bazi_llm_acceptance_synthetic_tier_passes",
            "passed": synthetic_result.get("passed") is True
            and int(synthetic_result.get("passed_count") or 0) == int(synthetic_result.get("case_count") or -1),
            "observed": {
                "suite_id": synthetic_result.get("suite_id"),
                "case_count": synthetic_result.get("case_count"),
                "passed_count": synthetic_result.get("passed_count"),
                "failed_count": synthetic_result.get("failed_count"),
            },
        },
        {
            "check_id": "bazi_llm_acceptance_training_signal_exists",
            "passed": training_signal.get("signal_id") == "v30.training_signal.bazi_llm_output_acceptance_quality"
            and float(training_signal.get("strength") or 0.0) >= 0.9,
            "observed": training_signal,
        },
        {
            "check_id": "accepted_and_rejected_paths_are_covered",
            "passed": int(payload.get("accepted_count") or 0) >= 2
            and int(payload.get("rejected_count") or 0) >= 3
            and int(payload.get("schema_rejected_count") or 0) >= 1
            and int(payload.get("role_failure_count") or 0) >= 1
            and int(payload.get("drift_rejected_count") or 0) >= 1,
            "observed": {
                "accepted_count": payload.get("accepted_count"),
                "rejected_count": payload.get("rejected_count"),
                "schema_rejected_count": payload.get("schema_rejected_count"),
                "role_failure_count": payload.get("role_failure_count"),
                "drift_rejected_count": payload.get("drift_rejected_count"),
            },
        },
        {
            "check_id": "training_targets_expression_and_question_strategy_only",
            "passed": payload.get("can_tune_expression") is True
            and payload.get("can_tune_question_strategy") is True
            and payload.get("can_tune_chart_facts") is False,
            "observed": {
                "target_training_domains": payload.get("target_training_domains"),
                "forbidden_training_domains": payload.get("forbidden_training_domains"),
                "can_tune_expression": payload.get("can_tune_expression"),
                "can_tune_question_strategy": payload.get("can_tune_question_strategy"),
                "can_tune_chart_facts": payload.get("can_tune_chart_facts"),
            },
        },
        {
            "check_id": "no_live_llm_or_chart_fact_mutation_required",
            "passed": int(payload.get("live_llm_required_count") or 0) == 0
            and int(payload.get("chart_fact_mutation_allowed_count") or 0) == 0,
            "observed": {
                "live_llm_required_count": payload.get("live_llm_required_count"),
                "chart_fact_mutation_allowed_count": payload.get("chart_fact_mutation_allowed_count"),
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_LLM_TRAINING_SYNTHETIC_READINESS_VERSION,
        "task": {
            "task_id": "BL6",
            "title": "Bazi LLM Training Signals And Synthetic Tier",
            "scope": "dedicated_synthetic_tier_and_training_signal_for_bazi_llm_acceptance",
        },
        "synthetic_result": synthetic_result,
        "training_signal": training_signal,
        "completion_summary": {
            "bazi_llm_output_acceptance_completion": 78 if ready else 72,
            "bazi_llm_training_signal_completion": 72 if ready else 50,
            "bazi_llm_synthetic_tier_completion": 75 if ready else 55,
            "bazi_llm_mainline_completion": 75 if ready else 70,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "bl6_bazi_llm_training_synthetic_ready"
            if ready
            else "bl6_bazi_llm_training_synthetic_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "BL7" if ready else "BL6-FIX",
            "title": "Bazi LLM Role And Locale Production Smoke"
            if ready
            else "Fix Bazi LLM Training Synthetic Readiness",
            "reason": "bazi_llm_training_signal_and_synthetic_tier_are_ready"
            if ready
            else "bazi_llm_training_synthetic_checks_failed",
        },
        "boundary": "bl6_trains_expression_and_question_strategy_not_chart_facts",
    }
