from __future__ import annotations


CENTRAL_FEEDBACK_OVERLAY_VERSION = "v30.central_feedback_overlay.v1"


def build_central_feedback_overlay(
    *,
    question_outcomes: list[dict[str, object]] | None = None,
    practitioner_selections: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    outcome_rows = [row for row in (question_outcomes or []) if isinstance(row, dict)]
    selection_rows = [row for row in (practitioner_selections or []) if isinstance(row, dict)]
    outcome_effects = [_effect_from_question_outcome(row) for row in outcome_rows]
    practitioner_effects = [_effect_from_practitioner_selection(row) for row in selection_rows]
    effects = [row for row in [*outcome_effects, *practitioner_effects] if row.get("delta")]
    return {
        "version": CENTRAL_FEEDBACK_OVERLAY_VERSION,
        "effect_count": len(effects),
        "question_outcome_count": len(outcome_rows),
        "practitioner_selection_count": len(selection_rows),
        "effects": effects[-80:],
        "domain_deltas": _aggregate(effects, "domain"),
        "topic_deltas": _aggregate(effects, "topic"),
        "claim_deltas": _aggregate(effects, "claim_id"),
        "requires_question_topics": _requires_question_topics(effects),
        "summary": _summary(effects),
        "training_signal": {
            "version": "v30.training_signal.central_feedback_overlay.v1",
            "trainable": True,
            "targets": [
                "feedback_to_claim_weight",
                "practitioner_selection_to_domain_weight",
                "question_answer_to_next_question_policy",
                "needs_question_priority_weight",
                "final_synthesis_feedback_priority",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "raw_rule_truth",
                "unconfirmed_hidden_factor_facts",
            ],
        },
        "chart_fact_mutation_allowed": False,
        "boundary": "central_feedback_overlay_changes_interpretation_weight_not_chart_facts",
    }


def overlay_adjustment_for_claim(claim: dict[str, object], overlay: dict[str, object]) -> dict[str, object]:
    claim_id = str(claim.get("claim_id") or "")
    domain = str(claim.get("domain") or "overview")
    claim_delta = _float(_dict(overlay.get("claim_deltas")).get(claim_id), 0.0)
    domain_delta = _float(_dict(overlay.get("domain_deltas")).get(domain), 0.0)
    topic_delta = _float(_dict(overlay.get("topic_deltas")).get(domain), 0.0)
    total = max(-0.18, min(0.18, claim_delta + domain_delta * 0.72 + topic_delta * 0.42))
    return {
        "version": "v30.central_feedback_claim_adjustment.v1",
        "claim_id": claim_id,
        "domain": domain,
        "claim_delta": round(claim_delta, 3),
        "domain_delta": round(domain_delta, 3),
        "topic_delta": round(topic_delta, 3),
        "score_delta": round(total, 3),
        "boundary": "feedback_claim_adjustment_updates_score_not_claim_fact",
    }


def _effect_from_question_outcome(outcome: dict[str, object]) -> dict[str, object]:
    topic = str(outcome.get("topic") or "")
    selected = str(outcome.get("selected_option") or "")
    domain = _domain_from_topic_or_option(topic, selected)
    status = str(outcome.get("outcome_status") or "answered")
    confidence = _float(outcome.get("confidence"), 0.6)
    base = -0.06 if status in {"skipped", "unclear"} else -0.16 if status == "denied" else 0.12
    delta = round(base * (0.70 + confidence * 0.30), 3)
    return {
        "version": "v30.central_feedback_effect.v1",
        "source": "question_outcome",
        "source_id": str(outcome.get("event_id") or outcome.get("question_id") or ""),
        "domain": domain,
        "topic": topic or domain,
        "claim_id": "",
        "action": status,
        "delta": delta,
        "confidence": confidence,
        "selected_option": selected,
        "requires_question": False,
        "boundary": "question_outcome_effect_updates_interpretation_weight_not_facts",
    }


def _effect_from_practitioner_selection(selection: dict[str, object]) -> dict[str, object]:
    effect = _dict(selection.get("effect"))
    option_set = _dict(selection.get("option_set"))
    belief_delta = _dict(effect.get("belief_delta"))
    delta = _float(belief_delta.get("delta"), 0.0)
    topic = str(effect.get("topic") or option_set.get("topic") or "")
    source_id = str(effect.get("source_id") or option_set.get("source_id") or "")
    return {
        "version": "v30.central_feedback_effect.v1",
        "source": "practitioner_selection",
        "source_id": str(selection.get("selection_id") or ""),
        "domain": _domain_from_topic_or_option(topic, " ".join(_list(selection.get("selected_option_ids")))),
        "topic": topic,
        "claim_id": source_id if source_id.startswith("claim.") else "",
        "stage_id": str(effect.get("stage_id") or option_set.get("stage_id") or ""),
        "action": str(selection.get("action") or ""),
        "delta": delta,
        "confidence": _float(selection.get("confidence"), 0.0),
        "selected_option_ids": [str(row) for row in _list(selection.get("selected_option_ids")) if row],
        "rejected_option_ids": [str(row) for row in _list(selection.get("rejected_option_ids")) if row],
        "requires_question": str(selection.get("action") or "") == "needs_question",
        "boundary": "practitioner_selection_effect_updates_interpretation_weight_not_facts",
    }


def _aggregate(effects: list[dict[str, object]], key: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in effects:
        name = str(row.get(key) or "")
        if not name:
            continue
        result[name] = round(max(-1.0, min(1.0, result.get(name, 0.0) + _float(row.get("delta"), 0.0))), 3)
    return result


def _requires_question_topics(effects: list[dict[str, object]]) -> list[str]:
    topics = []
    for row in effects:
        if row.get("requires_question") is True:
            topic = str(row.get("topic") or row.get("domain") or "")
            if topic and topic not in topics:
                topics.append(topic)
    return topics[:8]


def _summary(effects: list[dict[str, object]]) -> dict[str, object]:
    positive = [row for row in effects if _float(row.get("delta"), 0.0) > 0]
    negative = [row for row in effects if _float(row.get("delta"), 0.0) < 0]
    return {
        "positive_count": len(positive),
        "negative_count": len(negative),
        "net_delta": round(sum(_float(row.get("delta"), 0.0) for row in effects), 3),
        "source_types": sorted({str(row.get("source") or "") for row in effects if row.get("source")}),
        "boundary": "feedback_overlay_summary_is_weight_trace_not_fact",
    }


def _domain_from_topic_or_option(topic: str, value: str) -> str:
    text = f"{topic} {value}".lower()
    for domain in ("career", "wealth", "relationship", "health", "family", "timing"):
        if domain in text:
            return domain
    if topic in {"事业", "工作"}:
        return "career"
    if topic in {"财务", "财运"}:
        return "wealth"
    if topic in {"关系", "感情"}:
        return "relationship"
    if topic in {"健康", "身体"}:
        return "health"
    if topic in {"大运", "流年", "time_context"}:
        return "timing"
    return topic or "overview"


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
