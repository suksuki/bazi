from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.domain_projection import build_domain_projection
from v20.answer.evidence import EvidencePack
from v20.answer.measurement_policy import domain_label, feature_label, measurement_focus, measurement_stage, prediction_policy
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate


@dataclass(frozen=True)
class AnswerSection:
    title: str
    body: str
    feature_ids: tuple[str, ...]
    domain: str = ""
    section_type: str = "feature_measurement"
    measurement_topic: str = ""
    measurement_stage: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnswerPlan:
    version: str
    question_key: str
    sections: tuple[AnswerSection, ...]
    evidence_pack: EvidencePack
    measurement_focus: str = "bazi_measurement"
    prediction_policy: dict[str, object] | None = None
    domain_projection: dict[str, object] | None = None
    guardrails: tuple[str, ...] = (
        "ANSWER_PLAN_VERIFIED_CONTEXT_ONLY",
        "LLM_MAY_REWRITE_ONLY",
        "BAZI_MEASUREMENT_FIRST",
        "DOMAIN_PROJECTION_REQUIRED_FOR_APPLIED_TOPICS",
        "NO_UNBOUNDED_FORTUNE_CONCLUSION",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "question_key": self.question_key,
            "sections": [row.to_dict() for row in self.sections],
            "evidence_pack": self.evidence_pack.to_dict(),
            "measurement_focus": self.measurement_focus,
            "prediction_policy": self.prediction_policy or prediction_policy(),
            "domain_projection": self.domain_projection or {},
            "guardrails": list(self.guardrails),
        }


def build_answer_plan(question: QuestionCandidate, feature_layer: FeatureLayer, evidence_pack: EvidencePack) -> AnswerPlan:
    selected = [feature for feature in feature_layer.features if feature.feature_id in question.source_feature_ids]
    if not selected:
        selected = list(feature_layer.features[:3])
    sections: list[AnswerSection] = [
        AnswerSection(
            title="命理测算主线",
            body=(
                f"本次以「{question.title}」为入口，优先读取"
                f"「{question.measurement_topic}」相关的结构、证据和边界。"
            ),
            feature_ids=tuple(feature.feature_id for feature in selected[:4]),
            domain=question.domain,
            section_type="measurement_scope",
            measurement_topic=question.measurement_topic,
            measurement_stage=question.measurement_stage,
        )
    ]
    for feature in selected[:4]:
        topic = domain_label(feature.domain)
        focus = measurement_focus(feature)
        sections.append(
            AnswerSection(
                title=f"{topic}：{feature_label(feature)}",
                body=(
                    f"测算焦点：{focus}。{feature.boundary} "
                    f"已接入 {len(feature.evidence_refs)} 条已审查证据来源。"
                ),
                feature_ids=(feature.feature_id,),
                domain=feature.domain,
                section_type="feature_measurement",
                measurement_topic=topic,
                measurement_stage=measurement_stage(feature.domain),
            )
        )
    sections.append(
        AnswerSection(
            title="测算边界",
            body="当前回答给出命理结构判断和候选路径，不把候选特征写成确定事件、固定吉凶或具体时间点。",
            feature_ids=(),
            domain=question.domain,
            section_type="prediction_boundary",
            measurement_topic=question.measurement_topic,
            measurement_stage=question.measurement_stage,
        )
    )
    return AnswerPlan(
        version="v20.answer_plan.v1",
        question_key=question.question_key,
        sections=tuple(sections),
        evidence_pack=evidence_pack,
        prediction_policy=prediction_policy(),
        domain_projection=build_domain_projection(feature_layer, question.domain).to_dict(),
    )
