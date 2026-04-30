from __future__ import annotations

from typing import Any, Dict, List, Tuple


BAZI_FEATURE_LAYER_VERSION = "v19.p84.bazi_feature_spine.v1"
FEATURE_SCHEMA_VERSION = "v19.p84.bazi_feature_schema.v1"


FEATURE_PROFILES: Dict[str, Dict[str, Any]] = {
    "portrait.option.strength.strong_capacity": {
        "feature_id": "feature.strength.capacity_supported",
        "title": "日主承载有支持",
        "domain": "strength",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_strength_assessment", "q_useful_god_candidates"],
        "answer_boundary": "只能解释强弱承载证据，不直接断身强身弱。",
    },
    "portrait.option.strength.weak_capacity": {
        "feature_id": "feature.strength.capacity_needs_support",
        "title": "日主承载需复核",
        "domain": "strength",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_strength_assessment", "q_useful_god_candidates"],
        "answer_boundary": "适合解释承载不足的证据门槛，不输出喜忌硬结论。",
    },
    "portrait.option.strength.balanced_capacity": {
        "feature_id": "feature.strength.borderline_capacity",
        "title": "日主承载处在边界",
        "domain": "strength",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_strength_assessment", "q_day_master_month_anchor", "q_useful_god_candidates"],
        "answer_boundary": "只能给出强弱候选证据和继续复核方向。",
    },
    "portrait.option.useful_god.support_capacity": {
        "feature_id": "feature.useful_god.support_path_candidate",
        "title": "用神候选偏向扶身路径",
        "domain": "useful_god",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_useful_god_candidates", "q_strength_assessment"],
        "answer_boundary": "只能说候选扶身路径，不直接说喜什么五行。",
    },
    "portrait.option.useful_god.output_flow": {
        "feature_id": "feature.useful_god.output_flow_candidate",
        "title": "用神候选偏向输出通关",
        "domain": "useful_god",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_useful_god_candidates", "q_ten_god_focus"],
        "answer_boundary": "只能解释输出通关候选，不当作固定喜忌。",
    },
    "portrait.option.useful_god.constraint_order": {
        "feature_id": "feature.useful_god.constraint_order_candidate",
        "title": "用神候选偏向约束成序",
        "domain": "useful_god",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_useful_god_candidates", "q_pattern_structure"],
        "answer_boundary": "只能解释约束是否成序的证据门槛。",
    },
    "portrait.option.useful_god.not_ready": {
        "feature_id": "feature.useful_god.evidence_gate_not_ready",
        "title": "用神忌神证据门槛未闭合",
        "domain": "useful_god",
        "source_layer": ["natal", "hidden", "time"],
        "answer_readiness": "boundary_ready",
        "question_hooks": ["q_useful_god_candidates", "q_favorable_elements_boundary", "q_unfavorable_god_boundary"],
        "answer_boundary": "证据不足时必须输出候选和边界，不输出喜忌硬断。",
    },
    "portrait.option.ten_god.visible_relation": {
        "feature_id": "feature.ten_god.visible_relation_active",
        "title": "十神透出关系较明显",
        "domain": "ten_god",
        "source_layer": ["natal"],
        "answer_readiness": "ready",
        "question_hooks": ["q_ten_god_focus", "q_ten_god_metadata"],
        "answer_boundary": "十神透出只说明关系来源，不单独推出结果。",
    },
    "portrait.option.ten_god.hidden_relation": {
        "feature_id": "feature.ten_god.hidden_relation_active",
        "title": "十神藏干关系较重",
        "domain": "ten_god",
        "source_layer": ["hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_hidden_stem_role", "q_ten_god_metadata"],
        "answer_boundary": "藏干只补足来源层，不替代结果判断。",
    },
    "portrait.option.ten_god.mechanism_path": {
        "feature_id": "feature.ten_god.mechanism_path_pending",
        "title": "十神机制路径待验",
        "domain": "ten_god",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_ten_god_focus", "kbq_ten_god_interaction_boundary"],
        "answer_boundary": "十神同见不等于成机制，需要同层作用路径。",
    },
    "portrait.option.wealth.visible": {
        "feature_id": "feature.wealth.visible_material",
        "title": "财星素材可见",
        "domain": "wealth",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_income_stability", "q_income_factors", "kbq_wealth_access_route"],
        "answer_boundary": "只说明财富结构素材是否可观察，不断财富事件。",
    },
    "portrait.option.wealth.hidden": {
        "feature_id": "feature.wealth.hidden_or_weak_material",
        "title": "财星弱或隐藏",
        "domain": "wealth",
        "source_layer": ["hidden", "time"],
        "answer_readiness": "boundary_ready",
        "question_hooks": ["q_income_stability", "q_income_factors"],
        "answer_boundary": "只能解释财星来源层和可见度，不补造财富结论。",
    },
    "portrait.option.wealth.output_generates": {
        "feature_id": "feature.wealth.output_to_wealth_path",
        "title": "食伤生财路径候选",
        "domain": "wealth",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_income_path_structure", "kbq_income_path_route", "q_income_stability"],
        "answer_boundary": "只能解释输出到财富的结构路径，不断收入结果。",
    },
    "portrait.option.wealth.stable_access": {
        "feature_id": "feature.wealth.stable_access_candidate",
        "title": "收入结构较稳候选",
        "domain": "wealth",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "ready",
        "question_hooks": ["q_income_stability", "q_income_path_structure"],
        "answer_boundary": "只能讨论稳定性结构，不断发财破财。",
    },
    "portrait.option.wealth.constrained": {
        "feature_id": "feature.wealth.visible_but_constrained",
        "title": "财星可见但受牵制",
        "domain": "wealth",
        "source_layer": ["natal", "hidden", "time"],
        "answer_readiness": "ready",
        "question_hooks": ["q_income_stability", "q_signal_combination", "kbq_income_collision_route"],
        "answer_boundary": "适合解释收入稳定性和牵制路径，不输出财富事件。",
    },
    "portrait.option.wealth.volatility": {
        "feature_id": "feature.wealth.volatility_candidate",
        "title": "财富结构波动候选",
        "domain": "wealth",
        "source_layer": ["natal", "time"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_income_stability", "q_signal_combination"],
        "answer_boundary": "只能说结构波动候选，不断具体得失。",
    },
    "portrait.option.branch.natal_tension": {
        "feature_id": "feature.branch.natal_relation_tension",
        "title": "本命地支关系张力",
        "domain": "branch",
        "source_layer": ["natal"],
        "answer_readiness": "ready",
        "question_hooks": ["q_branch_relation_detail", "q_time_vs_natal_relation"],
        "answer_boundary": "只能解释关系发生在哪一层，不从关系名直接断吉凶。",
    },
    "portrait.option.branch.time_triggered": {
        "feature_id": "feature.branch.time_triggered_relation",
        "title": "时间层触发地支关系",
        "domain": "branch",
        "source_layer": ["time"],
        "answer_readiness": "ready",
        "question_hooks": ["q_time_vs_natal_relation", "kbq_time_vs_natal_relation", "q_time_context_boundary"],
        "answer_boundary": "时间层只作触发背景，不能改写本命结构。",
    },
    "portrait.option.branch.quiet": {
        "feature_id": "feature.branch.relation_quiet",
        "title": "地支关系相对安静",
        "domain": "branch",
        "source_layer": ["natal"],
        "answer_readiness": "boundary_ready",
        "question_hooks": ["q_structure_overview", "q_branch_relation_detail"],
        "answer_boundary": "没有明确关系时不补造冲合刑害。",
    },
    "portrait.option.time.active_trigger": {
        "feature_id": "feature.time.active_trigger_context",
        "title": "大运流年触发明显",
        "domain": "time",
        "source_layer": ["time"],
        "answer_readiness": "ready",
        "question_hooks": ["q_time_context_boundary", "q_luck_flow_layers", "q_time_vs_natal_relation"],
        "answer_boundary": "只解释时间背景如何触发结构，不断应期。",
    },
    "portrait.option.time.background": {
        "feature_id": "feature.time.background_only",
        "title": "时间层仅作背景",
        "domain": "time",
        "source_layer": ["time"],
        "answer_readiness": "boundary_ready",
        "question_hooks": ["q_time_context_boundary", "q_time_not_inference"],
        "answer_boundary": "时间词不能直接读成结果。",
    },
    "portrait.option.time.natal_priority": {
        "feature_id": "feature.time.natal_structure_priority",
        "title": "本命结构优先",
        "domain": "time",
        "source_layer": ["natal", "time"],
        "answer_readiness": "ready",
        "question_hooks": ["q_structure_overview", "q_time_context_boundary"],
        "answer_boundary": "先稳定本命结构，再看时间触发。",
    },
    "portrait.option.pattern.index_available": {
        "feature_id": "feature.pattern.index_candidate",
        "title": "格局索引已建立",
        "domain": "pattern",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_pattern_structure", "q_month_command_anchor"],
        "answer_boundary": "格局名只是索引，必须继续验证成格破格。",
    },
    "portrait.option.pattern.formation_review": {
        "feature_id": "feature.pattern.formation_review",
        "title": "成格条件待验",
        "domain": "pattern",
        "source_layer": ["natal", "hidden"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_pattern_structure", "q_ten_god_focus"],
        "answer_boundary": "只能解释成格条件，不把格局名当命运结论。",
    },
    "portrait.option.pattern.breaking_review": {
        "feature_id": "feature.pattern.breaking_review",
        "title": "破格条件待验",
        "domain": "pattern",
        "source_layer": ["natal", "time"],
        "answer_readiness": "review_ready",
        "question_hooks": ["q_pattern_structure", "q_branch_relation_detail"],
        "answer_boundary": "只能解释破格复核路径，不输出结果断语。",
    },
    "portrait.option.pattern.not_primary": {
        "feature_id": "feature.pattern.not_primary",
        "title": "暂不以格局为主",
        "domain": "pattern",
        "source_layer": ["natal"],
        "answer_readiness": "boundary_ready",
        "question_hooks": ["q_structure_overview", "q_ten_god_focus"],
        "answer_boundary": "格局证据不集中时先回到强弱、十神和地支关系。",
    },
}


DOMAIN_BUCKETS = {
    "strength": "strength_useful_god",
    "useful_god": "strength_useful_god",
    "wealth": "income_stability",
    "branch": "branch_relation",
    "time": "time_context",
    "pattern": "pattern_structure",
    "ten_god": "metadata",
}


def build_bazi_feature_layer(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    portrait = dict(agent_data.get("structure_portrait") or {})
    runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    knowledge_context = dict(agent_data.get("knowledge_context") or {})
    feedback = dict(agent_data.get("portrait_calibration_feedback") or {})
    features = _features_from_portrait(portrait, runtime_context, knowledge_context, feedback)
    if not features:
        features = _features_from_rule_graph(runtime_context)
    features = _dedupe_features(features)
    features.sort(key=lambda row: (float(row.get("priority_score") or 0), float(row.get("confidence") or 0), str(row.get("feature_id") or "")), reverse=True)
    question_bias = _question_bias(features)
    return {
        "ok": True,
        "version": BAZI_FEATURE_LAYER_VERSION,
        "schema_version": FEATURE_SCHEMA_VERSION,
        "status": "ready" if features else "no_features",
        "runtime_scope": "bazi_feature_spine_context_only_no_rule_mutation",
        "feature_count": len(features),
        "features": features[:16],
        "top_features": _top_feature_summary(features),
        "question_bias": question_bias,
        "portrait_projection": _portrait_projection(features),
        "feedback_summary": _compact_feedback(feedback),
        "cleanup": {
            "legacy_portrait_question_hooks": "deprecated_in_main_chain",
            "active_spine": "bazi_feature_layer",
            "rule_mutation": False,
            "answer_mutation": False,
        },
        "guardrails": [
            "BAZI_FEATURE_SPINE",
            "FEATURES_BRIDGE_RULES_PORTRAIT_QUESTIONS_ANSWERS",
            "PORTRAIT_IS_FEATURE_PROJECTION",
            "USER_FEEDBACK_CALIBRATES_FEATURE_CONFIDENCE_ONLY",
            "NO_RULE_MUTATION_FROM_FEEDBACK",
            "NO_HARD_VERDICT",
            "NO_DOMAIN_RESULT_PREDICTION",
        ],
    }


def compact_bazi_feature_layer(layer: Dict[str, Any], *, limit: int = 8) -> Dict[str, Any]:
    if not isinstance(layer, dict) or not layer:
        return {}
    features = [dict(row) for row in layer.get("features") or [] if isinstance(row, dict)]
    return {
        "version": layer.get("version") or BAZI_FEATURE_LAYER_VERSION,
        "schema_version": layer.get("schema_version") or FEATURE_SCHEMA_VERSION,
        "status": layer.get("status") or "",
        "runtime_scope": layer.get("runtime_scope") or "",
        "feature_count": int(layer.get("feature_count") or len(features)),
        "top_features": list(layer.get("top_features") or [])[:limit],
        "question_bias": dict(layer.get("question_bias") or {}),
        "portrait_projection": dict(layer.get("portrait_projection") or {}),
        "features": [
            {
                "feature_id": row.get("feature_id") or "",
                "title": row.get("title") or "",
                "domain": row.get("domain") or "",
                "confidence": row.get("confidence"),
                "feature_state": row.get("feature_state") or "",
                "answer_readiness": row.get("answer_readiness") or "",
                "question_hooks": list(row.get("question_hooks") or [])[:5],
                "evidence": list(row.get("evidence") or [])[:4],
                "knowledge_units": list(row.get("knowledge_units") or [])[:6],
                "rule_paths": list(row.get("rule_paths") or [])[:6],
                "portrait_projection": list(row.get("portrait_projection") or [])[:4],
                "answer_boundary": row.get("answer_boundary") or "",
            }
            for row in features[:limit]
        ],
        "guardrails": [
            "USE_FEATURE_SPINE_FOR_ROUTING",
            "FEATURE_CONTEXT_ONLY",
            "NO_RULE_MUTATION_FROM_FEEDBACK",
        ],
    }


def bazi_feature_layer_to_prompt_context(layer: Dict[str, Any], *, limit: int = 8) -> Dict[str, Any]:
    compact = compact_bazi_feature_layer(layer, limit=limit)
    compact["runtime_scope"] = "llm_prompt_bazi_feature_context_only"
    compact["guardrails"] = [
        "USE_BAZI_FEATURES_AS_ANALYSIS_SPINE",
        "EXPLAIN_FEATURE_EVIDENCE_AND_BOUNDARY",
        "DO_NOT_TURN_FEATURES_INTO_HARD_FORTUNE",
        "NO_INTERNAL_IDS_IN_USER_TEXT",
    ]
    return compact


def _features_from_portrait(
    portrait: Dict[str, Any],
    runtime_context: Dict[str, Any],
    knowledge_context: Dict[str, Any],
    feedback: Dict[str, Any],
) -> List[Dict[str, Any]]:
    paths = _runtime_paths(runtime_context)
    knowledge_ids = _knowledge_ids(knowledge_context)
    by_option = dict(feedback.get("by_option") or {}) if isinstance(feedback.get("by_option"), dict) else {}
    features = []
    for label in [dict(row) for row in portrait.get("labels") or [] if isinstance(row, dict)]:
        selected = dict(label.get("selected_option") or {})
        option_id = str(selected.get("option_id") or "")
        profile = FEATURE_PROFILES.get(option_id)
        if not profile:
            continue
        feature = _feature_from_label(label, selected, profile, paths, knowledge_ids, by_option)
        features.append(feature)
    return features


def _feature_from_label(
    label: Dict[str, Any],
    selected: Dict[str, Any],
    profile: Dict[str, Any],
    paths: List[Dict[str, Any]],
    knowledge_ids: List[str],
    by_option: Dict[str, Any],
) -> Dict[str, Any]:
    option_id = str(selected.get("option_id") or "")
    domain = str(profile.get("domain") or label.get("family") or "structure")
    matching_paths = _matching_paths(paths, domain)
    label_knowledge = [str(item) for item in label.get("knowledge_evidence_ids") or [] if str(item)]
    if not label_knowledge:
        label_knowledge = _matching_knowledge_ids(knowledge_ids, domain)
    option_feedback = dict(by_option.get(option_id) or {})
    feedback_count = int(option_feedback.get("count") or 0)
    analyst_count = int(option_feedback.get("analyst_count") or 0)
    option_score = float(selected.get("score") or 0)
    confidence = _clamp(
        float(label.get("compiled_score") or label.get("score") or 0) * 0.50
        + float(label.get("posterior_confidence") or label.get("confidence") or 0) * 0.28
        + option_score * 0.22
        + min(0.08, feedback_count * 0.025 + analyst_count * 0.035)
    )
    state = str(selected.get("selection_state") or label.get("portrait_assertion_state") or "system_suggested")
    if state == "system_suggested" and feedback_count:
        state = "feedback_observed"
    readiness = str(profile.get("answer_readiness") or "review_ready")
    priority = confidence * 100 + len(matching_paths) * 3 + len(label_knowledge) * 1.5
    if state == "analyst_confirmed":
        priority += 16
    elif state == "user_confirmed":
        priority += 10
    elif state == "rejected":
        priority -= 32
        readiness = "rejected"
    return {
        "feature_id": profile.get("feature_id") or option_id,
        "schema_version": FEATURE_SCHEMA_VERSION,
        "title": profile.get("title") or selected.get("title") or "",
        "domain": domain,
        "source_layer": list(profile.get("source_layer") or []),
        "source_label_id": label.get("label_id") or "",
        "source_option_id": option_id,
        "selected_option": {
            "option_id": option_id,
            "title": selected.get("title") or "",
            "selection_state": state,
            "score": selected.get("score"),
        },
        "evidence": _feature_evidence(label, selected, matching_paths),
        "evidence_refs": _dedupe([*(label.get("evidence_refs") or []), *(selected.get("evidence_refs") or [])])[:8],
        "rule_paths": [str(row.get("path_id") or row.get("knowledge_id") or "") for row in matching_paths if row.get("path_id") or row.get("knowledge_id")][:8],
        "knowledge_units": _dedupe([*label_knowledge, *[str(row.get("knowledge_id") or "") for row in matching_paths if row.get("knowledge_id")]])[:8],
        "confidence": round(confidence, 3),
        "priority_score": round(priority, 3),
        "feature_state": state,
        "answer_readiness": readiness,
        "question_hooks": _dedupe([*(profile.get("question_hooks") or []), *(label.get("question_hooks") or [])])[:8],
        "answer_boundary": profile.get("answer_boundary") or label.get("answer_boundary") or "只作命理特征解释，不输出结果断语。",
        "portrait_projection": _portrait_projection_for_feature(profile, selected),
        "feedback": {
            "count": feedback_count,
            "analyst_count": analyst_count,
            "average_rating": round(float(option_feedback.get("average_rating") or 0), 3),
            "runtime_scope": "feature_confidence_feedback_only_no_rule_mutation",
        },
        "runtime_scope": "bazi_feature_context_only_no_rule_mutation",
        "guardrails": [
            "FEATURE_IS_INTERMEDIATE_SIGNAL",
            "FEATURE_CAN_ROUTE_QUESTIONS_AND_ANSWERS",
            "FEATURE_IS_NOT_FORTUNE_VERDICT",
            "NO_RULE_MUTATION",
        ],
    }


def _features_from_rule_graph(runtime_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    features = []
    for row in _runtime_paths(runtime_context)[:8]:
        domain = str(row.get("domain") or row.get("topic_lane") or "structure")
        feature_id = f"feature.route.{domain}.{str(row.get('knowledge_id') or row.get('path_id') or 'path').replace('.', '_')}"
        features.append(
            {
                "feature_id": feature_id,
                "schema_version": FEATURE_SCHEMA_VERSION,
                "title": row.get("title") or row.get("knowledge_id") or "规则路径特征",
                "domain": _normalize_domain(domain),
                "source_layer": ["rule_graph"],
                "evidence": [row.get("reason") or "规则图路径命中"],
                "evidence_refs": [row.get("knowledge_id") or row.get("path_id") or ""],
                "rule_paths": [row.get("path_id") or ""],
                "knowledge_units": [row.get("knowledge_id") or ""],
                "confidence": round(min(0.78, float(row.get("score") or 0) / 100), 3),
                "priority_score": row.get("score") or 0,
                "feature_state": "rule_graph_suggested",
                "answer_readiness": "review_ready",
                "question_hooks": [],
                "answer_boundary": "规则图路径只能作为命理特征候选，不直接生成断语。",
                "portrait_projection": [],
                "runtime_scope": "bazi_feature_context_only_no_rule_mutation",
                "guardrails": ["FEATURE_IS_INTERMEDIATE_SIGNAL", "NO_RULE_MUTATION"],
            }
        )
    return features


def _question_bias(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    bucket_boosts: Dict[str, float] = {}
    question_boosts: Dict[str, float] = {}
    top_ids = []
    for feature in features:
        if str(feature.get("feature_state") or "") == "rejected":
            continue
        domain = str(feature.get("domain") or "")
        bucket = DOMAIN_BUCKETS.get(domain, domain or "structure")
        confidence = float(feature.get("confidence") or 0)
        readiness = str(feature.get("answer_readiness") or "")
        ready_bonus = 4 if readiness in {"ready", "boundary_ready"} else 2
        state_bonus = 6 if str(feature.get("feature_state") or "") == "analyst_confirmed" else 4 if str(feature.get("feature_state") or "") == "user_confirmed" else 0
        boost = confidence * 18 + ready_bonus + state_bonus
        bucket_boosts[bucket] = max(bucket_boosts.get(bucket, 0), boost)
        for key in feature.get("question_hooks") or []:
            if key:
                question_boosts[str(key)] = max(question_boosts.get(str(key), 0), boost + 3)
        if feature.get("feature_id"):
            top_ids.append(str(feature.get("feature_id")))
    ordered_questions = [key for key, _value in sorted(question_boosts.items(), key=lambda row: row[1], reverse=True)]
    ordered_buckets = [key for key, _value in sorted(bucket_boosts.items(), key=lambda row: row[1], reverse=True)]
    return {
        "version": BAZI_FEATURE_LAYER_VERSION,
        "runtime_scope": "feature_driven_question_ranking_only_no_result_mutation",
        "bucket_boosts": {key: round(value, 3) for key, value in bucket_boosts.items()},
        "question_boosts": {key: round(value, 3) for key, value in question_boosts.items()},
        "recommended_question_keys": ordered_questions[:8],
        "route_bucket_order": ordered_buckets[:8],
        "dominant_feature_ids": _dedupe(top_ids)[:8],
        "feature_driven": True,
    }


def _top_feature_summary(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "feature_id": row.get("feature_id") or "",
            "title": row.get("title") or "",
            "domain": row.get("domain") or "",
            "confidence": row.get("confidence"),
            "answer_readiness": row.get("answer_readiness") or "",
            "feature_state": row.get("feature_state") or "",
        }
        for row in features[:8]
    ]


def _portrait_projection(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for feature in features[:8]:
        for title in feature.get("portrait_projection") or []:
            rows.append(
                {
                    "feature_id": feature.get("feature_id") or "",
                    "domain": feature.get("domain") or "",
                    "title": title,
                    "confidence": feature.get("confidence"),
                    "feature_state": feature.get("feature_state") or "",
                }
            )
    return {
        "status": "ready" if rows else "empty",
        "runtime_scope": "feature_to_portrait_projection_only",
        "items": rows[:12],
    }


def _feature_evidence(label: Dict[str, Any], selected: Dict[str, Any], paths: List[Dict[str, Any]]) -> List[str]:
    evidence = []
    detail = str(selected.get("detail") or "")
    statement = str(label.get("candidate_statement") or "")
    if detail:
        evidence.append(detail)
    if statement:
        evidence.append(statement)
    for path in paths[:2]:
        reason = str(path.get("reason") or path.get("title") or path.get("knowledge_id") or "")
        if reason:
            evidence.append(reason)
    return _dedupe(evidence)[:5]


def _portrait_projection_for_feature(profile: Dict[str, Any], selected: Dict[str, Any]) -> List[str]:
    title = str(selected.get("title") or profile.get("title") or "")
    domain = str(profile.get("domain") or "")
    if not title:
        return []
    return [f"{_domain_label(domain)}：{title}"]


def _runtime_paths(runtime_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    paths = [dict(row) for row in runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    if paths:
        return paths
    route = dict(runtime_context.get("knowledge_route") or {})
    return [dict(row) for row in route.get("selected_paths") or [] if isinstance(row, dict)]


def _knowledge_ids(knowledge_context: Dict[str, Any]) -> List[str]:
    out = []
    for row in knowledge_context.get("items") or []:
        if isinstance(row, dict) and row.get("knowledge_id"):
            out.append(str(row.get("knowledge_id")))
    return _dedupe(out)


def _matching_paths(paths: List[Dict[str, Any]], domain: str) -> List[Dict[str, Any]]:
    normalized = _normalize_domain(domain)
    out = []
    for row in paths:
        blob = " ".join(str(row.get(key) or "") for key in ["domain", "topic_lane", "knowledge_id", "candidate_rule_id", "title"])
        if normalized in _normalize_domain(blob) or _domain_token(normalized) in blob:
            out.append(row)
    return out[:6]


def _matching_knowledge_ids(knowledge_ids: List[str], domain: str) -> List[str]:
    token = _domain_token(domain)
    return [item for item in knowledge_ids if token and token in item][:6]


def _normalize_domain(value: str) -> str:
    text = str(value or "")
    if "wealth" in text or "income" in text:
        return "wealth"
    if "strength" in text or "day_master" in text or "useful_god" in text:
        return "strength" if "useful_god" not in text else "useful_god"
    if "branch" in text or "relation" in text:
        return "branch"
    if "time" in text or "luck" in text:
        return "time"
    if "pattern" in text:
        return "pattern"
    if "ten_god" in text or "interaction" in text:
        return "ten_god"
    return text or "structure"


def _domain_token(domain: str) -> str:
    return {
        "wealth": "wealth",
        "strength": "strength",
        "useful_god": "useful_god",
        "branch": "branch",
        "time": "time",
        "pattern": "pattern",
        "ten_god": "ten_god",
    }.get(str(domain or ""), str(domain or ""))


def _domain_label(domain: str) -> str:
    return {
        "wealth": "财富",
        "strength": "强弱",
        "useful_god": "用神",
        "branch": "地支",
        "time": "时间",
        "pattern": "格局",
        "ten_god": "十神",
    }.get(str(domain or ""), "结构")


def _compact_feedback(feedback: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "version": feedback.get("version") or "",
        "status": feedback.get("status") or "",
        "count": int(feedback.get("count") or 0),
        "option_count": len(feedback.get("by_option") or {}) if isinstance(feedback.get("by_option"), dict) else 0,
        "runtime_scope": "feature_feedback_summary_only_no_rule_mutation",
    }


def _dedupe_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for feature in features:
        feature_id = str(feature.get("feature_id") or "")
        if not feature_id:
            continue
        current = merged.get(feature_id)
        if not current:
            merged[feature_id] = dict(feature)
            continue
        current["confidence"] = round(max(float(current.get("confidence") or 0), float(feature.get("confidence") or 0)), 3)
        current["priority_score"] = round(max(float(current.get("priority_score") or 0), float(feature.get("priority_score") or 0)), 3)
        current["evidence"] = _dedupe(list(current.get("evidence") or []) + list(feature.get("evidence") or []))[:6]
        current["rule_paths"] = _dedupe(list(current.get("rule_paths") or []) + list(feature.get("rule_paths") or []))[:8]
        current["knowledge_units"] = _dedupe(list(current.get("knowledge_units") or []) + list(feature.get("knowledge_units") or []))[:8]
    return list(merged.values())


def _dedupe(items: List[Any]) -> List[str]:
    out: List[str] = []
    for item in items:
        text = str(item or "")
        if text and text not in out:
            out.append(text)
    return out


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))
