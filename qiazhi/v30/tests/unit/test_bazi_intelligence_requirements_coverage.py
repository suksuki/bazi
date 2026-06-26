from __future__ import annotations

from copy import deepcopy

from v30.validation.bazi_intelligence_requirements_coverage import (
    BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE_VERSION,
    build_bazi_intelligence_requirements_coverage,
    run_bazi_intelligence_requirements_coverage,
)


def test_ir1_bazi_intelligence_requirements_coverage_ready() -> None:
    result = run_bazi_intelligence_requirements_coverage(reading_id="pytest-ir1-coverage")

    assert result["version"] == BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE_VERSION
    assert result["decision"]["requirements_coverage_ready"] is True
    assert result["decision"]["decision_status"] == "ir1_bazi_intelligence_requirements_covered"
    assert result["decision"]["passed_check_count"] == 6
    assert result["coverage_summary"]["core_modules_ready"] is True
    assert result["coverage_summary"]["multi_user_multi_locale_ready"] is True
    assert result["coverage_summary"]["continuous_qa_hidden_factor_ready"] is True
    assert result["coverage_summary"]["bazi_llm_ready"] is True
    assert result["coverage_summary"]["training_synthetic_ready"] is True
    assert result["coverage_summary"]["read_only_boundary_ready"] is True
    assert result["next_mainline_selection"]["task_id"] == "IR-S1"
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["synthetic_all_required"] is False
    assert result["decision"]["full_518k_required"] is False


def test_ir1_blocks_when_m3_core_spine_is_not_ready() -> None:
    ready = run_bazi_intelligence_requirements_coverage(reading_id="pytest-ir1-m3-block")
    final_runtime = deepcopy(ready["runtime_summary"])
    assert final_runtime["m3_status"] == "ready"

    payload = _builder_payload()
    runtime = deepcopy(payload["final_runtime"])
    runtime["question_plan"]["policy_effect"]["m3_completion_summary"]["status"] = "blocked"  # type: ignore[index]
    payload["final_runtime"] = runtime
    result = build_bazi_intelligence_requirements_coverage(**payload)

    assert result["decision"]["requirements_coverage_ready"] is False
    assert "core_bazi_module_chain_covers_original_calculation_need" in result["decision"]["failed_check_ids"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False


def test_ir1_admin_endpoint_is_read_only() -> None:
    from v30.api.app import create_app

    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/mainline/bazi-intelligence-requirements-coverage"
    )
    payload = route.endpoint(reading_id="pytest-ir1-admin")

    assert payload["version"] == BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE_VERSION
    assert payload["decision"]["requirements_coverage_ready"] is True
    assert payload["decision"]["policy_pointer_write_allowed"] is False
    assert payload["boundary"] == (
        "ir1_validates_integrated_bazi_intelligence_without_mutating_chart_facts_or_promoting_policy"
    )


def _builder_payload() -> dict[str, object]:
    # The public result intentionally summarizes runtime evidence; rebuild the full builder input
    # through the same runner path for mutation tests.
    from v30.hidden_factor import (
        HiddenFactorCalibration,
        build_hidden_factor_state,
        hidden_factor_feedback_from_payload,
    )
    from v30.presentation import build_presentation_model
    from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime
    from v30.validation import extract_training_signals, run_synthetic_tier
    from v30.validation.bazi_llm_closeout import run_bazi_llm_closeout

    initial = create_smoke_runtime("pytest-ir1-builder-full")
    chart_before = initial.chart_context.model_dump(mode="json")
    question_id = "q_v30_hidden_factor_boundary_discovery"
    answered = attach_question_outcome(
        initial,
        question_id,
        {
            "answer": "2020 年事业状态反复。",
            "selected_option": "career",
            "confidence": 0.82,
            "feedback_tags": ["career", "hidden_factor_followup"],
        },
    )
    calibration = HiddenFactorCalibration.model_validate(
        answered.question_plan.policy_effect["hidden_factor_calibration"]
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
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
    interaction = run_synthetic_tier("interaction_loop")
    bazi_llm = run_synthetic_tier("bazi_llm_acceptance")
    signal_ids = sorted(
        {signal.signal_id for signal in extract_training_signals(interaction) + extract_training_signals(bazi_llm)}
    )
    return {
        "initial_runtime": initial.model_dump(mode="json"),
        "final_runtime": final_runtime.model_dump(mode="json"),
        "projections": projections,
        "chart_fingerprint_before": chart_before,
        "chart_fingerprint_after": final_runtime.chart_context.model_dump(mode="json"),
        "question_id": question_id,
        "synthetic_interaction_loop": interaction.model_dump(mode="json"),
        "synthetic_bazi_llm_acceptance": bazi_llm.model_dump(mode="json"),
        "training_signal_ids": signal_ids,
        "bazi_llm_closeout": run_bazi_llm_closeout(reading_id="pytest-ir1-builder-bl8"),
    }
