from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.measurement_policy import (
    applied_domains,
    domain_label,
    feature_domains_for_applied_domain,
    measurement_stage,
)
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, rank_question_rows


@dataclass(frozen=True)
class QuestionCandidate:
    question_key: str
    title: str
    domain: str
    score: float
    source_feature_ids: tuple[str, ...]
    boundary: str
    measurement_topic: str
    measurement_stage: str
    role: str = "bazi_measurement_entry"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


QUESTION_LABELS = {
    "q_strength_assessment": "先看日主强弱与承载力吗？",
    "q_useful_god_candidates": "哪些用神路径可以作为候选？",
    "q_ten_god_focus": "十神显隐关系里先看哪一组？",
    "q_ten_god_metadata": "十神信息应如何进入测算？",
    "q_element_balance": "五行分布的结构偏向是什么？",
    "q_element_support_pressure": "五行分布如何影响扶抑压力？",
    "q_hidden_stem_role": "藏干在这个八字里承担什么结构作用？",
    "q_branch_relation_detail": "地支冲合刑害有哪些可见结构？",
    "q_time_vs_natal_relation": "原局与时间层应如何分开判断？",
    "q_time_layer_context": "显式时间层会触发哪些结构互动？",
    "q_time_relation_triggers": "时间干支与原局的触发边界是什么？",
    "q_structure_overview": "这个八字的整体结构主线是什么？",
    "q_income_stability": "财星与收入结构的测算边界是什么？",
    "q_income_factors": "哪些因素会影响财星材料的可用性？",
    "q_career_structure": "事业角色与工作结构应从哪条主线测算？",
    "q_relationship_structure": "关系互动结构的测算入口是什么？",
    "q_health_balance_boundary": "五行平衡与健康边界应如何测算？",
    "q_pattern_structure": "格局审查应从哪里开始？",
}

APPLIED_DOMAIN_QUESTION_KEYS = {
    "career": "q_career_structure",
    "relationship": "q_relationship_structure",
    "health": "q_health_balance_boundary",
}


def recommend_questions(
    feature_layer: FeatureLayer,
    *,
    limit: int = 14,
    ranking_policy: QuestionRankingPolicy | None = None,
) -> tuple[QuestionCandidate, ...]:
    rows: dict[str, QuestionCandidate] = {}
    for feature in feature_layer.features:
        for index, hook in enumerate(feature.question_hooks):
            score = round(feature.confidence + max(0, 4 - index) * 0.03, 3)
            current = rows.get(hook)
            feature_ids = (feature.feature_id,) if current is None else (*current.source_feature_ids, feature.feature_id)
            candidate = QuestionCandidate(
                question_key=hook,
                title=QUESTION_LABELS.get(hook, hook),
                domain=feature.domain,
                score=score if current is None else max(current.score, score),
                source_feature_ids=tuple(dict.fromkeys(feature_ids)),
                boundary=feature.boundary,
                measurement_topic=domain_label(feature.domain),
                measurement_stage=measurement_stage(feature.domain),
            )
            rows[hook] = candidate
    _add_applied_domain_questions(rows, feature_layer)
    ordered = rank_question_rows(tuple(rows.values()), ranking_policy)
    return tuple(ordered[:limit])


def _add_applied_domain_questions(rows: dict[str, QuestionCandidate], feature_layer: FeatureLayer) -> None:
    for domain in applied_domains():
        hook = APPLIED_DOMAIN_QUESTION_KEYS.get(domain)
        if not hook:
            continue
        source_domains = feature_domains_for_applied_domain(domain)
        sources = tuple(feature for feature in feature_layer.features if feature.domain in source_domains)
        if not sources:
            continue
        feature_ids = tuple(
            feature.feature_id
            for feature in sorted(sources, key=lambda row: row.confidence, reverse=True)[:8]
        )
        score = round(max(feature.confidence for feature in sources) + min(0.08, len(sources) * 0.012), 3)
        rows[hook] = QuestionCandidate(
            question_key=hook,
            title=QUESTION_LABELS[hook],
            domain=domain,
            score=score,
            source_feature_ids=feature_ids,
            boundary=f"{domain_label(domain)}必须经由 feature spine 的受控领域投影进入回答。",
            measurement_topic=domain_label(domain),
            measurement_stage=measurement_stage(domain),
        )
