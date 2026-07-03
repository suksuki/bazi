from __future__ import annotations


FEEDBACK_WEIGHT_UPDATER_VERSION = "v30.feedback_weight_updater.v1"
FEEDBACK_WEIGHT_UPDATE_VERSION = "v30.feedback_weight_update.v1"


def build_feedback_weight_update(
    *,
    claims: list[dict[str, object]],
    question_outcomes: list[dict[str, object]],
) -> dict[str, object]:
    signals = [
        _claim_feedback_signal(claim, question_outcomes)
        for claim in claims
        if isinstance(claim, dict)
    ]
    active = [row for row in signals if float(row.get("net_alignment") or 0.0) != 0.0]
    return {
        "version": FEEDBACK_WEIGHT_UPDATE_VERSION,
        "updater_version": FEEDBACK_WEIGHT_UPDATER_VERSION,
        "signal_count": len(signals),
        "active_signal_count": len(active),
        "claim_alignment_signals": signals,
        "summary": {
            "positive_claim_ids": [
                str(row.get("claim_id") or "")
                for row in active
                if float(row.get("net_alignment") or 0.0) > 0
            ][:8],
            "negative_claim_ids": [
                str(row.get("claim_id") or "")
                for row in active
                if float(row.get("net_alignment") or 0.0) < 0
            ][:8],
            "outcome_count": len(question_outcomes),
            "boundary": "feedback_summary_describes_weight_signals_not_chart_fact_changes",
        },
        "training_signal": {
            "version": "v30.training_signal.feedback_weight_update.v1",
            "trainable": True,
            "targets": [
                "feedback_alignment_weight",
                "feedback_contradiction_weight",
                "domain_answer_mapping",
                "selected_option_mapping",
                "confidence_weight",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "base_diagnosis_claim_text",
            ],
        },
        "boundary": "feedback_weight_update_adjusts_claim_ranking_signals_without_mutating_chart_facts",
    }


def _claim_feedback_signal(
    claim: dict[str, object],
    outcomes: list[dict[str, object]],
) -> dict[str, object]:
    claim_id = str(claim.get("claim_id") or "")
    domain = str(claim.get("domain") or "overview")
    claim_level = str(claim.get("claim_level") or "")
    support = 0.0
    contradiction = 0.0
    source_outcome_ids: list[str] = []
    matched_topics: list[str] = []
    selected_options: list[str] = []
    for outcome in outcomes:
        if not isinstance(outcome, dict):
            continue
        outcome_status = str(outcome.get("outcome_status") or "answered")
        topic = str(outcome.get("topic") or "")
        selected = str(outcome.get("selected_option") or "")
        confidence = _float(outcome.get("confidence"), 0.6)
        multiplier = 0.35 + confidence * 0.65
        topic_match = topic == domain or (domain == "timing" and topic in {"timing", "time_context"})
        option_match = bool(domain and domain in selected)
        if topic_match or option_match:
            source_outcome_ids.append(str(outcome.get("event_id") or outcome.get("question_id") or ""))
            if topic:
                matched_topics.append(topic)
            if selected:
                selected_options.append(selected)
        if outcome_status in {"skipped", "unclear"} and (topic_match or option_match):
            contradiction += 0.08 * multiplier
            continue
        if outcome_status == "denied" and (topic_match or option_match):
            contradiction += 0.24 * multiplier
            continue
        if topic_match:
            support += 0.24 * multiplier
        if option_match:
            support += 0.12 * multiplier
        if _structured_payload_matches_domain(outcome.get("structured_payload"), domain):
            support += 0.16 * multiplier
        if domain in {"health", "timing"} and outcome_status == "answered" and topic_match:
            support += 0.05 * multiplier
    net = max(-1.0, min(1.0, support - contradiction))
    return {
        "version": "v30.claim_feedback_alignment_signal.v1",
        "claim_id": claim_id,
        "domain": domain,
        "claim_level": claim_level,
        "support": round(min(1.0, support), 3),
        "contradiction": round(min(1.0, contradiction), 3),
        "net_alignment": round(net, 3),
        "source_outcome_ids": [row for row in source_outcome_ids if row][:6],
        "matched_topics": sorted(set(matched_topics)),
        "selected_options": sorted(set(selected_options))[:6],
        "chart_fact_mutation_allowed": False,
        "boundary": "claim_feedback_signal_updates_ranking_weight_not_chart_fact",
    }


def _structured_payload_matches_domain(payload: object, domain: str) -> bool:
    if not isinstance(payload, dict) or not domain:
        return False
    state_tags = payload.get("state_tags", [])
    if isinstance(state_tags, list) and any(domain in str(tag) for tag in state_tags):
        return True
    domain_value = str(payload.get("domain") or payload.get("topic") or "")
    return domain_value == domain


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
