from __future__ import annotations

from v30.contracts import BaziQuestionAnchor, FeatureEvidence, MainlineState, StructureState
from v30.interaction_constraints import answer_constraints_for_question
from v30.knowledge import KnowledgeRulePortraitSignal
from v30.semantics import semantic_projection_for_question


QUESTION_RECOMMENDER_VERSION = "v30.question_recommender.v1"
USER_QUESTION_INTENTS = {
    "ask_user_career_direction",
    "ask_user_wealth_tendency",
    "ask_user_relationship_pattern",
    "ask_user_timing_pressure",
    "ask_user_decision_blindspot",
}
CALIBRATION_INTENTS = {
    "discover_hidden_factor_amplifier",
    "review_useful_god_candidate_paths",
    "clarify_practical_reading_priority",
}


def recommend_questions(
    anchors: list[BaziQuestionAnchor],
    *,
    structure: StructureState,
    mainline: MainlineState,
    evidence: list[FeatureEvidence],
    active_policy_versions: dict[str, str],
    knowledge_rule_portrait_signals: list[KnowledgeRulePortraitSignal] | None = None,
    macro_dimension_signals: list[dict[str, object]] | None = None,
    question_policy: dict[str, object] | None = None,
    hidden_factor_state: dict[str, object] | None = None,
    question_outcomes: list[dict[str, object]] | None = None,
    central_brain_context: dict[str, object] | None = None,
    practical_reading_context: dict[str, object] | None = None,
    model_signal_summary: dict[str, object] | None = None,
    latent_question_strategy: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    evidence_by_id = {row.evidence_id: row for row in evidence}
    signals = knowledge_rule_portrait_signals or []
    macro_signals = macro_dimension_signals or []
    context_completion_guard_active = any(
        anchor.missing_requirements
        and (
            anchor.question_id == "q_v30_time_context_boundary"
            or anchor.intent_id == "confirm_missing_time_context"
        )
        for anchor in anchors
    )
    rows = [
        _score_anchor(
            anchor,
            structure=structure,
            mainline=mainline,
            evidence_by_id=evidence_by_id,
            active_policy_versions=active_policy_versions,
            knowledge_rule_portrait_signals=signals,
            macro_dimension_signals=macro_signals,
            question_policy=question_policy or {},
            hidden_factor_state=hidden_factor_state or {},
            question_outcomes=question_outcomes or [],
            central_brain_context=central_brain_context or {},
            practical_reading_context=practical_reading_context or {},
            model_signal_summary=model_signal_summary or {},
            latent_question_strategy=latent_question_strategy or {},
            context_completion_guard_active=context_completion_guard_active,
        )
        for anchor in anchors
    ]
    sorted_rows = sorted(
        rows,
        key=lambda row: (-float(row.get("_rank_score", row["score"])), _stage_priority(str(row["stage"])), str(row["question_id"])),
    )
    for row in sorted_rows:
        row.pop("_rank_score", None)
    return sorted_rows


def _score_anchor(
    anchor: BaziQuestionAnchor,
    *,
    structure: StructureState,
    mainline: MainlineState,
    evidence_by_id: dict[str, FeatureEvidence],
    active_policy_versions: dict[str, str],
    knowledge_rule_portrait_signals: list[KnowledgeRulePortraitSignal],
    macro_dimension_signals: list[dict[str, object]],
    question_policy: dict[str, object],
    hidden_factor_state: dict[str, object],
    question_outcomes: list[dict[str, object]],
    central_brain_context: dict[str, object],
    practical_reading_context: dict[str, object],
    model_signal_summary: dict[str, object],
    latent_question_strategy: dict[str, object],
    context_completion_guard_active: bool,
) -> dict[str, object]:
    score = 0.35
    reasons: list[str] = []
    domains = {evidence_by_id[eid].domain for eid in anchor.evidence_ids if eid in evidence_by_id}
    if anchor.missing_requirements and anchor.intent_id not in {
        "discover_hidden_factor_amplifier",
        "clarify_practical_reading_priority",
    }:
        score += 0.28
        reasons.append("missing_requirement_blocks_downstream_claims")
    if anchor.intent_id == "confirm_missing_time_context":
        score += 0.18
        reasons.append("context_completion_internal_gate")
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        score += 0.16
        reasons.append("hidden_factor_requires_dialogue_discovery")
    if anchor.intent_id == "clarify_practical_reading_priority":
        score += 0.13
        reasons.append("practical_reading_requires_domain_priority")
    if anchor.intent_id in USER_QUESTION_INTENTS:
        score += 0.24
        reasons.append("user_question_direct_answer_entry")
        if (
            context_completion_guard_active
            and central_brain_context.get("question_strategy") != "context_first_question_strategy"
            and not _has_explicit_topic_boost(question_policy, topic="hidden_factor", threshold=1.1)
        ):
            score += 0.42
            reasons.append("customer_question_entry_before_internal_context_completion")
    if mainline.quality_gate != "passed":
        score += 0.14
        reasons.append(f"mainline_quality_gate:{mainline.quality_gate}")
    if "useful_god" in domains:
        score += 0.12
        reasons.append("candidate_path_requires_evidence_review")
        if _has_signal(knowledge_rule_portrait_signals, "rule"):
            score += 0.05
            reasons.append("rule_signal_blocks_fixed_useful_god")
    if "ten_god" in domains and _has_signal(knowledge_rule_portrait_signals, "knowledge"):
        score += 0.03
        reasons.append("knowledge_signal_supports_ten_god_context")
    if anchor.intent_id == "discover_hidden_factor_amplifier" and _has_signal(knowledge_rule_portrait_signals, "portrait"):
        score += 0.05
        reasons.append("portrait_signal_requires_feedback_calibration")
    if anchor.intent_id == "discover_hidden_factor_amplifier" and hidden_factor_state.get("amplifier_candidate"):
        score += 0.08
        reasons.append("persisted_hidden_factor_state:amplifier_candidate")
    if anchor.intent_id == "discover_hidden_factor_amplifier" and hidden_factor_state.get("status") == "expired":
        score += 0.04
        reasons.append("persisted_hidden_factor_state:expired_requires_refresh")
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        alignment_score = _hidden_factor_alignment_score(hidden_factor_state)
        if alignment_score:
            score += min(0.07, alignment_score * 0.07)
            reasons.append(f"hidden_factor_event_alignment:{alignment_score}")
    if "branch_relation" in domains:
        score += 0.08
        reasons.append("structure_dynamic_relation_present")
    if _has_rule_evidence(evidence_by_id, anchor.evidence_ids):
        score += 0.04
        reasons.append("rule_evidence_bound_to_question")
    if structure.state.startswith("partial"):
        score += 0.06
        reasons.append(f"structure_state:{structure.state}")
    if structure.path_scores.get("mechanism_path_count", 0.0):
        score += 0.04
        reasons.append("mechanism_paths_scored")
    if structure.path_scores.get("dynamic_path_count", 0.0):
        score += 0.03
        reasons.append("dynamic_graph_paths_scored")
    stage = _stage(anchor)
    topic = _topic(anchor, domains)
    macro_matches = _macro_matches(anchor.intent_id, macro_dimension_signals)
    if macro_matches:
        score += min(0.06, 0.02 * len(macro_matches))
        reasons.append("macro_dimension_context:" + ",".join(macro_matches))
    practical_score, practical_reasons, practical_focus = _practical_reading_adjustment(
        intent_id=anchor.intent_id,
        topic=topic,
        practical_reading_context=practical_reading_context,
    )
    if practical_score:
        score += practical_score
        reasons.extend(practical_reasons)
    outcome_score, outcome_reasons = _question_outcome_adjustment(
        question_id=anchor.question_id,
        topic=topic,
        question_outcomes=question_outcomes,
    )
    if outcome_score:
        score += outcome_score
        reasons.extend(outcome_reasons)
    uncertainty_score, uncertainty_reasons = _interaction_uncertainty_adjustment(
        topic=topic,
        hidden_factor_state=hidden_factor_state,
        question_outcomes=question_outcomes,
        structure=structure,
    )
    if uncertainty_score:
        score += uncertainty_score
        reasons.extend(uncertainty_reasons)
    brain_score, brain_reasons = _central_brain_adjustment(
        anchor,
        stage=stage,
        topic=topic,
        central_brain_context=central_brain_context,
    )
    if brain_score:
        score += brain_score
        reasons.extend(brain_reasons)
    model_score, model_reasons = _model_signal_question_adjustment(
        topic=topic,
        model_signal_summary=model_signal_summary,
    )
    if model_score:
        score += model_score
        reasons.extend(model_reasons)
    latent_score, latent_reasons = _latent_question_strategy_adjustment(
        anchor,
        topic=topic,
        latent_question_strategy=latent_question_strategy,
    )
    if latent_score:
        score += latent_score
    reasons.extend(latent_reasons)
    latent_policy_score, latent_policy_reasons = _latent_bazi_attribute_policy_adjustment(
        anchor,
        topic=topic,
        question_policy=question_policy,
    )
    if latent_policy_score:
        score += latent_policy_score
        reasons.extend(latent_policy_reasons)
    if (
        context_completion_guard_active
        and anchor.intent_id == "discover_hidden_factor_amplifier"
        and not _has_explicit_topic_boost(question_policy, topic="hidden_factor", threshold=1.1)
    ):
        score -= 0.16
        reasons.append("context_completion_before_latent_calibration")
    question_policy_version = active_policy_versions.get("question_policy", "")
    if question_policy_version:
        score += 0.03
        reasons.append(f"question_policy:{question_policy_version}")
    base_policy_weight = _question_policy_weight(
        question_policy,
        question_id=anchor.question_id,
        intent_id=anchor.intent_id,
        stage=stage,
        topic=topic,
        context_completion_guard_active=context_completion_guard_active,
    )
    event_policy_weight, event_policy_reasons = _hidden_factor_event_policy_weight(
        question_policy,
        hidden_factor_state=hidden_factor_state,
        intent_id=anchor.intent_id,
        topic=topic,
    )
    policy_weight = round(max(0.1, min(2.0, base_policy_weight * event_policy_weight)), 3)
    if policy_weight != 1.0:
        score *= policy_weight
        reasons.append(f"question_policy_weight:{policy_weight}")
    reasons.extend(event_policy_reasons)
    if not reasons:
        reasons.append("baseline_mainline_review")
    expected_information_gain = _expected_information_gain(
        anchor,
        stage=stage,
        topic=topic,
        reasons=reasons,
        question_outcomes=question_outcomes,
        practical_focus=practical_focus,
    )
    row = {
        "question_id": anchor.question_id,
        "intent_id": anchor.intent_id,
        "anchor_id": anchor.anchor_id,
        "candidate_source": "question_recommender_candidate",
        "decision_owner": "dialogue_brain",
        "score": round(min(score, 1.0), 3),
        "_rank_score": round(score, 3),
        "stage": stage,
        "topic": topic,
        "evidence_ids": anchor.evidence_ids,
        "reasons": reasons,
        "interaction_type": _interaction_type(anchor.intent_id),
        "answer_mode": "direct_answer" if anchor.intent_id in USER_QUESTION_INTENTS else "calibration_feedback",
        "question_value": _question_value(stage, topic),
        "expected_information_gain": expected_information_gain,
        "semantic_projection": {},
        "question_score_components": {
            "base_score": 0.35,
            "policy_weight": policy_weight,
            "expected_information_gain": expected_information_gain.get("score"),
            "reason_count": len(reasons),
            "semantic_weight_slot": "",
            "boundary": "question_score_components_feed_dialogue_training_not_chart_facts",
        },
        "options": _structured_options(stage, topic, practical_focus),
        "answer_constraints": answer_constraints_for_question(stage=stage, topic=topic),
        "latent_question_strategy": _question_latent_strategy_projection(
            topic=topic,
            latent_question_strategy=latent_question_strategy,
        ),
        "quality_contract": {
            "version": "v30.high_value_question.v1",
            "purpose": _question_purpose(stage, topic),
            "optimizes_for": [
                "reduce_uncertainty",
                "calibrate_practical_reading",
                "select_next_question",
            ],
            "reading_focus": practical_focus,
            "boundary": "question_quality_guides_dialogue_not_chart_fact",
        },
        "policy_version": question_policy_version,
        "policy_weight": policy_weight,
        "boundary": "question_recommender_outputs_candidates_dialogue_brain_selects_customer_turn",
    }
    semantic_projection = semantic_projection_for_question(row)
    row["semantic_projection"] = semantic_projection
    components = row["question_score_components"]
    if isinstance(components, dict):
        components["semantic_weight_slot"] = semantic_projection.get("weight_slot", "")
        components["macro_domain"] = semantic_projection.get("macro_domain", "")
    return row


def _stage(anchor: BaziQuestionAnchor) -> str:
    if anchor.intent_id in USER_QUESTION_INTENTS:
        return "user_question_entry"
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "dialogue_discovery"
    if anchor.intent_id == "clarify_practical_reading_priority":
        return "practical_reading_followup"
    if anchor.missing_requirements:
        return "context_completion"
    if anchor.intent_id == "review_useful_god_candidate_paths":
        return "candidate_review"
    return "mainline_review"


def _stage_priority(stage: str) -> int:
    return {
        "context_completion": -1,
        "user_question_entry": 0,
        "dialogue_discovery": 1,
        "candidate_review": 2,
        "practical_reading_followup": 3,
        "mainline_review": 4,
    }.get(stage, 9)


def _topic(anchor: BaziQuestionAnchor, domains: set[str]) -> str:
    if anchor.intent_id == "ask_user_career_direction":
        return "career"
    if anchor.intent_id == "ask_user_wealth_tendency":
        return "wealth"
    if anchor.intent_id == "ask_user_relationship_pattern":
        return "relationship"
    if anchor.intent_id == "ask_user_timing_pressure":
        return "timing"
    if anchor.intent_id == "ask_user_decision_blindspot":
        return "decision"
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "hidden_factor"
    if anchor.intent_id == "clarify_practical_reading_priority":
        return "practical_reading"
    if "time_context" in domains or anchor.missing_requirements:
        return "time_context"
    if "useful_god" in domains:
        return "useful_god"
    if "branch_relation" in domains:
        return "structure_dynamic"
    return "mainline"


def _question_value(stage: str, topic: str) -> str:
    if stage == "user_question_entry":
        return {
            "career": "answer_career_direction",
            "wealth": "answer_wealth_tendency",
            "relationship": "answer_relationship_pattern",
            "timing": "answer_current_timing_pressure",
            "decision": "answer_decision_blindspot",
        }.get(topic, "answer_user_bazi_question")
    if stage == "context_completion":
        return "unlock_downstream_reading"
    if topic == "hidden_factor":
        return "validate_event_year_or_repeated_state"
    if topic == "practical_reading":
        return "focus_customer_priority_domain"
    if topic == "useful_god":
        return "review_candidate_path_before_answer"
    if topic == "structure_dynamic":
        return "resolve_dynamic_structure_relation"
    return "confirm_mainline_relevance"


def _question_purpose(stage: str, topic: str) -> str:
    purpose_by_value = {
        "answer_career_direction": "Answer the user's career direction question directly, then recommend a follow-up.",
        "answer_wealth_tendency": "Answer the user's wealth tendency question directly, then recommend a follow-up.",
        "answer_relationship_pattern": "Answer the user's relationship pattern question directly, then recommend a follow-up.",
        "answer_current_timing_pressure": "Answer the user's current timing pressure question directly, then recommend a follow-up.",
        "answer_decision_blindspot": "Answer the user's decision blind spot question directly, then recommend a follow-up.",
        "answer_user_bazi_question": "Answer a user-facing Bazi question directly.",
        "unlock_downstream_reading": "Complete required context before making practical claims.",
        "validate_event_year_or_repeated_state": "Check whether user feedback aligns with event-year and repeated-state hypotheses.",
        "focus_customer_priority_domain": "Select the practical life domain that should drive the next answer.",
        "review_candidate_path_before_answer": "Keep useful-god and candidate-path language bounded before explanation.",
        "resolve_dynamic_structure_relation": "Clarify whether dynamic branch relations should affect follow-up.",
        "confirm_mainline_relevance": "Confirm that the selected mainline is useful for the user session.",
    }
    return purpose_by_value[_question_value(stage, topic)]


def _expected_information_gain(
    anchor: BaziQuestionAnchor,
    *,
    stage: str,
    topic: str,
    reasons: list[str],
    question_outcomes: list[dict[str, object]],
    practical_focus: list[str],
) -> dict[str, object]:
    answered_ids = {
        str(row.get("question_id"))
        for row in question_outcomes
        if isinstance(row, dict) and row.get("constraint_valid", True) is not False
    }
    value = 0.32
    if stage == "context_completion":
        value += 0.28
    if topic in {"hidden_factor", "practical_reading"}:
        value += 0.18
    if anchor.missing_requirements:
        value += 0.12
    if anchor.question_id in answered_ids:
        value -= 0.22
    if any(reason.startswith("central_brain_") for reason in reasons):
        value += 0.04
    if practical_focus and topic == "practical_reading":
        value += 0.08
    return {
        "score": round(max(0.05, min(1.0, value)), 3),
        "primary_gain": _question_value(stage, topic),
        "reduces": _reduces(stage, topic),
        "practical_focus_domains": practical_focus,
        "uses_answer_for": [
            "update_question_dialogue_graph",
            "refresh_answer_context",
            "emit_training_signal",
        ],
        "boundary": "expected_information_gain_is_question_policy_signal_not_chart_fact",
    }


def _structured_options(stage: str, topic: str, practical_focus: list[str]) -> list[dict[str, object]]:
    if topic == "practical_reading":
        domains = practical_focus or ["career", "wealth", "relationship", "health"]
        return [
            _option(f"domain:{domain}", _domain_label(domain), domain, "domain_focus")
            for domain in domains[:4]
        ]
    if topic in {"career", "wealth", "relationship", "timing", "decision"}:
        labels = {
            "career": [
                ("career:direction", "先看方向", "direction"),
                ("career:pressure", "先看压力", "pressure"),
                ("career:timing", "先看节奏", "timing"),
            ],
            "wealth": [
                ("wealth:earning", "先看赚钱方式", "earning"),
                ("wealth:risk", "先看风险边界", "risk"),
                ("wealth:timing", "先看财务节奏", "timing"),
            ],
            "relationship": [
                ("relationship:pattern", "先看相处模式", "pattern"),
                ("relationship:tension", "先看反复矛盾", "tension"),
                ("relationship:timing", "先看关系节奏", "timing"),
            ],
            "timing": [
                ("timing:current", "先看当前阶段", "current"),
                ("timing:pressure", "先看压力来源", "pressure"),
                ("timing:choice", "先看选择窗口", "choice"),
            ],
            "decision": [
                ("decision:blindspot", "先看盲点", "blindspot"),
                ("decision:risk", "先看风险", "risk"),
                ("decision:action", "先看行动建议", "action"),
            ],
        }
        return [_option(option_id, label, value, "answer_focus") for option_id, label, value in labels.get(topic, [])]
    if topic == "hidden_factor":
        return [
            _option("hidden_factor:has_repeated_state", "有反复状态", "has_repeated_state", "feedback_signal"),
            _option("hidden_factor:has_event_year", "有明显年份", "has_event_year", "feedback_signal"),
            _option("hidden_factor:not_sure", "暂不确定", "not_sure", "feedback_signal"),
            _option("hidden_factor:default", "先按中性看", "default", "feedback_signal"),
            _option("hidden_factor:skip", "暂不回答", "skip", "feedback_signal"),
        ]
    if topic == "useful_god":
        return [
            _option("useful_god:review_path", "只复核路径", "review_path", "review_mode"),
            _option("useful_god:compare_candidates", "比较候选", "compare_candidates", "review_mode"),
        ]
    if stage == "context_completion":
        return [
            _option("time_context:confirm", "补充时间信息", "confirm", "context_completion"),
            _option("time_context:skip", "先不补充", "skip", "context_completion"),
        ]
    return []


def _option(option_id: str, label: str, value: str, option_type: str) -> dict[str, object]:
    return {
        "option_id": option_id,
        "label": label,
        "value": value,
        "option_type": option_type,
        "boundary": "structured_option_guides_question_strategy_not_chart_fact",
    }


def _domain_label(domain: str) -> str:
    return {
        "career": "事业",
        "wealth": "财务",
        "relationship": "关系",
        "health": "健康",
        "timing": "时机",
        "decision": "选择",
    }.get(domain, domain)


def _reduces(stage: str, topic: str) -> list[str]:
    if stage == "context_completion":
        return ["missing_time_or_timing_context", "unsupported_downstream_claims"]
    if topic == "hidden_factor":
        return ["hidden_factor_uncertainty", "event_year_alignment_uncertainty"]
    if topic == "practical_reading":
        return ["domain_priority_uncertainty", "generic_answer_risk"]
    if topic in {"career", "wealth", "relationship", "timing", "decision"}:
        return [f"{topic}_answer_uncertainty", "next_followup_selection"]
    if topic == "useful_god":
        return ["fixed_useful_god_verdict_risk", "candidate_path_uncertainty"]
    return ["mainline_relevance_uncertainty"]


def _has_signal(signals: list[KnowledgeRulePortraitSignal], signal_type: str) -> bool:
    return any(signal.signal_type == signal_type for signal in signals)


def _has_rule_evidence(evidence_by_id: dict[str, FeatureEvidence], evidence_ids: list[str]) -> bool:
    return any(evidence_by_id[eid].domain == "rule" for eid in evidence_ids if eid in evidence_by_id)


def _macro_matches(intent_id: str, macro_dimension_signals: list[dict[str, object]]) -> list[str]:
    rows: set[str] = set()
    for signal in macro_dimension_signals:
        hooks = signal.get("question_hooks", [])
        if not isinstance(hooks, list) or intent_id not in {str(row) for row in hooks}:
            continue
        domain = str(signal.get("domain", ""))
        if domain:
            rows.add(domain)
    return sorted(rows)


def _practical_reading_adjustment(
    *,
    intent_id: str,
    topic: str,
    practical_reading_context: dict[str, object],
) -> tuple[float, list[str], list[str]]:
    if not practical_reading_context:
        return 0.0, [], []
    gaps = practical_reading_context.get("question_gaps", [])
    if not isinstance(gaps, list):
        gaps = []
    focus_domains = _priority_domains(gaps)
    if intent_id == "clarify_practical_reading_priority":
        if focus_domains:
            return (
                0.1,
                ["practical_reading_gap:" + ",".join(focus_domains)],
                focus_domains,
            )
        return 0.03, ["practical_reading_ready_for_priority_check"], []
    if topic == "time_context" and any(str(row.get("domain")) == "timing" for row in gaps if isinstance(row, dict)):
        return 0.05, ["practical_reading_gap:timing"], ["timing"]
    return 0.0, [], focus_domains[:2]


def _priority_domains(gaps: list[object]) -> list[str]:
    rows = [
        (
            str(row.get("domain")),
            float(row.get("priority_score", 0.0)),
        )
        for row in gaps
        if isinstance(row, dict) and row.get("domain")
    ]
    rows = sorted(rows, key=lambda row: (-row[1], row[0]))
    return [domain for domain, _score in rows[:3]]


def _question_policy_weight(
    payload: dict[str, object],
    *,
    question_id: str,
    intent_id: str,
    stage: str,
    topic: str,
    context_completion_guard_active: bool,
) -> float:
    weights = payload.get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = (
        _lookup_weight(weights, "question_weights", question_id)
        * _lookup_weight(weights, "intent_weights", intent_id)
        * _lookup_weight(weights, "stage_weights", stage)
        * _lookup_weight(weights, "topic_weights", topic)
        * _model_signal_question_policy_weight(
            weights,
            stage=stage,
            topic=topic,
            context_completion_guard_active=context_completion_guard_active,
        )
    )
    return round(max(0.1, min(value, 2.0)), 3)


def _model_signal_question_policy_weight(
    weights: dict[object, object],
    *,
    stage: str,
    topic: str,
    context_completion_guard_active: bool,
) -> float:
    if stage != "user_question_entry":
        return 1.0
    if context_completion_guard_active:
        return 1.0
    policy = weights.get("model_signal_question_policy")
    if not isinstance(policy, dict):
        return 1.0
    topic_weights = policy.get("topic_weights")
    if not isinstance(topic_weights, dict):
        return 1.0
    value = topic_weights.get(topic, topic_weights.get("*", 1.0))
    if isinstance(value, int | float):
        return float(value)
    return 1.0


def _has_explicit_topic_boost(policy: dict[str, object], *, topic: str, threshold: float) -> bool:
    weights = policy.get("weights")
    if not isinstance(weights, dict):
        return False
    topic_weights = weights.get("topic_weights")
    if not isinstance(topic_weights, dict):
        return False
    value = topic_weights.get(topic)
    return isinstance(value, int | float) and float(value) >= threshold


def _latent_question_strategy_adjustment(
    anchor: BaziQuestionAnchor,
    *,
    topic: str,
    latent_question_strategy: dict[str, object],
) -> tuple[float, list[str]]:
    if topic != "hidden_factor" or anchor.intent_id != "discover_hidden_factor_amplifier":
        return 0.0, []
    if not latent_question_strategy:
        return 0.0, []
    need_score = _strategy_float(latent_question_strategy, "need_score", 0.0)
    ask_now = latent_question_strategy.get("ask_now") is True
    if ask_now:
        return min(0.035, need_score * 0.06), [
            f"latent_question_strategy:ask_now:{need_score}",
            f"latent_question_target_domain:{latent_question_strategy.get('target_domain', '')}",
        ]
    return -0.18, ["latent_question_strategy:not_needed_now"]


def _latent_bazi_attribute_policy_adjustment(
    anchor: BaziQuestionAnchor,
    *,
    topic: str,
    question_policy: dict[str, object],
) -> tuple[float, list[str]]:
    if topic != "hidden_factor" or anchor.intent_id != "discover_hidden_factor_amplifier":
        return 0.0, []
    weights = question_policy.get("weights")
    if not isinstance(weights, dict):
        return 0.0, []
    policy = weights.get("latent_bazi_attribute_policy")
    if not isinstance(policy, dict) or policy.get("can_tune_question_strategy") is not True:
        return 0.0, []
    if policy.get("can_tune_chart_facts") is True:
        return 0.0, ["latent_bazi_attribute_policy:chart_fact_tuning_blocked"]
    question_need_weight = _strategy_float(policy, "question_need_weight", 1.0)
    delta = max(0.0, min(0.025, (question_need_weight - 1.0) * 0.8))
    if not delta:
        return 0.0, []
    return delta, [
        f"latent_bazi_attribute_policy:question_need:{round(question_need_weight, 3)}",
        "latent_bazi_attribute_policy:personalization_not_chart_fact",
    ]


def _question_latent_strategy_projection(
    *,
    topic: str,
    latent_question_strategy: dict[str, object],
) -> dict[str, object]:
    if topic != "hidden_factor" or not latent_question_strategy:
        return {}
    return {
        "version": str(latent_question_strategy.get("version") or ""),
        "ask_now": bool(latent_question_strategy.get("ask_now")),
        "need_score": _strategy_float(latent_question_strategy, "need_score", 0.0),
        "target_domain": str(latent_question_strategy.get("target_domain") or ""),
        "target_state_tags": _strategy_list(latent_question_strategy.get("target_state_tags")),
        "target_latent_attributes": _strategy_list(latent_question_strategy.get("target_latent_attributes")),
        "question_prompt": str(latent_question_strategy.get("question_prompt") or ""),
        "skip_policy": latent_question_strategy.get("skip_policy", {}) if isinstance(latent_question_strategy.get("skip_policy"), dict) else {},
        "training_routes": _strategy_list(latent_question_strategy.get("training_routes")),
        "boundary": "question_projection_uses_latent_strategy_without_forcing_questionnaire_flow",
    }


def _strategy_float(payload: dict[str, object], key: str, default: float) -> float:
    try:
        return round(float(payload.get(key, default)), 3)
    except (TypeError, ValueError):
        return default


def _strategy_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]


def _hidden_factor_event_policy_weight(
    payload: dict[str, object],
    *,
    hidden_factor_state: dict[str, object],
    intent_id: str,
    topic: str,
) -> tuple[float, list[str]]:
    if topic != "hidden_factor" or intent_id != "discover_hidden_factor_amplifier":
        return 1.0, []
    weights = payload.get("weights")
    if not isinstance(weights, dict):
        return 1.0, []
    policy = weights.get("hidden_factor_event_policy", {})
    if not isinstance(policy, dict) or not hidden_factor_state:
        return 1.0, []
    status = str(hidden_factor_state.get("status") or "")
    if status == "conflicting":
        weight = _policy_float(policy, "conflict_multiplier", 0.88)
        return round(max(0.1, min(2.0, weight)), 3), ["hidden_factor_event_policy:conflict_priority"]
    if status == "user_denied":
        weight = _policy_float(policy, "denial_multiplier", 0.82)
        return round(max(0.1, min(2.0, weight)), 3), ["hidden_factor_event_policy:user_denial_priority"]
    if status == "expired":
        weight = _policy_float(policy, "expired_refresh_multiplier", 1.015)
        return round(max(0.1, min(2.0, weight)), 3), ["hidden_factor_event_policy:refresh_expired_feedback"]
    alignment_score = _hidden_factor_alignment_score(hidden_factor_state)
    min_alignment = _policy_float(policy, "min_alignment_score", 0.45)
    if hidden_factor_state.get("amplifier_candidate") and alignment_score >= min_alignment:
        candidate = _policy_float(policy, "candidate_alignment_multiplier", 1.02)
        time_layer = _policy_float(policy, "time_layer_alignment_multiplier", 1.0)
        max_positive = _policy_float(policy, "max_positive_multiplier", 1.06)
        weight = min(max_positive, candidate * time_layer)
        return round(max(0.1, min(2.0, weight)), 3), [f"hidden_factor_event_policy:aligned_candidate:{alignment_score}"]
    return 1.0, []


def _policy_float(policy: dict[str, object], key: str, default: float) -> float:
    try:
        return float(policy.get(key, default))
    except (TypeError, ValueError):
        return default


def _question_outcome_adjustment(
    *,
    question_id: str,
    topic: str,
    question_outcomes: list[dict[str, object]],
) -> tuple[float, list[str]]:
    if not question_outcomes:
        return 0.0, []
    latest_for_question = next(
        (
            row
            for row in reversed(question_outcomes)
            if isinstance(row, dict) and str(row.get("question_id")) == question_id
        ),
        {},
    )
    if latest_for_question and latest_for_question.get("constraint_valid") is False:
        return 0.62, ["invalid_input_retry_required", "question_outcome_invalid_not_suppressed"]
    answered_ids = {
        str(row.get("question_id"))
        for row in question_outcomes
        if isinstance(row, dict) and row.get("constraint_valid", True) is not False
    }
    answered_topics = {str(row.get("topic")) for row in question_outcomes if isinstance(row, dict)}
    if question_id in answered_ids:
        return -0.95, ["question_outcome_answered", "question_outcome_answered_suppressed"]
    if topic and topic in answered_topics:
        return 0.035, [f"question_outcome_topic_followup:{topic}"]
    return 0.0, []


def _interaction_uncertainty_adjustment(
    *,
    topic: str,
    hidden_factor_state: dict[str, object],
    question_outcomes: list[dict[str, object]],
    structure: StructureState,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if topic == "hidden_factor":
        status = str(hidden_factor_state.get("status") or "")
        if status in {"dialogue_in_progress", "expired"}:
            score += 0.12
            reasons.append("next_question_uncertainty:hidden_factor_needs_structured_feedback")
        if _latest_invalid_topic(question_outcomes) == "hidden_factor":
            score += 0.18
            reasons.append("next_question_retry:hidden_factor_invalid_structured_payload")
    if topic == "structure_dynamic" and structure.path_scores.get("dynamic_path_count", 0.0):
        score += 0.1
        reasons.append("next_question_uncertainty:dynamic_structure_path_needs_review")
    if topic == "useful_god" and not _has_negative_evidence(question_outcomes):
        score += 0.07
        reasons.append("next_question_uncertainty:useful_god_candidate_needs_counterevidence")
    return min(score, 0.35), reasons


def _latest_invalid_topic(question_outcomes: list[dict[str, object]]) -> str:
    for row in reversed(question_outcomes):
        if isinstance(row, dict) and row.get("constraint_valid") is False:
            return str(row.get("topic") or "")
    return ""


def _has_negative_evidence(question_outcomes: list[dict[str, object]]) -> bool:
    for row in question_outcomes:
        if not isinstance(row, dict):
            continue
        payload = row.get("structured_payload")
        if isinstance(payload, dict) and payload.get("negative_evidence"):
            return True
        tags = row.get("feedback_tags")
        if isinstance(tags, list) and any("negative" in str(tag) or "counter" in str(tag) for tag in tags):
            return True
    return False


def _interaction_type(intent_id: str) -> str:
    if intent_id in USER_QUESTION_INTENTS:
        return "user_question"
    if intent_id in CALIBRATION_INTENTS:
        return "calibration_probe"
    return "internal_review"


def _hidden_factor_alignment_score(hidden_factor_state: dict[str, object]) -> float:
    try:
        return round(float(hidden_factor_state.get("alignment_score") or 0.0), 3)
    except (TypeError, ValueError):
        return 0.0


def _central_brain_adjustment(
    anchor: BaziQuestionAnchor,
    *,
    stage: str,
    topic: str,
    central_brain_context: dict[str, object],
) -> tuple[float, list[str]]:
    unknown_context = central_brain_context.get("unknown_context", [])
    feedback_slots = central_brain_context.get("feedback_slots", [])
    strategy = str(central_brain_context.get("question_strategy") or "")
    if not isinstance(unknown_context, list):
        unknown_context = []
    if not isinstance(feedback_slots, list):
        feedback_slots = []
    score = 0.0
    reasons: list[str] = []
    unknown = {str(row) for row in unknown_context}
    slots = {str(row) for row in feedback_slots}
    if "time_layer_boundary" in unknown and topic == "time_context":
        score += 0.05
        reasons.append("central_brain_unknown_context:time_layer_boundary")
    if "hidden_factor_confirmation" in unknown and anchor.intent_id == "discover_hidden_factor_amplifier":
        score += 0.04
        reasons.append("central_brain_unknown_context:hidden_factor_confirmation")
    if "time_context_feedback" in slots and stage == "context_completion":
        score += 0.02
        reasons.append("central_brain_feedback_slot:time_context_feedback")
    if "hidden_factor_boundary_feedback" in slots and topic == "hidden_factor":
        score += 0.02
        reasons.append("central_brain_feedback_slot:hidden_factor_boundary_feedback")
    if strategy:
        reasons.append(f"central_brain_question_strategy:{strategy}")
    return score, reasons


def _model_signal_question_adjustment(
    *,
    topic: str,
    model_signal_summary: dict[str, object],
) -> tuple[float, list[str]]:
    if topic not in {"career", "wealth", "relationship", "timing", "decision", "hidden_factor"}:
        return 0.0, []
    bands = model_signal_summary.get("energy_bands", [])
    if not isinstance(bands, list):
        return 0.0, []
    dominant_families = [
        str(row.get("family"))
        for row in bands
        if isinstance(row, dict) and str(row.get("energy_band") or "") in {"high", "medium"}
    ][:3]
    if not dominant_families:
        return 0.0, []
    focus_by_family = {
        "wealth": {"wealth": 0.14, "decision": 0.04},
        "authority": {"career": 0.12, "decision": 0.08, "timing": 0.04},
        "output": {"timing": 0.11, "career": 0.05, "decision": 0.04},
        "resource": {"relationship": 0.08, "career": 0.06, "hidden_factor": 0.04},
        "self": {"relationship": 0.07, "decision": 0.06, "career": 0.04},
    }
    score = 0.0
    reasons: list[str] = []
    for family in dominant_families:
        family_focus = focus_by_family.get(family, {})
        if topic not in family_focus:
            continue
        score += family_focus[topic]
        reasons.append(f"model_signal_question_focus:{family}->{topic}")
    return min(score, 0.18), reasons


def _lookup_weight(weights: dict[object, object], bucket: str, key: str) -> float:
    raw_bucket = weights.get(bucket)
    if not isinstance(raw_bucket, dict):
        return 1.0
    value = raw_bucket.get(key, raw_bucket.get("*", 1.0))
    if isinstance(value, int | float):
        return float(value)
    return 1.0
