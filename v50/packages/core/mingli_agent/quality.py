from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import Field

from core.contracts.base import V50Model

from .contracts import ChartWorldInstance, MingliCognitiveDraft, MingliCognitiveRecord
from .fact_review import assertive_claim_text, deterministic_fact_conflicts


_GENERIC_PHRASES = (
    "有机会也有挑战",
    "保持积极心态",
    "平衡工作与生活",
    "相信自己",
    "顺其自然",
    "因人而异",
    "可以小步推进",
    "保留验证节点",
)

_MINGLI_CONCEPT_PATTERNS = {
    "fire_dominant": ("火旺", "火势", "火炎", "火炽", "火气当令"),
    "output_generates_wealth": ("食伤生财", "食神生财", "伤官生财"),
    "output_controls_pressure": ("食伤制杀", "食神制杀", "伤官制杀", "制杀"),
    "follow_momentum": ("从儿", "从势", "从强", "弃命", "顺势格"),
    "weak_day_master": ("身弱", "日主弱", "身轻"),
    "strong_day_master": ("身强", "日主强", "身旺"),
    "resource_peer_support": ("印比", "比劫帮身", "印星护体", "生扶日主"),
    "root_support": ("通根", "强根", "根气", "坐根"),
    "climate_regulation": ("调候", "寒暖燥湿", "火炎土燥"),
    "wealth_pressure": ("财多身弱", "财重身轻", "难任旺财", "富屋贫人"),
    "officer_pressure": ("官杀", "七杀", "正官"),
    "resource_disrupts_output": ("枭神夺食", "印重制食伤", "印夺食"),
    "mediation": ("通关", "桥接", "中介节点"),
    "combination_transformation": ("三合", "三会", "合局", "合化"),
    "clash_dynamic": ("冲战", "相冲", "夹冲", "冲克"),
}

_CONDITION_KEYS = {
    "conditions",
    "success_conditions",
    "failure_conditions",
    "falsifiers",
    "invalidating_conditions",
    "counter_conditions",
    "disconfirming_answer",
}

_EVIDENCE_REFERENCE_KEYS = {
    "evidence_refs",
    "supporting_evidence_refs",
    "counter_evidence_refs",
    "focus_refs",
    "candidate_path_refs",
    "competing_path_refs",
}


class CognitiveQualitySignals(V50Model):
    """Automated signals, never a substitute for professional Mingli review."""

    version: str = "deepbazi.cognitive_quality_signals.v1"
    status: Literal["diagnostic_only"] = "diagnostic_only"
    structural_specificity: float = Field(ge=0.0, le=1.0)
    falsifiability: float = Field(ge=0.0, le=1.0)
    causal_completeness: float = Field(ge=0.0, le=1.0)
    fact_traceability: float = Field(ge=0.0, le=1.0)
    deterministic_fact_consistency: float = Field(ge=0.0, le=1.0)
    generic_language_risk: float = Field(ge=0.0, le=1.0)
    chart_anchor_count: int = Field(ge=0)
    cited_fact_count: int = Field(ge=0)
    generic_phrase_hits: list[str] = Field(default_factory=list)
    factual_conflict_hits: list[str] = Field(default_factory=list)
    unsupported_fact_claim_hits: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    interpretation_boundary: str = "这些指标只诊断结构特异性与可审计性，不判断命理结论正确与否。"


class ContrastiveDistinctionSignals(V50Model):
    version: str = "deepbazi.contrastive_distinction_signals.v1"
    status: Literal["diagnostic_only"] = "diagnostic_only"
    text_similarity: float = Field(ge=0.0, le=1.0)
    reasoning_signature_similarity: float = Field(ge=0.0, le=1.0)
    contrastive_distinction: float = Field(ge=0.0, le=1.0)
    portable_template_risk: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    interpretation_boundary: str = "跨盘相似度是套话风险代理指标，不等于两张命盘必然不同。"


def evaluate_cognitive_quality(
    cognition: MingliCognitiveDraft | MingliCognitiveRecord | dict[str, Any],
    *,
    world: ChartWorldInstance,
) -> CognitiveQualitySignals:
    payload = _payload(cognition)
    if "cognition" in payload and isinstance(payload["cognition"], dict):
        payload = payload["cognition"]

    corpus = _text_corpus(payload)
    cited_refs = set(_collect_reference_values(payload))
    allowed_refs = set(world.allowed_evidence_refs)
    cited_fact_refs = {ref for ref in cited_refs if _evidence_ref_allowed(ref, allowed=allowed_refs)}
    traceability = 1.0 if not cited_refs else len(cited_fact_refs) / len(cited_refs)

    anchors = _chart_anchors(world)
    anchor_hits = {item for item in anchors if item and item in corpus}
    anchor_score = min(1.0, len(anchor_hits) / max(1, len(anchors)))

    claim_count = _claim_opportunity_count(payload)
    condition_count = _condition_count(payload)
    conditional_score = min(1.0, condition_count / max(1, claim_count))
    structural_specificity = _clamp(0.45 * traceability + 0.35 * anchor_score + 0.20 * conditional_score)

    falsifiable, falsifiable_opportunities = _falsifiability_counts(payload)
    falsifiability = _clamp(falsifiable / max(1, falsifiable_opportunities))
    causal_completeness = _causal_completeness(payload)

    generic_hits = [phrase for phrase in _GENERIC_PHRASES if phrase in corpus]
    fact_findings = deterministic_fact_conflicts(text=assertive_claim_text(payload), world=world)
    unsupported_fact_claims = [item for item in fact_findings if item.startswith("地支关系未建模:")]
    factual_conflicts = [item for item in fact_findings if item not in unsupported_fact_claims]
    sentences = _sentences(corpus)
    repetition = 0.0 if not sentences else 1.0 - (len(set(sentences)) / len(sentences))
    generic_risk = _clamp(
        0.55 * min(1.0, len(generic_hits) / 2)
        + 0.25 * repetition
        + 0.20 * (1.0 - anchor_score)
    )

    warnings: list[str] = []
    if structural_specificity < 0.55:
        warnings.append("结构特异性偏低：断法可能没有充分落到这张命盘的事实锚点。")
    if falsifiability < 0.55:
        warnings.append("可证伪性偏低：需要补充失效条件、反证或可区分 Probe。")
    if causal_completeness < 0.55:
        warnings.append("因果链偏薄：主做功或领域推演尚未形成来源、转化、目标与失效条件的闭环。")
    if generic_risk >= 0.45:
        warnings.append("通用语言风险偏高：建议人工检查跨盘可移植的套话。")
    if factual_conflicts:
        warnings.append("确定性事实一致性未通过：该结果不能进入专业质量晋级，需修正世界事实或重跑受影响推理阶段。")
    if unsupported_fact_claims:
        warnings.append("存在世界模型尚未覆盖的关系主张：需补充确定性关系事实或交由专业复核，不能自动判为正确。")

    return CognitiveQualitySignals(
        structural_specificity=round(structural_specificity, 4),
        falsifiability=round(falsifiability, 4),
        causal_completeness=round(causal_completeness, 4),
        fact_traceability=round(traceability, 4),
        deterministic_fact_consistency=1.0 if not factual_conflicts else 0.0,
        generic_language_risk=round(generic_risk, 4),
        chart_anchor_count=len(anchor_hits),
        cited_fact_count=len(cited_fact_refs),
        generic_phrase_hits=generic_hits,
        factual_conflict_hits=factual_conflicts,
        unsupported_fact_claim_hits=unsupported_fact_claims,
        warnings=warnings,
    )


def compare_cognitive_distinction(
    left: MingliCognitiveDraft | MingliCognitiveRecord | dict[str, Any],
    right: MingliCognitiveDraft | MingliCognitiveRecord | dict[str, Any],
) -> ContrastiveDistinctionSignals:
    left_payload = _cognition_payload(left)
    right_payload = _cognition_payload(right)
    text_similarity = _jaccard(_ngrams(_text_corpus(left_payload)), _ngrams(_text_corpus(right_payload)))
    signature_similarity = _jaccard(_reasoning_signatures(left_payload), _reasoning_signatures(right_payload))
    portable_risk = _clamp(0.35 * text_similarity + 0.65 * signature_similarity)
    distinction = _clamp(1.0 - portable_risk)
    warnings = []
    if portable_risk >= 0.68:
        warnings.append("两张盘的语言和推理签名高度相似，存在模板跨盘移植风险。")
    elif portable_risk >= 0.5:
        warnings.append("两张盘的区分度有限，建议人工检查主做功、失效条件与先验预测是否真正不同。")
    return ContrastiveDistinctionSignals(
        text_similarity=round(text_similarity, 4),
        reasoning_signature_similarity=round(signature_similarity, 4),
        contrastive_distinction=round(distinction, 4),
        portable_template_risk=round(portable_risk, 4),
        warnings=warnings,
    )


def _payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value)


def _cognition_payload(value: Any) -> dict[str, Any]:
    payload = _payload(value)
    return payload.get("cognition", payload)


def _text_corpus(payload: Any) -> str:
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, dict):
            for key, item in value.items():
                if key not in {"version", "record_id", "case_id", "world_id", "created_at", "model"}:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return "\n".join(values)


def _collect_reference_values(payload: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in _EVIDENCE_REFERENCE_KEYS and isinstance(value, list):
                refs.extend(str(item) for item in value)
            else:
                refs.extend(_collect_reference_values(value))
    elif isinstance(payload, list):
        for item in payload:
            refs.extend(_collect_reference_values(item))
    return refs


def _chart_anchors(world: ChartWorldInstance) -> set[str]:
    anchors = {pillar for pillar in world.pillars}
    anchors.update(character for pillar in world.pillars for character in pillar)
    for fact in world.facts:
        if fact.authority in {"deterministic_fact", "neutral_relation"}:
            anchors.update(token for token in re.findall(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{1,4}", fact.statement))
    return anchors


def _claim_opportunity_count(payload: dict[str, Any]) -> int:
    return max(
        1,
        len(payload.get("hypotheses", []))
        + len(payload.get("portrait", []))
        + len(payload.get("prior_predictions", []))
        + sum(len((payload.get(name) or {}).get("assertions", [])) for name in ("career", "wealth")),
    )


def _condition_count(payload: Any) -> int:
    count = 0
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in _CONDITION_KEYS:
                if isinstance(value, list):
                    count += len([item for item in value if str(item).strip()])
                elif str(value).strip():
                    count += 1
            else:
                count += _condition_count(value)
    elif isinstance(payload, list):
        count += sum(_condition_count(item) for item in payload)
    return count


def _falsifiability_counts(payload: dict[str, Any]) -> tuple[int, int]:
    supported = 0
    opportunities = 0
    for item in payload.get("hypotheses", []):
        opportunities += 1
        supported += bool(item.get("failure_conditions") or item.get("counter_evidence_refs"))
    work = payload.get("work_path") or {}
    opportunities += 1
    supported += bool(work.get("failure_conditions"))
    for item in payload.get("portrait", []):
        opportunities += 1
        supported += bool(item.get("falsifiers") or item.get("counter_evidence_refs"))
    for item in payload.get("prior_predictions", []):
        opportunities += 1
        supported += bool(item.get("disconfirming_answer"))
    for name in ("career", "wealth"):
        for item in (payload.get(name) or {}).get("assertions", []):
            opportunities += 1
            supported += bool(item.get("falsifiers") or item.get("counter_evidence_refs"))
    return int(supported), opportunities


def _causal_completeness(payload: dict[str, Any]) -> float:
    work = payload.get("work_path") or {}
    work_parts = (
        bool(work.get("source")),
        bool(work.get("transformations")),
        bool(work.get("target")),
        bool(work.get("body_function_relation")),
        bool(work.get("success_conditions")),
        bool(work.get("failure_conditions")),
    )
    scores = [sum(work_parts) / len(work_parts)]
    for name in ("career", "wealth"):
        domain = payload.get(name)
        if domain:
            scores.append(min(1.0, len(domain.get("causal_chain", [])) / 3))
    return _clamp(sum(scores) / len(scores))


def _reasoning_signatures(payload: dict[str, Any]) -> set[str]:
    signatures: set[str] = set()
    corpus = _text_corpus(payload)
    for concept, patterns in _MINGLI_CONCEPT_PATTERNS.items():
        if any(pattern in corpus for pattern in patterns):
            signatures.add(f"concept:{concept}")
    for item in payload.get("hypotheses", []):
        signatures.add(f"hypothesis:{_normalize(str(item.get('name', '')))}")
    work = payload.get("work_path") or {}
    signatures.add(f"work:{_normalize(''.join([
        *work.get("source", []),
        *work.get("transformations", []),
        *work.get("target", []),
        work.get("body_function_relation", ""),
    ]))}")
    for item in payload.get("useful_god_reasoning", []):
        signatures.add(f"useful:{_normalize(str(item.get('candidate', '')))}:{item.get('lens', '')}")
    return {item for item in signatures if item}


def _sentences(text: str) -> list[str]:
    return [item for item in (_normalize(part) for part in re.split(r"[。！？!?；;\n]+", text)) if len(item) >= 6]


def _ngrams(text: str, size: int = 3) -> set[str]:
    normalized = _normalize(text)
    return {normalized[index:index + size] for index in range(max(0, len(normalized) - size + 1))}


def _normalize(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]", "", text).lower()


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / max(1, len(left | right))


def _evidence_ref_allowed(ref: str, *, allowed: set[str]) -> bool:
    if ref in allowed:
        return True
    match = re.fullmatch(r"([FOK])(\d{3})\s*[-–—]\s*\1?(\d{3})", ref)
    if not match:
        return False
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    return end >= start and end - start <= 120 and f"{prefix}{start:03d}" in allowed and f"{prefix}{end:03d}" in allowed


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
