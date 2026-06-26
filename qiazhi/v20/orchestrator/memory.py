from __future__ import annotations

import hashlib
from typing import Any


BRAIN_MEMORY_SIGNAL_VERSION = "v20.orchestrator_brain_memory_signal.v1"


def build_brain_memory_signal(
    *,
    input_id: str,
    brain_state: dict[str, Any],
    mainline_arbitration: dict[str, Any],
    question_mainline_focus: dict[str, Any],
    selected_question: object,
    practitioner_session: dict[str, Any],
    latent_event_session: dict[str, Any],
) -> dict[str, object]:
    public = _dict(brain_state.get("public_summary", {}))
    review = _dict(brain_state.get("review_summary", {}))
    primary = _dict(mainline_arbitration.get("primary_mainline", {}))
    question = _question_dict(selected_question)
    signals = [
        *_coordination_signals(public, review, primary),
        *_practitioner_signals(practitioner_session, primary, question),
        *_latent_event_signals(latent_event_session, question),
    ]
    key = _memory_key(
        input_id,
        str(primary.get("candidate_key", "")),
        str(question.get("question_key", "")),
        str(public.get("coordination_status", "")),
        *(str(row.get("signal_key", "")) for row in signals if isinstance(row, dict)),
    )
    return {
        "version": BRAIN_MEMORY_SIGNAL_VERSION,
        "status": "active" if signals else "no_feedback_signal",
        "memory_key": key,
        "source": "BrainState+MainlineArbitration+QuestionFocus+PractitionerSession+LatentEventSession",
        "primary_mainline_key": primary.get("candidate_key", ""),
        "primary_title": public.get("primary_title", ""),
        "primary_domain": primary.get("domain", ""),
        "selected_question_key": question.get("question_key", ""),
        "selected_question_domain": question.get("domain", ""),
        "question_focus_status": question_mainline_focus.get("status", ""),
        "coordination_status": public.get("coordination_status", ""),
        "coordination_flags": list(review.get("coordination_flags", ())) if isinstance(review.get("coordination_flags", ()), list) else [],
        "signal_count": len(signals),
        "signals": signals,
        "runtime_mutation": False,
        "guardrails": [
            "BRAIN_MEMORY_SIGNAL_IS_APPENDABLE_TRAINING_MATERIAL_ONLY",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
            "NO_USER_VISIBLE_VERDICT_FROM_MEMORY_SIGNAL",
            "PROMOTION_REQUIRES_OFFLINE_VALIDATION",
        ],
    }


def _coordination_signals(
    public: dict[str, Any],
    review: dict[str, Any],
    primary: dict[str, Any],
) -> list[dict[str, object]]:
    flags = [str(row) for row in _list(review.get("coordination_flags")) if str(row)]
    if not flags:
        return []
    return [
        {
            "signal_key": "brain.coordination.review",
            "signal_type": "coordination_review",
            "domain": primary.get("domain", ""),
            "target": "orchestrator.mainline_coordination",
            "direction": "review_required",
            "strength": _review_strength(flags),
            "summary": str(public.get("coordination_note", "")),
            "allowed_use": "offline_orchestrator_memory_training",
            "runtime_rule_mutation": False,
        }
    ]


def _practitioner_signals(
    practitioner_session: dict[str, Any],
    primary: dict[str, Any],
    question: dict[str, Any],
) -> list[dict[str, object]]:
    rows = []
    for selection in _list(practitioner_session.get("selections")):
        item = _dict(selection)
        control_key = str(item.get("control_key", ""))
        option = str(item.get("option", ""))
        if not control_key:
            continue
        rows.append(
            {
                "signal_key": f"brain.practitioner.{_safe(control_key)}",
                "signal_type": "practitioner_structured_choice",
                "domain": _control_domain(control_key) or primary.get("domain", "") or question.get("domain", ""),
                "target": _target_for_control(control_key),
                "direction": _option_direction(option),
                "strength": 0.9 if control_key == "control.mainline_arbitration" else 0.74,
                "option": option,
                "primary_mainline_key": primary.get("candidate_key", ""),
                "selected_question_key": question.get("question_key", ""),
                "allowed_use": "offline_orchestrator_memory_training",
                "runtime_rule_mutation": False,
            }
        )
    return rows


def _latent_event_signals(
    latent_event_session: dict[str, Any],
    question: dict[str, Any],
) -> list[dict[str, object]]:
    rows = []
    for answer in _list(latent_event_session.get("answers")):
        item = _dict(answer)
        scenario_id = str(item.get("scenario_id", ""))
        if not scenario_id:
            continue
        rows.append(
            {
                "signal_key": f"brain.latent.{_safe(scenario_id)}",
                "signal_type": "latent_event_preference",
                "domain": _latent_domain(scenario_id) or question.get("domain", ""),
                "target": "orchestrator.question_and_timing_memory",
                "direction": str(item.get("result_option", "")) or "observed",
                "strength": _latent_strength(str(item.get("intensity", "")), str(item.get("confidence", ""))),
                "scenario_id": scenario_id,
                "year_option": str(item.get("year_option", "")),
                "selected_question_key": question.get("question_key", ""),
                "allowed_use": "personal_memory_signal_only",
                "runtime_rule_mutation": False,
            }
        )
    return rows


def _review_strength(flags: list[str]) -> float:
    if "primary_mainline_missing" in flags:
        return 1.0
    if "mainline_quality_review" in flags:
        return 0.82
    return 0.66


def _option_direction(option: str) -> str:
    return {
        "采用第一主线": "accept_primary",
        "切换到次级主线": "switch_to_supporting",
        "暂缓主线": "defer_mainline",
        "证据不足": "evidence_insufficient",
    }.get(option, option or "selected")


def _target_for_control(control_key: str) -> str:
    return {
        "control.day_master_strength": "orchestrator.strength_capacity_memory",
        "control.shang_guan_jian_guan": "orchestrator.ten_god_collision_memory",
        "control.wealth_capacity": "orchestrator.wealth_capacity_memory",
        "control.pattern_status": "orchestrator.pattern_memory",
        "control.mainline_arbitration": "orchestrator.mainline_arbitration_memory",
    }.get(control_key, "orchestrator.structured_choice_memory")


def _control_domain(control_key: str) -> str:
    return {
        "control.day_master_strength": "strength",
        "control.shang_guan_jian_guan": "career",
        "control.wealth_capacity": "wealth",
        "control.pattern_status": "pattern",
        "control.mainline_arbitration": "mainline",
    }.get(control_key, "")


def _latent_domain(scenario_id: str) -> str:
    return {
        "latent.wealth_change": "wealth",
        "latent.career_transition": "career",
        "latent.relationship_shift": "relationship",
        "latent.relocation_environment": "time",
        "latent.stress_recovery": "health",
        "latent.action_result": "strength",
    }.get(scenario_id, "")


def _latent_strength(intensity: str, confidence: str) -> float:
    intensity_score = {"none": 0.2, "mild": 0.42, "clear": 0.68, "strong": 0.86}.get(intensity, 0.4)
    confidence_score = {"low": 0.74, "medium": 0.88, "high": 1.0}.get(confidence, 0.82)
    return round(intensity_score * confidence_score, 3)


def _question_dict(selected_question: object) -> dict[str, Any]:
    if isinstance(selected_question, dict):
        return selected_question
    if hasattr(selected_question, "to_dict"):
        return selected_question.to_dict()
    return {
        "question_key": getattr(selected_question, "question_key", ""),
        "domain": getattr(selected_question, "domain", ""),
    }


def _memory_key(*values: str) -> str:
    raw = "|".join(values)
    return f"brain.memory.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() else "." for ch in value).strip(".")


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    return list(value) if isinstance(value, (list, tuple)) else []
