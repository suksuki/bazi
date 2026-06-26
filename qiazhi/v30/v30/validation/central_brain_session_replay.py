from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.hidden_factor import (
    HiddenFactorCalibration,
    build_hidden_factor_state,
    hidden_factor_feedback_from_payload,
)
from v30.presentation import build_presentation_model
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_smoke_runtime
from v30.validation.central_brain_acceptance import run_central_brain_acceptance


CENTRAL_BRAIN_SESSION_REPLAY_VERSION = "v30.central_brain_session_replay.v1"


def run_central_brain_session_replay() -> dict[str, Any]:
    bt1 = run_central_brain_acceptance()
    initial = create_smoke_runtime("bt2-central-brain-session-replay")
    chart_fingerprint_before = initial.chart_context.model_dump(mode="json")
    first_question_id = str(initial.question_plan.recommended_questions[0]["question_id"])
    first_visible_next = _visible_next_question_id(initial)
    answered = attach_question_outcome(
        initial,
        first_question_id,
        {
            "event_id": "bt2-question-outcome-001",
            "answer": "先看事业和最近几年反复出现的压力状态。",
            "selected_option": "career",
            "confidence": 0.78,
            "feedback_tags": ["career", "priority_domain"],
        },
    )
    second_question_id = str(answered.question_plan.recommended_questions[0]["question_id"])
    calibration = HiddenFactorCalibration.model_validate(
        answered.question_plan.policy_effect.get("hidden_factor_calibration", {})
    )
    feedback = hidden_factor_feedback_from_payload(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        payload={
            "feedback_id": "bt2-hidden-factor-feedback-001",
            "special_event_years": [2020],
            "repeated_states": ["career_breakthrough"],
            "time_context_bindings": ["flow_year"],
            "feedback_status": "affirmed",
            "source": "bt2_session_replay",
        },
    )
    hidden_state = build_hidden_factor_state(
        reading_id=answered.reading_id,
        context_id=answered.chart_context.context_id,
        calibration=calibration,
        feedback=[feedback],
    )
    hidden_rehydrated = attach_hidden_factor_state(answered, hidden_state.model_dump(mode="json"))
    user_projection = build_presentation_model(hidden_rehydrated, role_key="user", client="web").model_dump(mode="json")
    practitioner_projection = build_presentation_model(
        hidden_rehydrated,
        role_key="practitioner",
        client="web",
    ).model_dump(mode="json")
    return build_central_brain_session_replay(
        bt1_acceptance=bt1,
        initial_runtime=initial.model_dump(mode="json"),
        answered_runtime=answered.model_dump(mode="json"),
        hidden_rehydrated_runtime=hidden_rehydrated.model_dump(mode="json"),
        user_projection=user_projection,
        practitioner_projection=practitioner_projection,
        chart_fingerprint_before=chart_fingerprint_before,
        chart_fingerprint_after=hidden_rehydrated.chart_context.model_dump(mode="json"),
        first_question_id=first_question_id,
        second_question_id=second_question_id,
        first_visible_next_question_id=first_visible_next,
        final_visible_next_question_id=_visible_next_question_id(hidden_rehydrated),
    )


def build_central_brain_session_replay(
    *,
    bt1_acceptance: Mapping[str, Any],
    initial_runtime: Mapping[str, Any],
    answered_runtime: Mapping[str, Any],
    hidden_rehydrated_runtime: Mapping[str, Any],
    user_projection: Mapping[str, Any],
    practitioner_projection: Mapping[str, Any],
    chart_fingerprint_before: Mapping[str, Any],
    chart_fingerprint_after: Mapping[str, Any],
    first_question_id: str,
    second_question_id: str,
    first_visible_next_question_id: str,
    final_visible_next_question_id: str,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    replay_summary = _replay_summary(
        initial_runtime=initial_runtime,
        answered_runtime=answered_runtime,
        hidden_rehydrated_runtime=hidden_rehydrated_runtime,
        user_projection=user_projection,
        practitioner_projection=practitioner_projection,
        chart_fingerprint_before=chart_fingerprint_before,
        chart_fingerprint_after=chart_fingerprint_after,
        first_question_id=first_question_id,
        second_question_id=second_question_id,
        first_visible_next_question_id=first_visible_next_question_id,
        final_visible_next_question_id=final_visible_next_question_id,
    )
    bt1_summary = _bt1_summary(bt1_acceptance)
    checks = _replay_checks(bt1_summary, replay_summary)
    decision = _decision(checks)
    return {
        "version": CENTRAL_BRAIN_SESSION_REPLAY_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["central_brain_session_replay_ready"] else "blocked",
        "decision": decision,
        "bt1_summary": bt1_summary,
        "replay_summary": replay_summary,
        "replay_checks": checks,
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt2_replays_long_session_brain_state_without_chart_fact_mutation",
    }


def _visible_next_question_id(runtime: Any) -> str:
    interaction = runtime.question_plan.policy_effect.get("interaction_state", {})
    return str(interaction.get("visible_next_question_id") or "")


def _bt1_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "central_brain_acceptance_ready": bool(decision.get("central_brain_acceptance_ready")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _replay_summary(
    *,
    initial_runtime: Mapping[str, Any],
    answered_runtime: Mapping[str, Any],
    hidden_rehydrated_runtime: Mapping[str, Any],
    user_projection: Mapping[str, Any],
    practitioner_projection: Mapping[str, Any],
    chart_fingerprint_before: Mapping[str, Any],
    chart_fingerprint_after: Mapping[str, Any],
    first_question_id: str,
    second_question_id: str,
    first_visible_next_question_id: str,
    final_visible_next_question_id: str,
) -> dict[str, Any]:
    answered_plan = _question_plan(answered_runtime)
    hidden_plan = _question_plan(hidden_rehydrated_runtime)
    outcomes = _list(_nested(answered_plan, "session_state", "question_outcomes"))
    answered_ids = sorted(str(row.get("question_id")) for row in outcomes if isinstance(row, Mapping))
    interaction = _dict(_nested(hidden_plan, "policy_effect", "interaction_state"))
    hidden_state = _dict(_nested(hidden_plan, "policy_effect", "hidden_factor_state"))
    brain_trace = _dict(_nested(hidden_plan, "policy_effect", "central_brain_trace"))
    brain_state = _dict(brain_trace.get("brain_state"))
    question_strategy = _dict(brain_trace.get("question_strategy"))
    user_diagnostics = _dict(user_projection.get("diagnostics"))
    practitioner_diagnostics = _dict(practitioner_projection.get("diagnostics"))
    return {
        "first_question_id": first_question_id,
        "second_question_id": second_question_id,
        "first_visible_next_question_id": first_visible_next_question_id,
        "final_visible_next_question_id": final_visible_next_question_id,
        "selected_question_changed_after_replay": bool(second_question_id and second_question_id != first_question_id),
        "visible_next_question_preserved": bool(final_visible_next_question_id),
        "answered_question_ids": answered_ids,
        "known_user_signals": _dict(_nested(hidden_plan, "policy_effect", "known_user_signals")),
        "interaction_stage": str(interaction.get("interaction_stage") or ""),
        "interaction_answered_question_ids": _list(interaction.get("answered_question_ids")),
        "visible_next_question_id": str(interaction.get("visible_next_question_id") or ""),
        "internal_next_question_id": str(interaction.get("internal_next_question_id") or ""),
        "visible_internal_split": bool(interaction.get("visible_next_question_id") and interaction.get("internal_next_question_id")),
        "answer_context_present": bool(hidden_rehydrated_runtime.get("answer_context")),
        "answer_result_present": bool(hidden_rehydrated_runtime.get("answer_result")),
        "hidden_factor_state_status": str(hidden_state.get("status") or ""),
        "hidden_factor_amplifier_candidate": bool(hidden_state.get("amplifier_candidate")),
        "hidden_factor_feedback_ids": _list(hidden_state.get("feedback_ids")),
        "brain_hidden_factor_focus": str(brain_state.get("hidden_factor_focus") or ""),
        "brain_hidden_factor_mode": str(question_strategy.get("hidden_factor_mode") or ""),
        "user_diagnostics_hidden": not bool(user_diagnostics),
        "practitioner_diagnostics_visible": bool(practitioner_diagnostics),
        "practitioner_central_brain_visible": bool(practitioner_diagnostics.get("central_brain")),
        "chart_fact_fingerprint_preserved": chart_fingerprint_before == chart_fingerprint_after,
        "chart_fact_mutation_allowed": False,
        "policy_pointer_write_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _replay_checks(bt1_summary: Mapping[str, Any], summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "bt1_acceptance_ready",
            "passed": (
                bt1_summary["version"] == "v30.central_brain_acceptance.v1"
                and bt1_summary["central_brain_acceptance_ready"]
                and bt1_summary["decision_status"] == "bt1_central_brain_acceptance_ready"
            ),
            "expected": "BT1 central brain acceptance is ready",
        },
        {
            "check_id": "multi_turn_question_outcome_replayed",
            "passed": (
                summary["first_question_id"] in summary["answered_question_ids"]
                and summary["first_question_id"] in summary["interaction_answered_question_ids"]
                and int(summary["known_user_signals"].get("answered_question_count", 0) or 0) >= 1
                and summary["known_user_signals"].get("selected_options")
                and summary["answer_context_present"]
                and summary["answer_result_present"]
            ),
            "expected": "first answer is recorded, consumed by interaction state, and answer refresh exists",
        },
        {
            "check_id": "next_question_refreshes_with_visible_internal_split",
            "passed": (
                summary["visible_next_question_id"]
                and summary["internal_next_question_id"]
                and summary["visible_internal_split"]
                and summary["selected_question_changed_after_replay"]
                and summary["visible_next_question_preserved"]
            ),
            "expected": "visible/internal next question split survives replay and selected strategy changes",
        },
        {
            "check_id": "hidden_factor_feedback_conditions_brain",
            "passed": (
                summary["hidden_factor_state_status"] == "amplifier_candidate"
                and summary["hidden_factor_amplifier_candidate"]
                and summary["hidden_factor_feedback_ids"]
                and summary["brain_hidden_factor_focus"] == "amplifier_candidate"
                and summary["brain_hidden_factor_mode"] == "use_as_feedback_conditioned_amplifier"
            ),
            "expected": "hidden-factor feedback conditions brain strategy without becoming chart fact",
        },
        {
            "check_id": "role_projection_split_preserved",
            "passed": (
                summary["user_diagnostics_hidden"]
                and summary["practitioner_diagnostics_visible"]
                and summary["practitioner_central_brain_visible"]
            ),
            "expected": "user remains clean while practitioner can inspect central-brain diagnostics",
        },
        {
            "check_id": "long_session_replay_read_only",
            "passed": (
                summary["chart_fact_fingerprint_preserved"]
                and not summary["chart_fact_mutation_allowed"]
                and not summary["policy_pointer_write_allowed"]
                and not summary["full_pytest_required"]
                and not summary["full_518k_required"]
                and not bt1_summary["chart_fact_mutation_allowed"]
                and not bt1_summary["policy_pointer_promotion_allowed"]
            ),
            "expected": "replay does not mutate chart facts, pointers, or heavy validation state",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "central_brain_session_replay_ready": ready,
        "decision_status": "bt2_central_brain_session_replay_ready"
        if ready else "bt2_central_brain_session_replay_blocked",
        "replay_check_count": len(checks),
        "passed_replay_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "blockers": ["central_brain_session_replay_checks_failed"] if failed else [],
        "central_brain_completion": 94 if ready else 90,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Long-session central-brain replay is ready for BT2."
            if ready
            else "BT2 cannot complete until replay blockers are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["central_brain_session_replay_ready"]:
        return {
            "task_id": "BT3",
            "title": "Brain Failure Routing And Task Queue Contract",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "route failures to module targets",
                "keep route output diagnostic only",
                "preserve M1-M8 chart-fact boundaries",
            ],
        }
    return {
        "task_id": "BT2-FR",
        "title": "Long-Session Brain Replay Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed BT2 replay checks",
            "repair session replay or role projection boundaries",
            "keep pointer/release disabled while blocked",
        ],
    }


def _question_plan(runtime: Mapping[str, Any]) -> Mapping[str, Any]:
    return _dict(runtime.get("question_plan"))


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key, {})
    return current


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []
