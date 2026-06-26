from __future__ import annotations

from typing import Any, Mapping

from v30.contracts import ChartContext


LATENT_QUESTION_STRATEGY_VERSION = "v30.latent_question_need_strategy.v1"


DOMAIN_STATE_TAGS = {
    "career": ["career_pressure", "credential_pressure", "role_change"],
    "wealth": ["wealth_fluctuation", "partnership_distribution"],
    "relationship": ["relationship_repetition", "family_pressure"],
    "health": ["health_rhythm", "family_pressure"],
    "timing": ["role_change", "relocation_change"],
    "decision": ["career_pressure", "wealth_fluctuation"],
}


def build_latent_question_need_strategy(
    *,
    context: ChartContext,
    latent_attributes: Mapping[str, Any] | None = None,
    individualized_projection: Mapping[str, Any] | None = None,
    practical_reading_context: Mapping[str, Any] | None = None,
    model_signal_summary: Mapping[str, Any] | None = None,
    question_outcomes: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    attrs = _dict(latent_attributes)
    projection = _dict(individualized_projection)
    practical = _dict(practical_reading_context)
    model_signal = _dict(model_signal_summary)
    outcomes = question_outcomes or []
    skip = _skip_summary(outcomes)
    candidate_domains = _candidate_domains(practical, projection, model_signal)
    target_domain = candidate_domains[0] if candidate_domains else "career"
    target_tags = DOMAIN_STATE_TAGS.get(target_domain, DOMAIN_STATE_TAGS["career"])[:3]
    attrs_status = str(attrs.get("status") or "default")
    already_ready = bool(_dict(attrs.get("calculation_modifiers")).get("individualization_ready"))
    score = 0.0
    reasons: list[str] = []
    if attrs_status == "default":
        score += 0.34
        reasons.append("latent_attributes_default")
    if candidate_domains:
        score += 0.24
        reasons.append("bazi_domain_path_needs_personalization:" + ",".join(candidate_domains[:3]))
    if model_signal.get("status") == "ready":
        score += 0.08
        reasons.append("model_signal_ready_for_latent_calibration")
    if already_ready:
        score -= 0.28
        reasons.append("latent_attributes_already_inferred")
    if skip["recent_skip"]:
        score -= 0.42
        reasons.append("user_recently_skipped_latent_question")
    if skip["skip_count"] >= 2:
        score -= 0.28
        reasons.append("latent_question_cooldown_after_repeated_skip")
    score = round(max(0.0, min(1.0, score)), 3)
    ask_now = score >= 0.38 and not skip["skip_count"] >= 2
    return {
        "version": LATENT_QUESTION_STRATEGY_VERSION,
        "strategy_id": f"{context.reading_id}:latent-question-need",
        "reading_id": context.reading_id,
        "context_id": context.context_id,
        "ask_now": ask_now,
        "need_score": score,
        "target_domain": target_domain,
        "target_state_tags": target_tags,
        "target_latent_attributes": _target_attributes(target_domain),
        "question_prompt": _question_prompt(target_domain),
        "answer_options": _answer_options(target_domain),
        "skip_policy": {
            "allow_uncertain": True,
            "allow_refuse": True,
            "continue_with_neutral_defaults": True,
            "cooldown_after_skip": 2,
            "boundary": "skip_or_uncertain_answer_must_not_update_latent_attributes",
        },
        "training_routes": [
            "latent_question_need_quality",
            "latent_attribute_reverse_inference",
            "question_strategy_calibration",
        ],
        "reasons": reasons or ["latent_question_not_needed_by_current_context"],
        "chart_fact_mutation_allowed": False,
        "boundary": "latent_question_strategy_decides_when_to_ask_without_turning_questionnaire_into_primary_flow",
    }


def _candidate_domains(
    practical: Mapping[str, Any],
    projection: Mapping[str, Any],
    model_signal: Mapping[str, Any],
) -> list[str]:
    rows: list[tuple[str, float]] = []
    gaps = practical.get("question_gaps", [])
    if isinstance(gaps, list):
        for gap in gaps:
            if isinstance(gap, Mapping) and gap.get("domain"):
                rows.append((str(gap.get("domain")), _float(gap.get("priority_score")) + 0.2))
    domain_rows = projection.get("domain_path_projection", [])
    if isinstance(domain_rows, list):
        for row in domain_rows:
            if isinstance(row, Mapping) and row.get("domain"):
                rows.append((str(row.get("domain")), abs(_float(row.get("adjusted_path_score"), 1.0) - _float(row.get("base_path_score"), 1.0))))
    bands = model_signal.get("energy_bands", [])
    if isinstance(bands, list) and bands:
        rows.append(("career", 0.08))
    dedup: dict[str, float] = {}
    for domain, score in rows:
        if domain not in DOMAIN_STATE_TAGS:
            continue
        dedup[domain] = max(dedup.get(domain, 0.0), score)
    return [domain for domain, _score in sorted(dedup.items(), key=lambda item: (-item[1], item[0]))]


def _skip_summary(outcomes: list[Mapping[str, Any]]) -> dict[str, Any]:
    skip_values = {"hidden_factor:not_sure", "hidden_factor:skip", "hidden_factor:default"}
    hidden_outcomes = [row for row in outcomes if str(row.get("topic") or "") == "hidden_factor"]
    skip_count = 0
    for row in hidden_outcomes:
        selected = str(row.get("selected_option") or "")
        signal = _dict(row.get("interaction_turn_signal"))
        structured = _dict(signal.get("structured_payload"))
        if selected in skip_values or structured.get("confidence") == "uncertain":
            skip_count += 1
    latest = hidden_outcomes[-1] if hidden_outcomes else {}
    return {
        "skip_count": skip_count,
        "recent_skip": bool(latest and str(latest.get("selected_option") or "") in skip_values),
    }


def _target_attributes(domain: str) -> list[str]:
    return {
        "career": ["resource_index", "risk_index", "authority", "resource", "career_bias"],
        "wealth": ["risk_index", "stability_index", "wealth", "output", "wealth_bias"],
        "relationship": ["risk_index", "stability_index", "relationship_bias", "family_drag"],
        "health": ["risk_index", "recovery_index", "health_bias", "pressure_tolerance"],
        "timing": ["luck_index", "execution_index", "event_trigger_sensitivity"],
        "decision": ["choice_quality_index", "risk_index", "execution_index"],
    }.get(domain, ["luck_index", "stability_index"])


def _question_prompt(domain: str) -> str:
    return {
        "career": "过去遇到责任加重时，更常见的是压力转成资质/平台，还是转成消耗和不稳定？",
        "wealth": "遇到赚钱机会或合作分配时，更常见的是顺利转化，还是波动和损耗更明显？",
        "relationship": "关系压力出现时，更常见的是能沟通调整，还是反复拉扯和家庭牵制？",
        "health": "压力上来时，身心节律更容易稳住，还是作息、情绪或体力先波动？",
        "timing": "遇到阶段变化时，你更常主动抓机会，还是多半被环境推动？",
        "decision": "关键选择出现时，你更常快速行动，还是容易拖延、反复或错过窗口？",
    }.get(domain, "这类情况在现实中更常表现为顺势推进，还是压力和波动更明显？")


def _answer_options(domain: str) -> list[dict[str, str]]:
    common = [
        {"value": "uncertain", "label": "不确定"},
        {"value": "default", "label": "先按中性看"},
        {"value": "skip", "label": "暂不回答"},
    ]
    primary = {
        "career": [
            {"value": "pressure_to_resource", "label": "压力会逼出学习/资质/平台能力"},
            {"value": "pressure_to_volatility", "label": "压力更容易变成消耗或不稳定"},
        ],
        "wealth": [
            {"value": "opportunity_to_gain", "label": "机会较容易转成收益"},
            {"value": "opportunity_to_risk", "label": "波动、损耗或分配问题更明显"},
        ],
        "relationship": [
            {"value": "relationship_adjusts", "label": "能沟通调整"},
            {"value": "relationship_repeats", "label": "容易反复拉扯"},
        ],
        "health": [
            {"value": "rhythm_stable", "label": "压力下仍能稳住节律"},
            {"value": "rhythm_fluctuates", "label": "压力下节律先波动"},
        ],
    }.get(domain, [
        {"value": "active_capture", "label": "更容易主动抓住"},
        {"value": "passive_or_missed", "label": "更容易被动或错过"},
    ])
    return primary + common


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
