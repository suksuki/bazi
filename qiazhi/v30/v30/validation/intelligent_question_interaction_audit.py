from __future__ import annotations

from typing import Any

from v30.llm import build_bazi_llm_context_pack
from v30.presentation import build_presentation_model
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


INTELLIGENT_QUESTION_INTERACTION_AUDIT_VERSION = "v30.intelligent_question_interaction_audit.v1"


def run_intelligent_question_interaction_audit(
    reading_id: str = "iq1-intelligent-question-interaction",
) -> dict[str, object]:
    cases = [
        ("wood", "甲", "wood"),
        ("metal", "庚", "metal"),
        ("earth", "戊", "earth"),
        ("water", "壬", "water"),
    ]
    runtimes = {
        name: create_smoke_runtime(
            f"{reading_id}-{name}",
            day_master=day_master,
            day_master_element=element,
        )
        for name, day_master, element in cases
    }
    user_views = {
        name: build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
        for name, runtime in runtimes.items()
    }
    admin_views = {
        name: build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
        for name, runtime in runtimes.items()
    }
    base_runtime = runtimes["metal"]
    base_user_view = user_views["metal"]
    first_question_id = str(base_user_view["reading_surface"]["next_question"]["question_id"])
    answered_runtime = attach_question_outcome(
        base_runtime,
        first_question_id,
        {
            "answer": "先看财务和选择风险。",
            "selected_option": "wealth:risk",
            "confidence": 0.82,
            "feedback_tags": ["wealth", "customer_loop"],
        },
    )
    answered_view = build_presentation_model(
        answered_runtime,
        role_key="user",
        locale="zh",
        client="web",
    ).model_dump(mode="json")
    interaction_loop = run_synthetic_tier("interaction_loop")
    signals = extract_training_signals(interaction_loop)
    hidden_pack = build_bazi_llm_context_pack(
        answered_runtime,
        task_type="hidden_factor_dialogue",
        role_key="user",
    )
    domain_pack = build_bazi_llm_context_pack(
        answered_runtime,
        task_type="domain_followup",
        role_key="user",
        domain="wealth",
    )
    evidence = {
        "personalization": _personalization_summary(runtimes, user_views),
        "module_support": _module_support_summary(base_runtime),
        "non_template": _non_template_summary(base_runtime, base_user_view),
        "chain": _chain_summary(base_user_view, answered_runtime, answered_view, first_question_id),
        "training": _training_summary(interaction_loop.model_dump(mode="json"), signals),
        "roles": _role_summary(base_user_view, admin_views["metal"]),
        "llm": _llm_summary(hidden_pack, domain_pack, answered_runtime),
        "core_bazi": _core_bazi_summary(base_runtime, base_user_view, answered_runtime),
    }
    return build_intelligent_question_interaction_audit(evidence=evidence)


def build_intelligent_question_interaction_audit(*, evidence: dict[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "questions_are_tailored_to_different_bazi_contexts",
            "passed": _personalization_ready(_mapping(evidence.get("personalization"))),
            "observed": evidence.get("personalization", {}),
        },
        {
            "check_id": "question_strategy_consumes_core_bazi_modules",
            "passed": _module_support_ready(_mapping(evidence.get("module_support"))),
            "observed": evidence.get("module_support", {}),
        },
        {
            "check_id": "questions_are_evidence_bound_not_flat_templates",
            "passed": _non_template_ready(_mapping(evidence.get("non_template"))),
            "observed": evidence.get("non_template", {}),
        },
        {
            "check_id": "question_answer_forms_continuous_followup_chain",
            "passed": _chain_ready(_mapping(evidence.get("chain"))),
            "observed": evidence.get("chain", {}),
        },
        {
            "check_id": "interaction_loop_is_trainable_without_chart_fact_mutation",
            "passed": _training_ready(_mapping(evidence.get("training"))),
            "observed": evidence.get("training", {}),
        },
        {
            "check_id": "multi_role_projection_separates_customer_and_diagnostic_questions",
            "passed": _role_ready(_mapping(evidence.get("roles"))),
            "observed": evidence.get("roles", {}),
        },
        {
            "check_id": "llm_context_supports_question_followup_without_becoming_calculation_engine",
            "passed": _llm_ready(_mapping(evidence.get("llm"))),
            "observed": evidence.get("llm", {}),
        },
        {
            "check_id": "question_interaction_stays_centered_on_core_bazi_reading",
            "passed": _core_bazi_ready(_mapping(evidence.get("core_bazi"))),
            "observed": evidence.get("core_bazi", {}),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": INTELLIGENT_QUESTION_INTERACTION_AUDIT_VERSION,
        "task": {
            "task_id": "IQ1",
            "title": "Intelligent Question Interaction Audit",
            "scope": "audit tailored, module-backed, chained, trainable, role-aware, LLM-supported Bazi question interaction",
        },
        "audit_summary": evidence,
        "checks": checks,
        "decision": {
            "intelligent_question_interaction_ready": ready,
            "decision_status": "iq1_intelligent_question_interaction_ready"
            if ready
            else "iq1_intelligent_question_interaction_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "IQ-S1" if ready else "IQ1-FIX",
            "title": "Question Intelligence Steady State"
            if ready
            else "Fix Intelligent Question Interaction",
            "reason": "question_interaction_satisfies_8_point_business_audit"
            if ready
            else "intelligent_question_interaction_checks_failed",
        },
        "boundary": "iq1_audits_question_intelligence_for_bazi_calculation_without_chart_fact_mutation",
    }


def _personalization_summary(runtimes: dict[str, Any], user_views: dict[str, dict[str, Any]]) -> dict[str, object]:
    top_topics: dict[str, str] = {}
    top_questions: dict[str, str] = {}
    model_reasons: dict[str, list[str]] = {}
    dominant_families: dict[str, list[str]] = {}
    for name, runtime in runtimes.items():
        question = _mapping(_mapping(user_views[name].get("reading_surface")).get("next_question"))
        top_topics[name] = str(question.get("topic") or "")
        top_questions[name] = str(question.get("question_id") or "")
        runtime_questions = [
            row for row in runtime.question_plan.recommended_questions
            if row.get("question_id") == question.get("question_id")
        ]
        reasons = runtime_questions[0].get("reasons", []) if runtime_questions else []
        model_reasons[name] = [
            str(reason) for reason in reasons
            if str(reason).startswith("model_signal_question_focus:")
        ]
        bands = runtime.question_plan.policy_effect.get("model_signal_summary", {}).get("energy_bands", [])
        dominant_families[name] = [
            str(row.get("family"))
            for row in bands
            if isinstance(row, dict) and str(row.get("energy_band") or "") in {"high", "medium"}
        ][:3]
    return {
        "top_topics": top_topics,
        "top_questions": top_questions,
        "distinct_top_topic_count": len(set(top_topics.values())),
        "model_signal_reason_counts": {key: len(value) for key, value in model_reasons.items()},
        "model_signal_reasons": model_reasons,
        "dominant_families": dominant_families,
        "boundary": "bazi_model_signal_changes_question_priority_not_chart_facts",
    }


def _module_support_summary(runtime: Any) -> dict[str, object]:
    policy = runtime.question_plan.policy_effect
    graph = _mapping(policy.get("question_dialogue_graph"))
    return {
        "has_m3_completion": _mapping(policy.get("m3_completion_summary")).get("version") == "v30.m3_completion_summary.v1",
        "has_model_signal": _mapping(policy.get("model_signal_summary")).get("version") == "v30.model_signal_summary.v1",
        "has_ranked_decisions": {"strength", "structure_pattern", "useful_god"} <= set(_mapping(policy.get("ranked_decisions")).keys()),
        "has_practical_reading": _mapping(policy.get("practical_reading_context")).get("version") == "v30.practical_reading_context.v1",
        "has_central_brain": policy.get("central_brain_version") == "v30.central_brain.v1",
        "graph_node_count": len(graph.get("nodes", [])) if isinstance(graph.get("nodes"), list) else 0,
        "graph_edge_count": len(graph.get("edges", [])) if isinstance(graph.get("edges"), list) else 0,
    }


def _non_template_summary(runtime: Any, user_view: dict[str, Any]) -> dict[str, object]:
    questions = [
        row for row in runtime.question_plan.recommended_questions
        if row.get("interaction_type") == "user_question"
    ]
    visible_questions = user_view.get("questions", [])
    visible_questions = visible_questions if isinstance(visible_questions, list) else []
    return {
        "user_question_count": len(questions),
        "evidence_bound_count": sum(1 for row in questions if row.get("evidence_ids")),
        "reason_bound_count": sum(1 for row in questions if row.get("reasons")),
        "expected_information_gain_count": sum(1 for row in questions if _mapping(row.get("expected_information_gain")).get("primary_gain")),
        "quality_contract_count": sum(1 for row in questions if _mapping(row.get("quality_contract")).get("version") == "v30.high_value_question.v1"),
        "visible_label_source_count": sum(
            1 for row in visible_questions
            if str(_mapping(row).get("label_source") or "").startswith("expression_rendered")
        ),
    }


def _chain_summary(
    before_view: dict[str, Any],
    answered_runtime: Any,
    answered_view: dict[str, Any],
    first_question_id: str,
) -> dict[str, object]:
    state = _mapping(answered_runtime.question_plan.policy_effect.get("interaction_state"))
    before_next = str(_mapping(_mapping(before_view.get("reading_surface")).get("next_question")).get("question_id") or "")
    after_next = str(_mapping(_mapping(answered_view.get("reading_surface")).get("next_question")).get("question_id") or "")
    signals = _mapping(state.get("known_user_signals"))
    answer_panel = _mapping(answered_view.get("answer_panel"))
    return {
        "before_next_question_id": before_next,
        "after_next_question_id": after_next,
        "answered_question_id": first_question_id,
        "answered_question_ids": state.get("answered_question_ids", []),
        "selected_option_ids": state.get("selected_option_ids", []),
        "known_user_signal_topics": signals.get("topics", []),
        "interaction_stage": state.get("interaction_stage"),
        "answer_panel_present": bool(answer_panel),
        "boundary": state.get("boundary"),
    }


def _training_summary(suite: dict[str, Any], signals: list[Any]) -> dict[str, object]:
    signal_ids = {signal.signal_id for signal in signals}
    return {
        "suite_id": suite.get("suite_id"),
        "case_count": suite.get("case_count"),
        "passed_count": suite.get("passed_count"),
        "signal_ids": sorted(signal_ids),
        "has_interaction_state_signal": "v30.training_signal.interaction_state_machine" in signal_ids,
        "has_interaction_loop_signal": "v30.training_signal.interaction_loop_quality" in signal_ids,
        "has_question_outcome_signal": "v30.training_signal.question_dialogue_outcome" in signal_ids,
        "can_tune_chart_facts": False,
    }


def _role_summary(user_view: dict[str, Any], admin_view: dict[str, Any]) -> dict[str, object]:
    user_questions = user_view.get("questions", [])
    user_questions = user_questions if isinstance(user_questions, list) else []
    diagnostics = _mapping(admin_view.get("diagnostics"))
    graph = _mapping(diagnostics.get("question_dialogue_graph"))
    return {
        "user_question_count": len(user_questions),
        "user_calibration_question_count": sum(
            1 for row in user_questions
            if _mapping(row).get("interaction_type") == "calibration_probe"
        ),
        "user_diagnostics_hidden": user_view.get("diagnostics") == {},
        "admin_diagnostics_visible": bool(diagnostics),
        "admin_internal_next_question_visible": bool(graph.get("internal_next_question_id") or graph.get("next_question_id")),
    }


def _llm_summary(hidden_pack: dict[str, Any], domain_pack: dict[str, Any], answered_runtime: Any) -> dict[str, object]:
    answer_metadata = _mapping(answered_runtime.answer_result.llm_metadata if answered_runtime.answer_result else {})
    hidden_sections = _section_ids(hidden_pack.get("sections"))
    domain_sections = _section_ids(domain_pack.get("sections"))
    return {
        "hidden_pack_task": hidden_pack.get("task_type"),
        "hidden_pack_sections": hidden_sections,
        "domain_pack_task": domain_pack.get("task_type"),
        "domain_pack_sections": domain_sections,
        "answer_metadata_version": answer_metadata.get("version"),
        "answer_metadata_boundary": answer_metadata.get("boundary"),
        "chart_fact_mutation_allowed": False,
    }


def _core_bazi_summary(runtime: Any, user_view: dict[str, Any], answered_runtime: Any) -> dict[str, object]:
    before_chart = runtime.chart_context.model_dump(mode="json")
    after_chart = answered_runtime.chart_context.model_dump(mode="json")
    surface = _mapping(user_view.get("reading_surface"))
    core = _mapping(surface.get("core_bazi_reading"))
    return {
        "core_bazi_reading_version": core.get("version"),
        "surface_type": core.get("surface_type"),
        "chart_fingerprint_preserved": before_chart == after_chart,
        "next_question_topic": _mapping(surface.get("next_question")).get("topic"),
        "boundary": core.get("boundary"),
    }


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _section_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(
        str(row.get("section_id"))
        for row in value
        if isinstance(row, dict) and row.get("section_id")
    )


def _personalization_ready(summary: dict[str, Any]) -> bool:
    return (
        int(summary.get("distinct_top_topic_count") or 0) >= 3
        and all(count > 0 for count in _mapping(summary.get("model_signal_reason_counts")).values())
    )


def _module_support_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("has_m3_completion") is True
        and summary.get("has_model_signal") is True
        and summary.get("has_ranked_decisions") is True
        and summary.get("has_practical_reading") is True
        and summary.get("has_central_brain") is True
        and int(summary.get("graph_node_count") or 0) >= 5
        and int(summary.get("graph_edge_count") or 0) >= 2
    )


def _non_template_ready(summary: dict[str, Any]) -> bool:
    count = int(summary.get("user_question_count") or 0)
    return (
        count >= 5
        and int(summary.get("evidence_bound_count") or 0) >= count
        and int(summary.get("reason_bound_count") or 0) >= count
        and int(summary.get("expected_information_gain_count") or 0) >= count
        and int(summary.get("quality_contract_count") or 0) >= count
        and int(summary.get("visible_label_source_count") or 0) >= 4
    )


def _chain_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("before_next_question_id")
        and summary.get("after_next_question_id")
        and summary.get("before_next_question_id") != summary.get("after_next_question_id")
        and summary.get("answered_question_id") in set(summary.get("answered_question_ids", []))
        and summary.get("selected_option_ids")
        and summary.get("known_user_signal_topics")
        and summary.get("interaction_stage") == "followup_question_selection"
        and summary.get("answer_panel_present") is True
        and summary.get("boundary") == "interaction_state_guides_followup_not_chart_fact"
    )


def _training_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("suite_id") == "v30.synthetic.interaction_loop"
        and summary.get("case_count") == summary.get("passed_count")
        and int(summary.get("case_count") or 0) >= 5
        and summary.get("has_interaction_state_signal") is True
        and summary.get("has_interaction_loop_signal") is True
        and summary.get("has_question_outcome_signal") is True
        and summary.get("can_tune_chart_facts") is False
    )


def _role_ready(summary: dict[str, Any]) -> bool:
    return (
        int(summary.get("user_question_count") or 0) >= 4
        and int(summary.get("user_calibration_question_count") or 0) == 0
        and summary.get("user_diagnostics_hidden") is True
        and summary.get("admin_diagnostics_visible") is True
        and summary.get("admin_internal_next_question_visible") is True
    )


def _llm_ready(summary: dict[str, Any]) -> bool:
    hidden_sections = set(summary.get("hidden_pack_sections", []))
    domain_sections = set(summary.get("domain_pack_sections", []))
    return (
        summary.get("hidden_pack_task") == "hidden_factor_dialogue"
        and {"hidden_factor_state", "interaction_state", "known_user_signals"} <= hidden_sections
        and summary.get("domain_pack_task") == "domain_followup"
        and {"ranked_decisions", "practical_reading", "interaction_state", "known_user_signals"} <= domain_sections
        and summary.get("answer_metadata_version") == "v30.bazi_llm_answer_draft_call.v1"
        and summary.get("chart_fact_mutation_allowed") is False
    )


def _core_bazi_ready(summary: dict[str, Any]) -> bool:
    return (
        summary.get("core_bazi_reading_version") == "v30.core_bazi_reading.v1"
        and summary.get("surface_type") == "core_bazi_calculation"
        and summary.get("chart_fingerprint_preserved") is True
        and summary.get("next_question_topic") in {"career", "wealth", "relationship", "timing", "decision"}
    )
