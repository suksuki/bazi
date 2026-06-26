from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import Field

from v30.contracts import V30Model
from v30.hidden_factor.calibration import HiddenFactorCalibration


class EventYearSignal(V30Model):
    years: list[int] = Field(default_factory=list)
    year_count: int = 0
    is_multi_year: bool = False
    bound_to_time_context: bool = False
    context_bindings: list[str] = Field(default_factory=list)


class RepeatedStateSignal(V30Model):
    states: list[str] = Field(default_factory=list)
    state_count: int = 0
    domains: list[str] = Field(default_factory=list)
    is_narrow_domain_repeat: bool = False


class HiddenFactorFeedback(V30Model):
    feedback_id: str
    reading_id: str
    context_id: str
    special_event_years: list[int] = Field(default_factory=list)
    repeated_states: list[str] = Field(default_factory=list)
    time_context_bindings: list[str] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)
    feedback_status: str = "affirmed"
    source: str = "user_dialogue"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HiddenFactorState(V30Model):
    state_id: str
    reading_id: str
    context_id: str
    status: str
    amplifier_strength: float
    amplifier_candidate: bool
    special_event_years: list[int] = Field(default_factory=list)
    repeated_states: list[str] = Field(default_factory=list)
    event_year_signal: EventYearSignal = Field(default_factory=EventYearSignal)
    repeated_state_signal: RepeatedStateSignal = Field(default_factory=RepeatedStateSignal)
    alignment_score: float = 0.0
    time_layer_alignment_score: float = 0.0
    feedback_ids: list[str] = Field(default_factory=list)
    denied_feedback_ids: list[str] = Field(default_factory=list)
    conflict_feedback_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    next_feedback_needed: list[str] = Field(default_factory=list)
    boundary: str = "hidden_factor_state_feedback_hypothesis_not_chart_fact"
    stale_after_days: int = 90
    expires_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def build_hidden_factor_state(
    *,
    reading_id: str,
    context_id: str,
    calibration: HiddenFactorCalibration,
    feedback: list[HiddenFactorFeedback] | None = None,
) -> HiddenFactorState:
    feedback = feedback or []
    affirmed = [item for item in feedback if _feedback_status(item) == "affirmed"]
    denied = [item for item in feedback if _feedback_status(item) == "denied"]
    conflicted = [item for item in feedback if _feedback_status(item) == "conflicting"]
    years = sorted({year for item in affirmed for year in item.special_event_years})
    states = sorted({state for item in affirmed for state in item.repeated_states if state})
    context_bindings = sorted({binding for item in affirmed for binding in item.time_context_bindings if binding})
    event_signal = _event_year_signal(years, context_bindings)
    repeated_signal = _repeated_state_signal(states)
    alignment_score = _alignment_score(event_signal, repeated_signal)
    updated_at = datetime.now(timezone.utc)
    feedback_ids = [item.feedback_id for item in feedback]
    denied_ids = [item.feedback_id for item in denied]
    conflict_ids = [item.feedback_id for item in conflicted]
    strength = _amplifier_strength(
        calibration,
        event_signal,
        repeated_signal,
        alignment_score=alignment_score,
        denied_count=len(denied),
        conflict_count=len(conflicted),
    )
    status = _state_status(
        calibration,
        event_signal,
        repeated_signal,
        denied_count=len(denied),
        conflict_count=len(conflicted),
    )
    return HiddenFactorState(
        state_id=f"{reading_id}:hidden_factor_state",
        reading_id=reading_id,
        context_id=context_id,
        status=status,
        amplifier_strength=strength,
        amplifier_candidate=status in {"feedback_calibrated", "amplifier_candidate"},
        special_event_years=years,
        repeated_states=states,
        event_year_signal=event_signal,
        repeated_state_signal=repeated_signal,
        alignment_score=alignment_score,
        time_layer_alignment_score=_time_layer_alignment_score(event_signal),
        feedback_ids=feedback_ids,
        denied_feedback_ids=denied_ids,
        conflict_feedback_ids=conflict_ids,
        evidence_ids=calibration.evidence_ids,
        next_feedback_needed=_next_feedback_needed(calibration, years, states),
        expires_at=updated_at + timedelta(days=90),
        updated_at=updated_at,
    )


def merge_hidden_factor_state(
    existing: HiddenFactorState | None,
    incoming: HiddenFactorState,
) -> HiddenFactorState:
    if existing is None:
        return incoming
    years = sorted({*existing.special_event_years, *incoming.special_event_years})
    states = sorted({*existing.repeated_states, *incoming.repeated_states})
    context_bindings = sorted({
        *existing.event_year_signal.context_bindings,
        *incoming.event_year_signal.context_bindings,
    })
    event_signal = _event_year_signal(years, context_bindings)
    repeated_signal = _repeated_state_signal(states)
    alignment_score = _alignment_score(event_signal, repeated_signal)
    feedback_ids = [*existing.feedback_ids, *[row for row in incoming.feedback_ids if row not in existing.feedback_ids]]
    denied_feedback_ids = [
        *existing.denied_feedback_ids,
        *[row for row in incoming.denied_feedback_ids if row not in existing.denied_feedback_ids],
    ]
    conflict_feedback_ids = [
        *existing.conflict_feedback_ids,
        *[row for row in incoming.conflict_feedback_ids if row not in existing.conflict_feedback_ids],
    ]
    evidence_ids = [*existing.evidence_ids, *[row for row in incoming.evidence_ids if row not in existing.evidence_ids]]
    strength = round(max(existing.amplifier_strength, incoming.amplifier_strength), 3)
    if conflict_feedback_ids or (
        denied_feedback_ids
        and (years or states or existing.status in {"amplifier_candidate", "feedback_calibrated"})
    ):
        status = "conflicting"
        strength = round(min(strength, 0.52), 3)
    elif incoming.status == "user_denied" and not (years or states):
        status = "user_denied"
        strength = round(min(strength, incoming.amplifier_strength), 3)
    elif years and states and incoming.status in {"dialogue_in_progress", "feedback_calibrated", "amplifier_candidate"}:
        status = "amplifier_candidate"
        strength = max(strength, min(0.95, strength + 0.04 + alignment_score * 0.04))
    else:
        status = incoming.status if incoming.updated_at >= existing.updated_at else existing.status
    return incoming.model_copy(
        update={
            "status": status,
            "amplifier_strength": round(strength, 3),
            "amplifier_candidate": status in {"feedback_calibrated", "amplifier_candidate"},
            "special_event_years": years,
            "repeated_states": states,
            "event_year_signal": event_signal,
            "repeated_state_signal": repeated_signal,
            "alignment_score": alignment_score,
            "time_layer_alignment_score": _time_layer_alignment_score(event_signal),
            "feedback_ids": feedback_ids,
            "denied_feedback_ids": denied_feedback_ids,
            "conflict_feedback_ids": conflict_feedback_ids,
            "evidence_ids": evidence_ids,
            "expires_at": max(
                row
                for row in (existing.expires_at, incoming.expires_at)
                if row is not None
            ) if existing.expires_at or incoming.expires_at else None,
            "next_feedback_needed": [
                item
                for item in incoming.next_feedback_needed
                if not (item == "special_event_year" and years)
                and not (item == "repeated_state_pattern" and states)
            ],
        }
    )


def normalize_hidden_factor_state_payload(hidden_factor_state: dict[str, object]) -> dict[str, object]:
    payload = _compatible_hidden_factor_state_payload(hidden_factor_state)
    state = HiddenFactorState.model_validate(payload)
    now = datetime.now(timezone.utc)
    expires_at = state.expires_at
    if expires_at and expires_at < now and state.status not in {"user_denied", "conflicting", "not_applicable"}:
        needed = list(state.next_feedback_needed)
        if "refresh_hidden_factor_feedback" not in needed:
            needed.append("refresh_hidden_factor_feedback")
        state = state.model_copy(
            update={
                "status": "expired",
                "amplifier_candidate": False,
                "amplifier_strength": round(min(state.amplifier_strength, 0.35), 3),
                "next_feedback_needed": needed,
            }
        )
    return state.model_dump(mode="json")


def _compatible_hidden_factor_state_payload(hidden_factor_state: dict[str, object]) -> dict[str, object]:
    allowed = set(HiddenFactorState.model_fields)
    payload = {key: value for key, value in hidden_factor_state.items() if key in allowed}
    if "amplifier_strength" not in payload:
        try:
            payload["amplifier_strength"] = float(hidden_factor_state.get("confidence", 0.0))
        except (TypeError, ValueError):
            payload["amplifier_strength"] = 0.0
    if "special_event_years" not in payload:
        payload["special_event_years"] = _int_list(
            hidden_factor_state.get("special_event_years")
            or hidden_factor_state.get("special_years")
            or hidden_factor_state.get("special_year")
        )
    if "event_year_signal" not in payload:
        payload["event_year_signal"] = _event_year_signal(
            list(payload.get("special_event_years", [])),
            _str_list(hidden_factor_state.get("time_context_bindings")),
        ).model_dump(mode="json")
    if "repeated_state_signal" not in payload:
        payload["repeated_state_signal"] = _repeated_state_signal(
            _str_list(payload.get("repeated_states"))
        ).model_dump(mode="json")
    if "alignment_score" not in payload:
        payload["alignment_score"] = _alignment_score(
            EventYearSignal.model_validate(payload["event_year_signal"]),
            RepeatedStateSignal.model_validate(payload["repeated_state_signal"]),
        )
    if "time_layer_alignment_score" not in payload:
        payload["time_layer_alignment_score"] = _time_layer_alignment_score(
            EventYearSignal.model_validate(payload["event_year_signal"])
        )
    return payload


def hidden_factor_feedback_from_payload(
    *,
    reading_id: str,
    context_id: str,
    payload: dict[str, Any],
) -> HiddenFactorFeedback:
    feedback_id = str(payload.get("feedback_id") or payload.get("event_id") or f"{reading_id}:hidden-feedback")
    return HiddenFactorFeedback(
        feedback_id=feedback_id,
        reading_id=reading_id,
        context_id=context_id,
        special_event_years=_int_list(payload.get("special_event_years") or payload.get("special_event_year")),
        repeated_states=_str_list(payload.get("repeated_states") or payload.get("repeated_state")),
        time_context_bindings=_time_context_bindings(payload),
        boundary_notes=_str_list(payload.get("boundary_notes") or payload.get("boundary_note")),
        feedback_status=_feedback_status_from_payload(payload),
        source=str(payload.get("source") or "user_dialogue"),
    )


def _amplifier_strength(
    calibration: HiddenFactorCalibration,
    event_signal: EventYearSignal,
    repeated_signal: RepeatedStateSignal,
    *,
    alignment_score: float = 0.0,
    denied_count: int = 0,
    conflict_count: int = 0,
) -> float:
    score = calibration.hypothesis_strength
    if event_signal.year_count:
        score += min(0.18, event_signal.year_count * 0.055)
    if event_signal.bound_to_time_context:
        score += 0.035
    if repeated_signal.state_count:
        score += min(0.14, repeated_signal.state_count * 0.055)
    if repeated_signal.is_narrow_domain_repeat:
        score += 0.035
    if event_signal.year_count and repeated_signal.state_count:
        score += 0.08 + alignment_score * 0.05
    if denied_count:
        score -= min(0.22, denied_count * 0.16)
    if conflict_count:
        score -= min(0.18, conflict_count * 0.12)
    return round(max(0.05, min(0.95, score)), 3)


def _state_status(
    calibration: HiddenFactorCalibration,
    event_signal: EventYearSignal,
    repeated_signal: RepeatedStateSignal,
    *,
    denied_count: int = 0,
    conflict_count: int = 0,
) -> str:
    if calibration.status == "not_applicable":
        return "not_applicable"
    if conflict_count:
        return "conflicting"
    has_year = event_signal.year_count > 0
    has_state = repeated_signal.state_count > 0
    if denied_count and not (has_year or has_state):
        return "user_denied"
    if denied_count and (has_year or has_state):
        return "conflicting"
    if has_year and has_state:
        return "amplifier_candidate"
    if has_year or has_state:
        return "dialogue_in_progress"
    if calibration.amplifier_candidate:
        return "dialogue_in_progress"
    return "needs_dialogue"


def _event_year_signal(years: list[int], context_bindings: list[str]) -> EventYearSignal:
    return EventYearSignal(
        years=years,
        year_count=len(years),
        is_multi_year=len(years) > 1,
        bound_to_time_context=bool(context_bindings),
        context_bindings=context_bindings,
    )


def _repeated_state_signal(states: list[str]) -> RepeatedStateSignal:
    domains = sorted({_state_domain(state) for state in states})
    return RepeatedStateSignal(
        states=states,
        state_count=len(states),
        domains=domains,
        is_narrow_domain_repeat=bool(states) and len(domains) == 1,
    )


def _alignment_score(event_signal: EventYearSignal, repeated_signal: RepeatedStateSignal) -> float:
    if not event_signal.year_count or not repeated_signal.state_count:
        return 0.0
    score = 0.55
    if event_signal.is_multi_year:
        score += 0.16
    if event_signal.bound_to_time_context:
        score += 0.08
    if repeated_signal.is_narrow_domain_repeat:
        score += 0.14
    if repeated_signal.state_count > 1:
        score += 0.07
    return round(min(1.0, score), 3)


def _time_layer_alignment_score(event_signal: EventYearSignal) -> float:
    if not event_signal.year_count:
        return 0.0
    score = 0.35
    if event_signal.is_multi_year:
        score += 0.2
    if event_signal.bound_to_time_context:
        score += 0.35
    return round(min(1.0, score), 3)


def _state_domain(state: str) -> str:
    value = state.lower()
    if any(token in value for token in ("career", "work", "job", "office")):
        return "career"
    if any(token in value for token in ("relationship", "romance", "partner", "marriage")):
        return "relationship"
    if any(token in value for token in ("wealth", "money", "finance", "income")):
        return "wealth"
    if any(token in value for token in ("health", "body", "illness")):
        return "health"
    return "general"


def _feedback_status(item: HiddenFactorFeedback) -> str:
    value = item.feedback_status.strip().lower()
    if value in {"deny", "denied", "no", "false", "user_denied"}:
        return "denied"
    if value in {"conflict", "conflicting", "mixed"}:
        return "conflicting"
    if value in {"expired", "stale"}:
        return "expired"
    return "affirmed"


def _feedback_status_from_payload(payload: dict[str, Any]) -> str:
    raw = "affirmed"
    for key in ("feedback_status", "confirmation", "confirmed", "status"):
        if key in payload and payload[key] is not None:
            raw = payload[key]
            break
    if isinstance(raw, bool):
        return "affirmed" if raw else "denied"
    return str(raw)


def _next_feedback_needed(
    calibration: HiddenFactorCalibration,
    years: list[int],
    states: list[str],
) -> list[str]:
    needed = list(calibration.required_next_feedback)
    if not years and "special_event_year" not in needed:
        needed.append("special_event_year")
    if not states and "repeated_state_pattern" not in needed:
        needed.append("repeated_state_pattern")
    if years and states:
        needed = [item for item in needed if item not in {"special_event_year", "repeated_state_pattern"}]
    return needed


def _time_context_bindings(payload: dict[str, Any]) -> list[str]:
    explicit = _str_list(payload.get("time_context_bindings") or payload.get("time_context_binding"))
    bindings = set(explicit)
    if payload.get("luck_pillar"):
        bindings.add("luck_pillar")
    if payload.get("flow_year_pillar"):
        bindings.add("flow_year_pillar")
    if payload.get("time_layer_alignment") in {True, "true", "bound", "aligned"}:
        bindings.add("time_layer_alignment")
    return sorted(bindings)


def _int_list(value: object) -> list[int]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    rows: list[int] = []
    for item in values:
        try:
            rows.append(int(item))
        except (TypeError, ValueError):
            continue
    return rows


def _str_list(value: object) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [str(item).strip() for item in values if str(item).strip()]
