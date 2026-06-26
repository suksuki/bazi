from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


ANSWER_CONSTRAINTS_VERSION = "v30.answer_constraints.v1"
INTERACTION_TURN_SIGNAL_VERSION = "v30.interaction_turn_signal.v1"

MIN_YEAR = 1900
MAX_YEAR = 2100

ALLOWED_STATE_TAGS: dict[str, str] = {
    "career_pressure": "事业压力",
    "role_change": "岗位/职责变化",
    "wealth_fluctuation": "财务波动",
    "partnership_distribution": "合作/分配问题",
    "relationship_repetition": "关系反复",
    "family_pressure": "家庭压力",
    "health_rhythm": "作息/身心节律波动",
    "credential_pressure": "学习/证书/资质压力",
    "relocation_change": "迁移/环境变化",
}

ALLOWED_INTENSITY = {"light", "medium", "strong"}
ALLOWED_RECURRENCE = {"single", "repeated", "continuous"}
ALLOWED_CONFIDENCE = {"certain", "approximate", "uncertain"}
DOMAIN_OPTIONS = {"career", "wealth", "relationship", "health", "timing", "decision"}
HIDDEN_FACTOR_SKIP_OPTIONS = {"hidden_factor:not_sure", "hidden_factor:skip", "hidden_factor:default"}


def answer_constraints_for_question(*, stage: str, topic: str) -> dict[str, Any]:
    if topic == "hidden_factor":
        return {
            "version": ANSWER_CONSTRAINTS_VERSION,
            "constraint_type": "structured_hidden_factor",
            "required_fields": ["state_tags", "recurrence"],
            "optional_fields": ["years", "intensity", "confidence", "free_note", "selected_domain"],
            "year_range": [MIN_YEAR, MAX_YEAR],
            "allowed_state_tags": _option_rows(ALLOWED_STATE_TAGS),
            "allowed_intensity": _label_rows(
                {
                    "light": "轻微",
                    "medium": "明显",
                    "strong": "强烈",
                }
            ),
            "allowed_recurrence": _label_rows(
                {
                    "single": "单次",
                    "repeated": "反复",
                    "continuous": "持续",
                }
            ),
            "allowed_confidence": _label_rows(
                {
                    "certain": "确定",
                    "approximate": "大概",
                    "uncertain": "不确定",
                }
            ),
            "free_note_policy": "store_as_note_only",
            "invalid_input_action": "ask_user_to_reselect",
            "allowed_skip_options": _label_rows(
                {
                    "hidden_factor:not_sure": "不确定",
                    "hidden_factor:default": "先按中性看",
                    "hidden_factor:skip": "暂不回答",
                }
            ),
            "chart_fact_mutation_allowed": False,
            "boundary": "structured_hidden_factor_constraints_block_free_text_pollution",
        }
    if topic in DOMAIN_OPTIONS or topic == "practical_reading":
        return {
            "version": ANSWER_CONSTRAINTS_VERSION,
            "constraint_type": "domain_followup",
            "required_fields": [],
            "optional_fields": ["selected_domain", "free_note"],
            "allowed_domains": _label_rows(
                {
                    "career": "事业",
                    "wealth": "财务",
                    "relationship": "关系",
                    "health": "健康",
                    "timing": "时运",
                    "decision": "决策",
                }
            ),
            "free_note_policy": "store_as_note_only",
            "invalid_input_action": "accept_as_domain_note",
            "chart_fact_mutation_allowed": False,
            "boundary": "domain_followup_constraints_guide_question_strategy_not_chart_facts",
        }
    if topic == "useful_god":
        return {
            "version": ANSWER_CONSTRAINTS_VERSION,
            "constraint_type": "candidate_review",
            "required_fields": [],
            "optional_fields": ["selected_option", "free_note", "negative_evidence"],
            "free_note_policy": "store_as_note_only",
            "invalid_input_action": "ask_user_to_reselect",
            "chart_fact_mutation_allowed": False,
            "boundary": "candidate_review_constraints_block_fixed_useful_god_verdict",
        }
    if stage == "context_completion":
        return {
            "version": ANSWER_CONSTRAINTS_VERSION,
            "constraint_type": "timing_context_check",
            "required_fields": [],
            "optional_fields": ["years", "selected_option", "free_note"],
            "year_range": [MIN_YEAR, MAX_YEAR],
            "free_note_policy": "store_as_note_only",
            "invalid_input_action": "ask_user_to_reselect",
            "chart_fact_mutation_allowed": False,
            "boundary": "timing_context_constraints_do_not_create_event_facts",
        }
    return {
        "version": ANSWER_CONSTRAINTS_VERSION,
        "constraint_type": "free_note_only",
        "required_fields": [],
        "optional_fields": ["selected_option", "free_note"],
        "free_note_policy": "store_as_note_only",
        "invalid_input_action": "accept_as_note",
        "chart_fact_mutation_allowed": False,
        "boundary": "free_note_is_expression_context_not_calibration_weight",
    }


def validate_structured_interaction_payload(
    *,
    question_id: str,
    question_type: str,
    constraints: Mapping[str, Any] | None,
    structured_payload: Mapping[str, Any] | None,
    free_note: str = "",
    selected_option: str = "",
) -> dict[str, Any]:
    constraint_payload = dict(constraints or {})
    constraint_type = str(constraint_payload.get("constraint_type") or question_type or "free_note_only")
    payload = dict(structured_payload or {})
    errors: list[dict[str, str]] = []
    years = _valid_years(payload.get("years"), errors)
    state_tags = _valid_state_tags(payload.get("state_tags"), errors)
    intensity = _enum_value(payload.get("intensity"), ALLOWED_INTENSITY, "intensity", errors)
    recurrence = _enum_value(payload.get("recurrence"), ALLOWED_RECURRENCE, "recurrence", errors)
    confidence = _enum_value(payload.get("confidence"), ALLOWED_CONFIDENCE, "confidence", errors)
    selected_domain = _selected_domain(payload.get("selected_domain"), selected_option, errors)
    user_skipped_hidden = constraint_type == "structured_hidden_factor" and selected_option in HIDDEN_FACTOR_SKIP_OPTIONS
    required = {str(row) for row in _list(constraint_payload.get("required_fields"))}
    if "state_tags" in required and not state_tags and not user_skipped_hidden:
        errors.append({"field": "state_tags", "error": "required_selection_missing"})
    if "recurrence" in required and not recurrence and not user_skipped_hidden:
        errors.append({"field": "recurrence", "error": "required_selection_missing"})
    if "years" in required and not years and not user_skipped_hidden:
        errors.append({"field": "years", "error": "required_year_missing"})
    valid = not errors
    allowed_hidden = valid and not user_skipped_hidden and constraint_type == "structured_hidden_factor" and bool(state_tags)
    return {
        "version": INTERACTION_TURN_SIGNAL_VERSION,
        "question_id": question_id,
        "question_type": constraint_type,
        "structured_payload": {
            "years": years,
            "state_tags": state_tags,
            "intensity": intensity,
            "recurrence": recurrence,
            "confidence": confidence,
            "selected_domain": selected_domain,
        },
        "free_note": free_note.strip(),
        "valid": valid,
        "validation_errors": errors,
        "allowed_to_update_hidden_factor": allowed_hidden,
        "allowed_to_update_chart_facts": False,
        "latent_answer_status": "skipped_or_uncertain" if user_skipped_hidden else ("calibration_signal" if allowed_hidden else "note_only"),
        "free_note_policy": str(constraint_payload.get("free_note_policy") or "store_as_note_only"),
        "absorbed_signals": _absorbed_signals(
            selected_domain=selected_domain,
            allowed_hidden=allowed_hidden,
            free_note=free_note,
        ),
        "rejected_signals": _rejected_signals(errors=errors, constraint_type=constraint_type, payload=payload),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "interaction_turn_signal_is_bounded_feedback_not_chart_fact",
    }


def hidden_factor_feedback_payload_from_turn_signal(turn_signal: Mapping[str, Any], *, feedback_id: str) -> dict[str, Any]:
    structured = turn_signal.get("structured_payload", {})
    structured = structured if isinstance(structured, Mapping) else {}
    if turn_signal.get("allowed_to_update_hidden_factor") is not True:
        return {}
    return {
        "feedback_id": feedback_id,
        "special_event_years": _list(structured.get("years")),
        "repeated_states": _list(structured.get("state_tags")),
        "boundary_notes": [str(turn_signal.get("free_note") or "")] if turn_signal.get("free_note") else [],
        "feedback_status": "confirmed",
        "source": "unified_interaction_brain_structured_payload",
    }


def _option_rows(mapping: Mapping[str, str]) -> list[dict[str, str]]:
    return [{"value": key, "label": label} for key, label in mapping.items()]


def _label_rows(mapping: Mapping[str, str]) -> list[dict[str, str]]:
    return _option_rows(mapping)


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _valid_years(value: Any, errors: list[dict[str, str]]) -> list[int]:
    rows: list[int] = []
    for raw in _list(value):
        try:
            year = int(raw)
        except (TypeError, ValueError):
            errors.append({"field": "years", "error": "invalid_year"})
            continue
        if year < MIN_YEAR or year > MAX_YEAR:
            errors.append({"field": "years", "error": "year_out_of_range"})
            continue
        rows.append(year)
    return sorted(set(rows))


def _valid_state_tags(value: Any, errors: list[dict[str, str]]) -> list[str]:
    rows: list[str] = []
    for raw in _list(value):
        tag = str(raw or "").strip()
        if not tag:
            continue
        if tag not in ALLOWED_STATE_TAGS:
            errors.append({"field": "state_tags", "error": "unknown_state_tag"})
            continue
        rows.append(tag)
    return sorted(set(rows))


def _enum_value(value: Any, allowed: set[str], field: str, errors: list[dict[str, str]]) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text not in allowed:
        errors.append({"field": field, "error": "invalid_selection"})
        return ""
    return text


def _selected_domain(value: Any, selected_option: str, errors: list[dict[str, str]]) -> str:
    raw = str(value or "").strip()
    if not raw and selected_option.startswith("domain:"):
        raw = selected_option.split(":", 1)[1]
    if not raw:
        return ""
    if raw not in DOMAIN_OPTIONS:
        errors.append({"field": "selected_domain", "error": "invalid_domain"})
        return ""
    return raw


def _absorbed_signals(*, selected_domain: str, allowed_hidden: bool, free_note: str) -> list[str]:
    rows: list[str] = []
    if selected_domain:
        rows.append("selected_domain")
    if allowed_hidden:
        rows.append("hidden_factor")
    if free_note.strip():
        rows.append("free_note_note_only")
    return rows


def _rejected_signals(*, errors: list[dict[str, str]], constraint_type: str, payload: Mapping[str, Any]) -> list[str]:
    rows = [f"{row.get('field')}:{row.get('error')}" for row in errors]
    if constraint_type == "structured_hidden_factor" and payload.get("free_note") and not payload.get("state_tags"):
        rows.append("free_text_only_hidden_factor_update_blocked")
    return rows
