from __future__ import annotations

from dataclasses import replace

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, rank_question_rows
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QUESTION_LABELS, QuestionCandidate
from v20.measurement.domain_alignment import align_question_candidate


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


def recommend_decision_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
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
        )
        aligned = _aligned(candidate)
        if aligned:
            rows.append(aligned)
        rows.extend(_secondary_questions(decision, feature_layer))
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
    seeds = [str(row) for row in decision.get("question_seeds", ()) if str(row)]
    if seeds:
        return seeds[0]
    if domain == "strength":
        return "先看日主强弱与承载力吗？"
    if domain == "wealth":
        return "财星能不能用，要先看日主承载还是结构通道？"
    if domain == "career":
        return f"{label}是否会成为事业主线？"
    if domain == "branch":
        return "地支冲合刑害会牵动哪条结构？"
    if domain == "time":
        return "时间层进入后，先触发哪条原局结构？"
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
    )


def _secondary_questions(decision: dict[str, object], feature_layer: FeatureLayer) -> list[QuestionCandidate]:
    domain = str(decision.get("domain", ""))
    role = str(decision.get("role", ""))
    rows: list[QuestionCandidate] = []
    if domain == "time":
        rows.append(_make_question(
            "q_time_relation_triggers",
            "时间干支与原局的触发边界是什么？",
            "time",
            float(decision.get("score", 0.0)) + 0.04,
            decision,
            feature_layer,
        ))
    if domain == "wealth":
        rows.append(_make_question(
            "q_income_factors",
            "财星材料的来源和可用性如何复核？",
            "wealth",
            float(decision.get("score", 0.0)) + 0.02,
            decision,
            feature_layer,
        ))
    if domain == "element":
        rows.append(_make_question(
            "q_element_support_pressure",
            "五行分布如何影响扶抑压力？",
            "element",
            float(decision.get("score", 0.0)) + 0.03,
            decision,
            feature_layer,
        ))
    if domain == "ten_god" or ".ten_god." in str(decision.get("rule_key", "")):
        rows.append(_make_question(
            "q_hidden_stem_role",
            "藏干和明透分别承担什么结构作用？",
            "ten_god",
            float(decision.get("score", 0.0)) + (0.02 if role == "foundation_context" else 0.0),
            decision,
            feature_layer,
        ))
    return [row for row in (_aligned(item) for item in rows) if row is not None]


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
    )


def _explicit_question(question_key: str, feature_layer: FeatureLayer) -> QuestionCandidate | None:
    if question_key not in QUESTION_LABELS:
        return None
    domain = HOOK_DOMAIN_PREFERENCE.get(question_key, "branch")
    feature_ids = _domain_feature_ids(feature_layer, domain)
    candidate = QuestionCandidate(
        question_key=question_key,
        title=QUESTION_LABELS[question_key],
        domain=domain,
        score=0.5,
        source_feature_ids=feature_ids,
        boundary=_boundary(domain),
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
    )
    return _aligned(candidate)


def _domain_feature_ids(feature_layer: FeatureLayer, domain: str) -> tuple[str, ...]:
    direct = tuple(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if direct:
        return direct[:6]
    return tuple(feature.feature_id for feature in feature_layer.features[:4])
