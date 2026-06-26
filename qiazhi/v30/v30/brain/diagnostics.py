from __future__ import annotations

from pydantic import Field

from v30.contracts import CoreRuntimeResult, V30Model


ADAPTIVE_QUESTION_DIAGNOSTICS_VERSION = "v30.adaptive_question_diagnostics.v1"


class AdaptiveQuestionDecisionRow(V30Model):
    rank: int
    question_id: str
    intent_id: str
    stage: str
    topic: str
    score: float
    policy_weight: float
    policy_version: str
    reason_count: int
    central_brain_reason_count: int
    policy_reason_count: int
    feedback_reason_count: int
    boundary_reason_count: int
    reasons: list[str] = Field(default_factory=list)


class AdaptiveQuestionDiagnostics(V30Model):
    replay_id: str
    version: str
    reading_id: str
    trace_id: str
    selected_question_id: str | None = None
    next_question_id: str | None = None
    question_strategy: str
    runtime_focus: str
    alignment_status: str
    decision_count: int
    decision_rows: list[AdaptiveQuestionDecisionRow] = Field(default_factory=list)
    policy_weight_summary: dict[str, object] = Field(default_factory=dict)
    replay_inputs: dict[str, object] = Field(default_factory=dict)
    replay_controls: dict[str, object] = Field(default_factory=dict)
    boundaries: list[str] = Field(default_factory=list)


def build_adaptive_question_diagnostics(
    runtime: CoreRuntimeResult,
    *,
    central_brain_trace: dict[str, object] | None = None,
) -> AdaptiveQuestionDiagnostics:
    effect = runtime.question_plan.policy_effect
    trace = central_brain_trace if isinstance(central_brain_trace, dict) else _dict(effect.get("central_brain_trace"))
    graph = _dict(effect.get("question_dialogue_graph"))
    rows = [
        _decision_row(index, row)
        for index, row in enumerate(runtime.question_plan.recommended_questions, start=1)
    ]
    selected_question_id = _nested(trace, "question_strategy", "selected_question_id") or _selected_question_id(runtime)
    next_question_id = str(graph.get("next_question_id") or "") or None
    question_strategy = str(_nested(trace, "question_strategy", "strategy") or "")
    runtime_focus = str(_nested(trace, "runtime_plan", "focus") or "")
    return AdaptiveQuestionDiagnostics(
        replay_id=f"{runtime.reading_id}:adaptive-question-replay",
        version=ADAPTIVE_QUESTION_DIAGNOSTICS_VERSION,
        reading_id=runtime.reading_id,
        trace_id=runtime.trace_id,
        selected_question_id=str(selected_question_id) if selected_question_id else None,
        next_question_id=next_question_id,
        question_strategy=question_strategy,
        runtime_focus=runtime_focus,
        alignment_status=_alignment_status(rows, selected_question_id, next_question_id, question_strategy),
        decision_count=len(rows),
        decision_rows=rows,
        policy_weight_summary=_policy_weight_summary(rows, effect),
        replay_inputs=_replay_inputs(runtime, effect, trace),
        replay_controls={
            "can_replay_from_runtime_trace": True,
            "source": "runtime_trace_policy_effect",
            "compare_keys": ["rank", "score", "policy_weight", "reasons", "question_strategy"],
            "boundary": "diagnostic_replay_does_not_mutate_runtime_or_chart_facts",
        },
        boundaries=[
            "adaptive_question_diagnostics_are_trace_replay_not_chart_fact",
            "central_brain_coordinates_question_policy_without_mutating_policy_pointer",
            "feedback_conditioned_state_can_change_ordering_only_after_runtime_rehydration",
        ],
    )


def _decision_row(rank: int, row: dict[str, object]) -> AdaptiveQuestionDecisionRow:
    reasons = [str(reason) for reason in row.get("reasons", [])] if isinstance(row.get("reasons", []), list) else []
    return AdaptiveQuestionDecisionRow(
        rank=rank,
        question_id=str(row.get("question_id") or ""),
        intent_id=str(row.get("intent_id") or ""),
        stage=str(row.get("stage") or ""),
        topic=str(row.get("topic") or ""),
        score=_float(row.get("score")),
        policy_weight=_float(row.get("policy_weight"), default=1.0),
        policy_version=str(row.get("policy_version") or ""),
        reason_count=len(reasons),
        central_brain_reason_count=sum(1 for reason in reasons if reason.startswith("central_brain_")),
        policy_reason_count=sum(1 for reason in reasons if reason.startswith("question_policy") or reason.startswith("hidden_factor_event_policy")),
        feedback_reason_count=sum(1 for reason in reasons if reason.startswith("question_outcome") or reason.startswith("persisted_hidden_factor_state")),
        boundary_reason_count=sum(1 for reason in reasons if "boundary" in reason or "missing_requirement" in reason),
        reasons=reasons,
    )


def _policy_weight_summary(rows: list[AdaptiveQuestionDecisionRow], effect: dict[str, object]) -> dict[str, object]:
    weights = [row.policy_weight for row in rows]
    question_policy = _dict(effect.get("question_policy_payload"))
    policy_weights = _dict(question_policy.get("weights"))
    return {
        "active_question_policy": _dict(effect.get("active_policy_versions")).get("question_policy", ""),
        "weighted_decision_count": sum(1 for weight in weights if weight != 1.0),
        "min_policy_weight": min(weights) if weights else 1.0,
        "max_policy_weight": max(weights) if weights else 1.0,
        "average_policy_weight": round(sum(weights) / len(weights), 3) if weights else 1.0,
        "weight_buckets": sorted(str(key) for key in policy_weights.keys()),
        "hidden_factor_event_policy_present": isinstance(policy_weights.get("hidden_factor_event_policy"), dict),
    }


def _replay_inputs(
    runtime: CoreRuntimeResult,
    effect: dict[str, object],
    central_brain_trace: dict[str, object],
) -> dict[str, object]:
    return {
        "active_policy_versions": _dict(effect.get("active_policy_versions")),
        "mainline_id": runtime.mainline_state.mainline_id,
        "structure_id": runtime.structure_state.structure_id,
        "quality_gate": runtime.mainline_state.quality_gate,
        "time_status": str(runtime.chart_context.time_layers.get("status") or ""),
        "hidden_factor_status": str(_dict(effect.get("hidden_factor_state")).get("status") or _dict(effect.get("hidden_factor_calibration")).get("status") or ""),
        "question_outcome_count": len(_list(effect.get("question_outcomes"))),
        "central_brain_unknown_context": _nested(central_brain_trace, "brain_state", "unknown_context", default=[]),
        "feedback_slots": _nested(central_brain_trace, "session_memory", "feedback_slots", default=[]),
    }


def _alignment_status(
    rows: list[AdaptiveQuestionDecisionRow],
    selected_question_id: object,
    next_question_id: str | None,
    question_strategy: str,
) -> str:
    top_question_id = rows[0].question_id if rows else ""
    selected = str(selected_question_id or "")
    if top_question_id and selected == top_question_id and (not next_question_id or next_question_id == top_question_id):
        return "brain_graph_and_rank_aligned"
    if next_question_id and top_question_id == next_question_id:
        return "graph_and_rank_aligned"
    if selected and selected != top_question_id:
        return "selected_question_differs_from_current_rank"
    if question_strategy:
        return "brain_strategy_recorded"
    return "diagnostic_only"


def _selected_question_id(runtime: CoreRuntimeResult) -> str | None:
    if runtime.answer_context is not None:
        return runtime.answer_context.selected_question_anchor.question_id
    if runtime.question_plan.recommended_questions:
        return str(runtime.question_plan.recommended_questions[0].get("question_id") or "")
    return None


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _nested(payload: dict[str, object], section: str, key: str, *, default: object = None) -> object:
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return default
    return section_payload.get(key, default)


def _float(value: object, *, default: float = 0.0) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default
