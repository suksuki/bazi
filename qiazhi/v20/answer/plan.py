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
from v20.measurement.dimensions import dimension_payload


@dataclass(frozen=True)
class AnswerSection:
    title: str
    body: str
    feature_ids: tuple[str, ...]
    domain: str = ""
    section_type: str = "feature_measurement"
    measurement_topic: str = ""
    measurement_stage: str = ""
    dimension_key: str = ""
    dimension_layer: str = ""
    dimension_label: str = ""

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
    dimension_context: dict[str, object] | None = None
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
            "dimension_context": self.dimension_context or {},
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
                f"「{question.measurement_topic}」相关的命局线索、十神关系和可复核依据。"
            ),
            feature_ids=tuple(feature.feature_id for feature in selected[:4]),
            domain=question.domain,
            section_type="measurement_scope",
            measurement_topic=question.measurement_topic,
            measurement_stage=question.measurement_stage,
            dimension_key=question.dimension_key,
            dimension_layer=question.dimension_layer,
            dimension_label=question.dimension_label,
        )
    ]
    profile_section = _portrait_profile_section(question, feature_layer, decision_report or {})
    if profile_section:
        sections.append(profile_section)
    mainline_section = _mainline_section(decision_report or {}, question.domain)
    if mainline_section:
        sections.append(mainline_section)
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
                    **dimension_payload(row.domain),
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
                    **dimension_payload(feature.domain),
                )
            )
    sections.append(
        AnswerSection(
            title="测算边界",
            body="当前回答只说明命局里已经看到的关系和下一步可复核方向，不把它写成确定事件、固定吉凶或具体时间点。",
            feature_ids=(),
            domain=question.domain,
            section_type="prediction_boundary",
            measurement_topic=question.measurement_topic,
            measurement_stage=question.measurement_stage,
            dimension_key=question.dimension_key,
            dimension_layer=question.dimension_layer,
            dimension_label=question.dimension_label,
        )
    )
    return AnswerPlan(
        version="v20.answer_plan.v1",
        question_key=question.question_key,
        sections=tuple(sections),
        evidence_pack=evidence_pack,
        prediction_policy=prediction_policy(),
        domain_projection=build_domain_projection(feature_layer, question.domain).to_dict(),
        dimension_context=_answer_dimension_context(question, decision_report or {}),
    )


def _portrait_profile_section(
    question: QuestionCandidate,
    feature_layer: FeatureLayer,
    report: dict[str, object],
) -> AnswerSection | None:
    mainlines = _profile_mainlines(report.get("mainlines", ()), question.domain)
    decisions = _profile_decisions(report.get("decisions", ()), question.domain)
    runtime_decisions = _runtime_profile_decisions(report.get("runtime_decision_fusion", {}), question.domain)
    axes = _profile_axes(report.get("portrait_projection", {}), question.domain)
    if not (mainlines or decisions or runtime_decisions or axes):
        return None

    rows: list[str] = []
    rows.extend(runtime_decisions)
    rows.extend(mainlines)
    rows.extend(decisions)
    if axes:
        rows.append(f"画像轴：{_join_short_rows(axes, 2)}")

    boundary = "本段为结构化合成，不做固定命运结论。"
    body_parts = [
        "；".join(rows[:3]),
        _review_pressure(report, question.domain),
        boundary,
    ]
    feature_ids = _profile_feature_ids(feature_layer, question.domain)
    body = "；".join(part for part in body_parts if part)
    if not body:
        return None
    return AnswerSection(
        title="一页图谱画像",
        body=body,
        feature_ids=feature_ids,
        domain=question.domain,
        section_type="portrait_profile_summary",
        measurement_topic=domain_label(question.domain),
        measurement_stage=measurement_stage(question.domain),
        **dimension_payload(question.domain),
    )


def _profile_mainlines(mainlines: tuple[object, ...], selected_domain: str) -> list[str]:
    rows: list[str] = []
    for row in sorted(
        (row for row in mainlines if isinstance(row, dict)),
        key=lambda row: (float(row.get("score", 0.0) or 0.0), str(row.get("title", ""))),
        reverse=True,
    ):
        if not _mainline_matches_domain(row, selected_domain):
            continue
        title = _compact_profile_label(str(row.get("title", "")))
        summary = _compact_profile_summary(str(row.get("summary", "")))
        if title and summary:
            rows.append(f"{title}：{summary}")
        if len(rows) >= 2:
            break
    return rows


def _profile_decisions(decisions: tuple[object, ...], selected_domain: str) -> list[str]:
    rows: list[str] = []
    for decision in sorted(
        (row for row in decisions if isinstance(row, dict)),
        key=lambda row: (float(row.get("score", 0.0) or 0.0), str(row.get("label", ""))),
        reverse=True,
    ):
        if not _decision_matches_domain(decision, selected_domain):
            continue
        state = str(decision.get("status", ""))
        label = str(decision.get("label", ""))
        if not label:
            continue
        label = _compact_profile_label(label)
        support = _first_public_support(decision.get("support", ()))
        marker = f"，{support}" if support else ""
        rows.append(f"{_status_to_brief(state)}{label}{marker}")
        if len(rows) >= 3:
            break
    return rows


def _runtime_profile_decisions(runtime_fusion: object, selected_domain: str) -> list[str]:
    if not isinstance(runtime_fusion, dict):
        return []
    rows: list[str] = []
    for row in runtime_fusion.get("decisions", ()):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", ""))
        if domain and domain != selected_domain and selected_domain not in {domain, "strength"}:
            continue
        state = str(row.get("structural_state", ""))
        decision = str(row.get("user_facing_decision", ""))
        if not decision:
            continue
        boundary = str(row.get("user_facing_boundary", ""))
        rows.append(f"{_status_to_brief(state)}{_compact_profile_label(decision)}")
        if boundary:
            rows.append(f"界限：{boundary}")
    return rows[:3]


def _compact_profile_summary(value: str) -> str:
    if not value:
        return ""
    text = str(value)
    text = _compact_profile_label(text)
    text = text.replace("当前主线入口，RuleSpec 裁决主线，主规则为", "")
    text = text.replace("当前主线入口，", "")
    text = text.replace("主规则为", "")
    text = text.replace("主规则：", "")
    text = text.replace("RuleSpec 裁决主线，", "")
    text = text.replace("主为", "")
    text = text.replace("联动", "")
    text = text.strip().strip("。；;")
    # Keep the first short segment to avoid long proof-chain leakage into profile
    parts = [part.strip() for part in text.split("；") if part.strip()]
    if not parts:
        return text
    first = parts[0]
    if len(first) > 48:
        return first[:46] + "…"
    return first


def _compact_profile_label(value: str) -> str:
    text = str(value)
    text = text.replace("：明确成立", "")
    text = text.replace("：弱候选", "（弱候选）")
    text = text.replace("：需复核", "（需复核）")
    text = text.replace("：成而不纯", "（成而不纯）")
    text = text.replace("：已复核", "")
    text = text.replace("规则", "")
    text = text.replace("（（", "（").replace("））", "）")
    return text.strip("。；; \n")


def _profile_axes(portrait_projection: object, selected_domain: str) -> list[str]:
    if not isinstance(portrait_projection, dict):
        return []
    axis_rows: list[str] = []
    for row in portrait_projection.get("axes", ()):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", ""))
        if domain and not _mainline_matches_domain(row, selected_domain) and domain not in {selected_domain, "strength"}:
            continue
        label = str(row.get("label", ""))
        if label:
            axis_rows.append(label)
        if len(axis_rows) >= 2:
            break
    return axis_rows


def _review_pressure(report: dict[str, object], selected_domain: str) -> str:
    weak_or_review = []
    for decision in (row for row in report.get("decisions", ()) if isinstance(row, dict)):
        if not _decision_matches_domain(decision, selected_domain):
            continue
        state = str(decision.get("status", ""))
        if state in {"requires_review", "weak_candidate", "mixed", "volatile", "countered", "blocked"}:
            label = _compact_profile_label(str(decision.get('label', '')))
            weak_or_review.append(f"{_status_to_brief(state)}{label}")
    if not weak_or_review:
        return ""
    return f"复核重点：{_join_short_rows(weak_or_review, 2)}"


def _profile_feature_ids(feature_layer: FeatureLayer, selected_domain: str) -> tuple[str, ...]:
    selected: list[str] = []
    for feature in feature_layer.features:
        if feature.domain == selected_domain or feature.domain in {"strength", "ten_god"}:
            selected.append(feature.feature_id)
    if not selected:
        selected = [feature.feature_id for feature in feature_layer.features[:4]]
    return tuple(dict.fromkeys(selected))[:6]


def _status_to_brief(state: str) -> str:
    return {
        "confirmed": "成立：",
        "candidate": "候选：",
        "weak_candidate": "弱候选：",
        "mixed": "成而不纯：",
        "volatile": "岁运引动：",
        "requires_review": "需复核：",
        "blocked": "被压制：",
        "countered": "被反证：",
        "out_of_scope": "暂不支持：",
        "chain_candidate": "链式候选：",
        "buffer_candidate": "缓冲候选：",
    }.get(state, "状态：")


def _first_public_support(support: tuple[object, ...] | list[object] | object) -> str:
    if not support:
        return ""
    for item in support if isinstance(support, (tuple, list)) else (support,):
        text = _public_support_text(str(item))
        raw = str(item)
        if raw.startswith("evidence.") or raw.startswith("证据") or "证据." in raw:
            continue
        if "条件成立" in raw or "3/3" in raw:
            continue
        if text.startswith("evidence.") or text.startswith("证据") or "evidence." in text:
            continue
        if text:
            return text
    return ""


def _join_short_rows(rows: list[str], limit: int) -> str:
    return "；".join(str(row) for row in rows[:limit])


def _mainline_section(report: dict[str, object], selected_domain: str) -> AnswerSection | None:
    mainlines = [
        row for row in report.get("mainlines", ())
        if isinstance(row, dict) and _mainline_matches_domain(row, selected_domain)
    ]
    if not mainlines:
        return None
    rows = []
    feature_ids = []
    for row in mainlines[:3]:
        title = str(row.get("title", "命理主线"))
        summary = str(row.get("summary", ""))
        rows.append(f"{title}：{summary}")
        feature_ids.extend(str(item) for item in row.get("source_decision_keys", ()) if str(item))
    return AnswerSection(
        title="主线裁决",
        body="；".join(rows) + "。",
        feature_ids=tuple(dict.fromkeys(feature_ids)),
        domain=selected_domain,
        section_type="mainline_decision",
        measurement_topic=domain_label(selected_domain),
        measurement_stage=measurement_stage(selected_domain),
        **dimension_payload(selected_domain),
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
        support = "、".join(_public_support_text(str(item)) for item in row.get("support", ())[:3] if str(item))
        label = str(row.get("label", "命理裁决"))
        knowledge_hint = _knowledge_rule_public_hint(row)
        suffix = f"，复核重点：{knowledge_hint}" if knowledge_hint else ""
        rows.append(f"{label}：{support}{suffix}")
        feature_ids.extend(str(item) for item in row.get("feature_ids", ()) if str(item))
    return AnswerSection(
        title="主题投射画像",
        body="；".join(rows) + "。这些画像来自当前八字的实时排盘、规则判断和主题投射，不使用离线语料静态标签作为结论。",
        feature_ids=tuple(dict.fromkeys(feature_ids)),
        domain=selected_domain,
        section_type="portrait_projection_reading",
        measurement_topic=domain_label(selected_domain),
        measurement_stage=measurement_stage(selected_domain),
        **dimension_payload(selected_domain),
    )


def _decision_knowledge_section(domain: str, knowledge_refs: tuple[object, ...]) -> AnswerSection:
    labels = []
    for ref in knowledge_refs[:4]:
        knowledge_id = getattr(ref, "knowledge_id", "")
        title = KNOWLEDGE_LABELS_ZH.get(knowledge_id, getattr(ref, "title", ""))
        if title:
            labels.append(f"{title}：用于校对术语和判断范围")
    body = "；".join(labels) + "。" if labels else "当前回答以实时命局判断为主，知识库用于校对术语和判断范围。"
    return AnswerSection(
        title="知识依据",
        body=body,
        feature_ids=(),
        domain=domain,
        section_type="decision_knowledge_support",
        measurement_topic=domain_label(domain),
        measurement_stage=measurement_stage(domain),
        **dimension_payload(domain),
    )


def _knowledge_rule_public_hint(decision: dict[str, object]) -> str:
    labels = []
    for ref in decision.get("knowledge_rule_refs", ())[:2]:
        if not isinstance(ref, dict):
            continue
        for label in ref.get("portrait_labels", ())[:2]:
            if str(label):
                labels.append(str(label))
        if labels:
            break
    return "、".join(dict.fromkeys(labels[:2]))


def _mainline_matches_domain(row: dict[str, object], selected_domain: str) -> bool:
    domain = str(row.get("domain", ""))
    if domain in {selected_domain, "strength"}:
        return True
    if selected_domain == "career" and domain in {"career", "strength", "useful_god", "branch", "time"}:
        return True
    if selected_domain == "wealth" and domain in {"wealth", "strength", "useful_god", "branch", "time"}:
        return True
    if selected_domain == "useful_god" and domain in {"useful_god", "strength", "pattern"}:
        return True
    return False


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


def _public_support_text(value: str) -> str:
    element = {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }
    if value.startswith("arbitration:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为用神参考"
    if value.startswith("support:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为扶身候选"
    if value.startswith("release:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为泄秀候选"
    if value.startswith("channel:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为通道候选"
    if value.startswith("constraint:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向可作为约束候选"
    if value.startswith("evidence_gap:"):
        key = value.split(":", 1)[1]
        return f"{element.get(key, key)}方向属于证据缺口复核"
    return (
        value.replace("日主承载状态 borderline_capacity", "日主强弱接近分界需裁决")
        .replace("日主承载状态 capacity_needs_support", "日主偏弱需扶身复核")
        .replace("日主承载状态 supported_capacity", "日主有根气与生扶支撑")
        .replace("borderline_capacity", "日主强弱接近分界需裁决")
        .replace("capacity_needs_support", "日主偏弱需扶身复核")
        .replace("supported_capacity", "日主有根气与生扶支撑")
    )


def _decision_next_step_section(question: QuestionCandidate, report: dict[str, object]) -> AnswerSection:
    seeds = []
    for decision in report.get("decisions", ())[:5]:
        if isinstance(decision, dict):
            seeds.extend(str(row) for row in decision.get("question_seeds", ()) if str(row))
    body = "下一步可以继续追问：" + "；".join(dict.fromkeys(seeds[:3])) + "。" if seeds else f"下一步继续围绕「{question.title}」看命局线索和可复核依据。"
    return AnswerSection(
        title="下一步",
        body=body,
        feature_ids=tuple(question.source_feature_ids),
        domain=question.domain,
        section_type="decision_next_step",
        measurement_topic=question.measurement_topic,
        measurement_stage=question.measurement_stage,
        dimension_key=question.dimension_key,
        dimension_layer=question.dimension_layer,
        dimension_label=question.dimension_label,
    )


def _answer_dimension_context(question: QuestionCandidate, report: dict[str, object]) -> dict[str, object]:
    related = []
    for decision in report.get("decisions", ()):
        if isinstance(decision, dict) and _decision_matches_domain(decision, question.domain):
            related.append(
                {
                    "decision_key": str(decision.get("decision_key", "")),
                    "domain": str(decision.get("domain", "")),
                    "dimension_key": str(decision.get("dimension_key", "")),
                    "dimension_layer": str(decision.get("dimension_layer", "")),
                    "dimension_label": str(decision.get("dimension_label", "")),
                }
            )
    return {
        "version": "v20.answer_dimension_context.v1",
        "selected_dimension_key": question.dimension_key,
        "selected_dimension_layer": question.dimension_layer,
        "selected_dimension_label": question.dimension_label,
        "related_decision_dimensions": related[:8],
        "runtime_mutation": False,
        "guardrails": [
            "ANSWER_DIMENSIONS_ARE_COORDINATES_NOT_VERDICTS",
            "MACRO_DIMENSION_REQUIRES_MICRO_EVIDENCE",
        ],
    }
