from __future__ import annotations

from v20.answer.measurement_policy import (
    applied_domains,
    domain_label,
    feature_domains_for_applied_domain,
    measurement_stage,
)
from v20.answer.plan import AnswerPlan
from v20.features.schema import BaziFeature, FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.measurement.schema import MeasurementReport, MeasurementTopic


def build_measurement_report(
    feature_layer: FeatureLayer,
    questions: tuple[QuestionCandidate, ...],
    answer_plan: AnswerPlan,
    portrait_projection: dict[str, object],
) -> MeasurementReport:
    topic_keys = _topic_keys(feature_layer, questions)
    topics = tuple(_build_topic(topic_key, feature_layer.features, questions, answer_plan) for topic_key in topic_keys)
    return MeasurementReport(
        version="v20.measurement_report.v1",
        core_focus="bazi_measurement",
        selected_question_key=answer_plan.question_key,
        topics=topics,
        applied_domain_keys=tuple(topic.topic_key for topic in topics if topic.topic_key in applied_domains()),
        portrait_role=str(portrait_projection.get("role", "")),
    )


def _topic_keys(feature_layer: FeatureLayer, questions: tuple[QuestionCandidate, ...]) -> tuple[str, ...]:
    keys = {feature.domain for feature in feature_layer.features}
    keys.update(question.domain for question in questions)
    return tuple(sorted(keys, key=lambda key: (measurement_stage(key), domain_label(key))))


def _build_topic(
    topic_key: str,
    features: tuple[BaziFeature, ...],
    questions: tuple[QuestionCandidate, ...],
    answer_plan: AnswerPlan,
) -> MeasurementTopic:
    source_domains = feature_domains_for_applied_domain(topic_key)
    source_features = tuple(feature for feature in features if feature.domain in source_domains)
    topic_questions = tuple(question for question in questions if question.domain == topic_key)
    feature_ids = tuple(dict.fromkeys(feature.feature_id for feature in source_features[:8]))
    question_keys = tuple(dict.fromkeys(question.question_key for question in topic_questions))
    answer_titles = tuple(
        section.title
        for section in answer_plan.sections
        if section.domain == topic_key or any(feature_id in section.feature_ids for feature_id in feature_ids)
    )
    confidence = max((feature.confidence for feature in source_features), default=0.0)
    return MeasurementTopic(
        topic_key=topic_key,
        label=domain_label(topic_key),
        stage=measurement_stage(topic_key),
        status="ready" if source_features else "needs_feature_support",
        confidence=round(confidence, 3),
        source_feature_ids=feature_ids,
        question_keys=question_keys,
        answer_section_titles=answer_titles,
        boundary=f"{domain_label(topic_key)}只能由已编译特征、证据包和受控领域投影共同支持。",
    )
