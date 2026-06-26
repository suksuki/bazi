from __future__ import annotations

from typing import Any

from v30.validation.intelligent_question_interaction_audit import run_intelligent_question_interaction_audit
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


QUESTION_MODEL_SIGNAL_TRAINING_READINESS_VERSION = "v30.question_model_signal_training_readiness.v1"


def run_question_model_signal_training_readiness(
    reading_id: str = "iq2-question-model-signal-training",
) -> dict[str, object]:
    interaction_loop = run_synthetic_tier("interaction_loop")
    signals = extract_training_signals(interaction_loop)
    personalization_signal = next(
        (
            signal for signal in signals
            if signal.signal_id == "v30.training_signal.question_model_signal_personalization"
        ),
        None,
    )
    iq1 = run_intelligent_question_interaction_audit(reading_id=f"{reading_id}-iq1")
    return build_question_model_signal_training_readiness(
        interaction_loop=interaction_loop.model_dump(mode="json"),
        personalization_signal=personalization_signal.model_dump(mode="json") if personalization_signal else {},
        iq1_audit=iq1,
    )


def build_question_model_signal_training_readiness(
    *,
    interaction_loop: dict[str, Any],
    personalization_signal: dict[str, Any],
    iq1_audit: dict[str, Any],
) -> dict[str, object]:
    signal_payload = _mapping(personalization_signal.get("payload"))
    iq1_decision = _mapping(iq1_audit.get("decision"))
    checks = [
        {
            "check_id": "interaction_loop_synthetic_passes_after_model_signal_personalization",
            "passed": interaction_loop.get("suite_id") == "v30.synthetic.interaction_loop"
            and interaction_loop.get("case_count") == interaction_loop.get("passed_count")
            and int(interaction_loop.get("case_count") or 0) >= 5,
            "observed": {
                "suite_id": interaction_loop.get("suite_id"),
                "case_count": interaction_loop.get("case_count"),
                "passed_count": interaction_loop.get("passed_count"),
            },
        },
        {
            "check_id": "training_signal_extracts_model_signal_question_focus",
            "passed": personalization_signal.get("signal_id") == "v30.training_signal.question_model_signal_personalization"
            and personalization_signal.get("domain") == "question_intelligence"
            and float(personalization_signal.get("strength") or 0.0) >= 0.8,
            "observed": {
                "signal_id": personalization_signal.get("signal_id"),
                "domain": personalization_signal.get("domain"),
                "strength": personalization_signal.get("strength"),
            },
        },
        {
            "check_id": "signal_has_actionable_family_topic_coverage",
            "passed": int(signal_payload.get("model_signal_focused_count") or 0) >= 5
            and int(signal_payload.get("model_signal_focus_reason_count") or 0) >= 10
            and len(signal_payload.get("model_signal_focus_topics", [])) >= 4
            and len(signal_payload.get("model_signal_focus_pairs", [])) >= 6,
            "observed": {
                "model_signal_focused_count": signal_payload.get("model_signal_focused_count"),
                "model_signal_focus_reason_count": signal_payload.get("model_signal_focus_reason_count"),
                "model_signal_focus_topics": signal_payload.get("model_signal_focus_topics", []),
                "model_signal_focus_pairs": signal_payload.get("model_signal_focus_pairs", []),
            },
        },
        {
            "check_id": "signal_can_only_tune_question_strategy",
            "passed": signal_payload.get("can_tune_question_strategy") is True
            and signal_payload.get("can_tune_chart_facts") is False
            and int(signal_payload.get("chart_fact_mutation_allowed_count") or 0) == 0,
            "observed": {
                "can_tune_question_strategy": signal_payload.get("can_tune_question_strategy"),
                "can_tune_chart_facts": signal_payload.get("can_tune_chart_facts"),
                "chart_fact_mutation_allowed_count": signal_payload.get("chart_fact_mutation_allowed_count"),
                "boundary": signal_payload.get("boundary"),
            },
        },
        {
            "check_id": "iq1_audit_still_accepts_intelligent_question_interaction",
            "passed": iq1_audit.get("version") == "v30.intelligent_question_interaction_audit.v1"
            and iq1_decision.get("intelligent_question_interaction_ready") is True
            and iq1_decision.get("decision_status") == "iq1_intelligent_question_interaction_ready",
            "observed": {
                "iq1_version": iq1_audit.get("version"),
                "iq1_ready": iq1_decision.get("intelligent_question_interaction_ready"),
                "iq1_decision_status": iq1_decision.get("decision_status"),
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": QUESTION_MODEL_SIGNAL_TRAINING_READINESS_VERSION,
        "task": {
            "task_id": "IQ2",
            "title": "Question Model-Signal Training Readiness",
            "scope": "make model-signal-personalized question priority observable and trainable without chart-fact mutation",
        },
        "training_summary": {
            "interaction_loop_suite_id": interaction_loop.get("suite_id"),
            "interaction_loop_passed": interaction_loop.get("case_count") == interaction_loop.get("passed_count"),
            "personalization_signal_id": personalization_signal.get("signal_id", ""),
            "personalization_signal_strength": personalization_signal.get("strength", 0.0),
            "model_signal_focus_topics": signal_payload.get("model_signal_focus_topics", []),
            "model_signal_focus_pairs": signal_payload.get("model_signal_focus_pairs", []),
            "can_tune_question_strategy": signal_payload.get("can_tune_question_strategy") is True,
            "can_tune_chart_facts": signal_payload.get("can_tune_chart_facts") is True,
            "chart_fact_tuning_blocked": signal_payload.get("can_tune_chart_facts") is False,
        },
        "checks": checks,
        "decision": {
            "training_readiness_ready": ready,
            "decision_status": "iq2_question_model_signal_training_ready"
            if ready
            else "iq2_question_model_signal_training_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "next_mainline_selection": {
            "task_id": "IQ-S1" if ready else "IQ2-FIX",
            "title": "Question Intelligence Steady State"
            if ready
            else "Fix Question Model-Signal Training Readiness",
            "reason": "model_signal_personalized_question_strategy_is_trainable"
            if ready
            else "model_signal_question_training_checks_failed",
        },
        "boundary": "iq2_trains_question_strategy_from_model_signal_focus_without_mutating_chart_facts",
    }


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
