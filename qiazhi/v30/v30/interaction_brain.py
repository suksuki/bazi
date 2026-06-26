from __future__ import annotations

from typing import Any, Mapping

from v30.interaction_constraints import hidden_factor_feedback_payload_from_turn_signal


UNIFIED_INTERACTION_BRAIN_RESULT_VERSION = "v30.unified_interaction_brain_result.v1"


def process_interaction_turn(
    *,
    reading_id: str,
    question_id: str,
    turn_signal: Mapping[str, Any],
) -> dict[str, Any]:
    feedback_payload = hidden_factor_feedback_payload_from_turn_signal(
        turn_signal,
        feedback_id=f"{reading_id}:uib:{question_id}",
    )
    return {
        "version": UNIFIED_INTERACTION_BRAIN_RESULT_VERSION,
        "valid": bool(turn_signal.get("valid")),
        "question_id": str(turn_signal.get("question_id") or question_id),
        "question_type": str(turn_signal.get("question_type") or ""),
        "absorbed_signals": _str_list(turn_signal.get("absorbed_signals")),
        "rejected_signals": _str_list(turn_signal.get("rejected_signals")),
        "validation_errors": turn_signal.get("validation_errors", []) if isinstance(turn_signal.get("validation_errors"), list) else [],
        "allowed_to_update_hidden_factor": bool(turn_signal.get("allowed_to_update_hidden_factor")),
        "hidden_factor_feedback_payload": feedback_payload,
        "hidden_factor_feedback_saved": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "unified_interaction_brain_routes_structured_feedback_without_chart_fact_mutation",
    }


def mark_hidden_factor_feedback_saved(
    result: Mapping[str, Any],
    *,
    hidden_factor_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not hidden_factor_state:
        return dict(result)
    return {
        **dict(result),
        "hidden_factor_feedback_saved": True,
        "hidden_factor_state_status": str(hidden_factor_state.get("status") or ""),
    }


def public_interaction_brain_result(result: Mapping[str, Any]) -> dict[str, Any]:
    blocked = {"hidden_factor_feedback_payload"}
    return {key: value for key, value in dict(result).items() if key not in blocked}


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]
