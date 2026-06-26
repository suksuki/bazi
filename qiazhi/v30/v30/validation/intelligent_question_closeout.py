from __future__ import annotations

from typing import Any, Mapping

from v30.learning.auto_apply import _candidate_payload
from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.intelligent_question_chain_readiness import run_intelligent_question_chain_readiness
from v30.validation.intelligent_question_interaction_audit import run_intelligent_question_interaction_audit
from v30.validation.question_model_signal_training_readiness import run_question_model_signal_training_readiness
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


INTELLIGENT_QUESTION_CLOSEOUT_VERSION = "v30.intelligent_question_closeout.v1"


def run_intelligent_question_closeout(
    reading_id: str = "iq5-intelligent-question-closeout",
) -> dict[str, object]:
    iq1 = run_intelligent_question_interaction_audit(reading_id=f"{reading_id}-iq1")
    iq2 = run_question_model_signal_training_readiness(reading_id=f"{reading_id}-iq2")
    iq4 = run_intelligent_question_chain_readiness(reading_id=f"{reading_id}-iq4")
    interaction_loop = run_synthetic_tier("interaction_loop")
    signals = extract_training_signals(interaction_loop)
    question_policy_candidate = _candidate_payload("question_policy", f"{reading_id}-candidate", signals)
    runtime = create_smoke_runtime(f"{reading_id}-layers", day_master="庚", day_master_element="metal")
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    evidence = {
        "prior_gates": _prior_gate_summary(iq1, iq2, iq4),
        "layer_contract": _layer_contract_summary(runtime, user_view, admin_view),
        "training_candidate": _training_candidate_summary(interaction_loop.model_dump(mode="json"), signals, question_policy_candidate),
        "llm_and_role": _llm_and_role_summary(iq4),
        "core_boundary": _core_boundary_summary(iq4),
        "steady_state": _steady_state_summary(iq1, iq2, iq4),
    }
    return build_intelligent_question_closeout(evidence=evidence)


def build_intelligent_question_closeout(*, evidence: Mapping[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "iq1_iq2_iq4_gates_are_accepted",
            "passed": _prior_gates_ready(_mapping(evidence.get("prior_gates"))),
            "observed": evidence.get("prior_gates", {}),
        },
        {
            "check_id": "question_layers_are_separated_and_projected_by_role",
            "passed": _layer_contract_ready(_mapping(evidence.get("layer_contract"))),
            "observed": evidence.get("layer_contract", {}),
        },
        {
            "check_id": "question_training_candidate_is_bounded_and_available",
            "passed": _training_candidate_ready(_mapping(evidence.get("training_candidate"))),
            "observed": evidence.get("training_candidate", {}),
        },
        {
            "check_id": "llm_followup_and_role_boundaries_are_closed",
            "passed": _llm_and_role_ready(_mapping(evidence.get("llm_and_role"))),
            "observed": evidence.get("llm_and_role", {}),
        },
        {
            "check_id": "core_bazi_facts_remain_authoritative",
            "passed": _core_boundary_ready(_mapping(evidence.get("core_boundary"))),
            "observed": evidence.get("core_boundary", {}),
        },
        {
            "check_id": "question_intelligence_can_enter_steady_state",
            "passed": _steady_state_ready(_mapping(evidence.get("steady_state"))),
            "observed": evidence.get("steady_state", {}),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": INTELLIGENT_QUESTION_CLOSEOUT_VERSION,
        "task": {
            "task_id": "IQ5",
            "title": "Intelligent Question Closeout",
            "scope": "close the V30 intelligent question module into steady state across projection, training, LLM context, and no-mutation boundaries",
        },
        "closeout_summary": evidence,
        "checks": checks,
        "decision": {
            "intelligent_question_closeout_ready": ready,
            "check_count": len(checks),
            "passed_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "decision_status": "iq5_intelligent_question_closeout_ready" if ready else "iq5_intelligent_question_closeout_blocked",
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "module_completion": {
            "question_dialogue_graph": 98 if ready else 97,
            "question_policy_training": 92 if ready else 90,
            "llm_question_context": 92 if ready else 90,
            "status": "IQ-S1 steady state" if ready else "IQ5 blocked",
        },
        "policy_boundary": {
            "visible_questions": "customer-facing user_question anchors only",
            "structured_options": "session guidance and known_user_signals only",
            "internal_calibration": "admin/practitioner diagnostics only",
            "llm_scope": "expression and follow-up context rendering only",
            "training_scope": "question_strategy_and_followup_policy_only",
            "chart_fact_mutation_allowed": False,
            "boundary": "iq5_question_closeout_keeps_interaction_auxiliary_to_core_bazi_calculation",
        },
        "next_mainline_selection": {
            "task_id": "IQ-S1" if ready else "IQ5-FIX",
            "title": "Question Intelligence Steady State" if ready else "Fix Intelligent Question Closeout",
            "reason": (
                "intelligent_question_module_closed_for_current_scope"
                if ready
                else "repair failed question closeout checks"
            ),
        },
        "boundary": "intelligent_question_closeout_validates_question_module_without_mutating_bazi_facts",
    }


def _prior_gate_summary(iq1: Mapping[str, Any], iq2: Mapping[str, Any], iq4: Mapping[str, Any]) -> dict[str, object]:
    iq1_decision = _mapping(iq1.get("decision"))
    iq2_decision = _mapping(iq2.get("decision"))
    iq4_decision = _mapping(iq4.get("decision"))
    return {
        "iq1_version": iq1.get("version"),
        "iq1_ready": iq1_decision.get("intelligent_question_interaction_ready"),
        "iq1_passed": iq1_decision.get("passed_check_count"),
        "iq2_version": iq2.get("version"),
        "iq2_ready": iq2_decision.get("training_readiness_ready"),
        "iq2_passed": iq2_decision.get("passed_check_count"),
        "iq4_version": iq4.get("version"),
        "iq4_ready": iq4_decision.get("intelligent_question_chain_ready"),
        "iq4_passed": iq4_decision.get("passed_count"),
    }


def _layer_contract_summary(runtime: Any, user_view: Mapping[str, Any], admin_view: Mapping[str, Any]) -> dict[str, object]:
    recommendations = _list(runtime.question_plan.recommended_questions)
    user_questions = _list(user_view.get("questions"))
    user_interaction_types = {
        str(row.get("interaction_type"))
        for row in user_questions
        if isinstance(row, dict) and row.get("interaction_type")
    }
    all_interaction_types = {
        str(row.get("interaction_type"))
        for row in recommendations
        if isinstance(row, dict) and row.get("interaction_type")
    }
    option_count = sum(len(_list(row.get("options"))) for row in recommendations if isinstance(row, dict))
    admin_diag = _mapping(admin_view.get("diagnostics"))
    user_diag = _mapping(user_view.get("diagnostics"))
    state = _mapping(runtime.question_plan.policy_effect.get("interaction_state"))
    return {
        "recommendation_count": len(recommendations),
        "user_question_count": len(user_questions),
        "user_interaction_types": sorted(user_interaction_types),
        "all_interaction_types": sorted(all_interaction_types),
        "structured_option_count": option_count,
        "visible_next_question_id": state.get("visible_next_question_id", ""),
        "internal_next_question_id": state.get("internal_next_question_id", ""),
        "user_diagnostic_key_count": len(user_diag),
        "admin_has_question_dialogue_graph": "question_dialogue_graph" in admin_diag,
        "admin_has_interaction_state": "interaction_state" in admin_diag,
        "admin_has_adaptive_question_diagnostics": "adaptive_question_diagnostics" in admin_diag,
        "boundary": "visible_user_questions_structured_options_and_internal_calibration_are_separate_layers",
    }


def _training_candidate_summary(
    interaction_loop: Mapping[str, Any],
    signals: list[Any],
    question_policy_candidate: Mapping[str, Any],
) -> dict[str, object]:
    signal_ids = {str(getattr(signal, "signal_id", "")) for signal in signals}
    weights = _mapping(question_policy_candidate.get("weights"))
    model_policy = _mapping(weights.get("model_signal_question_policy"))
    interaction_policy = _mapping(weights.get("interaction_followup_policy"))
    adaptive_policy = _mapping(weights.get("adaptive_question_policy"))
    return {
        "interaction_loop_suite_id": interaction_loop.get("suite_id"),
        "interaction_loop_passed": interaction_loop.get("case_count") == interaction_loop.get("passed_count"),
        "signal_ids": sorted(signal_ids),
        "has_interaction_state_machine": "v30.training_signal.interaction_state_machine" in signal_ids,
        "has_interaction_loop_quality": "v30.training_signal.interaction_loop_quality" in signal_ids,
        "has_question_model_signal_personalization": "v30.training_signal.question_model_signal_personalization" in signal_ids,
        "has_model_signal_question_policy": bool(model_policy),
        "model_signal_policy_boundary": model_policy.get("boundary", ""),
        "model_signal_policy_can_tune_chart_facts": model_policy.get("can_tune_chart_facts"),
        "has_interaction_followup_policy": bool(interaction_policy),
        "has_adaptive_question_policy": bool(adaptive_policy),
        "candidate_training_signal_count": len(_list(question_policy_candidate.get("training_signals"))),
        "boundary": "question_policy_candidate_trains_strategy_not_chart_facts",
    }


def _llm_and_role_summary(iq4: Mapping[str, Any]) -> dict[str, object]:
    chain = _mapping(iq4.get("chain_summary"))
    llm = _mapping(chain.get("llm"))
    role = _mapping(chain.get("role_boundary"))
    return {
        "answer_task_type": llm.get("answer_task_type"),
        "answer_context_pack": llm.get("answer_context_pack"),
        "domain_followup_sections": llm.get("domain_followup_sections", []),
        "hidden_factor_sections": llm.get("hidden_factor_sections", []),
        "domain_raw_runtime_payload_included": llm.get("domain_raw_runtime_payload_included"),
        "domain_chart_fact_mutation_allowed": llm.get("domain_chart_fact_mutation_allowed"),
        "user_internal_next_visible": role.get("user_internal_next_visible"),
        "admin_has_interaction_state": role.get("admin_has_interaction_state"),
        "admin_has_question_outcomes": role.get("admin_has_question_outcomes"),
        "boundary": "llm_and_role_projection_render_chain_without_fact_generation",
    }


def _core_boundary_summary(iq4: Mapping[str, Any]) -> dict[str, object]:
    chain = _mapping(iq4.get("chain_summary"))
    core = _mapping(chain.get("core_boundary"))
    business = _mapping(chain.get("business_focus"))
    return {
        "core_fingerprint_unchanged": core.get("core_fingerprint_unchanged"),
        "question_outcome_count": core.get("question_outcome_count"),
        "model_signal_version": business.get("model_signal_version"),
        "ranked_decision_domains": business.get("ranked_decision_domains", []),
        "business_topics_present": business.get("business_topics_present", []),
        "boundary": core.get("boundary", ""),
    }


def _steady_state_summary(iq1: Mapping[str, Any], iq2: Mapping[str, Any], iq4: Mapping[str, Any]) -> dict[str, object]:
    decisions = [_mapping(row.get("decision")) for row in (iq1, iq2, iq4)]
    return {
        "full_pytest_required": any(row.get("full_pytest_required") is True for row in decisions),
        "synthetic_all_required": any(row.get("synthetic_all_required") is True for row in decisions),
        "full_518k_required": any(row.get("full_518k_required") is True for row in decisions),
        "live_llm_required": any(row.get("live_llm_required") is True for row in decisions),
        "policy_pointer_write_allowed": any(row.get("policy_pointer_write_allowed") is True for row in decisions),
        "chart_fact_mutation_allowed": any(row.get("chart_fact_mutation_allowed") is True for row in decisions),
        "next_task_ids": [
            str(_mapping(row.get("next_mainline_selection")).get("task_id", ""))
            for row in (iq1, iq2, iq4)
        ],
        "boundary": "iq_closeout_enters_steady_state_without_heavy_default_validation_or_pointer_write",
    }


def _prior_gates_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("iq1_ready") is True
        and int(summary.get("iq1_passed") or 0) >= 8
        and summary.get("iq2_ready") is True
        and int(summary.get("iq2_passed") or 0) >= 5
        and summary.get("iq4_ready") is True
        and int(summary.get("iq4_passed") or 0) >= 6
    )


def _layer_contract_ready(summary: Mapping[str, Any]) -> bool:
    return (
        int(summary.get("recommendation_count") or 0) >= 5
        and int(summary.get("user_question_count") or 0) >= 3
        and set(_list(summary.get("user_interaction_types"))) == {"user_question"}
        and "calibration_probe" in set(_list(summary.get("all_interaction_types")))
        and int(summary.get("structured_option_count") or 0) >= 5
        and summary.get("visible_next_question_id")
        and summary.get("internal_next_question_id")
        and int(summary.get("user_diagnostic_key_count") or 0) == 0
        and summary.get("admin_has_question_dialogue_graph") is True
        and summary.get("admin_has_interaction_state") is True
        and summary.get("admin_has_adaptive_question_diagnostics") is True
    )


def _training_candidate_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("interaction_loop_suite_id") == "v30.synthetic.interaction_loop"
        and summary.get("interaction_loop_passed") is True
        and summary.get("has_interaction_state_machine") is True
        and summary.get("has_interaction_loop_quality") is True
        and summary.get("has_question_model_signal_personalization") is True
        and summary.get("has_model_signal_question_policy") is True
        and summary.get("model_signal_policy_boundary") == "model_signal_question_policy_trains_question_strategy_not_chart_facts"
        and summary.get("model_signal_policy_can_tune_chart_facts") is False
        and summary.get("has_interaction_followup_policy") is True
        and summary.get("has_adaptive_question_policy") is True
    )


def _llm_and_role_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("answer_task_type") == "domain_followup"
        and summary.get("answer_context_pack") == "BaziDomainContext"
        and {"interaction_state", "known_user_signals"} <= set(_list(summary.get("domain_followup_sections")))
        and {"interaction_state", "known_user_signals"} <= set(_list(summary.get("hidden_factor_sections")))
        and summary.get("domain_raw_runtime_payload_included") is False
        and summary.get("domain_chart_fact_mutation_allowed") is False
        and summary.get("user_internal_next_visible") is False
        and summary.get("admin_has_interaction_state") is True
        and summary.get("admin_has_question_outcomes") is True
    )


def _core_boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("core_fingerprint_unchanged") is True
        and int(summary.get("question_outcome_count") or 0) >= 2
        and summary.get("model_signal_version") == "v30.model_signal_summary.v1"
        and len(_list(summary.get("ranked_decision_domains"))) >= 3
        and len(_list(summary.get("business_topics_present"))) >= 3
        and summary.get("boundary") == "question_outcomes_are_feedback_not_chart_facts"
    )


def _steady_state_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("full_pytest_required") is False
        and summary.get("synthetic_all_required") is False
        and summary.get("full_518k_required") is False
        and summary.get("live_llm_required") is False
        and summary.get("policy_pointer_write_allowed") is False
        and summary.get("chart_fact_mutation_allowed") is False
        and set(_list(summary.get("next_task_ids"))) == {"IQ-S1"}
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []
