from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer


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
    "q_hidden_stem_role": "藏干在这个八字里承担什么结构作用？",
    "q_branch_relation_detail": "地支冲合刑害有哪些可见结构？",
    "q_time_vs_natal_relation": "原局与时间层应如何分开判断？",
    "q_structure_overview": "这个八字的整体结构主线是什么？",
    "q_income_stability": "财星与收入结构的测算边界是什么？",
    "q_income_factors": "哪些因素会影响财星材料的可用性？",
    "q_pattern_structure": "格局审查应从哪里开始？",
}


def recommend_questions(feature_layer: FeatureLayer, *, limit: int = 8) -> tuple[QuestionCandidate, ...]:
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
    ordered = sorted(rows.values(), key=lambda row: (row.score, row.question_key), reverse=True)
    return tuple(ordered[:limit])
