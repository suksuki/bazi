from __future__ import annotations

from dataclasses import replace

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, rank_question_rows
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QUESTION_LABELS, QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload


QUESTION_KEY_BY_DOMAIN = {
    "strength": "q_strength_assessment",
    "wealth": "q_income_stability",
    "career": "q_career_structure",
    "ten_god": "q_ten_god_focus",
    "branch": "q_branch_relation_detail",
    "time": "q_time_layer_context",
    "element": "q_element_balance",
    "useful_god": "q_useful_god_candidates",
    "pattern": "q_pattern_structure",
    "relationship": "q_relationship_structure",
    "health": "q_health_balance_boundary",
}

CONTROL_DOMAIN = {
    "control.day_master_strength": "strength",
    "control.shang_guan_jian_guan": "career",
    "control.wealth_capacity": "wealth",
    "control.pattern_status": "pattern",
}

LATENT_SCENARIO_DOMAIN = {
    "latent.wealth_change": "wealth",
    "latent.career_transition": "career",
    "latent.relationship_shift": "relationship",
    "latent.relocation_environment": "time",
    "latent.stress_recovery": "health",
    "latent.action_result": "strength",
}


def recommend_decision_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    practitioner_selections: tuple[dict[str, object], ...] = (),
    latent_event_answers: tuple[dict[str, object], ...] = (),
    limit: int = 10,
) -> tuple[QuestionCandidate, ...]:
    rows = []
    for decision in decision_report.get("decisions", ()):
        if not isinstance(decision, dict):
            continue
        domain = str(decision.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        title = _question_title(decision)
        feature_ids = _feature_ids(decision, feature_layer, domain)
        candidate = QuestionCandidate(
            question_key=key,
            title=title,
            domain=domain,
            score=round(float(decision.get("score", 0.0)) + _role_boost(str(decision.get("role", ""))), 3),
            source_feature_ids=feature_ids,
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
        rows.extend(_secondary_questions(decision, feature_layer))
        rows.extend(_knowledge_rule_questions(decision, feature_layer))
    rows.extend(_practitioner_selection_questions(practitioner_selections, decision_report, feature_layer))
    rows.extend(_latent_event_questions(latent_event_answers, decision_report, feature_layer))
    if not rows:
        rows = [_fallback_question(feature_layer)]
    rows = _dedupe_questions(rows)
    return tuple(rank_question_rows(tuple(rows), QuestionRankingPolicy(
        policy_id="v20.question_ranking.dynamic_decision",
        source="dynamic_rule_decisions",
        status="active",
        max_adjustment=0.0,
    ))[:limit])


def _dedupe_questions(rows: list[QuestionCandidate]) -> list[QuestionCandidate]:
    by_key: dict[str, QuestionCandidate] = {}
    for row in rows:
        current = by_key.get(row.question_key)
        if current is None or row.score > current.score:
            by_key[row.question_key] = row
    return list(by_key.values())


def resolve_requested_question(
    questions: tuple[QuestionCandidate, ...],
    question_key: str,
    feature_layer: FeatureLayer,
) -> QuestionCandidate:
    if question_key:
        for question in questions:
            if question.question_key == question_key:
                return question
        explicit = _explicit_question(question_key, feature_layer)
        if explicit is not None:
            return explicit
    if questions:
        return questions[0]
    return _fallback_question(feature_layer)


def _aligned(candidate: QuestionCandidate) -> QuestionCandidate | None:
    alignment = align_question_candidate(
        question_key=candidate.question_key,
        domain=candidate.domain,
        title=candidate.title,
        source_feature_ids=candidate.source_feature_ids,
        boundary=candidate.boundary,
    )
    if not alignment.ok:
        return None
    return replace(
        candidate,
        alignment_status=alignment.status,
        bazi_focus=alignment.focus,
        alignment_score=alignment.score,
    )


def _question_title(decision: dict[str, object]) -> str:
    label = str(decision.get("label", "命理结构"))
    domain = str(decision.get("domain", ""))
    rule_key = str(decision.get("rule_key", ""))
    if rule_key == "rule.strength.capacity":
        status = str(decision.get("status", ""))
        if status == "needs_support":
            return "日主需要扶身时，先看印星、比劫还是通关？"
        if status == "borderline":
            return "日主强弱接近分界时，先裁决哪类证据？"
        if status == "supported":
            return "日主有支撑后，适合先看泄秀、财星还是官杀？"
        return "这个八字日主偏强还是偏弱，适合先看什么？"
    if rule_key == "rule.wealth.material":
        return "财运主要从哪些位置和十神线索看？"
    if rule_key == "rule.wealth.capacity_gate":
        return "财星可见时，日主能不能承接？"
    if rule_key == "rule.wealth.peer_competition":
        return "财运上先看机会，还是先看比劫竞争和承载力？"
    if rule_key == "rule.career.resource_buffer":
        return "事业压力中，印星能不能形成缓冲？"
    if rule_key == "rule.ten_god.source_layers":
        return "明透和藏干里，哪些十神最值得先看？"
    if rule_key == "rule.element.distribution":
        return "五行偏向会让这个盘更需要哪种平衡？"
    if rule_key == "rule.useful_god.candidate_gate":
        if "扶身" in label:
            return "用神方向要先扶身，还是另有通关路径？"
        if "泄秀" in label:
            return "用神方向适合先看泄秀还是财星通道？"
        if "财星通道" in label:
            return "用神方向能不能走财星通道？"
        if "官杀约束" in label:
            return "用神方向要不要先看官杀约束？"
        if "扶泄裁决" in label:
            return "用神方向先扶身还是先泄秀？"
        return "这个盘下一步适合先找哪类用神方向？"
    if rule_key == "rule.pattern.review_gate":
        if "墓库藏气" in label:
            return "格局判断要先复核哪一处墓库藏气？"
        return "格局判断要先看月令、透干还是十神组合？"
    if rule_key == "rule.ten_god.shang_guan_jian_guan":
        status = str(decision.get("status", ""))
        if status == "weakened_by_resource":
            return "伤官见官是否被印星缓冲？"
        return "伤官见官会怎样影响事业表达和规则？"
    if rule_key == "rule.ten_god.guan_sha_mixed":
        return "事业压力来自规则、竞争，还是角色混杂？"
    if rule_key == "rule.ten_god.output_to_wealth":
        return "食伤输出能不能形成财运通道？"
    if rule_key == "rule.wealth.output_wealth_capacity_chain":
        if "承载关" in label:
            return "食伤生财时，日主承接够不够？"
        if "承载需裁决" in label:
            return "食伤生财要先看承载还是通道？"
        return "食伤生财能否形成稳定财星通道？"
    if rule_key == "rule.career.output_authority_resource_chain":
        return "事业上官星、伤官和印星谁是主导？"
    if rule_key == "rule.branch.relations":
        return "地支冲合刑害会先影响哪一类事情？"
    if rule_key == "rule.relationship.interaction_projection":
        return "关系结构里更明显的是互动、约束还是承接？"
    if rule_key == "rule.health.balance_boundary":
        return "五行偏枯主要提示哪种平衡压力？"
    if rule_key == "rule.time.trigger":
        return "流年大运会先牵动事业、财运还是关系？"
    if domain == "strength":
        return "先看日主强弱与承载力吗？"
    if domain == "wealth":
        return "财运主要从哪些命局线索看？"
    if domain == "career":
        return f"{label}是否会成为事业主线？"
    if domain == "branch":
        return "地支冲合刑害会先影响哪一类事情？"
    if domain == "time":
        return "流年大运会先牵动哪一类事情？"
    return f"{label}应如何进入八字测算？"


def _feature_ids(decision: dict[str, object], feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    ids = tuple(str(row) for row in decision.get("feature_ids", ()) if str(row))
    if ids:
        return ids
    fallback = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if fallback:
        return fallback[:4]
    return tuple(feature.feature_id for feature in feature_layer.features[:3])


def _boundary(domain: str) -> str:
    if domain == "wealth":
        return "只解释财星来源、承载力和结构路径，不直接判断收益结果。"
    if domain == "career":
        return "只解释十神角色、格局候选和事业结构，不直接判断职位升降。"
    if domain == "relationship":
        return "只解释十神来源、地支互动和承接边界，不直接判断关系事件。"
    if domain == "health":
        return "只解释五行平衡和结构压力边界，不输出诊断或处理建议。"
    if domain == "time":
        return "时间层只作为触发背景，不输出无证据支撑的具体时间点。"
    return f"只解释{domain_label(domain)}的结构证据和裁决边界，不输出固定吉凶。"


def _role_boost(role: str) -> float:
    if role == "mainline_candidate":
        return 0.12
    if role == "foundation":
        return 0.07
    if role == "time_context":
        return 0.05
    return 0.0


def _fallback_question(feature_layer: FeatureLayer) -> QuestionCandidate:
    ids = tuple(feature.feature_id for feature in feature_layer.features[:4])
    return QuestionCandidate(
        question_key="q_structure_overview",
        title="这个八字先抓哪条结构主线？",
        domain="branch",
        score=0.3,
        source_feature_ids=ids,
        boundary="只做结构主线梳理，不输出固定吉凶。",
        measurement_topic=domain_label("branch"),
        measurement_stage=measurement_stage("branch"),
        **dimension_payload("branch"),
    )


def _secondary_questions(decision: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    domain = str(decision.get("domain", ""))
    role = str(decision.get("role", ""))
    rows: list[QuestionCandidate] = []
    if domain == "time":
        rows.append(_make_question(
            "q_time_relation_triggers",
            "这一步大运流年最容易牵动哪条主线？",
            "time",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "wealth":
        rows.append(_make_question(
            "q_income_factors",
            "财运的机会和限制分别在哪里？",
            "wealth",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "element":
        rows.append(_make_question(
            "q_element_support_pressure",
            "五行偏向会带来什么优势和压力？",
            "element",
            float(decision.get("score", 0.0)) - 0.02,
            decision,
            feature_layer,
        ))
    if domain == "ten_god" or ".ten_god." in str(decision.get("rule_key", "")):
        rows.append(_make_question(
            "q_hidden_stem_role",
            "藏干里有哪些容易被忽略的命理线索？",
            "ten_god",
            float(decision.get("score", 0.0)) - (0.01 if role == "foundation_context" else 0.02),
            decision,
            feature_layer,
        ))
    return [row for row in (_aligned(item) for item in rows) if row is not None]


def _knowledge_rule_questions(decision: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    domain = str(decision.get("domain", ""))
    for ref_index, ref in enumerate(decision.get("knowledge_rule_refs", ())[:2]):
        if not isinstance(ref, dict):
            continue
        for output in ref.get("question_outputs", ())[:2]:
            if not isinstance(output, dict):
                continue
            question_key = str(output.get("question_key", ""))
            title = _normalize_knowledge_question_title(str(output.get("title", "")), domain)
            output_domain = str(output.get("domain", "")) or domain
            if not question_key or not title:
                continue
            candidate = QuestionCandidate(
                question_key=question_key,
                title=title,
                domain=output_domain,
                score=round(float(decision.get("score", 0.0)) + 0.04 - ref_index * 0.01, 3),
                source_feature_ids=_feature_ids(decision, feature_layer, output_domain),
                boundary=_boundary(output_domain),
                measurement_topic=domain_label(output_domain),
                measurement_stage=measurement_stage(output_domain),
                **dimension_payload(output_domain),
            )
            aligned = _aligned(candidate)
            if aligned:
                rows.append(aligned)
    return rows


def _normalize_knowledge_question_title(title: str, domain: str) -> str:
    text = title.strip()
    if not text:
        return ""
    if any(token in text for token in ("feature", "hook", "metadata", "应如何进入")):
        return ""
    if domain == "wealth" and "财" not in text and "收入" not in text:
        return ""
    if domain == "career" and not any(token in text for token in ("事业", "规则", "压力", "表达", "印星", "官杀")):
        return ""
    if domain == "branch" and "冲合刑害" not in text:
        return "地支冲合刑害会先影响哪一类事情？"
    return text


def _practitioner_selection_questions(
    selections: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, selection in enumerate(selections[:4]):
        control_key = str(selection.get("control_key", ""))
        option = str(selection.get("option", ""))
        domain = CONTROL_DOMAIN.get(control_key, "branch")
        question_key, title = _practitioner_question(control_key, option)
        source_decision_keys = tuple(str(row) for row in selection.get("source_decision_keys", ()) if str(row))
        source_decision = _source_decision_for_selection(decisions, source_decision_keys, domain)
        candidate = QuestionCandidate(
            question_key=question_key,
            title=title,
            domain=domain,
            score=round(1.2 - index * 0.03, 3),
            source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def _latent_event_questions(
    answers: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, answer in enumerate(answers[:4]):
        scenario_id = str(answer.get("scenario_id", ""))
        domain = LATENT_SCENARIO_DOMAIN.get(scenario_id, "")
        if not domain:
            continue
        question_key, title = _latent_event_question(scenario_id, str(answer.get("result_option", "")))
        source_decision = _source_decision_for_selection(decisions, tuple(), domain)
        candidate = QuestionCandidate(
            question_key=question_key,
            title=title,
            domain=domain,
            score=round(1.12 - index * 0.03, 3),
            source_feature_ids=_feature_ids(source_decision or {}, feature_layer, domain),
            boundary=_boundary(domain),
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
            **dimension_payload(domain),
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def _latent_event_question(scenario_id: str, result_option: str) -> tuple[str, str]:
    if scenario_id == "latent.wealth_change":
        if result_option in {"income_down", "resource_pressure"}:
            return "q_income_stability", "财务压力出现时，命局里先看承载力还是外部牵动？"
        return "q_income_factors", "财务变化明显时，命局里哪些线索最容易被放大？"
    if scenario_id == "latent.career_transition":
        return "q_career_structure", "职业变化明显时，事业主线先看规则、平台还是表达？"
    if scenario_id == "latent.relationship_shift":
        return "q_relationship_structure", "关系变化明显时，命局里先看互动、约束还是承接？"
    if scenario_id == "latent.relocation_environment":
        return "q_time_layer_context", "环境变化明显时，大运流年会先牵动哪条结构线？"
    if scenario_id == "latent.stress_recovery":
        return "q_health_balance_boundary", "压力恢复节奏明显时，命局里先看哪类平衡边界？"
    if scenario_id == "latent.action_result":
        return "q_strength_assessment", "行动结果节奏明显时，先看日主承载还是资源支持？"
    return "q_structure_overview", "结合人生节点后，这个八字先复核哪条主线？"


def _source_decision_for_selection(
    decisions: list[dict[str, object]],
    source_decision_keys: tuple[str, ...],
    domain: str,
) -> dict[str, object] | None:
    for decision in decisions:
        if source_decision_keys and str(decision.get("decision_key", "")) in source_decision_keys:
            return decision
    for decision in decisions:
        if str(decision.get("domain", "")) == domain:
            return decision
    return None


def _practitioner_question(control_key: str, option: str) -> tuple[str, str]:
    if control_key == "control.day_master_strength":
        return "q_strength_assessment", f"命理师判为「{option}」后，下一步先看扶助还是泄耗？"
    if control_key == "control.shang_guan_jian_guan":
        if option == "成立":
            return "q_career_structure", "伤官见官已判成立，先看冲突来源还是化解路径？"
        if option == "被印化":
            return "q_career_structure", "印星能否化解表达冲规则？"
        if option == "被财通关":
            return "q_income_factors", "财星能不能把表达和规则通起来？"
        if option == "不成立":
            return "q_career_structure", "不取伤官见官后，事业主线改看哪里？"
        return "q_career_structure", f"伤官见官判为「{option}」后，事业先复核哪条线？"
    if control_key == "control.wealth_capacity":
        if option == "需扶身":
            return "q_income_stability", "财运要先扶身，还是先看财星来源？"
        if option == "走通关":
            return "q_useful_god_candidates", "财运通关路径应该先看哪一类用神？"
        if option == "看大运":
            return "q_time_layer_context", "财运要不要先看大运流年是否接力？"
        return "q_income_factors", f"财星承载判为「{option}」后，机会和限制在哪里？"
    if control_key == "control.pattern_status":
        if option in {"成格", "破格"}:
            return "q_pattern_structure", f"格局判为「{option}」后，最关键的成败点是什么？"
        return "q_pattern_structure", f"格局仍是「{option}」时，先复核哪几个条件？"
    return "q_structure_overview", "命理师裁决后，下一步先复核哪条结构主线？"


def _make_question(
    question_key: str,
    title: str,
    domain: str,
    score: float,
    decision: dict[str, object],
    feature_layer: FeatureLayer,
) -> QuestionCandidate:
    return QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=round(score, 3),
        source_feature_ids=_feature_ids(decision, feature_layer, domain),
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )


def _explicit_question(question_key: str, feature_layer: FeatureLayer) -> QuestionCandidate | None:
    if question_key not in QUESTION_LABELS:
        return None
    domain = HOOK_DOMAIN_PREFERENCE.get(question_key, "branch")
    feature_ids = _domain_feature_ids(feature_layer, domain)
    title = _explicit_question_title(question_key, feature_layer)
    candidate = QuestionCandidate(
        question_key=question_key,
        title=title,
        domain=domain,
        score=0.5,
        source_feature_ids=feature_ids,
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )
    return _aligned(candidate)


def _explicit_question_title(question_key: str, feature_layer: FeatureLayer) -> str:
    if question_key == "q_strength_assessment":
        ids = {feature.feature_id for feature in feature_layer.features}
        if "feature.strength.capacity_needs_support" in ids:
            return "日主需要扶身时，先看印星、比劫还是通关？"
        if "feature.strength.borderline_capacity" in ids:
            return "日主强弱接近分界时，先裁决哪类证据？"
        if "feature.strength.supported_capacity" in ids:
            return "日主有支撑后，适合先看泄秀、财星还是官杀？"
    if question_key == "q_useful_god_candidates":
        candidate = next((feature for feature in feature_layer.features if feature.feature_id == "feature.useful_god.candidate_paths"), None)
        state = str(getattr(candidate, "calibration_state", "")) if candidate else ""
        if "resource_support" in state or "peer_stabilizer" in state:
            return "用神方向要先扶身，还是另有通关路径？"
        if "output_release" in state:
            return "用神方向适合先看泄秀还是财星通道？"
        if "support_vs_release_review" in state:
            return "用神方向先扶身还是先泄秀？"
    return QUESTION_LABELS[question_key]


def _domain_feature_ids(feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    direct = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct[:6]
    return tuple(feature.feature_id for feature in feature_layer.features[:4])
