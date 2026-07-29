from __future__ import annotations

from typing import Any

from abu_v60.mingli.domain_contracts import MingliLifeDomainEvidenceVector
from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector
from abu_v60.provenance import content_hash, stable_ref

READING_BRIEF_VERSION = "v60.mingli-reading-brief.001"

_ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
_TIMING_LABELS = {
    "DAYUN": "大运",
    "ANNUAL": "流年",
    "MONTHLY": "流月",
}
_BLOCKER_LABELS = {
    "EFFECT_EVIDENCE_NOT_ADMITTED": "关系是否真正发生作用",
    "CAPACITY_MODEL_NOT_ADMITTED": "承载能力",
    "USABILITY_MODEL_NOT_ADMITTED": "结构可用性",
    "TIMING_ACTIVATION_NOT_ADMITTED": "时序激活",
    "COUNTER_EVIDENCE_MODEL_NOT_ADMITTED": "反证模型",
    "PROFESSIONAL_REVIEW_REQUIRED": "专业准入",
    "SOURCE_MANIFESTATION_EFFECT_UNRESOLVED": "来源显化是否有效",
    "SOURCE_MANIFESTATION_EVIDENCE_ABSENT": "来源显化证据",
    "COMPETING_PATH_SHARED_PARTICIPANTS": "竞争路径共享参与者",
}


class MingliReadingBriefProjector:
    """Turn one admitted Reading into a useful, bounded product summary."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        pillars: dict[str, str],
        fact_count: int,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
        life_domain_vector: MingliLifeDomainEvidenceVector,
        mechanism_comparison: dict[str, Any],
    ) -> dict[str, Any]:
        selected_ref = mechanism_comparison.get("selected_candidate_ref")
        selected_candidate = next(
            (
                candidate
                for candidate in mechanism_vector.candidates
                if candidate.candidate_ref == selected_ref
            ),
            None,
        )
        element_measurements = sorted(
            quant_vector.element_measurements,
            key=lambda item: (-item.total_membership_count, item.element),
        )
        leading_elements = "、".join(
            f"{_ELEMENT_LABELS[item.element]}{item.total_membership_count}份"
            for item in element_measurements[:2]
        )
        timing_coordinates = [
            {
                "layer": _TIMING_LABELS[item.layer],
                "pillar": item.pillar,
                "ten_god_label": item.ten_god_label,
            }
            for item in timing_vector.coordinates
        ]
        domain_windows = [
            {
                "domain": observation.domain,
                "label": observation.label,
                "statement": observation.statement,
                "question": observation.observation_prompt,
                "signal_status": observation.signal_status,
                "evidence_count": len(observation.evidence_refs),
            }
            for observation in life_domain_vector.observations
        ]
        focus = (
            {
                "candidate_ref": selected_candidate.candidate_ref,
                "label": selected_candidate.pattern_label,
                "statement": selected_candidate.structural_statement,
                "rationale": mechanism_comparison.get("rationale_summary"),
                "evidence_refs": list(
                    mechanism_comparison.get("evidence_refs_used")
                    or selected_candidate.support_evidence_refs
                ),
                "meaning": "当前优先核查方向，不是有效做功或人生结果定论。",
                "support": {
                    "direct_fact_count": len(
                        selected_candidate.support_evidence_refs
                    ),
                    "context_fact_count": len(
                        selected_candidate.context_evidence_refs
                    ),
                    "visible_occurrence_count": sum(
                        role.visible_occurrence_count
                        for role in selected_candidate.roles
                    ),
                    "hidden_occurrence_count": sum(
                        role.hidden_occurrence_count
                        for role in selected_candidate.roles
                    ),
                    "unresolved": [
                        _blocker_label(code)
                        for code in selected_candidate.blocker_codes
                    ],
                },
            }
            if selected_candidate is not None
            else {
                "candidate_ref": None,
                "label": "结构候选仍待比较",
                "statement": (
                    f"当前识别到 {len(mechanism_vector.candidates)} 条结构候选，"
                    "尚没有足够依据排列核查顺序。"
                ),
                "rationale": None,
                "evidence_refs": [],
                "meaning": "候选存在不等于机制成立。",
                "support": None,
            }
        )
        identity = {
            "brief_version": READING_BRIEF_VERSION,
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
            "quant_vector_ref": quant_vector.vector_ref,
            "mechanism_vector_ref": mechanism_vector.vector_ref,
            "timing_vector_ref": timing_vector.vector_ref,
            "life_domain_vector_ref": life_domain_vector.vector_ref,
            "comparison_decision_ref": mechanism_comparison.get("decision_ref"),
        }
        return {
            "brief_ref": stable_ref("v60-mingli-reading-brief", identity),
            "brief_hash": content_hash(identity),
            "brief_version": READING_BRIEF_VERSION,
            "headline": (
                f"{quant_vector.day_master_stem}日主 · "
                f"{len(mechanism_vector.candidates)}条结构候选待核查"
            ),
            "qualification": {
                "status": "FORMAL_BOUNDED_READING",
                "fact_count": fact_count,
                "candidate_count": len(mechanism_vector.candidates),
                "timing_coordinate_count": len(timing_coordinates),
                "decision_mode": (
                    mechanism_comparison.get("authority")
                    if mechanism_comparison.get("decision_ref")
                    else "SYSTEM_FACTS_ONLY"
                ),
                "meaning": "正式事实链已建立；未获专业准入的结论继续保持待定。",
            },
            "confirmed": [
                (
                    f"四柱为{pillars['year']}、{pillars['month']}、"
                    f"{pillars['day']}、{pillars['hour']}。"
                ),
                (
                    f"未加权成员统计中以{leading_elements}居前；"
                    "这描述构成，不直接等同旺衰。"
                ),
                (
                    f"当前时序坐标已定位到{len(timing_coordinates)}层，"
                    f"检出{len(timing_vector.relation_evidence)}条关系成员证据。"
                ),
            ],
            "focus": focus,
            "timing": {
                "analysis_date": timing_vector.analysis_date.isoformat(),
                "coordinates": timing_coordinates,
                "meaning": "时序只说明当前观察坐标与关系成员，不自动证明事件会发生。",
            },
            "life_domains": domain_windows,
            "boundaries": [
                "尚未计算专业概率或断命成功率。",
                "尚未确认候选机制的容量、可用性与有效做功。",
                "现实领域只给观察窗口，不把关注方向冒充人生结果。",
                "本摘要只读，不回写 LifeCase 或 V50 命理事实。",
            ],
            "lineage": {
                "reading_ref": reading.reading_ref,
                "reading_hash": reading.reading_hash,
                "quant_vector_ref": quant_vector.vector_ref,
                "mechanism_vector_ref": mechanism_vector.vector_ref,
                "timing_vector_ref": timing_vector.vector_ref,
                "life_domain_vector_ref": life_domain_vector.vector_ref,
                "decision_ref": mechanism_comparison.get("decision_ref"),
            },
            "professional_verdict": False,
            "probability_claim": False,
            "canonical_write_allowed": False,
        }


def _blocker_label(code: str) -> str:
    if code.startswith("VISIBLE_CARRIER_ABSENT:"):
        role = code.rsplit(":", 1)[-1]
        role_label = {
            "SOURCE": "起点",
            "BRIDGE": "承接",
            "TARGET": "去向",
        }.get(role, role)
        return f"{role_label}缺少明干承载"
    return _BLOCKER_LABELS.get(code, code)
