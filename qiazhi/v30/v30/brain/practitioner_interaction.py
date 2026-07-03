from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from v30.brain.text_options import build_practitioner_selection, role_visible_option_sets


PRACTITIONER_INTERACTION_STATE_VERSION = "v30.practitioner_interaction_state.v1"
PRACTITIONER_SELECTION_EFFECT_VERSION = "v30.practitioner_selection_effect.v1"
ADMIN_INTELLIGENCE_REPLAY_VERSION = "v30.admin_intelligence_replay.v1"

_POSITIVE_ACTIONS = {"select", "rank"}
_NEGATIVE_ACTIONS = {"reject", "downrank"}
_ACTION_DELTAS = {
    "select": 0.16,
    "rank": 0.20,
    "reject": -0.30,
    "downrank": -0.14,
    "needs_question": 0.06,
    "note": 0.0,
}


def collect_thinking_option_sets(thinking: dict[str, object] | None, *, role_key: str = "practitioner") -> list[dict[str, object]]:
    if not isinstance(thinking, dict):
        return []
    option_sets: list[dict[str, object]] = []
    seen: set[str] = set()
    stage_rows = [*_dict_rows(thinking.get("journey_steps")), *_dict_rows(thinking.get("steps"))]
    for step in stage_rows:
        point_set = _dict(step.get("stage_point_set"))
        for option_set in _dict_rows(point_set.get("option_sets")):
            option_set_id = str(option_set.get("option_set_id") or "")
            if not option_set_id or option_set_id in seen:
                continue
            seen.add(option_set_id)
            option_sets.append({
                **option_set,
                "stage_title": str(step.get("title") or ""),
                "stage_index": int(step.get("index") or len(option_sets) + 1),
            })
    return role_visible_option_sets(option_sets, role_key=role_key)


def find_option_set(thinking: dict[str, object] | None, option_set_id: str, *, role_key: str = "practitioner") -> dict[str, object] | None:
    for option_set in collect_thinking_option_sets(thinking, role_key=role_key):
        if str(option_set.get("option_set_id") or "") == option_set_id:
            return option_set
    return None


def build_practitioner_selection_record(
    option_set: dict[str, object],
    *,
    selected_option_ids: list[str],
    action: str = "select",
    ranked_option_ids: list[str] | None = None,
    rejected_option_ids: list[str] | None = None,
    note: str = "",
    confidence: float = 0.0,
    actor_id: str = "",
    created_at: str | None = None,
) -> dict[str, object]:
    valid_option_ids = {str(row.get("option_id") or "") for row in _dict_rows(option_set.get("options"))}
    selected = _valid_option_ids(selected_option_ids, valid_option_ids)
    ranked = _valid_option_ids(ranked_option_ids or selected, valid_option_ids)
    rejected = _valid_option_ids(rejected_option_ids or [], valid_option_ids)
    if action in _POSITIVE_ACTIONS and not selected:
        selected = ranked[:1]
    if action in _NEGATIVE_ACTIONS and not rejected and selected:
        rejected = selected[:]
    selection = build_practitioner_selection(
        option_set,
        action=action,
        selected_option_ids=selected,
        ranked_option_ids=ranked,
        rejected_option_ids=rejected,
        note=note,
        confidence=confidence,
    )
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    event_suffix = _compact_event_suffix(timestamp, len(selected), len(rejected), action)
    selection = {
        **selection,
        "selection_id": f"{selection['selection_id']}.{event_suffix}",
        "actor_id": actor_id,
        "created_at": timestamp,
        "option_set": _option_set_snapshot(option_set),
    }
    return {
        **selection,
        "effect": selection_effect_from_practitioner_selection(selection, option_set=option_set),
    }


def selection_effect_from_practitioner_selection(
    selection: dict[str, object],
    *,
    option_set: dict[str, object] | None = None,
) -> dict[str, object]:
    option_set = option_set or _dict(selection.get("option_set"))
    action = str(selection.get("action") or "select")
    delta = float(_ACTION_DELTAS.get(action, _ACTION_DELTAS["select"]))
    if action in _NEGATIVE_ACTIONS and delta > 0:
        delta = -delta
    selected = [str(row) for row in _list(selection.get("selected_option_ids")) if row]
    ranked = [str(row) for row in _list(selection.get("ranked_option_ids")) if row]
    rejected = [str(row) for row in _list(selection.get("rejected_option_ids")) if row]
    confidence = _bounded_float(selection.get("confidence"), default=0.0)
    weighted_delta = round(delta * (0.72 + confidence * 0.28), 3)
    return {
        "version": PRACTITIONER_SELECTION_EFFECT_VERSION,
        "selection_id": str(selection.get("selection_id") or ""),
        "option_set_id": str(selection.get("option_set_id") or option_set.get("option_set_id") or ""),
        "stage_id": str(option_set.get("stage_id") or ""),
        "source_id": str(option_set.get("source_id") or ""),
        "source_type": str(option_set.get("source_type") or ""),
        "topic": str(option_set.get("topic") or ""),
        "action": action,
        "selected_option_ids": selected,
        "ranked_option_ids": ranked,
        "rejected_option_ids": rejected,
        "belief_delta": {
            "target": "belief_state.option_candidate_weight",
            "delta": weighted_delta,
            "confidence": confidence,
            "direction": "raise" if weighted_delta > 0 else "lower" if weighted_delta < 0 else "annotate",
        },
        "stage_point_delta": {
            "target": "stage_point.display_priority",
            "delta": weighted_delta,
        },
        "final_synthesis_delta": {
            "target": "final_synthesis.evidence_order",
            "delta": weighted_delta,
            "ranked_option_ids": ranked,
        },
        "question_delta": {
            "target": "question_policy.next_question_priority",
            "delta": 0.12 if action == "needs_question" else 0.0,
        },
        "training_signal": {
            "signal_id": "v30.training_signal.practitioner_selection_alignment",
            "trainable": True,
            "label": action,
            "blocked_targets": [
                "four_pillars",
                "calendar_conversion",
                "birth_time",
                "raw_rule_truth",
                "luck_cycle_calculation",
            ],
        },
        "chart_fact_mutation_allowed": False,
        "boundary": "practitioner_selection_effect_updates_interpretation_weight_not_chart_facts",
    }


def build_practitioner_interaction_state(
    reading_id: str,
    thinking: dict[str, object] | None,
    selections: list[dict[str, object]] | None = None,
    *,
    role_key: str = "practitioner",
) -> dict[str, object]:
    selection_rows = [row for row in (selections or []) if isinstance(row, dict)]
    option_sets = collect_thinking_option_sets(thinking, role_key=role_key)
    selected_by_option_set = _selection_rows_by_option_set(selection_rows)
    enriched_option_sets = [
        _option_set_with_selection_state(option_set, selected_by_option_set.get(str(option_set.get("option_set_id") or ""), []))
        for option_set in option_sets
    ]
    effects = [_selection_effect(row) for row in selection_rows]
    return {
        "version": PRACTITIONER_INTERACTION_STATE_VERSION,
        "reading_id": reading_id,
        "role_key": role_key,
        "option_set_count": len(enriched_option_sets),
        "selection_count": len(selection_rows),
        "option_sets": enriched_option_sets,
        "selections": selection_rows[-50:],
        "selection_summary": _selection_summary(selection_rows),
        "belief_delta_preview": _belief_delta_preview(effects),
        "final_synthesis_priority": _final_synthesis_priority(effects),
        "chart_fact_mutation_allowed": False,
        "boundary": "practitioner_interaction_state_is_weight_and_training_overlay_not_chart_fact_source",
    }


def apply_practitioner_selection_effects_to_thinking(
    thinking: dict[str, object] | None,
    selections: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if not isinstance(thinking, dict):
        return {}
    selection_rows = [row for row in (selections or []) if isinstance(row, dict)]
    if not selection_rows:
        return thinking
    effects = [_selection_effect(row) for row in selection_rows]
    effects_by_source = _effect_delta_by_source(effects)
    enhanced_steps = []
    for step in _dict_rows(thinking.get("steps")):
        point_set = _dict(step.get("stage_point_set"))
        selected_points = _points_with_selection_effects(
            _dict_rows(point_set.get("selected_points")),
            effects_by_source=effects_by_source,
        )
        all_points = _points_with_selection_effects(
            _dict_rows(point_set.get("points")),
            effects_by_source=effects_by_source,
        )
        enhanced_point_set = {
            **point_set,
            "points": all_points,
            "selected_points": selected_points,
            "practitioner_selection_overlay": _stage_overlay_summary(str(step.get("step_id") or ""), effects),
        }
        enhanced_steps.append({
            **step,
            "stage_point_set": enhanced_point_set,
            "stage_points": selected_points if selected_points else step.get("stage_points", []),
        })
    return {
        **thinking,
        "steps": enhanced_steps,
        "practitioner_selection_effects": {
            "version": "v30.thinking_practitioner_selection_overlay.v1",
            "effect_count": len(effects),
            "effects": effects[-50:],
            "final_synthesis_priority": _final_synthesis_priority(effects),
            "chart_fact_mutation_allowed": False,
            "boundary": "thinking_overlay_applies_practitioner_weight_without_mutating_runtime_facts",
        },
    }


def build_admin_intelligence_replay(
    reading_id: str,
    thinking: dict[str, object] | None,
    selections: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    thinking = thinking if isinstance(thinking, dict) else {}
    selection_rows = [row for row in (selections or []) if isinstance(row, dict)]
    rows = []
    for index, step in enumerate(_dict_rows(thinking.get("steps")), start=1):
        point_set = _dict(step.get("stage_point_set"))
        projection = _dict(point_set.get("text_option_projection"))
        judge = _dict(_dict(step.get("summary_panel")).get("llm_metadata")).get("central_brain_review")
        judge = judge if isinstance(judge, dict) else _dict(_dict(step.get("analysis_result")).get("summary_decision"))
        prompt_profile = _dict(_dict(step.get("summary_policy")).get("prompt_profile"))
        rows.append({
            "step_index": index,
            "step_id": str(step.get("step_id") or ""),
            "title": str(step.get("title") or ""),
            "stage_point_replay": {
                "candidate_count": int(point_set.get("candidate_count") or 0),
                "selected_count": int(point_set.get("selected_count") or len(_dict_rows(point_set.get("selected_points")))),
                "discarded_count": len(_dict_rows(point_set.get("discarded_noise"))),
                "selected_points": _dict_rows(point_set.get("selected_points"))[:8],
                "discarded_noise": _dict_rows(point_set.get("discarded_noise"))[:8],
            },
            "text_option_replay": {
                "semantic_unit_count": int(projection.get("semantic_unit_count") or len(_dict_rows(point_set.get("semantic_units")))),
                "option_set_count": int(projection.get("option_set_count") or len(_dict_rows(point_set.get("option_sets")))),
                "option_sets": _dict_rows(point_set.get("option_sets"))[:8],
                "discarded_units": _dict_rows(projection.get("discarded_units"))[:8],
            },
            "brain_judge": _judge_snapshot(judge),
            "prompt_profile": prompt_profile,
            "practitioner_selections": _selections_for_step(selection_rows, str(step.get("step_id") or "")),
        })
    return {
        "version": ADMIN_INTELLIGENCE_REPLAY_VERSION,
        "reading_id": reading_id,
        "stage_count": len(rows),
        "stages": rows,
        "summary": {
            "stage_point_candidate_count": sum(row["stage_point_replay"]["candidate_count"] for row in rows),
            "stage_point_selected_count": sum(row["stage_point_replay"]["selected_count"] for row in rows),
            "stage_point_discarded_count": sum(row["stage_point_replay"]["discarded_count"] for row in rows),
            "option_set_count": sum(row["text_option_replay"]["option_set_count"] for row in rows),
            "semantic_unit_count": sum(row["text_option_replay"]["semantic_unit_count"] for row in rows),
            "practitioner_selection_count": len(selection_rows),
            "prompt_profile_count": len({str(row["prompt_profile"].get("profile_id") or "") for row in rows if row["prompt_profile"]}),
        },
        "practitioner_selection_summary": _selection_summary(selection_rows),
        "chart_fact_mutation_allowed": False,
        "boundary": "admin_intelligence_replay_explains_stage_option_judge_prompt_without_mutating_chart_facts",
    }


def _points_with_selection_effects(
    points: list[dict[str, object]],
    *,
    effects_by_source: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    enhanced = []
    for point in points:
        point_id = str(point.get("point_id") or "")
        effect = effects_by_source.get(point_id, {})
        delta = _bounded_float(effect.get("delta"), default=0.0)
        base_priority = _bounded_float(point.get("display_priority"), default=0.0)
        enhanced.append({
            **point,
            "display_priority_adjusted": round(base_priority + delta, 3),
            "practitioner_selection_effect": effect,
            "selected_by_practitioner": bool(effect.get("selected")),
            "downranked_by_practitioner": bool(effect.get("downranked")),
        })
    return sorted(
        enhanced,
        key=lambda row: (
            _bounded_float(row.get("display_priority_adjusted"), default=0.0),
            _bounded_float(row.get("confidence"), default=0.0),
        ),
        reverse=True,
    )


def _effect_delta_by_source(effects: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for effect in effects:
        source_id = str(effect.get("source_id") or "")
        if not source_id:
            continue
        delta = _bounded_float(_dict(effect.get("stage_point_delta")).get("delta"), default=0.0)
        prior = rows.get(source_id, {})
        rows[source_id] = {
            "source_id": source_id,
            "delta": round(_bounded_float(prior.get("delta"), default=0.0) + delta, 3),
            "selected": bool(prior.get("selected")) or str(effect.get("action") or "") in _POSITIVE_ACTIONS,
            "downranked": bool(prior.get("downranked")) or str(effect.get("action") or "") in _NEGATIVE_ACTIONS,
            "selection_ids": [*_list(prior.get("selection_ids")), str(effect.get("selection_id") or "")],
        }
    return rows


def _stage_overlay_summary(stage_id: str, effects: list[dict[str, object]]) -> dict[str, object]:
    rows = [effect for effect in effects if str(effect.get("stage_id") or "") == stage_id]
    return {
        "version": "v30.stage_practitioner_selection_overlay.v1",
        "selection_count": len(rows),
        "positive_count": sum(1 for row in rows if str(row.get("action") or "") in _POSITIVE_ACTIONS),
        "negative_count": sum(1 for row in rows if str(row.get("action") or "") in _NEGATIVE_ACTIONS),
        "chart_fact_mutation_allowed": False,
    }


def _option_set_with_selection_state(option_set: dict[str, object], selections: list[dict[str, object]]) -> dict[str, object]:
    latest = selections[-1] if selections else {}
    return {
        **option_set,
        "selection_state": {
            "selection_count": len(selections),
            "latest_action": str(latest.get("action") or ""),
            "selected_option_ids": _list(latest.get("selected_option_ids")),
            "ranked_option_ids": _list(latest.get("ranked_option_ids")),
            "rejected_option_ids": _list(latest.get("rejected_option_ids")),
            "note": str(latest.get("note") or ""),
        },
    }


def _selection_rows_by_option_set(selections: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    rows: dict[str, list[dict[str, object]]] = {}
    for selection in selections:
        option_set_id = str(selection.get("option_set_id") or "")
        if option_set_id:
            rows.setdefault(option_set_id, []).append(selection)
    return rows


def _selection_summary(selections: list[dict[str, object]]) -> dict[str, object]:
    by_action: dict[str, int] = {}
    by_topic: dict[str, int] = {}
    for selection in selections:
        action = str(selection.get("action") or "select")
        topic = str(_dict(selection.get("option_set")).get("topic") or "")
        by_action[action] = by_action.get(action, 0) + 1
        if topic:
            by_topic[topic] = by_topic.get(topic, 0) + 1
    return {
        "version": "v30.practitioner_selection_summary.v1",
        "selection_count": len(selections),
        "by_action": by_action,
        "by_topic": by_topic,
        "chart_fact_mutation_allowed": False,
    }


def _belief_delta_preview(effects: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "selection_id": str(effect.get("selection_id") or ""),
            "option_set_id": str(effect.get("option_set_id") or ""),
            "stage_id": str(effect.get("stage_id") or ""),
            "topic": str(effect.get("topic") or ""),
            **_dict(effect.get("belief_delta")),
        }
        for effect in effects[-50:]
    ]


def _final_synthesis_priority(effects: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for effect in effects[-50:]:
        delta = _dict(effect.get("final_synthesis_delta"))
        rows.append({
            "selection_id": str(effect.get("selection_id") or ""),
            "stage_id": str(effect.get("stage_id") or ""),
            "source_id": str(effect.get("source_id") or ""),
            "topic": str(effect.get("topic") or ""),
            "delta": _bounded_float(delta.get("delta"), default=0.0),
            "ranked_option_ids": _list(delta.get("ranked_option_ids")),
        })
    return sorted(rows, key=lambda row: abs(float(row.get("delta") or 0.0)), reverse=True)


def _selection_effect(selection: dict[str, object]) -> dict[str, object]:
    effect = selection.get("effect")
    if isinstance(effect, dict):
        return effect
    return selection_effect_from_practitioner_selection(selection)


def _selections_for_step(selections: list[dict[str, object]], stage_id: str) -> list[dict[str, object]]:
    return [
        selection
        for selection in selections
        if str(_dict(selection.get("option_set")).get("stage_id") or "") == stage_id
    ][-20:]


def _judge_snapshot(judge: dict[str, object]) -> dict[str, object]:
    if not judge:
        return {}
    scores = _dict(judge.get("scores") or judge.get("score_breakdown"))
    return {
        "status": str(judge.get("status") or judge.get("decision_status") or ""),
        "quality_score": judge.get("quality_score", judge.get("score", "")),
        "scores": scores,
        "failures": _list(judge.get("failures") or judge.get("failed_check_ids")),
        "accepted": judge.get("accepted", judge.get("passed", "")),
    }


def _option_set_snapshot(option_set: dict[str, object]) -> dict[str, object]:
    return {
        "option_set_id": str(option_set.get("option_set_id") or ""),
        "source_type": str(option_set.get("source_type") or ""),
        "source_id": str(option_set.get("source_id") or ""),
        "stage_id": str(option_set.get("stage_id") or ""),
        "topic": str(option_set.get("topic") or ""),
        "title": str(option_set.get("title") or ""),
        "question": str(option_set.get("question") or ""),
        "selection_mode": str(option_set.get("selection_mode") or ""),
        "options": _dict_rows(option_set.get("options")),
        "option_value_score": option_set.get("option_value_score", 0),
        "boundary": str(option_set.get("boundary") or ""),
    }


def _valid_option_ids(rows: list[str], valid_option_ids: set[str]) -> list[str]:
    if not valid_option_ids:
        return _unique([str(row) for row in rows if row])
    return _unique([str(row) for row in rows if str(row) in valid_option_ids])


def _compact_event_suffix(created_at: str, selected_count: int, rejected_count: int, action: str) -> str:
    digits = "".join(ch for ch in created_at if ch.isdigit())
    return f"{digits[-10:] or 'event'}{selected_count}{rejected_count}{action[:1]}"


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _dict_rows(value: object) -> list[dict[str, object]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for row in rows:
        if not row or row in seen:
            continue
        seen.add(row)
        result.append(row)
    return result


def _bounded_float(value: object, *, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(-1.0, min(1.0, number))
