from __future__ import annotations

from v30.brain import CENTRAL_BRAIN_VERSION
from v30.runtime import attach_hidden_factor_state, create_smoke_runtime


def test_runtime_exposes_central_brain_trace_as_mainline_coordinator() -> None:
    runtime = create_smoke_runtime("v30-central-brain")
    effect = runtime.question_plan.policy_effect
    trace = effect["central_brain_trace"]

    assert effect["central_brain_version"] == CENTRAL_BRAIN_VERSION
    assert trace["version"] == CENTRAL_BRAIN_VERSION
    assert trace["brain_state"]["reading_id"] == runtime.reading_id
    assert trace["brain_state"]["active_mainline_id"] == runtime.mainline_state.mainline_id
    assert trace["question_strategy"]["selected_question_id"] == runtime.question_plan.recommended_questions[0]["question_id"]
    assert trace["expression_orchestration"]["surface_status"] == "clean"
    assert trace["session_memory"]["memory_policy"] == "runtime_memory_is_traceable_and_feedback_conditioned"
    assert "expression_quality_feedback" in trace["session_memory"]["feedback_slots"]
    assert trace["role_state"]["visibility"] == "user_visible"
    assert trace["feedback_strategy"]["no_review_gate"] is True
    assert "expression" in trace["feedback_strategy"]["training_routes"]
    assert runtime.question_plan.policy_effect["recommendation_brain_context"]["question_strategy"] == "context_first_question_strategy"
    assert "central_brain_question_strategy:context_first_question_strategy" in trace["question_strategy"]["reasons"]
    assert "central_brain_coordinates_only" in trace["boundaries"]
    assert "central_brain_does_not_write_database_or_redis_directly" in trace["boundaries"]


def test_central_brain_routes_hidden_factor_unknown_context_to_training() -> None:
    runtime = create_smoke_runtime("v30-central-brain-hidden")
    trace = runtime.question_plan.policy_effect["central_brain_trace"]
    domains = {row["target_signal_domain"] for row in trace["training_signal_routes"]}

    assert "hidden_factor" in domains
    assert "hidden_factor_confirmation" in trace["brain_state"]["unknown_context"]
    assert "hidden_factor_boundary_feedback" in trace["session_memory"]["feedback_slots"]
    assert "hidden_factor_confirmation" in trace["feedback_strategy"]["capture_targets"]
    assert "refresh_hidden_factor_state" in trace["feedback_strategy"]["immediate_effect"]
    assert "ask_hidden_factor_confirmation_question" in trace["runtime_plan"]["next_actions"]


def test_central_brain_recomputes_after_hidden_factor_state_rehydrate() -> None:
    runtime = create_smoke_runtime("v30-central-brain-rehydrate")
    state = {
        "state_id": "v30-central-brain-rehydrate:hidden_factor_state",
        "reading_id": "v30-central-brain-rehydrate",
        "context_id": runtime.chart_context.context_id,
        "status": "amplifier_candidate",
        "amplifier_candidate": True,
        "confidence": 0.82,
        "special_years": ["2020"],
        "repeated_states": ["career_breakthrough"],
        "evidence_ids": [],
        "boundaries": ["feedback_conditioned_not_chart_fact"],
        "feedback": [],
    }

    rehydrated = attach_hidden_factor_state(runtime, state)
    trace = rehydrated.question_plan.policy_effect["central_brain_trace"]

    assert trace["brain_state"]["hidden_factor_focus"] == "amplifier_candidate"
    assert trace["question_strategy"]["hidden_factor_mode"] == "use_as_feedback_conditioned_amplifier"


def test_admin_presentation_consumes_central_brain_diagnostics() -> None:
    from v30.presentation import build_presentation_model

    runtime = create_smoke_runtime("v30-central-brain-presentation")
    payload = build_presentation_model(runtime, role_key="admin", client="admin").model_dump(mode="json")
    brain = payload["diagnostics"]["central_brain"]

    assert brain["version"] == CENTRAL_BRAIN_VERSION
    assert brain["focus"] == "bind_time_context_before_deep_verdict"
    assert brain["expression_surface"] == "clean"
    assert set(brain["training_routes"]) >= {"question_intelligence", "expression", "hidden_factor"}
