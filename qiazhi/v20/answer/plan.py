from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from v20.answer.domain_projection import build_domain_projection
from v20.answer.domain_reading import KNOWLEDGE_LABELS_ZH, build_domain_reading_sections
from v20.answer.evidence import EvidencePack
from v20.answer.measurement_policy import (
    domain_label,
    feature_label,
    feature_public_summary,
    measurement_focus,
    measurement_stage,
    prediction_policy,
)
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeRetrievalReport


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


def build_answer_plan(
    question: QuestionCandidate,
    feature_layer: FeatureLayer,
    evidence_pack: EvidencePack,
    knowledge_report: KnowledgeRetrievalReport | None = None,
    rule_candidate_report: dict[str, object] | None = None,
    decision_report: dict[str, object] | None = None,
) -> AnswerPlan:
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
    decision_section = _decision_section(decision_report or {}, question.domain)
    if decision_section:
        sections.append(decision_section)
    knowledge_refs = tuple(knowledge_report.refs) if knowledge_report is not None else ()
    if decision_report:
        sections.append(_decision_knowledge_section(question.domain, knowledge_refs))
        sections.append(_decision_next_step_section(question, decision_report))
    else:
        for row in build_domain_reading_sections(
            question,
            tuple(selected),
            feature_layer,
            knowledge_refs,
            rule_candidate_report or {},
        ):
            sections.append(
                AnswerSection(
                    title=row.title,
                    body=row.body,
                    feature_ids=row.feature_ids,
                    domain=row.domain,
                    section_type=row.section_type,
                    measurement_topic=domain_label(row.domain),
                    measurement_stage=measurement_stage(row.domain),
                )
            )
        for feature in selected[:4]:
            topic = domain_label(feature.domain)
            focus = measurement_focus(feature)
            public_summary = feature_public_summary(feature)
            summary_sentence = f" {public_summary}" if public_summary else ""
            sections.append(
                AnswerSection(
                    title=f"{topic}：{feature_label(feature)}",
                    body=(
                        f"测算焦点：{focus}。{feature.boundary} "
                        f"已接入 {len(feature.evidence_refs)} 条已审查证据来源。"
                        f"{summary_sentence}"
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


def _decision_section(report: dict[str, object], selected_domain: str) -> AnswerSection | None:
    decisions = [
        row for row in report.get("decisions", ())
        if isinstance(row, dict) and _decision_matches_domain(row, selected_domain)
    ]
    if not decisions:
        return None
    rows = []
    feature_ids = []
    for row in decisions[:4]:
        support = "、".join(str(item) for item in row.get("support", ())[:3] if str(item))
        label = str(row.get("label", "命理裁决"))
        status = str(row.get("status", "candidate"))
        rows.append(f"{label}（{status}）：{support}")
        feature_ids.extend(str(item) for item in row.get("feature_ids", ()) if str(item))
    return AnswerSection(
        title="动态裁决画像",
        body="；".join(rows) + "。这些画像来自当前八字的规则命中与裁决，不使用离线语料静态标签作为结论。",
        feature_ids=tuple(dict.fromkeys(feature_ids)),
        domain=selected_domain,
        section_type="dynamic_decision_portrait",
        measurement_topic=domain_label(selected_domain),
        measurement_stage=measurement_stage(selected_domain),
    )


def _decision_knowledge_section(domain: str, knowledge_refs: tuple[object, ...]) -> AnswerSection:
    labels = []
    for ref in knowledge_refs[:4]:
        knowledge_id = getattr(ref, "knowledge_id", "")
        title = KNOWLEDGE_LABELS_ZH.get(knowledge_id, getattr(ref, "title", ""))
        if title:
            labels.append(f"{title}：只提供术语、证据范围和越界提醒")
    body = "；".join(labels) + "。" if labels else "当前回答以动态裁决画像为主，知识库只提供边界和术语支持。"
    return AnswerSection(
        title="知识依据",
        body=body,
        feature_ids=(),
        domain=domain,
        section_type="decision_knowledge_support",
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
    )


def _decision_matches_domain(row: dict[str, object], selected_domain: str) -> bool:
    domain = str(row.get("domain", ""))
    rule_key = str(row.get("rule_key", ""))
    if domain in {selected_domain, "strength", "branch", "time"}:
        return True
    if selected_domain == "ten_god" and ".ten_god." in rule_key:
        return True
    if selected_domain == "career" and (domain == "ten_god" or ".ten_god." in rule_key):
        return True
    if selected_domain == "wealth" and (domain in {"ten_god", "useful_god", "element"} or ".wealth." in rule_key):
        return True
    return False


def _decision_next_step_section(question: QuestionCandidate, report: dict[str, object]) -> AnswerSection:
    seeds = []
    for decision in report.get("decisions", ())[:5]:
        if isinstance(decision, dict):
            seeds.extend(str(row) for row in decision.get("question_seeds", ()) if str(row))
    body = "下一步可以继续追问：" + "；".join(dict.fromkeys(seeds[:3])) + "。" if seeds else f"下一步继续围绕「{question.title}」复核主线、证据和边界。"
    return AnswerSection(
        title="下一步",
        body=body,
        feature_ids=tuple(question.source_feature_ids),
        domain=question.domain,
        section_type="decision_next_step",
        measurement_topic=question.measurement_topic,
        measurement_stage=question.measurement_stage,
    )
