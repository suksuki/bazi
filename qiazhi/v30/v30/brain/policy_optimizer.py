from __future__ import annotations

from typing import Any

from v30.brain.contracts import BrainTrainingExample

CENTRAL_BRAIN_POLICY_OPTIMIZER_VERSION = "v30.central_brain_policy_optimizer.v1"


def optimize_central_brain_policy(
    examples: list[BrainTrainingExample],
    *,
    base_policy: dict[str, Any] | None = None,
    min_examples: int = 3,
    max_delta: float = 0.06,
) -> dict[str, Any]:
    safe_examples = [example for example in examples if _example_is_safe(example)]
    base_weights = _base_weights(base_policy or {})
    if len(safe_examples) < min_examples:
        return {
            "version": CENTRAL_BRAIN_POLICY_OPTIMIZER_VERSION,
            "status": "insufficient_data",
            "example_count": len(safe_examples),
            "min_examples": min_examples,
            "weights": base_weights,
            "weight_deltas": {},
            "promotion_signal": "blocked",
            "blocked_reason": "not_enough_safe_brain_training_examples",
            "chart_fact_mutation_allowed": False,
            "boundary": "central_brain_policy_optimizer_trains_policy_weights_not_chart_facts",
        }
    metrics = _aggregate_metrics(safe_examples)
    deltas = _weight_deltas(metrics, max_delta=max_delta)
    weights = {key: round(base_weights.get(key, 1.0) + deltas.get(key, 0.0), 3) for key in base_weights}
    promotion_signal = "eligible"
    blocked_reasons: list[str] = []
    if metrics["average_template_risk"] > 0.45:
        promotion_signal = "blocked"
        blocked_reasons.append("template_risk_too_high")
    if metrics["average_overclaim_risk"] > 0.45:
        promotion_signal = "blocked"
        blocked_reasons.append("overclaim_risk_too_high")
    if metrics["average_claim_correctness"] < 0.45:
        promotion_signal = "blocked"
        blocked_reasons.append("claim_correctness_too_low")
    return {
        "version": CENTRAL_BRAIN_POLICY_OPTIMIZER_VERSION,
        "status": "ready",
        "example_count": len(safe_examples),
        "metrics": metrics,
        "weights": weights,
        "weight_deltas": deltas,
        "promotion_signal": promotion_signal,
        "blocked_reasons": blocked_reasons,
        "trainable_targets": sorted({target for example in safe_examples for target in example.trainable_targets}),
        "blocked_targets": ["chart_facts", "calendar_conversion", "pillar_calculation", "unconfirmed_hidden_factor_facts"],
        "chart_fact_mutation_allowed": False,
        "boundary": "central_brain_policy_optimizer_trains_policy_weights_not_chart_facts",
    }


def _example_is_safe(example: BrainTrainingExample) -> bool:
    return (
        example.safety.chart_fact_mutation_allowed is False
        and example.safety.llm_fact_injection_detected is False
        and example.safety.production_policy_write_allowed is False
        and not {"chart_facts", "calendar_conversion", "pillar_calculation", "unconfirmed_hidden_factor_facts"}.intersection(example.trainable_targets)
    )


def _base_weights(policy: dict[str, Any]) -> dict[str, float]:
    weights = policy.get("weights") if isinstance(policy.get("weights"), dict) else policy
    weights = weights if isinstance(weights, dict) else {}
    defaults = {
        "claim_score.support_strength": 1.0,
        "claim_score.evidence_diversity": 1.0,
        "claim_score.graph_path_coherence": 1.0,
        "claim_score.feedback_alignment": 1.0,
        "claim_score.actionability": 1.0,
        "claim_score.counter_evidence_penalty": 1.0,
        "claim_score.missing_context_penalty": 1.0,
        "claim_score.overclaim_penalty": 1.0,
        "next_action.information_gain": 1.0,
        "next_action.claim_impact": 1.0,
        "next_action.user_cost_penalty": 1.0,
        "next_action.overask_penalty": 1.0,
        "final_synthesis.evidence_binding": 1.0,
        "final_synthesis.conclusion_strength": 1.0,
        "final_synthesis.advice_actionability": 1.0,
        "final_synthesis.template_risk_penalty": 1.0,
        "final_synthesis.overclaim_risk_penalty": 1.0,
    }
    for key in defaults:
        defaults[key] = _float(weights.get(key), defaults[key])
    return defaults


def _aggregate_metrics(examples: list[BrainTrainingExample]) -> dict[str, Any]:
    count = max(1, len(examples))
    answered_count = sum(1 for example in examples if example.outcome.user_answered)
    useful_count = sum(1 for example in examples if example.outcome.followup_useful is True)
    contradiction_count = sum(1 for example in examples if example.outcome.contradiction_found)
    return {
        "average_claim_correctness": round(sum(example.structured_labels.claim_correctness for example in examples) / count, 3),
        "average_question_information_gain": round(sum(example.structured_labels.question_information_gain for example in examples) / count, 3),
        "average_advice_actionability": round(sum(example.structured_labels.advice_actionability for example in examples) / count, 3),
        "average_template_risk": round(sum(example.structured_labels.template_risk for example in examples) / count, 3),
        "average_overclaim_risk": round(sum(example.structured_labels.overclaim_risk for example in examples) / count, 3),
        "average_user_cost": round(sum(example.structured_labels.user_cost for example in examples) / count, 3),
        "answered_rate": round(answered_count / count, 3),
        "useful_followup_rate": round(useful_count / count, 3),
        "contradiction_rate": round(contradiction_count / count, 3),
    }


def _weight_deltas(metrics: dict[str, Any], *, max_delta: float) -> dict[str, float]:
    quality = _float(metrics.get("average_claim_correctness"))
    info_gain = _float(metrics.get("average_question_information_gain"))
    actionability = _float(metrics.get("average_advice_actionability"))
    template_risk = _float(metrics.get("average_template_risk"))
    overclaim_risk = _float(metrics.get("average_overclaim_risk"))
    user_cost = _float(metrics.get("average_user_cost"))
    useful = _float(metrics.get("useful_followup_rate"))
    contradiction = _float(metrics.get("contradiction_rate"))
    return {
        "claim_score.support_strength": _clip((quality - 0.5) * 0.08, max_delta),
        "claim_score.evidence_diversity": _clip((quality - 0.5) * 0.05, max_delta),
        "claim_score.graph_path_coherence": _clip((quality + actionability - 1.0) * 0.04, max_delta),
        "claim_score.feedback_alignment": _clip((useful - contradiction) * 0.05, max_delta),
        "claim_score.actionability": _clip((actionability - 0.5) * 0.08, max_delta),
        "claim_score.counter_evidence_penalty": _clip(contradiction * 0.06, max_delta),
        "claim_score.missing_context_penalty": _clip((0.5 - info_gain) * 0.03, max_delta),
        "claim_score.overclaim_penalty": _clip(overclaim_risk * 0.08, max_delta),
        "next_action.information_gain": _clip((info_gain - 0.5) * 0.08, max_delta),
        "next_action.claim_impact": _clip((quality - 0.5) * 0.04, max_delta),
        "next_action.user_cost_penalty": _clip(user_cost * 0.05, max_delta),
        "next_action.overask_penalty": _clip(template_risk * 0.03 + user_cost * 0.03, max_delta),
        "final_synthesis.evidence_binding": _clip((quality - 0.5) * 0.06, max_delta),
        "final_synthesis.conclusion_strength": _clip((quality + actionability - 1.0) * 0.05, max_delta),
        "final_synthesis.advice_actionability": _clip((actionability - 0.5) * 0.08, max_delta),
        "final_synthesis.template_risk_penalty": _clip(template_risk * 0.08, max_delta),
        "final_synthesis.overclaim_risk_penalty": _clip(overclaim_risk * 0.08, max_delta),
    }


def _clip(value: float, max_delta: float) -> float:
    return round(max(-max_delta, min(max_delta, value)), 3)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
