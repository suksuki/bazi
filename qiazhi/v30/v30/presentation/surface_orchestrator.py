from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult


USER_VISIBLE_ROLES = {"guest", "user"}


def build_surface_orchestration(
    runtime: CoreRuntimeResult,
    *,
    reading_summary: dict[str, object],
    final_synthesis: dict[str, object],
    domain_cards: list[dict[str, object]],
    current_dialogue_turn: dict[str, object],
    next_question: dict[str, object],
    dialogue: dict[str, object],
    questions: list[dict[str, object]],
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    calibration_surface = _calibration_surface(
        current_dialogue_turn=current_dialogue_turn,
        role_key=role_key,
    )
    conversation_surface = _conversation_surface(
        current_dialogue_turn=current_dialogue_turn,
        next_question=next_question,
        dialogue=dialogue,
        questions=questions,
    )
    thinking_surface = _thinking_surface(runtime)
    return {
        "version": "v30.surface_orchestrator.v1",
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "surface_order": [
            "reading_surface",
            "calibration_surface",
            "conversation_surface",
            "thinking_surface",
        ],
        "state_machine": {
            "version": "v30.surface_state_machine.v1",
            "initial": "reading_first",
            "allowed_transitions": [
                "reading_first -> optional_calibration_probe",
                "optional_calibration_probe -> refined_reading",
                "refined_reading -> optional_conversation",
                "optional_conversation -> context_update",
                "context_update -> refined_reading",
            ],
            "boundary": "surface_state_machine_routes_user_surfaces_not_chart_facts",
        },
        "reading_surface_policy": _reading_surface_policy(
            reading_summary=reading_summary,
            final_synthesis=final_synthesis,
            domain_cards=domain_cards,
        ),
        "output_pipeline": output_pipeline_contract(),
        "calibration_surface": calibration_surface,
        "conversation_surface": conversation_surface,
        "thinking_surface": thinking_surface,
        "legacy_compatibility": {
            "version": "v30.surface_legacy_compatibility.v1",
            "direct_legacy_fields_exposed": role_key not in USER_VISIBLE_ROLES,
            "current_dialogue_turn_retained": role_key not in USER_VISIBLE_ROLES,
            "next_question_retained": role_key not in USER_VISIBLE_ROLES,
            "dialogue_retained": role_key not in USER_VISIBLE_ROLES,
            "frontend_should_prefer": [
                "reading_surface.calibration_surface",
                "reading_surface.conversation_surface",
                "reading_surface.thinking_surface",
            ],
            "reading_surface_current_dialogue_turn_is_legacy": True,
            "boundary": "legacy_fields_are_role_gated_and_not_customer_product_entries",
        },
        "boundary": "surface_orchestrator_routes_outputs_without_making_bazi_decisions",
    }


def surface_orchestration_policy() -> dict[str, object]:
    return {
        "version": "v30.surface_orchestration_policy.v1",
        "reading_first": True,
        "probe_only_when_valuable": True,
        "conversation_user_invited_only": True,
        "thinking_requested_only": True,
        "frontend_should_not_render_current_dialogue_turn_in_stage_pages": True,
        "legacy_current_dialogue_turn_status": "diagnostic_compatibility_only",
        "customer_direct_legacy_fields_hidden": True,
        "boundary": "surface_policy_separates_reading_probe_conversation_and_thinking",
    }


def output_pipeline_contract() -> dict[str, object]:
    return {
        "version": "v30.surface_output_pipeline.v1",
        "stages": [
            {
                "stage": "signals",
                "owner": "engines_and_signal_registry",
                "product_output": "evidence_bound_material",
                "chart_fact_mutation_allowed": False,
            },
            {
                "stage": "verdict",
                "owner": "decision_engine",
                "product_output": "ranked_verdicts_and_branch_candidates",
                "chart_fact_mutation_allowed": False,
            },
            {
                "stage": "advice",
                "owner": "central_brain_final_synthesis",
                "product_output": "conclusion_first_advice",
                "chart_fact_mutation_allowed": False,
            },
            {
                "stage": "explanation",
                "owner": "llm_expression_adapter",
                "product_output": "customer_readable_expression",
                "chart_fact_mutation_allowed": False,
            },
            {
                "stage": "dialogue_refinement",
                "owner": "calibration_surface_and_conversation_surface",
                "product_output": "user_feedback_and_followup_context",
                "chart_fact_mutation_allowed": False,
            },
        ],
        "runtime_order": [
            "SignalRegistry",
            "DecisionContract",
            "Verdict",
            "Advice",
            "Explanation",
            "DialogueRefinement",
        ],
        "llm_role": "expression_and_dialogue_language_after_core_verdict",
        "decision_authority": "DecisionEngineVerdict",
        "brain_role": "orchestrates_evidence_weight_feedback_quality_and_surface_routing",
        "boundary": "output_pipeline_turns_engine_signals_into_user_output_without_chart_fact_mutation",
    }


def _reading_surface_policy(
    *,
    reading_summary: dict[str, object],
    final_synthesis: dict[str, object],
    domain_cards: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "version": "v30.reading_surface_policy.v1",
        "primary_surface": True,
        "report_first": True,
        "must_show_verdict_before_questions": True,
        "auto_show_conversation": False,
        "auto_show_probe": False,
        "conversation_entry_position": "after_report_or_user_invited",
        "thinking_entry_position": "requested_by_user",
        "has_final_synthesis": bool(final_synthesis.get("conclusion") or final_synthesis.get("advice")),
        "domain_card_count": len(domain_cards),
        "status": str(reading_summary.get("status") or "ready"),
        "boundary": "reading_surface_policy_keeps_report_output_separate_from_dialogue",
    }


def _calibration_surface(
    *,
    current_dialogue_turn: dict[str, object],
    role_key: str,
) -> dict[str, object]:
    probe_cards: list[dict[str, object]] = []
    if _is_probe_turn(current_dialogue_turn):
        card = _probe_card(current_dialogue_turn)
        if card:
            probe_cards.append(card)
    max_default_visible = 2 if role_key not in USER_VISIBLE_ROLES else 1
    return {
        "version": "v30.calibration_surface.v1",
        "status": "available" if probe_cards else "not_needed",
        "visible_probe_count": min(len(probe_cards), max_default_visible),
        "visible_probe_cards": probe_cards[:max_default_visible],
        "probe_policy": {
            "version": "v30.calibration_probe_policy.v1",
            "max_default_visible": max_default_visible,
            "skippable_required": True,
            "allowed_triggers": [
                "hidden_attribute_calibration",
                "conflicting_evidence_blocks_verdict",
                "single_answer_materially_changes_advice",
            ],
            "disallowed_triggers": [
                "generic_conversation",
                "stage_navigation",
                "legacy_question_pool",
            ],
            "boundary": "probe_policy_prevents_generic_dialogue_from_entering_stage_pages",
        },
        "entry_policy": {
            "inline_collapsed": True,
            "auto_open": False,
            "requires_context_match": True,
            "boundary": "calibration_probe_is_contextual_and_optional",
        },
        "boundary": "calibration_surface_contains_only_high_value_structured_probe_cards",
    }


def _probe_card(current_dialogue_turn: dict[str, object]) -> dict[str, object]:
    question = _dict(current_dialogue_turn.get("question"))
    if not question.get("question_id"):
        return {}
    options = _option_rows(question)
    return {
        "version": "v30.calibration_probe_card.v1",
        "card_id": f"probe:{question.get('question_id')}",
        "question_id": str(question.get("question_id") or ""),
        "stage_id": str(current_dialogue_turn.get("stage_id") or ""),
        "title": "校准这个判断",
        "reason": str(current_dialogue_turn.get("why_now") or "只补一个会影响本页判断的关键背景。"),
        "prompt": str(question.get("label") or question.get("question") or question.get("question_id") or ""),
        "topic": str(question.get("topic") or ""),
        "answer_constraints": _dict(question.get("answer_constraints")),
        "response_option_set": _dict(question.get("response_option_set")),
        "options": options[:5],
        "skippable": True,
        "target_hidden_attribute": _target_hidden_attribute(question, current_dialogue_turn),
        "target_claim_ids": _string_list(current_dialogue_turn.get("target_claim_ids"))[:4],
        "visual_hint": _dict(current_dialogue_turn.get("visual_hint")),
        "submit_contract": {
            "version": "v30.surface_submit_contract.v1",
            "submit_surface": "calibration_surface",
            "submit_source_id": f"probe:{question.get('question_id')}",
            "method": "POST",
            "endpoint_template": "/api/v30/readings/{reading_id}/questions/{question_id}/answer",
            "required_payload_fields": [
                "answer",
                "submit_surface",
                "submit_source_id",
                "selected_option",
                "structured_payload",
            ],
            "deprecated_legacy_source": "reading_surface.current_dialogue_turn.question",
            "boundary": "calibration_submit_contract_routes_probe_feedback_not_conversation",
        },
        "output_contract": [
            "AnswerSignal",
            "HiddenAttributeUpdate",
            "SignalConfidenceDiff",
            "VerdictAdviceRefinement",
        ],
        "presentation": {
            "style": "inline_collapsed",
            "label": "校准",
            "boundary": "probe_card_is_not_a_conversation_thread",
        },
        "boundary": "calibration_probe_card_updates_context_without_mutating_chart_facts",
    }


def _conversation_surface(
    *,
    current_dialogue_turn: dict[str, object],
    next_question: dict[str, object],
    dialogue: dict[str, object],
    questions: list[dict[str, object]],
) -> dict[str, object]:
    suggested_question = _suggested_conversation_question(current_dialogue_turn, next_question)
    return {
        "version": "v30.conversation_surface.v1",
        "status": "available",
        "title": "连续智能对话",
        "entry_policy": {
            "user_invited_only": True,
            "auto_open": False,
            "auto_submit": False,
            "can_start_from_seed": True,
            "can_start_from_user_question": True,
            "boundary": "conversation_surface_never_auto_interrupts_reading_stage",
        },
        "cta": [
            {"action": "continue_dialogue", "label": "继续追问"},
            {"action": "ask_new_question", "label": "问一个新问题"},
            {"action": "explain_current_verdict", "label": "解释当前结论"},
        ],
        "submit_contract": {
            "version": "v30.surface_submit_contract.v1",
            "submit_surface": "conversation_surface",
            "create_endpoint_template": "/api/v30/readings/{reading_id}/dialogues",
            "append_endpoint_template": "/api/v30/readings/{reading_id}/dialogues/{dialogue_id}/turns",
            "legacy_answer_endpoint_allowed": False,
            "boundary": "conversation_submit_contract_uses_dialogue_session_endpoints",
        },
        "suggested_question": suggested_question,
        "dialogue_summary": {
            "version": str(dialogue.get("version") or ""),
            "status": str(dialogue.get("status") or ""),
            "summary": str(dialogue.get("summary") or ""),
            "progress": _dict(dialogue.get("progress")),
        },
        "seed_source": {
            "question_count": len(questions),
            "legacy_next_question_id": str(next_question.get("question_id") or ""),
            "boundary": "question_candidates_are_seed_material_not_stage_page_content",
        },
        "boundary": "conversation_surface_is_invited_chat_not_report_interrupt",
    }


def _thinking_surface(runtime: CoreRuntimeResult) -> dict[str, object]:
    stage_points = runtime.question_plan.policy_effect.get("stage_points", [])
    if not isinstance(stage_points, list):
        stage_points = []
    central = runtime.question_plan.policy_effect.get("central_reading_state", {})
    central = central if isinstance(central, dict) else {}
    return {
        "version": "v30.thinking_surface.v1",
        "status": "available",
        "entry_label": "查看分析过程",
        "entry_policy": {
            "requested_only": True,
            "auto_open": False,
            "show_raw_prompt": False,
            "show_raw_schema": False,
            "boundary": "thinking_surface_is_process_visibility_not_report_body",
        },
        "process_summary": {
            "stage_point_count": len(stage_points),
            "has_central_decision_trace": bool(central.get("brain_decision_trace")),
            "visible_process_kinds": [
                "stage_summary",
                "evidence_link",
                "decision_boundary",
            ],
        },
        "boundary": "thinking_surface_exposes_process_without_dialogue_navigation",
    }


def _is_probe_turn(current_dialogue_turn: dict[str, object]) -> bool:
    if current_dialogue_turn.get("action") != "ask":
        return False
    question = _dict(current_dialogue_turn.get("question"))
    if not question.get("question_id"):
        return False
    decision = _dict(current_dialogue_turn.get("decision_basis"))
    selected_action = str(decision.get("selected_action") or "")
    if selected_action == "ask_hidden_attribute_probe":
        return True
    if str(question.get("topic") or "") == "hidden_factor":
        return True
    constraints = _dict(question.get("answer_constraints"))
    if str(constraints.get("type") or "") == "structured_hidden_factor":
        return True
    if str(constraints.get("answer_type") or "") == "structured_hidden_factor":
        return True
    response_set = _dict(question.get("response_option_set"))
    if str(response_set.get("kind") or "") == "structured_hidden_factor":
        return True
    return False


def _suggested_conversation_question(
    current_dialogue_turn: dict[str, object],
    next_question: dict[str, object],
) -> dict[str, object]:
    if _is_probe_turn(current_dialogue_turn):
        return {}
    question = _dict(current_dialogue_turn.get("question"))
    if not question:
        question = next_question
    if not isinstance(question, dict) or not question.get("question_id"):
        return {}
    return {
        "question_id": str(question.get("question_id") or ""),
        "label": str(question.get("label") or question.get("question") or ""),
        "topic": str(question.get("topic") or ""),
        "auto_open": False,
        "source": "central_brain_seed",
        "boundary": "suggested_question_is_conversation_seed_not_stage_inline_question",
    }


def _target_hidden_attribute(
    question: dict[str, object],
    current_dialogue_turn: dict[str, object],
) -> str:
    constraints = _dict(question.get("answer_constraints"))
    explicit = str(
        constraints.get("target_hidden_attribute")
        or constraints.get("target_attribute")
        or constraints.get("target")
        or ""
    )
    if explicit:
        return explicit
    semantic = _dict(current_dialogue_turn.get("semantic_focus"))
    slot = str(semantic.get("selected_slot") or "")
    if slot:
        return slot
    topic = str(question.get("topic") or "")
    return topic or "hidden_factor"


def _option_rows(question: dict[str, object]) -> list[dict[str, object]]:
    response_set = _dict(question.get("response_option_set"))
    set_options = response_set.get("options")
    if isinstance(set_options, list) and set_options:
        return [_public_option(row) for row in set_options if isinstance(row, dict)]
    options = question.get("options")
    if isinstance(options, list):
        return [_public_option(row) for row in options if isinstance(row, dict)]
    return []


def _public_option(row: dict[str, object]) -> dict[str, object]:
    return {
        "option_id": str(row.get("option_id") or row.get("value") or ""),
        "label": str(row.get("label") or row.get("value") or ""),
        "value": str(row.get("value") or row.get("option_id") or ""),
        "option_type": str(row.get("option_type") or row.get("kind") or ""),
    }


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: object) -> list[str]:
    return [str(row) for row in value if row] if isinstance(value, list) else []
