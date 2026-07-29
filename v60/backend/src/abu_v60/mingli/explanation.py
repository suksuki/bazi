from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.mingli.domain_contracts import MingliLifeDomainEvidenceVector
from abu_v60.mingli.explanation_contracts import (
    MingliEvidenceCitation,
    MingliExplanationClaim,
    MingliExplanationEnvelope,
)
from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector
from abu_v60.provenance import stable_ref

_SLOT_LABELS = {"year": "年", "month": "月", "day": "日", "hour": "时"}
_LAYER_LABELS = {"DAYUN": "大运", "ANNUAL": "流年", "MONTHLY": "流月"}
_RELATION_LABELS = {
    "same_branch_membership": "同支",
    "six_clash_membership": "六冲",
    "six_harmony_membership": "六合",
}
_UNRESOLVED_LABELS = {
    "activation": "当前时序是否真正激活结构",
    "direction": "变化最终朝哪个方向发展",
    "event_outcome": "现实事件结果",
    "mechanism_capacity": "结构是否具有足够承载能力",
    "probability": "事件发生概率",
    "usability": "结构是否可用",
    "EFFECT_EVIDENCE_NOT_ADMITTED": "关系是否真正发生作用",
    "CAPACITY_MODEL_NOT_ADMITTED": "承载能力模型",
    "USABILITY_MODEL_NOT_ADMITTED": "结构可用性",
    "TIMING_ACTIVATION_NOT_ADMITTED": "时序激活",
    "COUNTER_EVIDENCE_MODEL_NOT_ADMITTED": "反证模型",
    "PROFESSIONAL_REVIEW_REQUIRED": "专业准入",
    "SOURCE_MANIFESTATION_EFFECT_UNRESOLVED": "来源显化是否有效",
    "SOURCE_MANIFESTATION_EVIDENCE_ABSENT": "来源显化证据",
    "COMPETING_PATH_SHARED_PARTICIPANTS": "竞争路径共享参与者",
}


class MingliExplanationProjector:
    """Explain one Reading without producing a second interpretation."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        facts: Sequence[Mapping[str, Any]],
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
        life_domain_vector: MingliLifeDomainEvidenceVector,
        mechanism_comparison: Mapping[str, Any],
    ) -> MingliExplanationEnvelope:
        if (
            reading.case_ref != mechanism_vector.case_ref
            or reading.case_ref != timing_vector.case_ref
            or reading.case_ref != life_domain_vector.case_ref
        ):
            raise ValueError("mingli_explanation_lineage_mismatch")
        evidence = self._evidence_index(
            facts=facts,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
        )
        foundation_claim = self._foundation_claim(reading=reading, facts=facts)
        mechanism_claims = tuple(
            self._mechanism_claim(
                reading=reading,
                candidate=candidate,
                evidence=evidence,
                comparison=mechanism_comparison,
            )
            for candidate in mechanism_vector.candidates
        )
        domain_claims = tuple(
            self._domain_claim(
                reading=reading,
                observation=observation,
                evidence=evidence,
            )
            for observation in life_domain_vector.observations
        )
        claims = (foundation_claim, *mechanism_claims, *domain_claims)
        authority = mechanism_comparison.get("authority") or "SYSTEM_FACTS_ONLY"
        return MingliExplanationEnvelope.issue(
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            claims=claims,
            confirmed_count=1,
            candidate_count=len(mechanism_claims),
            observation_count=len(domain_claims),
            decision_authority=authority,
            decision_meaning=(
                "系统仅确认可复算事实。"
                if authority == "SYSTEM_FACTS_ONLY"
                else "规则只排列核查顺序，不确认有效做功。"
                if authority == "RULE_ENGINE"
                else "Gemma4 只在给定证据中比较核查顺序，不创造事实或结论。"
            ),
        )

    @staticmethod
    def _foundation_claim(
        *,
        reading: MingliReadingEnvelope,
        facts: Sequence[Mapping[str, Any]],
    ) -> MingliExplanationClaim:
        pillar_facts = tuple(fact for fact in facts if fact.get("fact_type") == "pillar_identity")
        citations = tuple(_fact_citation(fact) for fact in pillar_facts)
        identity = {
            "reading_ref": reading.reading_ref,
            "claim_kind": "CONFIRMED_FOUNDATION",
            "evidence_refs": [item.evidence_ref for item in citations],
        }
        return MingliExplanationClaim(
            claim_ref=stable_ref("v60-mingli-explanation-claim", identity),
            claim_kind="CONFIRMED_FOUNDATION",
            title="命盘基础事实",
            statement="四柱身份由出生输入与固定历法算法生成，可以按同一版本重复计算。",
            epistemic_status="CONFIRMED",
            decision_basis="SYSTEM_DETERMINISTIC",
            support_evidence=citations,
            counter_evidence=(),
            counter_evidence_status="AVAILABLE",
            unresolved_questions=(),
            competing_claim_refs=(),
            source_profile_refs=(reading.foundation_profile.profile_ref,),
            boundary="确认四柱不等于已经确认旺衰、做功或人生事件。",
        )

    @staticmethod
    def _mechanism_claim(
        *,
        reading: MingliReadingEnvelope,
        candidate: MechanismCandidateEvidence,
        evidence: Mapping[str, MingliEvidenceCitation],
        comparison: Mapping[str, Any],
    ) -> MingliExplanationClaim:
        support = _resolve_citations(
            (*candidate.support_evidence_refs, *candidate.context_evidence_refs),
            evidence,
        )
        counter = _resolve_citations(candidate.counter_evidence_refs, evidence)
        selected = comparison.get("selected_candidate_ref") == candidate.candidate_ref
        basis = (
            "BOUNDED_ATTENTION_COMPARISON"
            if selected and comparison.get("decision_ref")
            else "VERSIONED_RULE_CANDIDATE"
        )
        identity = {
            "reading_ref": reading.reading_ref,
            "candidate_ref": candidate.candidate_ref,
            "support_refs": [item.evidence_ref for item in support],
            "counter_refs": [item.evidence_ref for item in counter],
        }
        return MingliExplanationClaim(
            claim_ref=stable_ref("v60-mingli-explanation-claim", identity),
            claim_kind="MECHANISM_CANDIDATE",
            title=candidate.pattern_label,
            statement=candidate.structural_statement,
            epistemic_status="CANDIDATE",
            decision_basis=basis,
            support_evidence=support,
            counter_evidence=counter,
            counter_evidence_status=("AVAILABLE" if counter else candidate.counter_evidence_status),
            unresolved_questions=tuple(_unresolved_label(code) for code in candidate.blocker_codes),
            competing_claim_refs=candidate.competing_candidate_refs,
            source_profile_refs=(
                reading.mechanism_evidence_profile.profile_ref,
                candidate.pattern_ref,
            ),
            boundary=(
                f"{candidate.forbidden_shortcut} 当前只能作为结构候选，"
                "不能直接写成有效做功或人生结论。"
            ),
        )

    @staticmethod
    def _domain_claim(
        *,
        reading: MingliReadingEnvelope,
        observation: Any,
        evidence: Mapping[str, MingliEvidenceCitation],
    ) -> MingliExplanationClaim:
        support = _resolve_citations(observation.evidence_refs, evidence)
        identity = {
            "reading_ref": reading.reading_ref,
            "observation_ref": observation.observation_ref,
            "support_refs": [item.evidence_ref for item in support],
        }
        return MingliExplanationClaim(
            claim_ref=stable_ref("v60-mingli-explanation-claim", identity),
            claim_kind="LIFE_DOMAIN_WINDOW",
            title=observation.label,
            statement=observation.statement,
            epistemic_status="OBSERVE",
            decision_basis="ATTENTION_WINDOW_POLICY",
            support_evidence=support,
            counter_evidence=(),
            counter_evidence_status="NOT_ADMITTED",
            unresolved_questions=tuple(
                _unresolved_label(item) for item in observation.unresolved_dimensions
            ),
            competing_claim_refs=observation.mechanism_candidate_refs,
            source_profile_refs=(
                reading.mechanism_evidence_profile.profile_ref,
                reading.timing_evidence_profile.profile_ref,
            ),
            boundary=(
                f"观察问题：{observation.observation_prompt} 它用于收集现实反馈，不是事件预言。"
            ),
        )

    @staticmethod
    def _evidence_index(
        *,
        facts: Sequence[Mapping[str, Any]],
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> dict[str, MingliEvidenceCitation]:
        index = {str(fact["fact_ref"]): _fact_citation(fact) for fact in facts}
        index.update(
            {
                item.evidence_ref: MingliEvidenceCitation(
                    evidence_ref=item.evidence_ref,
                    evidence_kind="SOURCE_MANIFESTATION",
                    summary=(
                        f"{_SLOT_LABELS[item.visible_slot]}干{item.visible_stem}与"
                        f"{_SLOT_LABELS[item.source_slot]}支{item.source_branch}所藏"
                        f"{item.hidden_stem}存在"
                        f"{'同干' if item.source_match_kind == 'EXACT_IDENTITY' else '同五行'}"
                        "来源证据；效力未确认。"
                    ),
                    epistemic_status="MEMBERSHIP_ONLY",
                    source_refs=(quant_vector.quant_profile_ref, *item.evidence_refs),
                )
                for item in quant_vector.source_manifestation_evidence
            }
        )
        index.update(
            {
                item.candidate_ref: MingliEvidenceCitation(
                    evidence_ref=item.candidate_ref,
                    evidence_kind="MECHANISM_CANDIDATE",
                    summary=f"{item.pattern_label}是结构候选，尚未确认有效性。",
                    epistemic_status="CANDIDATE_ONLY",
                    source_refs=(mechanism_vector.mechanism_profile_ref,),
                )
                for item in mechanism_vector.candidates
            }
        )
        index.update(
            {
                item.coordinate_ref: MingliEvidenceCitation(
                    evidence_ref=item.coordinate_ref,
                    evidence_kind="TIMING_COORDINATE",
                    summary=(
                        f"当前{_LAYER_LABELS[item.layer]}坐标为"
                        f"{item.pillar}（{item.ten_god_label}）。"
                    ),
                    epistemic_status="COORDINATE_ONLY",
                    source_refs=(timing_vector.timing_profile_ref,),
                )
                for item in timing_vector.coordinates
            }
        )
        index.update(
            {
                item.evidence_ref: MingliEvidenceCitation(
                    evidence_ref=item.evidence_ref,
                    evidence_kind="TIMING_RELATION",
                    summary=(
                        f"{_LAYER_LABELS[item.timing_layer]}支{item.timing_branch}与"
                        f"原局{_SLOT_LABELS[item.natal_slot]}支{item.natal_branch}"
                        f"存在{_RELATION_LABELS[item.relation_type]}成员关系；作用未确认。"
                    ),
                    epistemic_status="MEMBERSHIP_ONLY",
                    source_refs=(item.rule_ref, *item.evidence_refs),
                )
                for item in timing_vector.relation_evidence
            }
        )
        index.update(
            {
                item.overlap_ref: MingliEvidenceCitation(
                    evidence_ref=item.overlap_ref,
                    evidence_kind="TIMING_CANDIDATE_OVERLAP",
                    summary=(
                        f"{_LAYER_LABELS[item.timing_layer]}的"
                        f"{item.timing_ten_god_label}与候选角色标签交叠；"
                        "不等于时序已经激活该候选。"
                    ),
                    epistemic_status="CANDIDATE_ONLY",
                    source_refs=(timing_vector.timing_profile_ref, item.candidate_ref),
                )
                for item in timing_vector.candidate_overlaps
            }
        )
        index[mechanism_vector.vector_ref] = MingliEvidenceCitation(
            evidence_ref=mechanism_vector.vector_ref,
            evidence_kind="VERSIONED_VECTOR",
            summary="当前结构候选来自同一份版本化机制证据向量。",
            epistemic_status="CANDIDATE_ONLY",
            source_refs=(mechanism_vector.mechanism_profile_ref,),
        )
        index[timing_vector.vector_ref] = MingliEvidenceCitation(
            evidence_ref=timing_vector.vector_ref,
            evidence_kind="VERSIONED_VECTOR",
            summary="当前时序材料来自同一份版本化时序证据向量。",
            epistemic_status="COORDINATE_ONLY",
            source_refs=(timing_vector.timing_profile_ref,),
        )
        return index


def _fact_citation(fact: Mapping[str, Any]) -> MingliEvidenceCitation:
    payload = fact.get("fact_json", {})
    fact_type = str(fact["fact_type"])
    slot = str(payload.get("slot") or _slot_from_ref(str(fact["subject_ref"])))
    slot_label = _SLOT_LABELS.get(slot, slot)
    if fact_type == "pillar_identity":
        summary = f"{slot_label}柱为{payload['pillar']}。"
    elif fact_type == "stem_element":
        summary = f"{slot_label}干{payload['stem']}属{_element_label(payload['element'])}。"
    elif fact_type == "stem_polarity":
        summary = (
            f"{slot_label}干{payload['stem']}为{'阳' if payload['polarity'] == 'yang' else '阴'}。"
        )
    elif fact_type == "hidden_stem_membership":
        summary = (
            f"{slot_label}支{payload['branch']}含藏干{payload['hidden_stem']}；这里只确认成员关系。"
        )
    else:
        left = _SLOT_LABELS.get(str(payload["left_slot"]), str(payload["left_slot"]))
        right = _SLOT_LABELS.get(str(payload["right_slot"]), str(payload["right_slot"]))
        relation = "六冲" if fact_type == "six_clash_membership" else "六合"
        summary = (
            f"{left}支{payload['left_branch']}与{right}支{payload['right_branch']}"
            f"属于{relation}成员关系；作用未确认。"
        )
    return MingliEvidenceCitation(
        evidence_ref=str(fact["fact_ref"]),
        evidence_kind="DETERMINISTIC_FACT",
        summary=summary,
        epistemic_status=(
            "CONFIRMED"
            if fact_type in {"pillar_identity", "stem_element", "stem_polarity"}
            else "MEMBERSHIP_ONLY"
        ),
        source_refs=(str(fact["source_ref"]),),
    )


def _resolve_citations(
    refs: Sequence[str],
    evidence: Mapping[str, MingliEvidenceCitation],
) -> tuple[MingliEvidenceCitation, ...]:
    return tuple(evidence[ref] for ref in dict.fromkeys(refs) if ref in evidence)


def _unresolved_label(code: str) -> str:
    if code.startswith("VISIBLE_CARRIER_ABSENT:"):
        role = {"SOURCE": "起点", "BRIDGE": "承接", "TARGET": "去向"}.get(
            code.rsplit(":", 1)[-1],
            code,
        )
        return f"{role}缺少明干承载"
    return _UNRESOLVED_LABELS.get(code, code)


def _slot_from_ref(subject_ref: str) -> str:
    parts = subject_ref.split(":")
    return parts[1] if len(parts) > 1 else subject_ref


def _element_label(element: Any) -> str:
    return {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }.get(str(element), str(element))
