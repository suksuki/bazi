from __future__ import annotations

from collections import Counter
from typing import Any


INTERACTION_SESSION_MODEL_VERSION = "v20.interaction_session_model.v1"


def build_interaction_session_model(
    *,
    selected_question: object,
    questions: tuple[object, ...],
    question_intent_model: dict[str, Any],
    practitioner_session: dict[str, Any],
    latent_event_session: dict[str, Any],
    decision_report: dict[str, Any],
) -> dict[str, Any]:
    signals = [
        *_signals_from_practitioner(practitioner_session),
        *_signals_from_latent(latent_event_session),
        *_signals_from_selected_question(selected_question, question_intent_model),
    ]
    signal_counts = Counter(str(row["signal_type"]) for row in signals)
    selected_domain = str(getattr(selected_question, "domain", ""))
    return {
        "version": INTERACTION_SESSION_MODEL_VERSION,
        "status": "ready",
        "algorithm": "session_signal_fusion_phase1",
        "source": "QuestionIntent+PractitionerSelection+LatentEvent+DecisionReport",
        "selected_question_key": str(getattr(selected_question, "question_key", "")),
        "selected_question_title": str(getattr(selected_question, "title", "")),
        "selected_domain": selected_domain,
        "question_count": len(questions),
        "signal_count": len(signals),
        "signal_type_counts": dict(sorted(signal_counts.items())),
        "signals": tuple(signals),
        "next_actions": _next_actions(selected_domain, signals, decision_report),
        "runtime_mutation": False,
        "guardrails": (
            "INTERACTION_SIGNALS_RERANK_AND_CALIBRATE_ONLY",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_CORE_FACT_MUTATION",
            "PRACTITIONER_AND_USER_INPUTS_REQUIRE_VALIDATION_BEFORE_POLICY_USE",
        ),
    }


def _signals_from_practitioner(session: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for effect in session.get("selection_effects", ()):
        if not isinstance(effect, dict):
            continue
        rows.append(
            {
                "signal_id": f"signal.practitioner.{effect.get('control_key', '')}",
                "signal_type": "practitioner_control",
                "domain": _control_domain(str(effect.get("control_key", ""))),
                "strength": 0.84,
                "effect": effect.get("effect", ""),
                "matched_question_keys": tuple(effect.get("matched_question_keys", ())),
                "runtime_rule_mutation": False,
            }
        )
    return tuple(rows)


def _signals_from_latent(session: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = []
    for effect in session.get("selection_effects", ()):
        if not isinstance(effect, dict):
            continue
        rows.append(
            {
                "signal_id": f"signal.latent.{effect.get('scenario_id', '')}",
                "signal_type": "latent_event_answer",
                "domain": _latent_domain(str(effect.get("scenario_id", ""))),
                "strength": 0.68,
                "effect": effect.get("effect", ""),
                "matched_question_keys": tuple(effect.get("matched_question_keys", ())),
                "runtime_rule_mutation": False,
            }
        )
    return tuple(rows)


def _signals_from_selected_question(selected_question: object, question_intent_model: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    binding = question_intent_model.get("selected_question_intent", {})
    if not isinstance(binding, dict):
        binding = {}
    return (
        {
            "signal_id": f"signal.question.selected.{getattr(selected_question, 'question_key', '')}",
            "signal_type": "selected_question",
            "domain": str(getattr(selected_question, "domain", "")),
            "strength": 0.72,
            "effect": "answer_plan_focus",
            "matched_intent_ids": tuple(binding.get("matched_intent_ids", ())),
            "primary_intent_type": str(binding.get("primary_intent_type", "")),
            "runtime_rule_mutation": False,
        },
    )


def _next_actions(domain: str, signals: list[dict[str, Any]], decision_report: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    decision_domains = {
        str(row.get("domain", ""))
        for row in decision_report.get("decisions", ())
        if isinstance(row, dict) and row.get("domain")
    }
    rows = [
        {
            "action_key": f"next.answer.{domain or 'overview'}",
            "action_type": "answer_selected_question",
            "domain": domain,
            "reason": "selected_question_is_current_session_focus",
        }
    ]
    if signals:
        rows.append(
            {
                "action_key": f"next.rerank.{domain or 'overview'}",
                "action_type": "rerank_followup_questions",
                "domain": domain,
                "reason": "session_signals_available",
            }
        )
    if domain and domain in decision_domains:
        rows.append(
            {
                "action_key": f"next.evidence_pack.{domain}",
                "action_type": "refresh_evidence_pack",
                "domain": domain,
                "reason": "domain_has_runtime_decisions",
            }
        )
    return tuple(rows)


def _control_domain(control_key: str) -> str:
    return {
        "control.day_master_strength": "strength",
        "control.shang_guan_jian_guan": "career",
        "control.wealth_capacity": "wealth",
        "control.pattern_status": "pattern",
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
