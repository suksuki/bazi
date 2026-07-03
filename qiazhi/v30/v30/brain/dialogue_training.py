from __future__ import annotations

DIALOGUE_TRAINING_TRACE_VERSION = "v30.dialogue_training_trace.v1"


def build_dialogue_training_trace(
    *,
    dialogue_plan: dict[str, object],
    feedback_weight_update: dict[str, object],
    question_outcomes: list[dict[str, object]],
) -> dict[str, object]:
    semantic_trace = dialogue_plan.get("semantic_trace", {})
    semantic_trace = semantic_trace if isinstance(semantic_trace, dict) else {}
    decision_features = dialogue_plan.get("decision_features", {})
    decision_features = decision_features if isinstance(decision_features, dict) else {}
    current_question = dialogue_plan.get("current_question", {})
    current_question = current_question if isinstance(current_question, dict) else {}
    feedback_summary = feedback_weight_update.get("summary", {})
    feedback_summary = feedback_summary if isinstance(feedback_summary, dict) else {}
    answered = [
        row for row in question_outcomes
        if isinstance(row, dict) and row.get("constraint_valid", True) is not False
    ]
    return {
        "version": DIALOGUE_TRAINING_TRACE_VERSION,
        "trainable": True,
        "dialogue_action": str(dialogue_plan.get("action") or ""),
        "current_question_id": str(dialogue_plan.get("current_question_id") or ""),
        "current_macro_domain": _nested_str(current_question, "semantic_projection", "macro_domain"),
        "semantic_training_slots": _str_list(semantic_trace.get("training_slots")),
        "decision_features": {
            "top_claim_score": _float(decision_features.get("top_claim_score"), 0.0),
            "current_question_score": _float(decision_features.get("current_question_score"), 0.0),
            "necessity_score": _float(decision_features.get("necessity_score"), 0.0),
            "user_cost": _float(decision_features.get("user_cost"), 0.0),
            "overask_penalty": _float(decision_features.get("overask_penalty"), 0.0),
            "answered_count": int(_float(decision_features.get("answered_count"), 0.0)),
        },
        "feedback_labels": {
            "answered_count": len(answered),
            "positive_claim_ids": _str_list(feedback_summary.get("positive_claim_ids"))[:8],
            "contradicted_claim_ids": _str_list(feedback_summary.get("contradicted_claim_ids"))[:8],
        },
        "trainable_targets": [
            "dialogue_action_policy",
            "question_selection_policy",
            "semantic_question_weight",
            "macro_domain_question_slot_weight",
            "hidden_factor_probe_slot_weight",
            "answer_quality_policy",
            "overask_penalty_weight",
            "user_cost_weight",
        ],
        "blocked_targets": [
            "chart_facts",
            "calendar_conversion",
            "pillar_calculation",
            "unconfirmed_hidden_factor_facts",
        ],
        "quality_gates": {
            "requires_single_customer_question": True,
            "requires_semantic_slot": bool(_str_list(semantic_trace.get("training_slots"))),
            "requires_chart_fact_immutability": True,
            "requires_feedback_separation": True,
        },
        "boundary": "dialogue_training_trace_extracts_policy_learning_signal_without_mutating_bazi_facts",
    }


def _nested_str(payload: dict[str, object], section: str, key: str) -> str:
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return ""
    return str(section_payload.get(key) or "")


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
