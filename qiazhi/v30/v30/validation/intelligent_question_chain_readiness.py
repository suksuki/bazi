from __future__ import annotations

from typing import Any, Mapping

from v30.llm import build_bazi_llm_context_pack
from v30.presentation import build_presentation_model
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


INTELLIGENT_QUESTION_CHAIN_READINESS_VERSION = "v30.intelligent_question_chain_readiness.v1"


def run_intelligent_question_chain_readiness(
    reading_id: str = "iq4-intelligent-question-chain",
) -> dict[str, object]:
    initial = create_smoke_runtime(reading_id, day_master="庚", day_master_element="metal")
    initial_fingerprint = _core_fingerprint(initial)
    initial_view = build_presentation_model(initial, role_key="user", locale="zh", client="web").model_dump(mode="json")
    first_question_id = _visible_question_id(initial_view)
    first = attach_question_outcome(
        initial,
        first_question_id,
        {
            "answer": "先看财富风险和近期选择。",
            "selected_option": "wealth:risk",
            "confidence": 0.84,
            "feedback_tags": ["wealth", "decision", "customer_loop"],
        },
    )
    first_view = build_presentation_model(first, role_key="user", locale="zh", client="web").model_dump(mode="json")
    second_question_id = _visible_question_id(first_view)
    second = attach_question_outcome(
        first,
        second_question_id,
        {
            "answer": "继续看事业方向，最近有岗位选择压力。",
            "selected_option": "career:direction",
            "confidence": 0.78,
            "feedback_tags": ["career", "timing", "customer_loop"],
        },
    )
    second_view_user = build_presentation_model(second, role_key="user", locale="zh", client="web").model_dump(mode="json")
    second_view_admin = build_presentation_model(second, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    domain_pack = build_bazi_llm_context_pack(second, task_type="domain_followup", role_key="user", domain="career")
    hidden_pack = build_bazi_llm_context_pack(second, task_type="hidden_factor_dialogue", role_key="user")
    interaction_loop = run_synthetic_tier("interaction_loop")
    signals = extract_training_signals(interaction_loop)
    evidence = {
        "chain": _chain_summary(initial_view, first_view, second_view_user, first_question_id, second_question_id, second),
        "core_boundary": _core_boundary_summary(initial_fingerprint, second),
        "role_boundary": _role_boundary_summary(second_view_user, second_view_admin),
        "llm": _llm_summary(second, domain_pack, hidden_pack),
        "training": _training_summary(interaction_loop.model_dump(mode="json"), signals),
        "business_focus": _business_focus_summary(second),
    }
    return build_intelligent_question_chain_readiness(evidence=evidence)


def build_intelligent_question_chain_readiness(*, evidence: Mapping[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "multi_turn_chain_advances_visible_question_and_memory",
            "passed": _chain_ready(_mapping(evidence.get("chain"))),
            "observed": evidence.get("chain", {}),
        },
        {
            "check_id": "question_chain_preserves_core_bazi_facts",
            "passed": _core_boundary_ready(_mapping(evidence.get("core_boundary"))),
            "observed": evidence.get("core_boundary", {}),
        },
        {
            "check_id": "multi_role_projection_keeps_customer_surface_clean",
            "passed": _role_boundary_ready(_mapping(evidence.get("role_boundary"))),
            "observed": evidence.get("role_boundary", {}),
        },
        {
            "check_id": "llm_context_uses_chain_state_without_becoming_calculation_engine",
            "passed": _llm_ready(_mapping(evidence.get("llm"))),
            "observed": evidence.get("llm", {}),
        },
        {
            "check_id": "question_chain_is_trainable_without_chart_fact_mutation",
            "passed": _training_ready(_mapping(evidence.get("training"))),
            "observed": evidence.get("training", {}),
        },
        {
            "check_id": "question_chain_remains_centered_on_core_bazi_business_reading",
            "passed": _business_focus_ready(_mapping(evidence.get("business_focus"))),
            "observed": evidence.get("business_focus", {}),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": INTELLIGENT_QUESTION_CHAIN_READINESS_VERSION,
        "task": {
            "task_id": "IQ4",
            "title": "Intelligent Question Chain Readiness",
            "scope": "validate multi-turn Bazi question-answer chain quality, role safety, LLM context, and training boundaries",
        },
        "chain_summary": evidence,
        "checks": checks,
        "decision": {
            "intelligent_question_chain_ready": ready,
            "check_count": len(checks),
            "passed_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "decision_status": "iq4_intelligent_question_chain_ready" if ready else "iq4_intelligent_question_chain_blocked",
        },
        "policy_boundary": {
            "chart_fact_mutation_allowed": False,
            "llm_fact_generation_allowed": False,
            "question_training_scope": "question_strategy_and_followup_policy_only",
            "boundary": "iq4_question_chain_trains_interaction_strategy_not_chart_facts",
        },
        "next_mainline_selection": {
            "task_id": "IQ-S1" if ready else "IQ4-FIX",
            "title": "Question Intelligence Steady State" if ready else "Fix Intelligent Question Chain",
            "reason": (
                "multi-turn question chain is ready for steady-state monitoring"
                if ready
                else "repair failed multi-turn question chain readiness checks"
            ),
        },
        "boundary": "intelligent_question_chain_readiness_validates_interaction_without_mutating_bazi_facts",
    }


def _chain_summary(
    initial_view: Mapping[str, Any],
    first_view: Mapping[str, Any],
    second_view: Mapping[str, Any],
    first_question_id: str,
    second_question_id: str,
    runtime: Any,
) -> dict[str, object]:
    state = _mapping(runtime.question_plan.policy_effect.get("interaction_state"))
    known = _mapping(runtime.question_plan.session_state.get("known_user_signals"))
    outcomes = _list(runtime.question_plan.session_state.get("question_outcomes"))
    first_next = _visible_question_id(first_view)
    second_next = _visible_question_id(second_view)
    answer_panel = _mapping(second_view.get("answer_panel"))
    return {
        "initial_question_id": first_question_id,
        "first_followup_question_id": first_next,
        "second_answered_question_id": second_question_id,
        "second_followup_question_id": second_next,
        "answered_question_ids": state.get("answered_question_ids", []),
        "selected_option_ids": state.get("selected_option_ids", []),
        "known_user_signals": known,
        "outcome_count": len(outcomes),
        "answer_panel_present": bool(answer_panel),
        "llm_status": _mapping(answer_panel.get("llm_metadata")).get("status"),
        "initial_next_changed_after_first_answer": first_question_id != first_next,
        "second_next_changed_after_second_answer": second_question_id != second_next,
        "boundary": state.get("boundary", ""),
        "initial_has_core_reading": bool(_mapping(initial_view.get("core_bazi_reading"))),
    }


def _core_boundary_summary(initial_fingerprint: dict[str, object], runtime: Any) -> dict[str, object]:
    final_fingerprint = _core_fingerprint(runtime)
    return {
        "initial_fingerprint": initial_fingerprint,
        "final_fingerprint": final_fingerprint,
        "core_fingerprint_unchanged": initial_fingerprint == final_fingerprint,
        "question_outcome_count": len(_list(runtime.question_plan.session_state.get("question_outcomes"))),
        "boundary": "question_outcomes_are_feedback_not_chart_facts",
    }


def _role_boundary_summary(user_view: Mapping[str, Any], admin_view: Mapping[str, Any]) -> dict[str, object]:
    user_diag = _mapping(user_view.get("diagnostics"))
    admin_diag = _mapping(admin_view.get("diagnostics"))
    user_questions = _list(user_view.get("questions"))
    admin_questions = _list(admin_view.get("questions"))
    return {
        "user_diagnostics_keys": sorted(user_diag.keys()),
        "admin_diagnostics_keys": sorted(admin_diag.keys()),
        "user_question_count": len(user_questions),
        "admin_question_count": len(admin_questions),
        "user_internal_next_visible": "internal_next_question_id" in str(user_view.get("reading_surface", {})),
        "admin_has_interaction_state": "interaction_state" in admin_diag,
        "admin_has_question_outcomes": "question_outcomes" in admin_diag,
        "boundary": "customer_projection_hides_internal_question_strategy",
    }


def _llm_summary(runtime: Any, domain_pack: Any, hidden_pack: Any) -> dict[str, object]:
    answer = runtime.answer_result
    metadata = answer.llm_metadata if answer is not None else {}
    domain_sections = _section_ids(domain_pack)
    hidden_sections = _section_ids(hidden_pack)
    return {
        "answer_task_type": metadata.get("task_type", ""),
        "answer_context_pack": _mapping(metadata.get("prompt_request")).get("context_pack", ""),
        "domain_followup_sections": domain_sections,
        "hidden_factor_sections": hidden_sections,
        "domain_raw_runtime_payload_included": bool(_pack_value(domain_pack, "raw_runtime_payload_included")),
        "hidden_raw_runtime_payload_included": bool(_pack_value(hidden_pack, "raw_runtime_payload_included")),
        "domain_chart_fact_mutation_allowed": bool(_pack_value(domain_pack, "chart_fact_mutation_allowed")),
        "hidden_chart_fact_mutation_allowed": bool(_pack_value(hidden_pack, "chart_fact_mutation_allowed")),
        "boundary": "llm_context_renders_chain_state_not_chart_facts",
    }


def _training_summary(interaction_loop: Mapping[str, Any], signals: list[Any]) -> dict[str, object]:
    signal_ids = {str(getattr(signal, "signal_id", "")) for signal in signals}
    return {
        "suite_id": interaction_loop.get("suite_id"),
        "case_count": interaction_loop.get("case_count"),
        "passed_count": interaction_loop.get("passed_count"),
        "signal_ids": sorted(signal_ids),
        "has_interaction_state_machine": "v30.training_signal.interaction_state_machine" in signal_ids,
        "has_interaction_loop_quality": "v30.training_signal.interaction_loop_quality" in signal_ids,
        "has_question_model_signal_personalization": "v30.training_signal.question_model_signal_personalization" in signal_ids,
        "boundary": "interaction_training_signals_tune_question_strategy_not_chart_facts",
    }


def _business_focus_summary(runtime: Any) -> dict[str, object]:
    policy = runtime.question_plan.policy_effect
    practical = _mapping(policy.get("practical_reading_context"))
    ranked = _mapping(policy.get("ranked_decisions"))
    model_signal = _mapping(policy.get("model_signal_summary"))
    recommendations = _list(runtime.question_plan.recommended_questions)
    user_topics = [
        str(row.get("topic"))
        for row in recommendations
        if isinstance(row, dict) and row.get("interaction_type") == "user_question"
    ]
    return {
        "has_core_bazi_reading_inputs": bool(runtime.chart_context.natal_pillars or runtime.chart_context.input_pillars),
        "practical_status": practical.get("status", ""),
        "ranked_decision_domains": sorted(ranked.keys()),
        "model_signal_version": model_signal.get("version", ""),
        "user_question_topics": user_topics[:5],
        "business_topics_present": sorted(set(user_topics) & {"career", "wealth", "relationship", "timing", "decision"}),
        "boundary": "question_chain_supports_core_bazi_reading_not_replaces_it",
    }


def _chain_ready(summary: Mapping[str, Any]) -> bool:
    known = _mapping(summary.get("known_user_signals"))
    return (
        summary.get("initial_next_changed_after_first_answer") is True
        and summary.get("second_next_changed_after_second_answer") is True
        and int(summary.get("outcome_count") or 0) >= 2
        and len(_list(summary.get("answered_question_ids"))) >= 2
        and len(_list(summary.get("selected_option_ids"))) >= 2
        and int(known.get("answered_question_count") or 0) >= 2
        and summary.get("answer_panel_present") is True
        and summary.get("boundary") == "interaction_state_guides_followup_not_chart_fact"
    )


def _core_boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("core_fingerprint_unchanged") is True
        and int(summary.get("question_outcome_count") or 0) >= 2
        and summary.get("boundary") == "question_outcomes_are_feedback_not_chart_facts"
    )


def _role_boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("user_internal_next_visible") is False
        and summary.get("admin_has_interaction_state") is True
        and summary.get("admin_has_question_outcomes") is True
        and int(summary.get("user_question_count") or 0) > 0
    )


def _llm_ready(summary: Mapping[str, Any]) -> bool:
    domain_sections = set(_list(summary.get("domain_followup_sections")))
    hidden_sections = set(_list(summary.get("hidden_factor_sections")))
    return (
        summary.get("answer_task_type") == "domain_followup"
        and summary.get("answer_context_pack") == "BaziDomainContext"
        and {"ranked_decisions", "practical_reading", "interaction_state", "known_user_signals"} <= domain_sections
        and {"hidden_factor_state", "interaction_state", "known_user_signals"} <= hidden_sections
        and summary.get("domain_raw_runtime_payload_included") is False
        and summary.get("hidden_raw_runtime_payload_included") is False
        and summary.get("domain_chart_fact_mutation_allowed") is False
        and summary.get("hidden_chart_fact_mutation_allowed") is False
    )


def _training_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("suite_id") == "v30.synthetic.interaction_loop"
        and summary.get("case_count") == summary.get("passed_count")
        and summary.get("has_interaction_state_machine") is True
        and summary.get("has_interaction_loop_quality") is True
        and summary.get("has_question_model_signal_personalization") is True
        and summary.get("boundary") == "interaction_training_signals_tune_question_strategy_not_chart_facts"
    )


def _business_focus_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("has_core_bazi_reading_inputs") is True
        and summary.get("practical_status") in {"ready", "natal_only"}
        and len(_list(summary.get("ranked_decision_domains"))) >= 3
        and summary.get("model_signal_version") == "v30.model_signal_summary.v1"
        and len(_list(summary.get("business_topics_present"))) >= 3
    )


def _core_fingerprint(runtime: Any) -> dict[str, object]:
    context = runtime.chart_context
    return {
        "input_pillars": context.input_pillars,
        "natal_pillars": context.natal_pillars,
        "day_master": context.day_master,
        "day_master_element": context.day_master_element,
        "time_layers": context.time_layers,
    }


def _visible_question_id(view: Mapping[str, Any]) -> str:
    surface = _mapping(view.get("reading_surface"))
    question = _mapping(surface.get("next_question"))
    return str(question.get("question_id") or "")


def _section_ids(pack: Any) -> list[str]:
    if isinstance(pack, Mapping):
        sections = pack.get("sections", [])
    else:
        sections = getattr(pack, "sections", [])
    return [
        str(row.get("section_id"))
        for row in sections
        if isinstance(row, dict) and row.get("section_id")
    ]


def _pack_value(pack: Any, key: str) -> Any:
    if isinstance(pack, Mapping):
        return pack.get(key)
    return getattr(pack, key, None)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []
