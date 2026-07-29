from __future__ import annotations

from collections.abc import Sequence

from abu_v60.mingli.mechanism_contracts import (
    MechanismCandidateEvidence,
    MingliMechanismEvidenceVector,
)
from abu_v60.mingli.mechanism_qualification_contracts import (
    CandidateMechanismQualification,
    MechanismQualificationCheck,
    MingliMechanismQualificationEnvelope,
)
from abu_v60.mingli.quant_contracts import MingliQuantFoundationVector
from abu_v60.mingli.reading import MingliReadingEnvelope
from abu_v60.mingli.timing_contracts import (
    MingliTimingEvidenceVector,
    TimingCandidateOverlap,
)


class MingliMechanismQualificationProjector:
    """Show what each candidate has and lacks without deciding that it works."""

    def project(
        self,
        *,
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> MingliMechanismQualificationEnvelope:
        self._validate_lineage(
            reading=reading,
            quant_vector=quant_vector,
            mechanism_vector=mechanism_vector,
            timing_vector=timing_vector,
        )
        candidates = tuple(
            self._candidate(
                candidate=candidate,
                overlaps=tuple(
                    item
                    for item in timing_vector.candidate_overlaps
                    if item.candidate_ref == candidate.candidate_ref
                ),
            )
            for candidate in mechanism_vector.candidates
        )
        summary = (
            f"{len(candidates)} 条候选已具备结构材料；"
            "根源承接、时序激活、反证、作用与容量仍需分别核证。"
            if candidates
            else "当前命盘没有达到本版最低结构门槛的候选机制。"
        )
        return MingliMechanismQualificationEnvelope.issue(
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            quant_vector_ref=quant_vector.vector_ref,
            quant_vector_hash=quant_vector.vector_hash,
            mechanism_vector_ref=mechanism_vector.vector_ref,
            mechanism_vector_hash=mechanism_vector.vector_hash,
            timing_vector_ref=timing_vector.vector_ref,
            timing_vector_hash=timing_vector.vector_hash,
            candidates=tuple(sorted(candidates, key=lambda item: item.candidate_ref)),
            summary=summary,
        )

    @staticmethod
    def _validate_lineage(
        *,
        reading: MingliReadingEnvelope,
        quant_vector: MingliQuantFoundationVector,
        mechanism_vector: MingliMechanismEvidenceVector,
        timing_vector: MingliTimingEvidenceVector,
    ) -> None:
        if len(
            {
                reading.case_ref,
                quant_vector.case_ref,
                mechanism_vector.case_ref,
                timing_vector.case_ref,
            }
        ) != 1:
            raise ValueError("mechanism_qualification_case_lineage_mismatch")
        if len(
            {
                reading.chart_version_ref,
                quant_vector.chart_version_ref,
                mechanism_vector.chart_version_ref,
                timing_vector.chart_version_ref,
            }
        ) != 1:
            raise ValueError("mechanism_qualification_chart_lineage_mismatch")
        expected_refs = (
            (reading.quant_vector_ref, quant_vector.vector_ref),
            (reading.mechanism_vector_ref, mechanism_vector.vector_ref),
            (reading.timing_vector_ref, timing_vector.vector_ref),
        )
        expected_hashes = (
            (reading.quant_vector_hash, quant_vector.vector_hash),
            (reading.mechanism_vector_hash, mechanism_vector.vector_hash),
            (reading.timing_vector_hash, timing_vector.vector_hash),
        )
        if any(left != right for left, right in (*expected_refs, *expected_hashes)):
            raise ValueError("mechanism_qualification_vector_lineage_mismatch")

    def _candidate(
        self,
        *,
        candidate: MechanismCandidateEvidence,
        overlaps: Sequence[TimingCandidateOverlap],
    ) -> CandidateMechanismQualification:
        source_role = next(role for role in candidate.roles if role.role_id == "SOURCE")
        source_refs = source_role.manifestation_evidence_refs
        timing_refs = tuple(sorted(item.overlap_ref for item in overlaps))
        checks = (
            MechanismQualificationCheck(
                dimension="STRUCTURAL_ROLES",
                label="结构角色",
                status="PRESENT",
                evidence_refs=candidate.support_evidence_refs,
                meaning="起点、承接与去向在同一版本命盘中均有成员事实。",
                next_evidence="继续核对这些角色之间是否具有可承载的真实作用关系。",
                falsifier="任一必要角色在同一版本命盘中不存在时，撤销该结构候选。",
            ),
            MechanismQualificationCheck(
                dimension="SOURCE_MANIFESTATION",
                label="根源与显化",
                status="PARTIAL" if source_refs else "MISSING",
                evidence_refs=source_refs,
                meaning=(
                    "已见来源成员与明干载体的对应，但尚未证明根可用、承载充足。"
                    if source_refs
                    else "当前没有来源成员与明干载体的直接对应证据。"
                ),
                next_evidence="需要准入根、透、月令及受损状态的证据规则。",
                falsifier="来源成员不存在，或正式受损规则否定其承接时，该项不成立。",
            ),
            MechanismQualificationCheck(
                dimension="TIMING_OVERLAP",
                label="时序交叠",
                status="PARTIAL" if timing_refs else "MISSING",
                evidence_refs=timing_refs,
                meaning=(
                    "当前大运、流年或流月出现同角色标签；这只是交叠，不等于激活。"
                    if timing_refs
                    else "当前冻结时序中未出现与该候选直接重合的角色标签。"
                ),
                next_evidence="需要正式激活规则与同一观察窗口内的现实事件证据。",
                falsifier="观察窗口内没有相应时序条件，或后续事件未呈现预期作用时，该项被削弱。",
            ),
            MechanismQualificationCheck(
                dimension="COUNTER_EVIDENCE",
                label="反证",
                status="NOT_ADMITTED",
                evidence_refs=candidate.counter_evidence_refs,
                meaning="反证模型尚未正式准入，不能把没有反证记录当成支持。",
                next_evidence="需要版本化反证规则，以及与候选逐项对应的反例证据。",
                falsifier="一旦准入的反证命中必要角色、承接或事件结果，候选必须降级。",
            ),
            MechanismQualificationCheck(
                dimension="EFFECT",
                label="实际作用",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="结构存在不等于关系已经发生作用。",
                next_evidence="需要有来源的作用方向、完成条件和结果证据规则。",
                falsifier="正式事件或关系证据显示作用未发生、方向相反或被阻断。",
            ),
            MechanismQualificationCheck(
                dimension="CAPACITY",
                label="承载能力",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="当前没有把月令、根透、受损与竞争关系合成为容量判断。",
                next_evidence="需要独立版本的容量模型与专业审阅，不得使用旧强弱启发式。",
                falsifier="正式容量证据显示来源或承接无法负担该路径。",
            ),
            MechanismQualificationCheck(
                dimension="USABILITY",
                label="可用性",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="作用、容量和时序未解决前，不能判断这条结构是否可用。",
                next_evidence="需要作用、容量、时序和反证同时达到准入条件。",
                falsifier="任一必要维度被正式否定时，可用性不得成立。",
            ),
            MechanismQualificationCheck(
                dimension="PROFESSIONAL_ADMISSION",
                label="专业准入",
                status="NOT_ADMITTED",
                evidence_refs=(),
                meaning="当前候选只允许解释和研究，不是正式有效做功结论。",
                next_evidence="需要 Owner 专业审阅通过的规则版本与完整证据清单。",
                falsifier="规则来源、适用边界或证据链不完整时，继续保持未准入。",
            ),
        )
        present_count = sum(item.status in {"PRESENT", "PARTIAL"} for item in checks)
        return CandidateMechanismQualification(
            candidate_ref=candidate.candidate_ref,
            pattern_ref=candidate.pattern_ref,
            pattern_label=candidate.pattern_label,
            checks=checks,
            evidence_present_count=present_count,
            unresolved_or_unadmitted_count=len(checks) - present_count,
            readiness="STRUCTURE_CANDIDATE_ONLY",
            professional_admission=False,
        )
