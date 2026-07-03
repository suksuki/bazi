from __future__ import annotations

from v30.semantics import build_semantic_dialogue_trace

DIALOGUE_PLANNER_VERSION = "v30.dialogue_planner.v1"
DIALOGUE_PLAN_VERSION = "v30.dialogue_plan.v1"
CUSTOMER_DECISION_FIELD = "reading_surface.conversation_surface"
LEGACY_CUSTOMER_DECISION_FIELD = "reading_surface.current_dialogue_turn"
SURFACE_DECISION_FIELDS = {
    "calibration": "reading_surface.calibration_surface",
    "conversation": "reading_surface.conversation_surface",
    "thinking": "reading_surface.thinking_surface",
}


def build_dialogue_plan(
    *,
    claim_scores: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    question_dialogue_graph: dict[str, object],
    interaction_state: dict[str, object],
    central_feedback_overlay: dict[str, object] | None = None,
) -> dict[str, object]:
    overlay = central_feedback_overlay if isinstance(central_feedback_overlay, dict) else {}
    next_question = _select_next_question(
        recommendations,
        interaction_state=interaction_state,
        question_dialogue_graph=question_dialogue_graph,
        central_feedback_overlay=overlay,
    )
    next_action = _next_action(claim_scores, next_question=next_question, interaction_state=interaction_state)
    stage_opportunities = _stage_question_opportunities(claim_scores, next_question)
    current_turn_seed = _current_turn_seed(next_action, next_question, stage_opportunities, claim_scores)
    decision_features = _decision_features(
        claim_scores=claim_scores,
        recommendations=recommendations,
        next_question=next_question,
        interaction_state=interaction_state,
    )
    semantic_trace = build_semantic_dialogue_trace(
        claim_scores=claim_scores,
        recommendations=recommendations,
        current_question=next_question,
    )
    return {
        "version": DIALOGUE_PLAN_VERSION,
        "planner_version": DIALOGUE_PLANNER_VERSION,
        "decision_owner": "dialogue_brain",
        "customer_decision_field": CUSTOMER_DECISION_FIELD,
        "legacy_customer_decision_field": LEGACY_CUSTOMER_DECISION_FIELD,
        "surface_decision_fields": SURFACE_DECISION_FIELDS,
        "legacy_customer_decision_field_status": "diagnostic_compatibility_only",
        "action": str(next_action.get("action") or ""),
        "reason": str(next_action.get("reason") or ""),
        "current_question_id": str(next_question.get("question_id") or ""),
        "current_question": next_question,
        "next_action": next_action,
        "stage_question_opportunities": stage_opportunities,
        "current_turn_seed": current_turn_seed,
        "selection_inputs": {
            "interaction_visible_question_id": str(interaction_state.get("visible_next_question_id") or ""),
            "invalid_retry_question_id": str(interaction_state.get("invalid_retry_question_id") or ""),
            "graph_memory_question_id": str(question_dialogue_graph.get("next_question_id") or ""),
            "graph_internal_memory_question_id": str(question_dialogue_graph.get("internal_next_question_id") or ""),
            "candidate_count": len(recommendations),
            "candidate_sources": sorted({
                str(row.get("candidate_source") or "unknown")
                for row in recommendations
                if isinstance(row, dict)
            }),
            "boundary": "selection_inputs_are_memory_and_candidates_not_customer_decision_fields",
        },
        "semantic_trace": semantic_trace,
        "decision_features": decision_features,
        "training_signal": {
            "version": "v30.training_signal.dialogue_plan.v1",
            "trainable": True,
            "targets": [
                "dialogue_action_policy",
                "question_selection_policy",
                "overask_penalty_weight",
                "user_cost_weight",
                "stage_question_policy",
                "semantic_question_weight",
            "macro_domain_question_slot_weight",
            "central_feedback_needs_question_topic_weight",
        ],
            "features": sorted(decision_features.keys()),
            "semantic_training_slots": semantic_trace.get("training_slots", []),
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "unconfirmed_hidden_factor_facts",
            ],
        },
        "boundary": "dialogue_plan_selects_surface_route_from_candidates_without_mutating_chart_facts",
    }


def _next_action(
    claim_scores: list[dict[str, object]],
    *,
    next_question: dict[str, object],
    interaction_state: dict[str, object],
) -> dict[str, object]:
    invalid_retry = str(interaction_state.get("invalid_retry_question_id") or "")
    top = claim_scores[0] if claim_scores else {}
    top_score = float(top.get("score") or 0.0)
    if invalid_retry:
        action = "ask_stage_question"
        reason = "invalid_structured_answer_requires_retry"
    elif not claim_scores:
        action = "continue_next_stage"
        reason = "no_candidate_claim_ready"
    elif top.get("requires_question") and next_question:
        action = "ask_stage_question"
        reason = "high_value_claim_needs_user_calibration"
    elif top_score >= 0.72:
        action = "conclude_stage"
        reason = "top_claim_has_enough_multi_module_support"
    elif next_question:
        action = "ask_stage_question"
        reason = "question_has_higher_information_gain_than_premature_conclusion"
    else:
        action = "conclude_stage"
        reason = "no_better_question_available"
    return {
        "version": "v30.central_reading_action.v1",
        "action": action,
        "reason": reason,
        "top_claim_id": str(top.get("claim_id") or ""),
        "top_claim_score": top_score,
        "question_id": str(next_question.get("question_id") or ""),
        "boundary": "central_reading_action_selects_next_step_without_mutating_facts",
    }


def _select_next_question(
    recommendations: list[dict[str, object]],
    *,
    interaction_state: dict[str, object],
    question_dialogue_graph: dict[str, object],
    central_feedback_overlay: dict[str, object],
) -> dict[str, object]:
    requested_topics = [
        str(row)
        for row in _list(central_feedback_overlay.get("requires_question_topics"))
        if str(row)
    ]
    for topic in requested_topics:
        for row in recommendations:
            if str(row.get("topic") or "") == topic:
                return _question_projection(row)
    preferred_ids = [
        str(interaction_state.get("invalid_retry_question_id") or ""),
        str(interaction_state.get("visible_next_question_id") or ""),
        str(question_dialogue_graph.get("next_question_id") or ""),
    ]
    for preferred in preferred_ids:
        if not preferred:
            continue
        for row in recommendations:
            if str(row.get("question_id") or "") == preferred:
                return _question_projection(row)
    return _question_projection(recommendations[0]) if recommendations else {}


def _question_projection(row: dict[str, object]) -> dict[str, object]:
    return {
        "question_id": str(row.get("question_id") or ""),
        "intent_id": str(row.get("intent_id") or ""),
        "stage": str(row.get("stage") or ""),
        "topic": str(row.get("topic") or ""),
        "score": _float(row.get("score"), 0.0),
        "candidate_source": str(row.get("candidate_source") or ""),
        "decision_owner": "dialogue_brain",
        "question_value": row.get("question_value") or "",
        "answer_mode": row.get("answer_mode") or "",
        "answer_constraints": row.get("answer_constraints") if isinstance(row.get("answer_constraints"), dict) else {},
        "expected_information_gain": row.get("expected_information_gain") if isinstance(row.get("expected_information_gain"), dict) else {},
        "semantic_projection": row.get("semantic_projection") if isinstance(row.get("semantic_projection"), dict) else {},
        "boundary": "dialogue_plan_question_projection_is_internal_selection_not_chart_fact",
    }


def _stage_question_opportunities(
    claim_scores: list[dict[str, object]],
    next_question: dict[str, object],
) -> list[dict[str, object]]:
    if not next_question:
        return []
    step_id = _step_id_for_question(next_question)
    target_claims = [
        str(row.get("claim_id") or "")
        for row in claim_scores
        if row.get("requires_question") is True
        and str(row.get("domain") or "") in {str(next_question.get("topic") or ""), "hidden_factor", "useful_god"}
    ][:4]
    if not target_claims and claim_scores:
        target_claims = [str(claim_scores[0].get("claim_id") or "")]
    return [{
        "version": "v30.stage_question_opportunity.v1",
        "step_id": step_id,
        "stage": str(next_question.get("stage") or ""),
        "topic": str(next_question.get("topic") or ""),
        "question_id": str(next_question.get("question_id") or ""),
        "target_claim_ids": target_claims,
        "display_mode": "inline_stage_question",
        "reason": "stage_question_reduces_claim_uncertainty",
        "decision_owner": "dialogue_brain",
        "boundary": "stage_question_updates_weights_not_chart_facts",
    }]


def _current_turn_seed(
    next_action: dict[str, object],
    next_question: dict[str, object],
    stage_opportunities: list[dict[str, object]],
    claim_scores: list[dict[str, object]],
) -> dict[str, object]:
    question_id = str(next_question.get("question_id") or "")
    opportunity = {}
    for row in stage_opportunities:
        if isinstance(row, dict) and str(row.get("question_id") or "") == question_id:
            opportunity = row
            break
    target_claim_ids = opportunity.get("target_claim_ids") if isinstance(opportunity, dict) else []
    if not isinstance(target_claim_ids, list) or not target_claim_ids:
        target_claim_ids = [
            str(row.get("claim_id") or "")
            for row in claim_scores
            if row.get("requires_question") is True
        ][:4]
    return {
        "version": "v30.dialogue_turn_seed.v1",
        "action": str(next_action.get("action") or ""),
        "question_id": question_id,
        "stage_id": str(opportunity.get("step_id") or ""),
        "target_claim_ids": [str(row) for row in target_claim_ids if row][:4],
        "decision_owner": "dialogue_brain",
        "source_plan_version": DIALOGUE_PLAN_VERSION,
        "boundary": "dialogue_turn_seed_guides_projection_without_overriding_chart_facts",
    }


def _decision_features(
    *,
    claim_scores: list[dict[str, object]],
    recommendations: list[dict[str, object]],
    next_question: dict[str, object],
    interaction_state: dict[str, object],
) -> dict[str, object]:
    top = claim_scores[0] if claim_scores else {}
    answered = interaction_state.get("answered_question_ids", [])
    answered_count = len(answered) if isinstance(answered, list) else 0
    top_claim_score = _float(top.get("score"), 0.0)
    question_score = _float(next_question.get("score"), 0.0)
    requires_question_count = sum(1 for row in claim_scores if isinstance(row, dict) and row.get("requires_question") is True)
    overask_penalty = min(0.6, answered_count * 0.12)
    user_cost = 0.34 if str(next_question.get("topic") or "") == "hidden_factor" else 0.22 if next_question else 0.0
    necessity_score = max(0.0, min(1.0, question_score + requires_question_count * 0.08 - overask_penalty - user_cost * 0.2))
    return {
        "top_claim_id": str(top.get("claim_id") or ""),
        "top_claim_score": round(top_claim_score, 3),
        "top_claim_requires_question": bool(top.get("requires_question")),
        "requires_question_count": requires_question_count,
        "candidate_question_count": len(recommendations),
        "current_question_score": round(question_score, 3),
        "answered_count": answered_count,
        "user_cost": round(user_cost, 3),
        "overask_penalty": round(overask_penalty, 3),
        "necessity_score": round(necessity_score, 3),
        "invalid_retry_active": bool(interaction_state.get("invalid_retry_question_id")),
    }


def _step_id_for_question(question: dict[str, object]) -> str:
    topic = str(question.get("topic") or "")
    stage = str(question.get("stage") or "")
    if topic in {"time_context", "timing"} or stage == "context_completion":
        return "timing_layers"
    if topic in {"useful_god", "structure_dynamic", "decision"} or stage == "candidate_review":
        return "path_reasoning"
    if topic in {"hidden_factor"} or stage == "dialogue_discovery":
        return "portrait_projection"
    if topic in {"career", "wealth", "relationship", "health", "practical_reading"}:
        return "domain_synthesis"
    if stage == "mainline_review":
        return "structure_reasoning"
    return ""


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
