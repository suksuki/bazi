from __future__ import annotations

from v30.brain.contracts import (
    BrainState,
    CentralBrainTrace,
    ExpressionOrchestration,
    FeedbackStrategy,
    QuestionDialogueStrategy,
    RoleState,
    RuntimePlannerDecision,
    SessionMemory,
    TrainingSignalRoute,
)
from v30.contracts import AnswerContext, CoreRuntimeResult


CENTRAL_BRAIN_VERSION = "v30.central_brain.v1"
ROLE_VOICE = {
    "guest": "warm_plain_bazi",
    "user": "calm_bazi_consultation",
    "practitioner": "dense_bazi_practitioner",
    "analyst": "traceable_bazi_analyst",
    "admin": "diagnostic_operator",
    "lab": "validation_researcher",
}


def build_recommendation_brain_context(
    *,
    reading_id: str,
    role_key: str,
    active_mainline_id: str,
    time_status: str,
    hidden_factor_status: str,
) -> dict[str, object]:
    unknown_context: list[str] = []
    if time_status != "bound":
        unknown_context.append("time_layer_boundary")
    if hidden_factor_status in {"needs_dialogue", "dialogue_in_progress"}:
        unknown_context.append("hidden_factor_confirmation")
    feedback_slots = ["question_answer_feedback", "expression_quality_feedback"]
    if "hidden_factor_confirmation" in unknown_context:
        feedback_slots.append("hidden_factor_boundary_feedback")
    if "time_layer_boundary" in unknown_context:
        feedback_slots.append("time_context_feedback")
    return {
        "version": CENTRAL_BRAIN_VERSION,
        "reading_id": reading_id,
        "role_key": role_key,
        "active_mainline_id": active_mainline_id,
        "unknown_context": unknown_context,
        "feedback_slots": feedback_slots,
        "question_strategy": _strategy_from_unknown_context(unknown_context),
        "feedback_training_routes": _feedback_training_routes(unknown_context),
    }


def build_expression_role_state(
    *,
    reading_id: str,
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    diagnostics_visible = role_key in {"analyst", "admin", "lab"}
    return {
        "role_state_id": f"{reading_id}:brain-role-state:{role_key}",
        "role_key": role_key,
        "visibility": "diagnostic" if diagnostics_visible else "user_visible",
        "answer_density": "diagnostic" if diagnostics_visible else ("compact" if client == "mobile" else "standard"),
        "diagnostics_visible": diagnostics_visible,
        "expression_voice": ROLE_VOICE.get(role_key, ROLE_VOICE["user"]),
        "client": client,
    }


def build_central_brain_trace(
    runtime: CoreRuntimeResult,
    *,
    answer_context: AnswerContext | None,
    expression_plan: dict[str, object] | None = None,
    rendered_narrative: dict[str, object] | None = None,
) -> CentralBrainTrace:
    selected_question = _selected_question(runtime, answer_context)
    hidden_status = _hidden_factor_status(runtime)
    state = BrainState(
        state_id=f"{runtime.reading_id}:brain-state",
        reading_id=runtime.reading_id,
        role_key=runtime.question_plan.role_key,
        session_phase=_session_phase(runtime, hidden_status),
        active_mainline_id=runtime.mainline_state.mainline_id,
        selected_question_id=selected_question.get("question_id"),
        known_context=_known_context(runtime),
        unknown_context=_unknown_context(runtime),
        hidden_factor_focus=hidden_status,
    )
    session_memory = _build_session_memory(runtime, state)
    role_state = _build_role_state(runtime, expression_plan)
    runtime_plan = RuntimePlannerDecision(
        decision_id=f"{runtime.reading_id}:brain-runtime-plan",
        focus=_runtime_focus(state),
        next_actions=_next_actions(state),
        safeguards=[
            "preserve_chart_context",
            "preserve_structure_and_mainline_boundaries",
            "do_not_promote_hidden_factor_without_feedback",
            "route_feedback_to_training_signals",
        ],
    )
    question_strategy = QuestionDialogueStrategy(
        strategy_id=f"{runtime.reading_id}:brain-question-strategy",
        selected_question_id=selected_question.get("question_id"),
        selected_intent_id=selected_question.get("intent_id"),
        strategy=_question_strategy_name(state),
        reasons=_question_strategy_reasons(selected_question, state),
        hidden_factor_mode=_hidden_factor_mode(hidden_status),
    )
    expression_orchestration = ExpressionOrchestration(
        orchestration_id=f"{runtime.reading_id}:brain-expression",
        expression_plan_id=_string_field(expression_plan, "plan_id"),
        rendered_narrative_id=_string_field(rendered_narrative, "narrative_id"),
        style_profile_id=_style_profile_id(expression_plan),
        surface_status=_surface_status(rendered_narrative),
        safeguards=[
            "separate_internal_runtime_language_from_surface_bazi_language",
            "block_user_visible_engineering_token_leakage",
            "preserve_portrait_projection_boundary",
        ],
    )
    feedback_strategy = _build_feedback_strategy(runtime, state, expression_orchestration)
    return CentralBrainTrace(
        trace_id=f"{runtime.reading_id}:central-brain-trace",
        version=CENTRAL_BRAIN_VERSION,
        brain_state=state,
        session_memory=session_memory,
        role_state=role_state,
        runtime_plan=runtime_plan,
        question_strategy=question_strategy,
        expression_orchestration=expression_orchestration,
        feedback_strategy=feedback_strategy,
        training_signal_routes=_training_signal_routes(runtime, state, expression_orchestration),
        boundaries=[
            "central_brain_coordinates_only",
            "central_brain_does_not_mutate_chart_facts",
            "central_brain_does_not_write_database_or_redis_directly",
            "central_brain_does_not_auto_apply_policy_without_validation_gate",
        ],
    )


def _build_session_memory(runtime: CoreRuntimeResult, state: BrainState) -> SessionMemory:
    feedback_slots = ["question_answer_feedback", "expression_quality_feedback"]
    if "hidden_factor_confirmation" in state.unknown_context:
        feedback_slots.append("hidden_factor_boundary_feedback")
    if "time_layer_boundary" in state.unknown_context:
        feedback_slots.append("time_context_feedback")
    return SessionMemory(
        memory_id=f"{runtime.reading_id}:brain-session-memory",
        known_context=state.known_context,
        unknown_context=state.unknown_context,
        last_selected_question_id=state.selected_question_id,
        feedback_slots=feedback_slots,
        memory_policy="runtime_memory_is_traceable_and_feedback_conditioned",
    )


def _build_role_state(
    runtime: CoreRuntimeResult,
    expression_plan: dict[str, object] | None,
) -> RoleState:
    role = runtime.question_plan.role_key
    diagnostics_visible = role in {"analyst", "admin", "lab"}
    expression_voice = _style_profile_voice(expression_plan) or ROLE_VOICE.get(role, ROLE_VOICE["user"])
    return RoleState(
        role_state_id=f"{runtime.reading_id}:brain-role-state:{role}",
        role_key=role,
        visibility="diagnostic" if diagnostics_visible else "user_visible",
        answer_density="diagnostic" if diagnostics_visible else "standard",
        diagnostics_visible=diagnostics_visible,
        expression_voice=expression_voice,
    )


def _build_feedback_strategy(
    runtime: CoreRuntimeResult,
    state: BrainState,
    expression_orchestration: ExpressionOrchestration,
) -> FeedbackStrategy:
    capture_targets = ["selected_question_response", "answer_usefulness", "expression_fit"]
    immediate_effect = ["refresh_question_dialogue_strategy", "refresh_rendered_narrative"]
    training_routes = ["question_intelligence", "expression"]
    if "hidden_factor_confirmation" in state.unknown_context:
        capture_targets.append("hidden_factor_confirmation")
        immediate_effect.append("refresh_hidden_factor_state")
        training_routes.append("hidden_factor")
    if "time_layer_boundary" in state.unknown_context:
        capture_targets.append("time_context_boundary")
        training_routes.append("context_binding")
    if expression_orchestration.surface_status != "clean":
        immediate_effect.append("tune_expression_policy_candidate")
    return FeedbackStrategy(
        strategy_id=f"{runtime.reading_id}:brain-feedback-strategy",
        capture_targets=capture_targets,
        immediate_effect=immediate_effect,
        training_routes=training_routes,
        no_review_gate=True,
    )


def _selected_question(
    runtime: CoreRuntimeResult,
    answer_context: AnswerContext | None,
) -> dict[str, object]:
    return runtime.question_plan.recommended_questions[0] if runtime.question_plan.recommended_questions else {}


def _hidden_factor_status(runtime: CoreRuntimeResult) -> str:
    state = runtime.question_plan.policy_effect.get("hidden_factor_state", {})
    if isinstance(state, dict) and state.get("status"):
        return str(state["status"])
    calibration = runtime.question_plan.policy_effect.get("hidden_factor_calibration", {})
    if isinstance(calibration, dict) and calibration.get("status"):
        return str(calibration["status"])
    return "unknown"


def _session_phase(runtime: CoreRuntimeResult, hidden_status: str) -> str:
    if hidden_status in {"needs_dialogue", "dialogue_in_progress"}:
        return "context_binding"
    if runtime.answer_context is not None or runtime.answer_result is not None:
        return "answer_ready"
    return "runtime_ready"


def _known_context(runtime: CoreRuntimeResult) -> list[str]:
    known = ["natal_pillars", "day_master", "structure_state", "mainline_state"]
    if runtime.chart_context.time_layers.get("luck_pillar"):
        known.append("luck_pillar")
    if runtime.chart_context.time_layers.get("flow_year_pillar"):
        known.append("flow_year_pillar")
    return known


def _unknown_context(runtime: CoreRuntimeResult) -> list[str]:
    unknown: list[str] = []
    if runtime.chart_context.time_layers.get("status") != "bound":
        unknown.append("time_layer_boundary")
    if _hidden_factor_status(runtime) in {"needs_dialogue", "dialogue_in_progress"}:
        unknown.append("hidden_factor_confirmation")
    return unknown


def _runtime_focus(state: BrainState) -> str:
    if "time_layer_boundary" in state.unknown_context:
        return "bind_time_context_before_deep_verdict"
    if "hidden_factor_confirmation" in state.unknown_context:
        return "ask_hidden_factor_boundary_question"
    return "answer_selected_mainline_question"


def _next_actions(state: BrainState) -> list[str]:
    actions = ["render_role_aware_surface_text"]
    if "time_layer_boundary" in state.unknown_context:
        actions.insert(0, "ask_time_context_boundary_question")
    if "hidden_factor_confirmation" in state.unknown_context:
        actions.append("ask_hidden_factor_confirmation_question")
    actions.append("record_feedback_for_training")
    return actions


def _question_strategy_name(state: BrainState) -> str:
    return _strategy_from_unknown_context(state.unknown_context)


def _question_strategy_reasons(
    selected_question: dict[str, object],
    state: BrainState,
) -> list[str]:
    reasons = [str(row) for row in selected_question.get("reasons", [])]
    strategy_reason = f"central_brain_question_strategy:{_question_strategy_name(state)}"
    if strategy_reason not in reasons:
        reasons.append(strategy_reason)
    return reasons


def _strategy_from_unknown_context(unknown_context: list[str]) -> str:
    if "time_layer_boundary" in unknown_context:
        return "context_first_question_strategy"
    if "hidden_factor_confirmation" in unknown_context:
        return "hidden_factor_discovery_strategy"
    return "mainline_followup_strategy"


def _feedback_training_routes(unknown_context: list[str]) -> list[str]:
    routes = ["question_intelligence", "expression"]
    if "hidden_factor_confirmation" in unknown_context:
        routes.append("hidden_factor")
    if "time_layer_boundary" in unknown_context:
        routes.append("context_binding")
    return routes


def _hidden_factor_mode(hidden_status: str) -> str:
    if hidden_status in {"amplifier_candidate", "feedback_calibrated"}:
        return "use_as_feedback_conditioned_amplifier"
    if hidden_status in {"user_denied", "conflicting"}:
        return "keep_as_boundary_not_fact"
    return "discover_through_dialogue"


def _training_signal_routes(
    runtime: CoreRuntimeResult,
    state: BrainState,
    expression_orchestration: ExpressionOrchestration,
) -> list[TrainingSignalRoute]:
    routes = [
        TrainingSignalRoute(
            route_id=f"{runtime.reading_id}:route:question",
            source="question_strategy",
            target_signal_domain="question_intelligence",
            reason="selected question and reasons should train recommendation policy",
        ),
        TrainingSignalRoute(
            route_id=f"{runtime.reading_id}:route:expression",
            source="expression_orchestration",
            target_signal_domain="expression",
            reason="surface status and leakage checks should train expression policy",
        ),
    ]
    if "hidden_factor_confirmation" in state.unknown_context:
        routes.append(
            TrainingSignalRoute(
                route_id=f"{runtime.reading_id}:route:hidden_factor",
                source="brain_state.hidden_factor_focus",
                target_signal_domain="hidden_factor",
                reason="hidden factor unknown context should train dialogue probes",
            )
        )
    if expression_orchestration.surface_status != "clean":
        routes.append(
            TrainingSignalRoute(
                route_id=f"{runtime.reading_id}:route:expression_leakage",
                source="rendered_narrative.diagnostics",
                target_signal_domain="expression",
                reason="engineering token leakage must tune style policy",
            )
        )
    return routes


def _style_profile_id(expression_plan: dict[str, object] | None) -> str | None:
    style = expression_plan.get("style_profile") if expression_plan else None
    if not isinstance(style, dict):
        return None
    value = style.get("style_profile_id")
    return str(value) if value else None


def _style_profile_voice(expression_plan: dict[str, object] | None) -> str | None:
    style = expression_plan.get("style_profile") if expression_plan else None
    if not isinstance(style, dict):
        return None
    value = style.get("voice")
    return str(value) if value else None


def _surface_status(rendered_narrative: dict[str, object] | None) -> str:
    diagnostics = rendered_narrative.get("diagnostics") if rendered_narrative else None
    if isinstance(diagnostics, dict) and diagnostics.get("forbidden_token_hits"):
        return "needs_expression_tuning"
    return "clean"


def _string_field(payload: dict[str, object] | None, key: str) -> str | None:
    if not payload:
        return None
    value = payload.get(key)
    return str(value) if value else None
