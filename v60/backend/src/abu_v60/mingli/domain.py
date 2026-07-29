from __future__ import annotations

from dataclasses import dataclass

from abu_v60.mingli.domain_contracts import (
    LifeDomainObservation,
    MingliLifeDomainEvidenceVector,
)
from abu_v60.mingli.mechanism_contracts import MingliMechanismEvidenceVector
from abu_v60.mingli.timing_contracts import MingliTimingEvidenceVector
from abu_v60.provenance import content_hash

LIFE_DOMAIN_EVIDENCE_COMPILER_VERSION = (
    "v60.mingli-life-domain-evidence-compiler.001"
)
LIFE_DOMAIN_EVIDENCE_POLICY_REF = "v60.life-domain-attention-policy.001"


@dataclass(frozen=True)
class _DomainDefinition:
    domain: str
    label: str
    mechanism_pattern_refs: tuple[str, ...]
    timing_labels: tuple[str, ...]
    statement: str
    observation_prompt: str


_DOMAIN_DEFINITIONS = (
    _DomainDefinition(
        domain="career",
        label="事业与职责",
        mechanism_pattern_refs=(
            "bazi.mechanism.output-to-pressure@1",
            "bazi.mechanism.pressure-resource-self@1",
            "bazi.mechanism.wealth-to-pressure@1",
        ),
        timing_labels=("七杀", "伤官", "偏印", "正印", "正官", "食神"),
        statement=(
            "当前证据适合观察职责、交付方式与评价标准是否出现变化；"
            "它不等于职位或成败已经确定。"
        ),
        observation_prompt=(
            "这个观察窗口里，最先可核验的是职责、交付方式，还是评价标准的变化？"
        ),
    ),
    _DomainDefinition(
        domain="wealth",
        label="成果与交换",
        mechanism_pattern_refs=(
            "bazi.mechanism.output-to-wealth@1",
            "bazi.mechanism.wealth-to-pressure@1",
        ),
        timing_labels=("伤官", "偏财", "正财", "食神"),
        statement=(
            "当前证据适合观察成果是否形成可归因的交换或收入；"
            "它不等于财务结果已经发生。"
        ),
        observation_prompt=(
            "这个观察窗口里，成果会先形成可归因交换、改变外部要求，还是尚未落地？"
        ),
    ),
    _DomainDefinition(
        domain="relationship",
        label="关系与边界",
        mechanism_pattern_refs=(),
        timing_labels=("七杀", "偏财", "劫财", "正官", "正财", "比肩"),
        statement=(
            "当前只具备关系角色的时序标签证据，尚无获准的关系机制；"
            "不能由此直接推导伴侣、承诺或关系走向。"
        ),
        observation_prompt=(
            "这个观察窗口里，现实中最先变化的是互动频率、边界，还是承诺方式？"
        ),
    ),
)


class MingliLifeDomainEvidenceCompiler:
    """Route admitted evidence into user-facing domains without predicting events."""

    def compile(
        self,
        *,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> MingliLifeDomainEvidenceVector:
        if (
            mechanism_vector.case_ref != timing_vector.case_ref
            or mechanism_vector.chart_version_ref != timing_vector.chart_version_ref
        ):
            raise ValueError("life_domain_vector_lineage_mismatch")

        policy_payload = {
            "policy_ref": LIFE_DOMAIN_EVIDENCE_POLICY_REF,
            "compiler_version": LIFE_DOMAIN_EVIDENCE_COMPILER_VERSION,
            "mechanism_profile_ref": mechanism_vector.mechanism_profile_ref,
            "timing_profile_ref": timing_vector.timing_profile_ref,
            "definitions": [
                {
                    "domain": item.domain,
                    "mechanism_pattern_refs": item.mechanism_pattern_refs,
                    "timing_labels": item.timing_labels,
                }
                for item in _DOMAIN_DEFINITIONS
            ],
            "semantics": "ATTENTION_WINDOW_ONLY",
            "forbidden": (
                "auspiciousness",
                "event_prediction",
                "professional_mechanism_verdict",
                "probability",
                "relationship_outcome",
            ),
        }
        observations = tuple(
            self._compile_observation(
                definition=definition,
                mechanism_vector=mechanism_vector,
                timing_vector=timing_vector,
            )
            for definition in _DOMAIN_DEFINITIONS
        )
        return MingliLifeDomainEvidenceVector.issue(
            case_ref=timing_vector.case_ref,
            chart_version_ref=timing_vector.chart_version_ref,
            life_case_revision_ref=timing_vector.life_case_revision_ref,
            mechanism_vector_ref=mechanism_vector.vector_ref,
            mechanism_vector_hash=mechanism_vector.vector_hash,
            timing_vector_ref=timing_vector.vector_ref,
            timing_vector_hash=timing_vector.vector_hash,
            policy_ref=LIFE_DOMAIN_EVIDENCE_POLICY_REF,
            policy_hash=content_hash(policy_payload),
            observations=observations,
        )

    @staticmethod
    def _compile_observation(
        *,
        definition: _DomainDefinition,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> LifeDomainObservation:
        candidates = tuple(
            candidate
            for candidate in mechanism_vector.candidates
            if candidate.pattern_ref in definition.mechanism_pattern_refs
        )
        candidate_refs = tuple(
            sorted(candidate.candidate_ref for candidate in candidates)
        )
        coordinates = tuple(
            coordinate
            for coordinate in timing_vector.coordinates
            if coordinate.ten_god_label in definition.timing_labels
        )
        coordinate_refs = tuple(
            sorted(coordinate.coordinate_ref for coordinate in coordinates)
        )
        overlaps = tuple(
            overlap
            for overlap in timing_vector.candidate_overlaps
            if overlap.candidate_ref in candidate_refs
            and overlap.timing_coordinate_ref in coordinate_refs
        )
        overlap_refs = tuple(sorted(overlap.overlap_ref for overlap in overlaps))
        related_timing_evidence = tuple(
            item
            for item in timing_vector.relation_evidence
            if item.timing_coordinate_ref in coordinate_refs
        )
        evidence_refs = tuple(
            sorted(
                {
                    mechanism_vector.vector_ref,
                    timing_vector.vector_ref,
                    *coordinate_refs,
                    *overlap_refs,
                    *(
                        evidence_ref
                        for candidate in candidates
                        for evidence_ref in candidate.support_evidence_refs
                    ),
                    *(item.evidence_ref for item in related_timing_evidence),
                }
            )
        )
        if overlap_refs:
            signal_status = "TIMING_MECHANISM_OVERLAP"
        elif coordinate_refs and candidate_refs:
            signal_status = "TIMING_AND_MECHANISM_PRESENT"
        elif coordinate_refs:
            signal_status = "TIMING_ONLY"
        elif candidate_refs:
            signal_status = "MECHANISM_ONLY"
        else:
            signal_status = "NO_BOUNDED_EVIDENCE"
        return LifeDomainObservation.issue(
            domain=definition.domain,
            label=definition.label,
            signal_status=signal_status,
            statement=definition.statement,
            observation_prompt=definition.observation_prompt,
            timing_coordinate_refs=coordinate_refs,
            mechanism_candidate_refs=candidate_refs,
            overlap_refs=overlap_refs,
            evidence_refs=evidence_refs,
            unresolved_dimensions=(
                "activation",
                "direction",
                "event_outcome",
                "mechanism_capacity",
                "probability",
                "usability",
            ),
        )
