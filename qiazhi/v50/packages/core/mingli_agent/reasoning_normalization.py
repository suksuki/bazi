from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel

from core.life_domains import LifeDomain
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    CognitiveHypothesis,
    DiscriminatingProbe,
    DomainCausalReading,
    DualLensCognitionDraft,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    PatternHypothesisDraft,
    PredictionProbeDraft,
    PriorPrediction,
    WholeChartCognitionDraft,
    WorkPathPortraitDraft,
)
from core.mingli_agent.fact_review import audit_professional_facts, deterministic_fact_conflicts
from core.mingli_agent.reliability import normalize_strategy_dimensions
from core.mingli_agent.reasoning_utils import _hypothesis_signature, _unique
from core.mingli_agent.reasoning_validation import _citation_allowed, _semantic_text_errors


T = TypeVar("T", bound=BaseModel)


def _normalize_work_strategy_dimensions(work: WorkPathPortraitDraft) -> WorkPathPortraitDraft:
    return work.model_copy(update={
        "useful_god_reasoning": normalize_strategy_dimensions(work.useful_god_reasoning),
    })

def _normalize_baseline_cognition(
    *,
    whole: WholeChartCognitionDraft,
    world: ChartWorldInstance,
) -> tuple[MingliCognitiveDraft, PatternHypothesisDraft, list[str]]:
    pattern = PatternHypothesisDraft(
        first_look=whole.first_look,
        whole_chart_thesis=whole.whole_chart_thesis,
        salient_phenomena=whole.salient_phenomena,
        hypotheses=whole.hypotheses,
        selected_hypothesis_id=whole.selected_hypothesis_id,
        evidence_refs=whole.evidence_refs,
    )
    work = _normalize_work_strategy_dimensions(
        WorkPathPortraitDraft(
            work_path=whole.work_path,
            useful_god_reasoning=whole.useful_god_reasoning,
            portrait=whole.portrait,
            unresolved_questions=whole.unresolved_questions,
            evidence_refs=whole.evidence_refs,
        )
    )
    predictions = PredictionProbeDraft(
        prior_predictions=whole.prior_predictions,
        next_probe=whole.next_probe,
    )
    dual_lens = whole.dual_lens if world.ziwei_profile.get("reasoning_ready") else None
    assembled = _assemble_whole_chart(
        pattern=pattern,
        work=work,
        predictions=predictions,
        dual_lens=dual_lens,
    )
    return MingliCognitiveDraft(**assembled.model_dump(mode="json")), pattern, []

def _whole_chart_from_record(record: MingliCognitiveRecord) -> WholeChartCognitionDraft:
    payload = {
        field: getattr(record.cognition, field)
        for field in WholeChartCognitionDraft.model_fields
    }
    whole = WholeChartCognitionDraft.model_validate(payload)
    return WholeChartCognitionDraft.model_validate(sanitize_public_mingli_payload(whole.model_dump(mode="json")))

def sanitize_public_mingli_payload(value: Any, *, _preserve_machine_value: bool = False) -> Any:
    if _preserve_machine_value:
        return value
    if isinstance(value, dict):
        return {
            key: sanitize_public_mingli_payload(
                child,
                _preserve_machine_value=_is_machine_contract_key(key),
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [sanitize_public_mingli_payload(child) for child in value]
    if not isinstance(value, str):
        return value
    text = value
    text = re.sub(r"未记录（仅凭\s*V\d+\s*导入）", "资料未完整记录", text, flags=re.IGNORECASE)
    text = re.sub(r"未记录（\s*V\d+\s*导入）", "资料未完整记录", text, flags=re.IGNORECASE)
    text = re.sub(r"V\d+\s*导入", "历史档案", text, flags=re.IGNORECASE)
    text = re.sub(r"V\d+", "历史版本", text, flags=re.IGNORECASE)
    text = re.sub(r"admin_profile|fixture|runtime|schema", "内部资料", text, flags=re.IGNORECASE)
    return text.replace("会彻底改变", "需要重新评估").replace("彻底改变", "需要重新评估").replace("结构性崩塌", "原有路径可能失效")

def _is_machine_contract_key(key: str) -> bool:
    normalized = key.lower()
    return (
        normalized in {"version", "case_version", "from_case_version", "to_case_version"}
        or normalized.endswith(("_id", "_ids", "_ref", "_refs", "_hash", "_key", "_version", "_versions", "_fingerprint"))
    )

def _domain_context_payload(payload: dict[str, Any], *, relevant_palaces: list[str]) -> dict[str, Any]:
    output = json.loads(json.dumps(payload, ensure_ascii=False))
    profile = output.get("ziwei_profile") or {}
    palaces = profile.get("palaces") or {}
    requested = {
        name.replace("大限", "").replace("流年", "")
        for name in relevant_palaces
    }
    profile["palaces"] = {
        name: value
        for name, value in palaces.items()
        if name in requested
    }
    output["ziwei_profile"] = profile
    return output

def _normalize_domain_reading(reading: DomainCausalReading, *, domain: LifeDomain) -> DomainCausalReading:
    causal_chain = list(reading.causal_chain)
    if len(causal_chain) == 1:
        lines = [item.strip(" -\t") for item in re.split(r"\n+", causal_chain[0]) if item.strip(" -\t")]
        if 2 <= len(lines) <= 6:
            causal_chain = lines
    del domain
    return reading.model_copy(update={"causal_chain": causal_chain})

def _domain_reading_citations(reading: DomainCausalReading) -> set[str]:
    return {
        ref
        for assertion in reading.assertions
        for ref in [*assertion.evidence_refs, *assertion.counter_evidence_refs]
        if ref
    }

def _baseline_cognitive_reference_ids(record: MingliCognitiveRecord) -> set[str]:
    cognition = record.cognition
    refs = {record.record_id}
    refs.update(item.phenomenon_id for item in cognition.salient_phenomena)
    refs.update(item.hypothesis_id for item in cognition.hypotheses)
    refs.update(item.assertion_id for item in cognition.portrait)
    refs.update(item.prediction_id for item in cognition.prior_predictions)
    if cognition.dual_lens is not None:
        refs.update(item.observation_id for item in cognition.dual_lens.palace_observations)
    return {ref for ref in refs if ref}

def _all_citations(draft: MingliCognitiveDraft) -> set[str]:
    refs = set(draft.evidence_refs)
    refs.update(ref for item in draft.salient_phenomena for ref in item.evidence_refs)
    refs.update(ref for item in draft.hypotheses for ref in item.supporting_evidence_refs)
    refs.update(ref for item in draft.hypotheses for ref in item.counter_evidence_refs)
    refs.update(draft.work_path.evidence_refs)
    refs.update(ref for item in draft.useful_god_reasoning for ref in item.evidence_refs)
    refs.update(ref for item in draft.portrait for ref in item.evidence_refs)
    for domain in (draft.career, draft.wealth):
        if domain is not None:
            refs.update(ref for item in domain.assertions for ref in item.evidence_refs)
    refs.update(ref for item in draft.prior_predictions for ref in item.evidence_refs)
    return {ref for ref in refs if ref}

def _domain_evidence_refs(*domains: DomainCausalReading) -> list[str]:
    return _unique([
        ref
        for domain in domains
        for assertion in domain.assertions
        for ref in [*assertion.evidence_refs, *assertion.counter_evidence_refs]
    ])

def _apply_scope_boundary(value: T) -> T:
    """Remove unsupported event drama without rewriting the Mingli reasoning."""

    replacements = {
        "资金链断裂": "资源承载明显失衡",
        "重大健康危机": "未开放领域的外部因素",
        "健康危机": "未开放领域的外部因素",
        "健康受损": "未开放领域的外部因素",
        "筋骨疼痛": "未开放领域的外部因素",
        "肝胆": "未开放领域",
        "疾病": "未开放领域因素",
        "失业": "职业连续性中断",
        "重大挫折": "路径明显受阻",
        "重大变故": "外部条件显著变化",
        "必然破财": "资源风险显著上升",
        "招灾": "风险显著上升",
        "死亡": "极端外部因素",
    }

    def rewrite(item: Any) -> Any:
        if isinstance(item, str):
            for source, target in replacements.items():
                item = item.replace(source, target)
            item = re.sub(r"20\d{2}\s*(?:-|—|–|至|到)\s*20\d{2}\s*年?", "相关行运阶段", item)
            return item
        if isinstance(item, list):
            return [rewrite(child) for child in item]
        if isinstance(item, dict):
            return {key: rewrite(child) for key, child in item.items()}
        return item

    return type(value).model_validate(rewrite(value.model_dump(mode="json")))

def _filter_evidence_refs(value: T, *, world: ChartWorldInstance) -> T:
    """Keep LLM cognition intact while dropping references that do not exist."""

    allowed = set(world.allowed_evidence_refs)

    def rewrite(item: Any, key: str = "") -> Any:
        if isinstance(item, list):
            if key.endswith("evidence_refs"):
                return [ref for ref in item if isinstance(ref, str) and _citation_allowed(ref=ref, allowed=allowed)]
            return [rewrite(child) for child in item]
        if isinstance(item, dict):
            return {child_key: rewrite(child, child_key) for child_key, child in item.items()}
        return item

    return type(value).model_validate(rewrite(value.model_dump(mode="json")))

def _sanitize_work_questions(work: WorkPathPortraitDraft, *, world: ChartWorldInstance) -> WorkPathPortraitDraft:
    questions: list[str] = []
    for question in work.unresolved_questions:
        # A question is not an asserted natal fact, but its premise can still be
        # unusable. Convert only the interrogative wrapper for this product-only
        # sanitation check; Phase-0 raw review never calls this function.
        asserted_premise = re.sub(r"^(?:请确认|请判断)?(?:是否|能否|会否)(?:存在|构成|形成)?", "命局存在", question)
        asserted_premise = asserted_premise.rstrip("？?")
        errors = _semantic_text_errors(text=question, world=world, include_deterministic=False)
        errors.extend(deterministic_fact_conflicts(text=asserted_premise, world=world))
        if not errors:
            questions.append(question)
    return work.model_copy(update={"unresolved_questions": questions})

def _soften_prediction_text(text: str) -> str:
    replacements = {
        "绝对阈值": "明显界限",
        "吉凶判定": "阶段判断",
        "瞬间转为凶险": "短期内明显承压",
        "立即崩塌": "较快失去支撑",
        "结构性崩塌": "结构明显失衡",
        "彻底改变": "明显调整",
        "一定会": "更可能",
        "注定": "更可能",
    }
    softened = text
    for source, target in replacements.items():
        softened = softened.replace(source, target)
    softened = re.sub(r"(?<![不非])必然", "更可能", softened)
    return softened

def _sanitize_preview_line(text: str) -> str:
    cleaned = re.sub(r"[（(\[]\s*(?:F|O|K)\d{3}(?:\s*[,，、]\s*(?:F|O|K)\d{3})*\s*[）)\]]", "", text)
    return re.sub(r"\s{2,}", " ", cleaned).strip()

def _extract_completed_json_string(text: str, *, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*', text)
    if not match or match.end() >= len(text) or text[match.end()] != '"':
        return None
    start = match.end()
    escaped = False
    for index in range(start + 1, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            try:
                value = json.loads(text[start : index + 1])
            except json.JSONDecodeError:
                return None
            return value if isinstance(value, str) else None
    return None

def _extract_first_completed_json_array_string(text: str, *, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[\s*', text)
    if not match or match.end() >= len(text) or text[match.end()] != '"':
        return None
    synthetic = '{"value":' + text[match.end() :]
    return _extract_completed_json_string(synthetic, key="value")

def _preview_is_fact_safe(*, text: str, world: ChartWorldInstance) -> bool:
    if deterministic_fact_conflicts(text=text, world=world):
        return False
    return not any(
        item.severity in {"hard", "major"}
        for item in audit_professional_facts(
            text=text,
            world=world,
            claim_ref="baseline_stream_preview",
        )
    )

def _normalize_prediction_probe(
    predictions: PredictionProbeDraft,
    *,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    world: ChartWorldInstance,
) -> PredictionProbeDraft:
    """Repair presentation bookkeeping locally without asking the model to rethink the chart."""

    safe_predictions: list[PriorPrediction] = []
    seen_claims: set[str] = set()
    for item in predictions.prior_predictions:
        candidate = item.model_copy(update={
            "claim": _soften_prediction_text(item.claim),
            "why_predicted": _soften_prediction_text(item.why_predicted),
            "disconfirming_answer": _soften_prediction_text(item.disconfirming_answer),
        })
        signature = re.sub(r"\s+", "", candidate.claim)
        if not signature or signature in seen_claims:
            continue
        seen_claims.add(signature)
        safe_predictions.append(candidate)
        if len(safe_predictions) == 3:
            break

    selected_ref = pattern.selected_hypothesis_id
    for assertion in work.portrait:
        if len(safe_predictions) == 3:
            break
        claim = _soften_prediction_text(assertion.claim)
        signature = re.sub(r"\s+", "", claim)
        if not signature or signature in seen_claims:
            continue
        candidate = PriorPrediction(
            prediction_id=f"portrait-{assertion.assertion_id}",
            claim=claim,
            why_predicted=_soften_prediction_text(assertion.rationale),
            target_hypothesis_ref=selected_ref,
            evidence_refs=list(assertion.evidence_refs),
            disconfirming_answer=(
                _soften_prediction_text(assertion.falsifiers[0])
                if assertion.falsifiers
                else "如果长期现实表现与这条倾向相反，应降低这条判断的权重。"
            ),
        )
        seen_claims.add(signature)
        safe_predictions.append(candidate)

    probe = predictions.next_probe
    probe_updates = {key: _soften_prediction_text(value) for key, value in probe.expected_updates.items()}
    probe = probe.model_copy(update={
        "question": _soften_prediction_text(probe.question),
        "purpose": _soften_prediction_text(probe.purpose),
        "options": [_soften_prediction_text(item) for item in probe.options],
        "expected_updates": probe_updates,
    })
    hypothesis_refs = [item.hypothesis_id for item in pattern.hypotheses]
    probe_refs = _unique([*probe.distinguishes_hypothesis_refs, *hypothesis_refs])[:2]
    if len(probe_refs) < 2 or len(probe.options) < 2:
        probe_refs = _unique([selected_ref, *hypothesis_refs])[:2]
        options = probe.options[:2] if len(probe.options) >= 2 else [
            "先形成自己的方案，在行动中根据反馈调整",
            "先弄清规则和边界，条件明确后再行动",
        ]
        probe = DiscriminatingProbe(
            probe_id=probe.probe_id or "probe-local-safe",
            question="面对一项既需要独立判断、又有明确规则约束的任务时，你通常更接近哪种做法？",
            purpose="用现实中的处理方式区分当前保留的两个命局解释。",
            distinguishes_hypothesis_refs=probe_refs,
            options=options,
            expected_updates={
                options[0]: f"增强 {probe_refs[0]}" if probe_refs else "增强主动处理解释",
                options[1]: f"增强 {probe_refs[1]}" if len(probe_refs) > 1 else "增强环境约束解释",
            },
        )
    else:
        probe = probe.model_copy(update={"distinguishes_hypothesis_refs": probe_refs})

    return predictions.model_copy(update={
        "prior_predictions": safe_predictions,
        "next_probe": probe,
    })

def _probe_needs_local_fallback(*, probe: DiscriminatingProbe, world: ChartWorldInstance) -> bool:
    del world
    return len(probe.options) < 2 or len(probe.distinguishes_hypothesis_refs) < 2

def _sanitize_pattern_alternatives(pattern: PatternHypothesisDraft, *, world: ChartWorldInstance) -> PatternHypothesisDraft:
    hypotheses: list[CognitiveHypothesis] = []
    for hypothesis in pattern.hypotheses:
        name = hypothesis.name
        if hypothesis.hypothesis_id == pattern.selected_hypothesis_id and "从" in name and ("制杀" in name or "食伤" in name):
            base_name = re.split(r"[（(]", name, maxsplit=1)[0].strip()
            if base_name and "从" not in base_name and ("制杀" in base_name or "食伤" in base_name):
                name = base_name
        cleaned = hypothesis.model_copy(update={
            "name": name,
            "success_conditions": [item for item in hypothesis.success_conditions if not _semantic_text_errors(text=item, world=world)],
            "failure_conditions": [item for item in hypothesis.failure_conditions if not _semantic_text_errors(text=item, world=world)],
        })
        core_text = f"{cleaned.name} {cleaned.thesis} {cleaned.rejection_reason}"
        if cleaned.hypothesis_id != pattern.selected_hypothesis_id and _semantic_text_errors(text=core_text, world=world):
            continue
        hypotheses.append(cleaned)

    selected = next((item for item in hypotheses if item.hypothesis_id == pattern.selected_hypothesis_id), None)
    safe_selected_thesis = selected.thesis if selected and not _semantic_text_errors(text=selected.thesis, world=world) else ""
    first_look = pattern.first_look
    if _semantic_text_errors(text=first_look, world=world) and safe_selected_thesis:
        first_look = safe_selected_thesis
    whole_chart_thesis = pattern.whole_chart_thesis
    if _semantic_text_errors(text=whole_chart_thesis, world=world) and safe_selected_thesis:
        whole_chart_thesis = safe_selected_thesis
    salient = [
        item
        for item in pattern.salient_phenomena
        if not _semantic_text_errors(text=f"{item.observation} {item.why_it_matters}", world=world)
    ]
    return pattern.model_copy(update={
        "first_look": first_look,
        "whole_chart_thesis": whole_chart_thesis,
        "salient_phenomena": salient,
        "hypotheses": hypotheses,
    })

def _repair_pattern_locally(pattern: PatternHypothesisDraft, *, world: ChartWorldInstance) -> PatternHypothesisDraft:
    safe: list[CognitiveHypothesis] = []
    seen_ids: set[str] = set()
    seen_signatures: set[str] = set()
    for hypothesis in sorted(pattern.hypotheses, key=lambda item: item.rank):
        core_text = f"{hypothesis.name} {hypothesis.thesis} {hypothesis.rejection_reason}"
        signature = _hypothesis_signature(hypothesis)
        fact_conflicts = [
            item
            for item in deterministic_fact_conflicts(text=core_text, world=world)
            if not item.startswith("地支关系未建模:")
        ]
        if (
            fact_conflicts
            or hypothesis.hypothesis_id in seen_ids
            or signature in seen_signatures
        ):
            continue
        seen_ids.add(hypothesis.hypothesis_id)
        seen_signatures.add(signature)
        safe.append(hypothesis)

    if not safe:
        return pattern
    selected_id = pattern.selected_hypothesis_id
    if selected_id not in {item.hypothesis_id for item in safe}:
        selected_id = safe[0].hypothesis_id
    normalized = [
        item.model_copy(update={
            "rank": index,
            "status": "primary" if item.hypothesis_id == selected_id else "alternative",
        })
        for index, item in enumerate(safe, start=1)
    ]
    selected = next(item for item in normalized if item.hypothesis_id == selected_id)
    first_look = pattern.first_look
    if any(not item.startswith("地支关系未建模:") for item in deterministic_fact_conflicts(text=first_look, world=world)):
        first_look = selected.thesis
    whole_chart_thesis = pattern.whole_chart_thesis
    if any(not item.startswith("地支关系未建模:") for item in deterministic_fact_conflicts(text=whole_chart_thesis, world=world)):
        whole_chart_thesis = selected.thesis
    return pattern.model_copy(update={
        "first_look": first_look,
        "whole_chart_thesis": whole_chart_thesis,
        "hypotheses": normalized,
        "selected_hypothesis_id": selected_id,
    })

def _normalize_dual_probe_refs(
    dual_lens: DualLensCognitionDraft,
    *,
    pattern: PatternHypothesisDraft,
) -> DualLensCognitionDraft:
    probe = dual_lens.cross_lens_probe
    if len(probe.distinguishes_hypothesis_refs) >= 2:
        return dual_lens
    refs = _unique([*probe.distinguishes_hypothesis_refs, pattern.selected_hypothesis_id, "ziwei:current_stage"])
    return dual_lens.model_copy(update={
        "cross_lens_probe": probe.model_copy(update={"distinguishes_hypothesis_refs": refs}),
    })

def _assemble_whole_chart(
    *,
    pattern: PatternHypothesisDraft,
    work: WorkPathPortraitDraft,
    predictions: PredictionProbeDraft,
    dual_lens: DualLensCognitionDraft | None,
) -> WholeChartCognitionDraft:
    pattern_payload = pattern.model_dump(mode="json")
    pattern_payload.pop("evidence_refs", None)
    return WholeChartCognitionDraft(
        **pattern_payload,
        work_path=work.work_path,
        useful_god_reasoning=work.useful_god_reasoning,
        portrait=work.portrait,
        prior_predictions=predictions.prior_predictions,
        next_probe=predictions.next_probe,
        dual_lens=dual_lens,
        unresolved_questions=work.unresolved_questions,
        evidence_refs=_unique([
            *pattern.evidence_refs,
            *work.evidence_refs,
            *(dual_lens.evidence_refs if dual_lens else []),
        ]),
    )

def _normalize_pattern_bookkeeping(pattern: PatternHypothesisDraft) -> PatternHypothesisDraft:
    salient = list(pattern.salient_phenomena[:3])
    refs = _unique([
        *pattern.evidence_refs,
        *(ref for item in salient for ref in item.evidence_refs),
        *(ref for item in pattern.hypotheses for ref in item.supporting_evidence_refs),
        *(ref for item in pattern.hypotheses for ref in item.counter_evidence_refs),
    ])
    return pattern.model_copy(update={"salient_phenomena": salient, "evidence_refs": refs})
