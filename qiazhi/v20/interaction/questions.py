from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from dataclasses import replace
from typing import Any

from v20.answer.measurement_policy import (
    applied_domains,
    domain_label,
    feature_label,
    feature_public_summary,
    feature_domains_for_applied_domain,
    measurement_stage,
)
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, rank_question_rows
from v20.measurement.domain_alignment import align_question_candidate
from v20.measurement.dimensions import dimension_payload


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
    question_id: str = ""
    dimension_key: str = ""
    dimension_layer: str = ""
    dimension_label: str = ""
    alignment_status: str = "pending_bazi_alignment"
    bazi_focus: str = ""
    alignment_score: float = 0.0
    role: str = "bazi_measurement_entry"
    source_decision_key: str = ""
    source_rule_key: str = ""
    source_decision_status: str = ""
    source_decision_label: str = ""
    question_strategy: str = ""
    next_question_atom_id: str = ""
    next_question_topic: str = ""
    next_question_stage: str = ""
    next_question_score: float = 0.0
    next_question_score_reasons: tuple[str, ...] = ()
    display_title: str = ""
    question_anchor: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


QUESTION_LABELS = {
    "q_strength_assessment": "这个八字日主偏强还是偏弱，适合先看什么？",
    "q_useful_god_candidates": "这个盘下一步适合先找哪类用神方向？",
    "q_useful_god_evidence_gaps": "用神方向还缺哪些关键依据？",
    "q_ten_god_focus": "十神显隐关系里先看哪一组？",
    "q_ten_god_metadata": "十神信息应如何进入测算？",
    "q_element_balance": "五行分布的结构偏向是什么？",
    "q_element_support_pressure": "五行偏向会带来什么优势和压力？",
    "q_hidden_stem_role": "藏干里有哪些容易被忽略的命理线索？",
    "q_branch_relation_detail": "地支冲合刑害有哪些可见结构？",
    "q_time_vs_natal_relation": "原局与时间层应如何分开判断？",
    "q_time_layer_context": "流年大运会先牵动事业、财运还是关系？",
    "q_time_relation_triggers": "这一步大运流年最容易牵动哪条主线？",
    "q_structure_overview": "这个八字的整体结构主线是什么？",
    "q_income_stability": "财星结构与收入主题的测算边界是什么？",
    "q_income_factors": "财运的机会和限制分别在哪里？",
    "q_career_structure": "事业主题应回到哪条命理结构主线？",
    "q_relationship_structure": "关系主题应从十神与地支哪个入口测算？",
    "q_health_balance_boundary": "五行偏枯主要提示哪种平衡压力？",
    "q_pattern_structure": "格局审查应从哪里开始？",
}

APPLIED_DOMAIN_QUESTION_KEYS = {
    "wealth": "q_income_stability",
    "career": "q_career_structure",
    "relationship": "q_relationship_structure",
    "health": "q_health_balance_boundary",
}

HOOK_DOMAIN_PREFERENCE = {
    "q_strength_assessment": "strength",
    "q_useful_god_candidates": "useful_god",
    "q_useful_god_evidence_gaps": "useful_god",
    "q_ten_god_focus": "ten_god",
    "q_ten_god_metadata": "ten_god",
    "q_hidden_stem_role": "ten_god",
    "q_element_balance": "element",
    "q_element_support_pressure": "element",
    "q_branch_relation_detail": "branch",
    "q_time_vs_natal_relation": "branch",
    "q_structure_overview": "branch",
    "q_time_layer_context": "time",
    "q_time_relation_triggers": "time",
    "q_income_stability": "wealth",
    "q_income_factors": "wealth",
    "q_career_structure": "career",
    "q_relationship_structure": "relationship",
    "q_health_balance_boundary": "health",
    "q_pattern_structure": "pattern",
}


QUESTION_STRATEGY = {
    "default": "feature_hook",
    "applied_domain": "domain_projection",
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
            title = _personalized_question_title(hook, feature)
            keep_current = _keep_current_question(current, feature.domain, hook, score)
            candidate = QuestionCandidate(
                question_key=hook,
                title=current.title if keep_current else title,
                domain=current.domain if keep_current else feature.domain,
                score=score if current is None else max(current.score, score),
                source_feature_ids=tuple(dict.fromkeys(feature_ids)),
                boundary=current.boundary if keep_current else feature.boundary,
                measurement_topic=current.measurement_topic if keep_current else domain_label(feature.domain),
                measurement_stage=current.measurement_stage if keep_current else measurement_stage(feature.domain),
                **(dimension_payload(current.domain) if keep_current else dimension_payload(feature.domain)),
                question_strategy=QUESTION_STRATEGY["default"],
            )
            candidate = replace(
                candidate,
                question_id=_question_id(
                    candidate.question_key,
                    candidate.title,
                    candidate.domain,
                    candidate.source_feature_ids,
                    str(hook),
                    str(score),
                    question_strategy=QUESTION_STRATEGY["default"],
                ),
            )
            rows[hook] = candidate
    _add_applied_domain_questions(rows, feature_layer)
    aligned_rows = tuple(_aligned_question(row) for row in rows.values())
    aligned_rows = tuple(row for row in aligned_rows if row is not None)
    ordered = rank_question_rows(aligned_rows, ranking_policy)
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
        ordered_sources = sorted(sources, key=lambda row: row.confidence, reverse=True)
        feature_ids = tuple(feature.feature_id for feature in ordered_sources[:8])
        score = round(max(feature.confidence for feature in sources) + min(0.08, len(sources) * 0.012), 3)
        current = rows.get(hook)
        keep_current = _keep_current_question(current, domain, hook, score)
        title_sources = _preferred_applied_sources(domain, ordered_sources)
        rows[hook] = QuestionCandidate(
            question_key=hook,
            title=current.title if keep_current else _applied_question_title(hook, domain, title_sources),
            domain=current.domain if keep_current else domain,
            score=score if current is None else max(current.score, score),
            source_feature_ids=tuple(dict.fromkeys((*current.source_feature_ids, *feature_ids))) if current else feature_ids,
            boundary=current.boundary if keep_current else f"{domain_label(domain)}必须经由 feature spine 的受控领域投影进入回答。",
            measurement_topic=current.measurement_topic if keep_current else domain_label(domain),
            measurement_stage=current.measurement_stage if keep_current else measurement_stage(domain),
            **(dimension_payload(current.domain) if keep_current else dimension_payload(domain)),
            question_strategy=QUESTION_STRATEGY["applied_domain"],
        )
        rows[hook] = replace(
            rows[hook],
            question_id=_question_id(
                rows[hook].question_key,
                rows[hook].title,
                rows[hook].domain,
                rows[hook].source_feature_ids,
                domain,
                "applied",
                question_strategy=QUESTION_STRATEGY["applied_domain"],
            ),
        )


def _keep_current_question(current: QuestionCandidate | None, feature_domain: str, hook: str, score: float) -> bool:
    if current is None:
        return False
    preferred = HOOK_DOMAIN_PREFERENCE.get(hook, "")
    current_preferred = bool(preferred and current.domain == preferred)
    feature_preferred = bool(preferred and feature_domain == preferred)
    if feature_preferred and not current_preferred:
        return False
    if current_preferred and not feature_preferred:
        return True
    return current.score > score


def _preferred_applied_sources(domain: str, sources: list) -> list:  # noqa: ANN001
    preferred_domains = feature_domains_for_applied_domain(domain)
    ordered = []
    for preferred in preferred_domains:
        ordered.extend(feature for feature in sources if feature.domain == preferred)
    ordered.extend(feature for feature in sources if feature not in ordered)
    return ordered


def _personalized_question_title(hook: str, feature) -> str:  # noqa: ANN001
    default = QUESTION_LABELS.get(hook, hook)
    summary = _question_material(feature)
    label = feature_label(feature)
    if not summary and not label:
        return default
    material = summary or label
    if hook == "q_strength_assessment":
        return f"{_clip(material, 24)}，日主偏强还是偏弱？"
    if hook == "q_useful_god_candidates":
        return f"{_clip(material, 24)}，适合先找哪类用神方向？"
    if hook == "q_useful_god_evidence_gaps":
        return f"{_clip(material, 24)}，还缺哪些关键依据？"
    if hook == "q_ten_god_focus":
        return f"{_clip(material, 24)}，先看哪条十神主线？"
    if hook == "q_ten_god_metadata":
        return f"{_clip(material, 24)}，十神如何进入测算？"
    if hook == "q_hidden_stem_role":
        return f"{_clip(material, 24)}，藏干里有什么容易忽略？"
    if hook == "q_element_balance":
        return f"{_clip(material, 24)}，五行偏向怎么读？"
    if hook == "q_element_support_pressure":
        return f"{_clip(material, 24)}，扶抑压力在哪里？"
    if hook == "q_branch_relation_detail":
        return f"{_clip(material, 24)}，地支互动怎么分层？"
    if hook == "q_structure_overview":
        return f"{_clip(material, 24)}，整体结构主线是什么？"
    if hook == "q_time_layer_context":
        return f"{_clip(material, 24)}，大运流年先牵动什么？"
    if hook == "q_time_relation_triggers":
        return f"{_clip(material, 24)}，会先牵动哪条主线？"
    if hook == "q_income_factors":
        return f"{_clip(material, 24)}，机会和限制在哪里？"
    if hook == "q_income_stability":
        return f"{_clip(material, 24)}，财星结构边界是什么？"
    if hook == "q_career_structure":
        return f"{_clip(material, 24)}，事业主题从哪条命理结构进入？"
    if hook == "q_relationship_structure":
        return f"{_clip(material, 24)}，关系主题从十神或地支哪里进入？"
    if hook == "q_health_balance_boundary":
        return f"{_clip(material, 24)}，主要提示哪种平衡压力？"
    return default


def _applied_question_title(hook: str, domain: str, sources: list) -> str:  # noqa: ANN001
    material = ""
    for feature in sources:
        material = _question_material(feature)
        if material:
            break
    if not material:
        material = domain_label(domain)
    if hook == "q_income_stability":
        return f"{_clip(material, 24)}，财星结构边界是什么？"
    if hook == "q_career_structure":
        return f"{_clip(material, 24)}，事业主题从哪条命理结构进入？"
    if hook == "q_relationship_structure":
        return f"{_clip(material, 24)}，关系主题从十神或地支哪里进入？"
    if hook == "q_health_balance_boundary":
        return f"{_clip(material, 24)}，主要提示哪种平衡压力？"
    return QUESTION_LABELS.get(hook, hook)


def _question_material(feature) -> str:  # noqa: ANN001
    label = feature_label(feature)
    if feature.domain in {"strength", "element", "useful_god", "pattern"} and label:
        return label
    summary = feature_public_summary(feature).strip().rstrip("。")
    for prefix in ("结构材料：", "结构摘要：", "十神焦点：", "地支结构材料：", "地支结构焦点：", "财星材料：", "候选摘要："):
        if summary.startswith(prefix):
            summary = summary[len(prefix):]
            break
    return summary or label


def _aligned_question(candidate: QuestionCandidate) -> QuestionCandidate | None:
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


def _question_id(
    question_key: str,
    title: str,
    domain: str,
    source_feature_ids: tuple[str, ...],
    namespace: str,
    marker: str,
    question_strategy: str = "",
) -> str:
    signature = f"{question_key}|{domain}|{title}|{';'.join(source_feature_ids)}|{namespace}|{marker}|{question_strategy}"
    digest = hashlib.blake2s(signature.encode("utf-8"), digest_size=5).hexdigest()
    return f"{question_key}:{digest}"


def _clip(value: str, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
