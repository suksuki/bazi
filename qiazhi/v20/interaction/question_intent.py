from __future__ import annotations

from collections import Counter
from typing import Any

from v20.answer.measurement_policy import domain_label
from v20.features.state_model import feature_state_by_domain


QUESTION_INTENT_MODEL_VERSION = "v20.question_intent_model.v1"


INTENT_BY_STATE = {
    "confirmed": "confirm_structure",
    "candidate": "explore_candidate",
    "weak_candidate": "collect_evidence",
    "mixed": "resolve_mixed_state",
    "volatile": "inspect_timing_trigger",
    "requires_review": "ask_practitioner_review",
    "blocked": "explain_boundary",
    "out_of_scope": "suppress_output",
    "active": "explore_structure",
    "evidence_gap": "collect_evidence",
}


def build_question_intent_model(
    *,
    decision_report: dict[str, Any],
    feature_state_model: dict[str, Any],
    questions: tuple[object, ...],
    selected_question: object,
    runtime_decision_fusion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intents = _intents(decision_report, feature_state_model, runtime_decision_fusion=runtime_decision_fusion)
    bindings = tuple(_question_binding(question, intents) for question in questions)
    selected_key = str(getattr(selected_question, "question_key", ""))
    selected_binding = next((row for row in bindings if row["question_key"] == selected_key), {})
    intent_counts = Counter(str(row["intent_type"]) for row in intents)
    return {
        "version": QUESTION_INTENT_MODEL_VERSION,
        "status": "ready" if intents else "empty",
        "algorithm": "utility_intent_ranking_phase1",
        "source": "DecisionFusion+MainlineDecision+PortraitAxis+FeatureState",
        "intent_count": len(intents),
        "question_binding_count": len(bindings),
        "intent_type_counts": dict(sorted(intent_counts.items())),
        "intents": intents,
        "question_bindings": bindings,
        "selected_question_intent": selected_binding,
        "runtime_mutation": False,
        "guardrails": (
            "QUESTION_INTENTS_ARE_GENERATED_FROM_DECISION_AND_FEATURE_STATE",
            "RANKING_CAN_REORDER_NOT_CREATE_FACTS",
            "NO_QUESTION_WITHOUT_BAZI_ALIGNMENT",
            "LLM_ROUTING_MAY_SELECT_NOT_DECIDE",
        ),
    }


def _intents(
    decision_report: dict[str, Any],
    feature_state_model: dict[str, Any],
    runtime_decision_fusion: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    feature_by_domain = feature_state_by_domain(feature_state_model)
    fusion_payload = runtime_decision_fusion or {}
    for row in tuple(row for row in fusion_payload.get("decisions", ()) if isinstance(row, dict)):
        rows.append(_intent_from_runtime_fusion(row))
    for mainline in decision_report.get("mainlines", ()):
        if not isinstance(mainline, dict):
            continue
        rows.append(_intent_from_mainline(mainline, feature_by_domain))
    for axis in decision_report.get("portrait_projection", {}).get("axes", ()):
        if not isinstance(axis, dict):
            continue
        rows.append(_intent_from_axis(axis))
    for state in feature_state_model.get("evidence_gap_features", ()):
        if not isinstance(state, dict):
            continue
        rows.append(_intent_from_feature_gap(state))
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["domain"]), str(row["intent_type"]), str(row["source_id"]))
        current = deduped.get(key)
        if current is None or float(row["priority"]) > float(current["priority"]):
            deduped[key] = row
    return tuple(sorted(deduped.values(), key=lambda row: (row["priority"], row["domain"]), reverse=True)[:32])


def _intent_from_mainline(mainline: dict[str, Any], feature_by_domain: dict[str, tuple[dict[str, Any], ...]]) -> dict[str, Any]:
    domain = str(mainline.get("domain", ""))
    state = str(mainline.get("status", "candidate"))
    intent_type = INTENT_BY_STATE.get(state, "explore_structure")
    features = feature_by_domain.get(domain, ())
    return {
        "intent_id": f"intent.mainline.{domain}",
        "intent_type": intent_type,
        "domain": domain,
        "title": str(mainline.get("title", "")) or f"{domain_label(domain)}主线",
        "prompt_goal": _prompt_goal(domain, intent_type),
        "priority": round(float(mainline.get("score", 0.0) or 0.0) + 0.12, 3),
        "source": "mainline_decision",
        "source_id": str(mainline.get("mainline_key", "")),
        "source_decision_keys": tuple(str(row) for row in mainline.get("source_decision_keys", ()) if str(row)),
        "source_feature_ids": tuple(str(row.get("feature_id", "")) for row in features[:6] if row.get("feature_id")),
        "boundary": "问题只推进证据复核和结构澄清，不生成命运断语。",
    }


def _intent_from_axis(axis: dict[str, Any]) -> dict[str, Any]:
    domain = str(axis.get("domain", ""))
    intent_type = str(axis.get("portrait_intent_type", "")) or "explore_structure"
    return {
        "intent_id": f"intent.portrait_axis.{domain}",
        "intent_type": intent_type,
        "domain": domain,
        "title": str(axis.get("profile_tag", "")) or str(axis.get("label", "")) or f"{domain_label(domain)}画像",
        "prompt_goal": _prompt_goal(domain, intent_type),
        "priority": round(max(0.05, float(axis.get("peak_confidence", 0.0) or 0.0) - 0.12), 3),
        "source": "portrait_axis",
        "source_id": str(axis.get("axis_id", "")),
        "source_decision_keys": (),
        "source_feature_ids": tuple(str(row) for row in axis.get("feature_ids", ()) if str(row)),
        "boundary": "画像轴只作为问题入口，不作为人格或命运结论。",
    }


def _intent_from_runtime_fusion(decision: dict[str, Any]) -> dict[str, Any]:
    domain = str(decision.get("domain", ""))
    state = str(decision.get("structural_state", "candidate"))
    intent_type = INTENT_BY_STATE.get(state, "resolve_mixed_state")
    source_decision_keys = tuple(str(row) for row in decision.get("target_decision_keys", ()) if str(row))
    if not source_decision_keys:
        source_key = str(decision.get("source_decision_key", ""))
        if source_key:
            source_decision_keys = (source_key,)
    feature_ids = tuple(str(row) for row in decision.get("feature_ids", ()) if str(row))
    return {
        "intent_id": f"intent.runtime_fusion.{decision.get('decision_key', decision.get('domain', 'unknown'))}",
        "intent_type": intent_type,
        "domain": domain,
        "title": _compact_title_from_text(str(decision.get("user_facing_decision", ""))) or f"{domain_label(domain)}运行结构决策",
        "prompt_goal": _prompt_goal(domain, intent_type),
        "priority": round(float(decision.get("confidence", 0.0) or 0.0) + 0.15, 3),
        "source": "runtime_decision_fusion",
        "source_id": str(decision.get("decision_key", "")),
        "source_decision_keys": source_decision_keys,
        "source_feature_ids": feature_ids,
        "boundary": str(decision.get("user_facing_boundary", "")) or "按结构先后提问，不做固定结论。",
    }


def _compact_title_from_text(value: str, limit: int = 42) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def _intent_from_feature_gap(state: dict[str, Any]) -> dict[str, Any]:
    domain = str(state.get("domain", ""))
    return {
        "intent_id": f"intent.feature_gap.{state.get('feature_id', '')}",
        "intent_type": "collect_evidence",
        "domain": domain,
        "title": str(state.get("title", "")) or f"{domain_label(domain)}证据缺口",
        "prompt_goal": _prompt_goal(domain, "collect_evidence"),
        "priority": round(float(state.get("priority", 0.0) or 0.0) + 0.04, 3),
        "source": "feature_state",
        "source_id": str(state.get("feature_id", "")),
        "source_decision_keys": tuple(str(row) for row in state.get("decision_keys", ()) if str(row)),
        "source_feature_ids": (str(state.get("feature_id", "")),),
        "boundary": "证据缺口只能触发追问或复核，不直接触发结论。",
    }


def _question_binding(question: object, intents: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    key = str(getattr(question, "question_key", ""))
    domain = str(getattr(question, "domain", ""))
    matched = tuple(row for row in intents if str(row.get("domain", "")) == domain)
    primary = matched[0] if matched else {}
    return {
        "question_key": key,
        "title": str(getattr(question, "title", "")),
        "domain": domain,
        "matched_intent_ids": tuple(str(row.get("intent_id", "")) for row in matched[:4] if row.get("intent_id")),
        "primary_intent_type": str(primary.get("intent_type", "")),
        "intent_priority": float(primary.get("priority", 0.0) or 0.0),
        "source_feature_ids": tuple(str(row) for row in getattr(question, "source_feature_ids", ()) if str(row)),
    }


def _prompt_goal(domain: str, intent_type: str) -> str:
    topic = domain_label(domain)
    goals = {
        "confirm_structure": f"确认{topic}结构是否已经具备足够证据。",
        "explore_candidate": f"展开{topic}候选路径，找出主证据和反证。",
        "collect_evidence": f"补齐{topic}证据缺口。",
        "resolve_mixed_state": f"裁决{topic}成而不纯或互相牵制的部分。",
        "inspect_timing_trigger": f"查看{topic}是否被大运流年引动。",
        "ask_practitioner_review": f"把{topic}交给命理师复核主次。",
        "explain_boundary": f"解释{topic}为什么不能直接输出结论。",
    }
    return goals.get(intent_type, f"围绕{topic}继续澄清结构。")
