from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

from core.life_domains import LifeDomain
from core.mingli_agent.contracts import (
    DomainCausalReading,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    UsefulGodReasoning,
)


_DIMENSION_QUESTIONS = {
    "climate": "原局寒暖燥湿需要怎样调节",
    "support_balance": "日主承载与扶抑关系如何平衡",
    "structure": "格局成立与破坏需要什么条件",
    "transformation": "冲突力量如何制化或通关",
    "work_path": "主做功闭环需要什么条件",
    "timing": "当前岁运阶段应增强或控制什么",
    "domain": "当前人生专题在什么条件下成立",
}


def normalize_strategy_dimensions(items: Iterable[UsefulGodReasoning]) -> list[UsefulGodReasoning]:
    output: list[UsefulGodReasoning] = []
    for item in items:
        lens = {"seasonal": "climate", "repair": "transformation"}.get(item.lens, item.lens)
        scope = (
            "current_timing" if lens == "timing"
            else "domain_condition" if lens == "domain"
            else "natal"
        )
        output.append(item.model_copy(update={
            "lens": lens,
            "scope": scope,
            "question_answered": item.question_answered or _DIMENSION_QUESTIONS.get(lens, ""),
        }))
    return output


def cognition_semantic_signature(cognition: MingliCognitiveDraft) -> str:
    selected = next(
        (item for item in cognition.hypotheses if item.hypothesis_id == cognition.selected_hypothesis_id),
        cognition.hypotheses[0] if cognition.hypotheses else None,
    )
    payload = {
        "selected_hypothesis": {
            "name": selected.name if selected else "",
            "thesis": selected.thesis if selected else "",
            "confidence": selected.confidence if selected else "",
        },
        "work_path": {
            "source": cognition.work_path.source,
            "transformations": cognition.work_path.transformations,
            "target": cognition.work_path.target,
            "closure": cognition.work_path.closure,
            "success_conditions": cognition.work_path.success_conditions,
            "failure_conditions": cognition.work_path.failure_conditions,
        },
        "strategies": sorted(
            (
                item.lens,
                item.scope,
                item.candidate,
                item.role,
                tuple(item.applicable_conditions),
                tuple(item.invalidating_conditions),
            )
            for item in cognition.useful_god_reasoning
        ),
        "competing": sorted(
            (item.name, item.thesis, item.confidence)
            for item in cognition.hypotheses
            if item.hypothesis_id != cognition.selected_hypothesis_id
        ),
        "unknowns": sorted(cognition.unresolved_questions),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def domain_request_fingerprint(
    *,
    record: MingliCognitiveRecord,
    world_id: str,
    domain: LifeDomain,
    user_question: str,
    case_version: str,
    chart_version_id: str = "",
    temporal_scope: str = "current",
    implementation_versions: dict[str, str] | None = None,
    input_context_hash: str = "",
) -> str:
    payload = {
        "world_id": world_id,
        "record_id": record.record_id,
        "baseline_signature": record.reliability_signature or cognition_semantic_signature(record.cognition),
        "case_version": case_version,
        "chart_version_id": chart_version_id,
        "domain": domain.value,
        "user_question": " ".join(user_question.strip().split()),
        "temporal_scope": temporal_scope,
        "implementation_versions": implementation_versions or {},
        "input_context_hash": input_context_hash,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def domain_baseline_override_reason(
    *,
    reading: DomainCausalReading,
    record: MingliCognitiveRecord,
) -> str:
    """Detect explicit baseline replacement, not ordinary domain qualification."""

    payload = json.dumps(reading.model_dump(mode="json"), ensure_ascii=False)
    explicit_override = re.search(
        r"(?:推翻|改写|取代|否定)(?:原有|原局|整盘|基线|主假设|主做功)|"
        r"(?:原有|原局|整盘|基线|主假设|主做功)[^。；，]{0,12}(?:不成立|错误|应改为)",
        payload,
    )
    if explicit_override:
        return explicit_override.group(0)

    primary = next(
        (item for item in record.cognition.hypotheses if item.hypothesis_id == record.cognition.selected_hypothesis_id),
        None,
    )
    if primary:
        for alternative in record.cognition.hypotheses:
            if alternative.hypothesis_id == primary.hypothesis_id or not alternative.name.strip():
                continue
            if alternative.name in payload and re.search(
                rf"{re.escape(alternative.name)}[^。；，]{{0,16}}(?:才是|应为|取代|而非)",
                payload,
            ):
                return f"专题把替代假设“{alternative.name}”提升为整盘主线"
    return ""
