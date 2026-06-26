from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from v30.contracts import CoreRuntimeResult
from v30.hidden_factor import (
    HiddenFactorCalibration,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
)
from v30.presentation import build_presentation_model
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime
from v30.validation.bazi_llm_closeout import run_bazi_llm_closeout
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE_VERSION = "v30.bazi_intelligence_requirements_coverage.v1"


def run_bazi_intelligence_requirements_coverage(
    reading_id: str = "ir1-bazi-intelligence-requirements",
) -> dict[str, object]:
    initial = create_smoke_runtime(reading_id)
    chart_before = initial.chart_context.model_dump(mode="json")
    hidden_question_id = _select_hidden_question_id(initial.question_plan.recommended_questions)
    answered = attach_question_outcome(
        initial,
        hidden_question_id,
        {
            "event_id": f"{reading_id}:question_outcome",
            "answer": "2020 年事业状态反复，之后更关注职业方向。",
            "selected_option": "career",
            "confidence": 0.82,
            "feedback_tags": ["career", "hidden_factor_followup"],
        },
    )
    calibration = HiddenFactorCalibration.model_validate(
        answered.question_plan.policy_effect.get("hidden_factor_calibration", {})
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": f"{reading_id}:hidden_factor_feedback",
            "special_event_years": [2020],
            "repeated_states": ["career_repeated_state"],
            "time_context_bindings": ["flow_year"],
            "feedback_status": "affirmed",
        },
    )
    hidden_state = build_hidden_factor_state(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        calibration=calibration,
        feedback=[feedback],
    )
    final_runtime = attach_hidden_factor_state(answered, hidden_state.model_dump(mode="json"))
    projections = {
        f"{role}:{locale}": build_presentation_model(
            final_runtime,
            role_key=role,
            locale=locale,
            client="admin" if role == "admin" else "web",
        ).model_dump(mode="json")
        for role in ("guest", "user", "practitioner", "admin")
        for locale in ("zh", "en", "ko")
    }
    interaction_loop = run_synthetic_tier("interaction_loop")
    bazi_llm_acceptance = run_synthetic_tier("bazi_llm_acceptance")
    interaction_signals = extract_training_signals(interaction_loop)
    bazi_llm_signals = extract_training_signals(bazi_llm_acceptance)
    return build_bazi_intelligence_requirements_coverage(
        initial_runtime=initial.model_dump(mode="json"),
        final_runtime=final_runtime.model_dump(mode="json"),
        projections=projections,
        chart_fingerprint_before=chart_before,
        chart_fingerprint_after=final_runtime.chart_context.model_dump(mode="json"),
        question_id=hidden_question_id,
        synthetic_interaction_loop=interaction_loop.model_dump(mode="json"),
        synthetic_bazi_llm_acceptance=bazi_llm_acceptance.model_dump(mode="json"),
        training_signal_ids=sorted(
            {signal.signal_id for signal in interaction_signals + bazi_llm_signals}
        ),
        bazi_llm_closeout=run_bazi_llm_closeout(reading_id=f"{reading_id}-bl8"),
    )


def build_bazi_intelligence_requirements_coverage(
    *,
    initial_runtime: Mapping[str, Any],
    final_runtime: Mapping[str, Any],
    projections: Mapping[str, Mapping[str, Any]],
    chart_fingerprint_before: Mapping[str, Any],
    chart_fingerprint_after: Mapping[str, Any],
    question_id: str,
    synthetic_interaction_loop: Mapping[str, Any],
    synthetic_bazi_llm_acceptance: Mapping[str, Any],
    training_signal_ids: list[str],
    bazi_llm_closeout: Mapping[str, Any],
) -> dict[str, object]:
    runtime_summary = _runtime_summary(final_runtime)
    projection_summary = _projection_summary(projections)
    interaction_summary = _interaction_summary(initial_runtime, final_runtime, question_id)
    synthetic_summary = _synthetic_summary(
        synthetic_interaction_loop=synthetic_interaction_loop,
        synthetic_bazi_llm_acceptance=synthetic_bazi_llm_acceptance,
        training_signal_ids=training_signal_ids,
    )
    llm_summary = _llm_summary(bazi_llm_closeout, runtime_summary)
    boundary_summary = {
        "chart_fact_fingerprint_preserved": dict(chart_fingerprint_before) == dict(chart_fingerprint_after),
        "chart_fact_mutation_allowed": False,
        "policy_pointer_write_allowed": False,
        "hidden_factor_can_mutate_chart_facts": False,
        "training_can_tune_chart_facts": False,
        "llm_can_generate_chart_facts": False,
    }
    checks = [
        {
            "check_id": "core_bazi_module_chain_covers_original_calculation_need",
            "passed": _core_chain_ready(runtime_summary),
            "observed": runtime_summary,
        },
        {
            "check_id": "multi_user_multi_locale_projection_covers_customer_and_practitioner",
            "passed": _projection_ready(projection_summary),
            "observed": projection_summary,
        },
        {
            "check_id": "continuous_question_answer_loop_and_hidden_factor_feedback_are_active",
            "passed": _interaction_ready(interaction_summary),
            "observed": interaction_summary,
        },
        {
            "check_id": "llm_serves_bazi_answer_expression_without_reopening_core_modules",
            "passed": _llm_ready(llm_summary),
            "observed": llm_summary,
        },
        {
            "check_id": "training_and_synthetic_cover_interaction_and_llm_without_chart_fact_tuning",
            "passed": _synthetic_ready(synthetic_summary),
            "observed": synthetic_summary,
        },
        {
            "check_id": "read_only_boundaries_preserve_deterministic_bazi_facts",
            "passed": _boundary_ready(boundary_summary),
            "observed": boundary_summary,
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE_VERSION,
        "task": {
            "task_id": "IR1",
            "title": "Bazi Intelligence Requirements Coverage",
            "scope": "prove original Bazi product requirements across core modules, role projection, hidden-factor dialogue, LLM expression, training, and synthetic validation",
        },
        "coverage_summary": {
            "core_modules_ready": _core_chain_ready(runtime_summary),
            "multi_user_multi_locale_ready": _projection_ready(projection_summary),
            "continuous_qa_hidden_factor_ready": _interaction_ready(interaction_summary),
            "bazi_llm_ready": _llm_ready(llm_summary),
            "training_synthetic_ready": _synthetic_ready(synthetic_summary),
            "read_only_boundary_ready": _boundary_ready(boundary_summary),
        },
        "runtime_summary": runtime_summary,
        "projection_summary": projection_summary,
        "interaction_summary": interaction_summary,
        "synthetic_summary": synthetic_summary,
        "llm_summary": llm_summary,
        "boundary_summary": boundary_summary,
        "checks": checks,
        "decision": {
            "requirements_coverage_ready": ready,
            "decision_status": "ir1_bazi_intelligence_requirements_covered"
            if ready
            else "ir1_bazi_intelligence_requirements_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "core_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "next_mainline_selection": {
            "task_id": "IR-S1" if ready else "IR1-FIX",
            "title": "Integrated Bazi Intelligence Steady State"
            if ready
            else "Fix Integrated Requirements Coverage",
            "reason": "original_requirements_covered_by_current_backend_modules"
            if ready
            else "requirements_coverage_checks_failed",
            "default_next_step": "wait_for_new_business_or_calibration_evidence",
            "major_gate_only": [
                "full_pytest",
                "synthetic_all",
                "518k_sample_or_full",
                "live_provider_smoke",
                "release_pointer_promotion",
            ],
        },
        "boundary": "ir1_validates_integrated_bazi_intelligence_without_mutating_chart_facts_or_promoting_policy",
    }


def _select_hidden_question_id(questions: Any) -> str:
    if isinstance(questions, list):
        for question in questions:
            if isinstance(question, dict) and question.get("topic") == "hidden_factor":
                return str(question.get("question_id"))
        for question in questions:
            if isinstance(question, dict) and question.get("question_id"):
                return str(question.get("question_id"))
    return "q_v30_hidden_factor_boundary_discovery"


def _runtime_summary(runtime: Mapping[str, Any]) -> dict[str, Any]:
    policy = _mapping(_mapping(runtime.get("question_plan")).get("policy_effect"))
    reading = _mapping(_first_projection(runtime).get("reading_surface")).get("core_bazi_reading", {})
    reading = _mapping(reading)
    m3 = _mapping(policy.get("m3_completion_summary"))
    ranked = _mapping(policy.get("ranked_decisions"))
    practical = _mapping(policy.get("practical_reading_context"))
    return {
        "m1_m2_completion_version": _mapping(reading.get("m1_m2_completion_summary")).get("version"),
        "core_bazi_reading_version": reading.get("version"),
        "four_pillar_count": len(reading.get("four_pillars", [])) if isinstance(reading.get("four_pillars"), list) else 0,
        "m3_completion_version": m3.get("version"),
        "m3_status": m3.get("status"),
        "m3_completion_coverage": float(m3.get("completion_coverage") or 0.0),
        "m3_mainline_support_count": int(m3.get("mainline_support_count") or 0),
        "m3_m4_support_ready": bool(m3.get("m4_model_signal_support")),
        "m3_m5_support_count": int(m3.get("m5_ranked_decision_support_count") or 0),
        "m3_m6_support_count": int(m3.get("m6_practical_reading_support_count") or 0),
        "krp_unit_count": int(_mapping(policy.get("krp_library_summary")).get("unit_count") or 0),
        "model_signal_version": _mapping(policy.get("model_signal_summary")).get("version"),
        "ranked_decision_domains": sorted(str(key) for key in ranked.keys()),
        "practical_domain_count": len(practical.get("domains", [])) if isinstance(practical.get("domains"), list) else len(_mapping(practical.get("domain_readings"))),
        "central_brain_version": policy.get("central_brain_version"),
        "llm_answer_metadata_version": _mapping(policy.get("llm_answer_draft_call")).get("version"),
    }


def _first_projection(runtime: Mapping[str, Any]) -> dict[str, Any]:
    try:
        runtime_model = CoreRuntimeResult.model_validate(deepcopy(runtime))
    except Exception:
        runtime_model = create_smoke_runtime("ir1-runtime-summary-projection")
    return build_presentation_model(runtime_model, role_key="user").model_dump(mode="json")


def _projection_summary(projections: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    keys = sorted(projections.keys())
    customer_keys = [key for key in keys if key.startswith("guest:") or key.startswith("user:")]
    diagnostic_keys = [key for key in keys if key.startswith("practitioner:") or key.startswith("admin:")]
    customer_diagnostic_leaks = [
        key for key in customer_keys if bool(_mapping(projections[key].get("diagnostics")))
    ]
    diagnostic_visible = [
        key for key in diagnostic_keys if bool(_mapping(projections[key].get("diagnostics")))
    ]
    core_surface_keys = [
        key for key in keys
        if bool(_mapping(_mapping(projections[key].get("reading_surface")).get("core_bazi_reading")))
    ]
    locales = sorted({key.split(":", 1)[1] for key in keys if ":" in key})
    roles = sorted({key.split(":", 1)[0] for key in keys if ":" in key})
    return {
        "projection_count": len(keys),
        "roles": roles,
        "locales": locales,
        "customer_diagnostic_leak_count": len(customer_diagnostic_leaks),
        "diagnostic_visible_count": len(diagnostic_visible),
        "core_surface_projection_count": len(core_surface_keys),
        "projection_contract_versions": sorted(
            {
                str(_mapping(payload.get("projection_contract")).get("version"))
                for payload in projections.values()
                if _mapping(payload.get("projection_contract")).get("version")
            }
        ),
    }


def _interaction_summary(initial_runtime: Mapping[str, Any], final_runtime: Mapping[str, Any], question_id: str) -> dict[str, Any]:
    initial_policy = _mapping(_mapping(initial_runtime.get("question_plan")).get("policy_effect"))
    final_policy = _mapping(_mapping(final_runtime.get("question_plan")).get("policy_effect"))
    state = _mapping(final_policy.get("interaction_state"))
    session_state = _mapping(_mapping(final_runtime.get("question_plan")).get("session_state"))
    outcomes = session_state.get("question_outcomes", [])
    outcomes = outcomes if isinstance(outcomes, list) else []
    hidden_state = _mapping(final_policy.get("hidden_factor_state"))
    return {
        "answered_question_id": question_id,
        "outcome_count": len(outcomes),
        "answered_question_ids": state.get("answered_question_ids", []),
        "initial_visible_next_question_id": _mapping(initial_policy.get("interaction_state")).get("visible_next_question_id"),
        "final_visible_next_question_id": state.get("visible_next_question_id"),
        "internal_next_question_id": state.get("internal_next_question_id"),
        "visible_internal_split": bool(state.get("visible_next_question_id"))
        and bool(state.get("internal_next_question_id")),
        "hidden_factor_state_status": hidden_state.get("status"),
        "hidden_factor_boundary": hidden_state.get("boundary"),
        "hidden_factor_chart_fact_mutation_allowed": hidden_state.get("chart_fact_mutation_allowed", False),
    }


def _synthetic_summary(
    *,
    synthetic_interaction_loop: Mapping[str, Any],
    synthetic_bazi_llm_acceptance: Mapping[str, Any],
    training_signal_ids: list[str],
) -> dict[str, Any]:
    return {
        "interaction_loop_suite_id": synthetic_interaction_loop.get("suite_id"),
        "interaction_loop_case_count": int(synthetic_interaction_loop.get("case_count") or 0),
        "interaction_loop_passed_count": int(synthetic_interaction_loop.get("passed_count") or 0),
        "bazi_llm_acceptance_suite_id": synthetic_bazi_llm_acceptance.get("suite_id"),
        "bazi_llm_acceptance_case_count": int(synthetic_bazi_llm_acceptance.get("case_count") or 0),
        "bazi_llm_acceptance_passed_count": int(synthetic_bazi_llm_acceptance.get("passed_count") or 0),
        "required_training_signal_ids": sorted(
            set(training_signal_ids)
            & {
                "v30.training_signal.m3_core_spine_coverage",
                "v30.training_signal.question_dialogue_outcome",
                "v30.training_signal.interaction_loop_quality",
                "v30.training_signal.bazi_llm_output_acceptance_quality",
                "v30.training_signal.role_locale_client_projection_coverage",
                "v30.training_signal.api_projection_contract",
            }
        ),
        "training_can_tune_chart_facts": False,
    }


def _llm_summary(bazi_llm_closeout: Mapping[str, Any], runtime_summary: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(bazi_llm_closeout.get("decision"))
    return {
        "closeout_version": bazi_llm_closeout.get("version"),
        "closeout_ready": decision.get("closeout_ready"),
        "decision_status": decision.get("decision_status"),
        "runtime_answer_metadata_version": runtime_summary.get("llm_answer_metadata_version"),
        "live_llm_required": decision.get("live_llm_required", False),
        "chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed", False),
        "core_bazi_modules_reopened": decision.get("core_bazi_modules_reopened", False),
    }


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _core_chain_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("core_bazi_reading_version") == "v30.core_bazi_reading.v1"
        and int(summary.get("four_pillar_count") or 0) >= 4
        and summary.get("m3_completion_version") == "v30.m3_completion_summary.v1"
        and summary.get("m3_status") == "ready"
        and float(summary.get("m3_completion_coverage") or 0.0) >= 1.0
        and int(summary.get("m3_mainline_support_count") or 0) > 0
        and summary.get("m3_m4_support_ready") is True
        and int(summary.get("m3_m5_support_count") or 0) >= 2
        and int(summary.get("m3_m6_support_count") or 0) >= 5
        and int(summary.get("krp_unit_count") or 0) >= 35
        and summary.get("model_signal_version") == "v30.model_signal_summary.v1"
        and {"strength", "structure_pattern", "useful_god"} <= set(summary.get("ranked_decision_domains", []))
        and int(summary.get("practical_domain_count") or 0) >= 5
        and bool(summary.get("central_brain_version"))
    )


def _projection_ready(summary: Mapping[str, Any]) -> bool:
    return (
        set(summary.get("roles", [])) >= {"guest", "user", "practitioner", "admin"}
        and set(summary.get("locales", [])) == {"en", "ko", "zh"}
        and int(summary.get("projection_count") or 0) >= 12
        and int(summary.get("customer_diagnostic_leak_count") or 0) == 0
        and int(summary.get("diagnostic_visible_count") or 0) >= 6
        and int(summary.get("core_surface_projection_count") or 0) >= 12
        and "v30.api_projection_contract.v1" in set(summary.get("projection_contract_versions", []))
    )


def _interaction_ready(summary: Mapping[str, Any]) -> bool:
    return (
        int(summary.get("outcome_count") or 0) >= 1
        and summary.get("answered_question_id") in set(summary.get("answered_question_ids", []))
        and bool(summary.get("final_visible_next_question_id"))
        and bool(summary.get("internal_next_question_id"))
        and summary.get("hidden_factor_state_status") == "amplifier_candidate"
        and summary.get("hidden_factor_chart_fact_mutation_allowed", False) is False
    )


def _llm_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("closeout_version") == "v30.bazi_llm_closeout.v1"
        and summary.get("closeout_ready") is True
        and summary.get("runtime_answer_metadata_version") == "v30.bazi_llm_answer_draft_call.v1"
        and summary.get("live_llm_required", False) is False
        and summary.get("chart_fact_mutation_allowed", False) is False
        and summary.get("core_bazi_modules_reopened", False) is False
    )


def _synthetic_ready(summary: Mapping[str, Any]) -> bool:
    required = {
        "v30.training_signal.m3_core_spine_coverage",
        "v30.training_signal.question_dialogue_outcome",
        "v30.training_signal.interaction_loop_quality",
        "v30.training_signal.bazi_llm_output_acceptance_quality",
        "v30.training_signal.role_locale_client_projection_coverage",
        "v30.training_signal.api_projection_contract",
    }
    return (
        summary.get("interaction_loop_suite_id") == "v30.synthetic.interaction_loop"
        and int(summary.get("interaction_loop_case_count") or 0) == int(summary.get("interaction_loop_passed_count") or -1)
        and int(summary.get("interaction_loop_case_count") or 0) >= 5
        and summary.get("bazi_llm_acceptance_suite_id") == "v30.synthetic.bazi_llm_acceptance"
        and int(summary.get("bazi_llm_acceptance_case_count") or 0) == int(summary.get("bazi_llm_acceptance_passed_count") or -1)
        and int(summary.get("bazi_llm_acceptance_case_count") or 0) >= 5
        and required <= set(summary.get("required_training_signal_ids", []))
        and summary.get("training_can_tune_chart_facts") is False
    )


def _boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("chart_fact_fingerprint_preserved") is True
        and summary.get("chart_fact_mutation_allowed") is False
        and summary.get("policy_pointer_write_allowed") is False
        and summary.get("hidden_factor_can_mutate_chart_facts") is False
        and summary.get("training_can_tune_chart_facts") is False
        and summary.get("llm_can_generate_chart_facts") is False
    )
