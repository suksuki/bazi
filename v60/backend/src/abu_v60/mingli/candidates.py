from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from abu_v60.mingli.contracts import (
    CandidatePathParticipant,
    CandidatePathStatus,
    CandidateResolutionStatus,
    MingliCandidatePath,
)
from abu_v60.mingli.qualification import CandidateQualificationEngine
from abu_v60.provenance import stable_ref

STRUCTURAL_CANDIDATE_COMPILER_VERSION = "v60.structural-candidate-compiler.001"

_RELATION_LABELS = {
    "six_harmony_membership": "六合",
    "six_clash_membership": "六冲",
}
_SLOT_LABELS = {
    "year": "年支",
    "month": "月支",
    "day": "日支",
    "hour": "时支",
}
_MISSING_REQUIREMENTS = (
    "relation_effect",
    "usable_root",
    "mechanism_capacity",
    "time_activation",
    "professional_admission",
)


class StructuralCandidateCompiler:
    """Compile inspectable relation candidates without deciding their effect."""

    def __init__(
        self,
        qualification_engine: CandidateQualificationEngine | None = None,
    ) -> None:
        self._qualification_engine = qualification_engine or CandidateQualificationEngine()

    @property
    def qualification_profile_ref(self) -> str:
        return self._qualification_engine.profile_ref

    def compile(
        self,
        *,
        chart_version_ref: str,
        facts: Sequence[Mapping[str, Any]],
    ) -> tuple[MingliCandidatePath, ...]:
        candidates = [
            candidate
            for fact in facts
            if (candidate := self._compile_fact(chart_version_ref, fact)) is not None
        ]
        return tuple(sorted(candidates, key=lambda item: item.candidate_ref))

    def _compile_fact(
        self,
        chart_version_ref: str,
        fact: Mapping[str, Any],
    ) -> MingliCandidatePath | None:
        fact_type = str(fact.get("fact_type", ""))
        relation_label = _RELATION_LABELS.get(fact_type)
        payload = fact.get("fact_json")
        if (
            relation_label is None
            or fact.get("authority") != "SYSTEM_DETERMINISTIC_BOUNDED"
            or not isinstance(payload, Mapping)
            or payload.get("membership_only") is not True
            or payload.get("effect_not_inferred") is not True
        ):
            return None

        fact_ref = fact.get("fact_ref")
        source_ref = fact.get("source_ref")
        subject_ref = fact.get("subject_ref")
        object_ref = fact.get("object_ref")
        left_slot = payload.get("left_slot")
        right_slot = payload.get("right_slot")
        left_branch = payload.get("left_branch")
        right_branch = payload.get("right_branch")
        required = (
            fact_ref,
            source_ref,
            subject_ref,
            object_ref,
            left_slot,
            right_slot,
            left_branch,
            right_branch,
        )
        if not all(isinstance(value, str) and value for value in required):
            return None
        if left_slot not in _SLOT_LABELS or right_slot not in _SLOT_LABELS:
            return None

        participants = (
            CandidatePathParticipant(
                participant_ref=subject_ref,
                slot=left_slot,
                branch=left_branch,
                label=f"{_SLOT_LABELS[left_slot]}{left_branch}",
            ),
            CandidatePathParticipant(
                participant_ref=object_ref,
                slot=right_slot,
                branch=right_branch,
                label=f"{_SLOT_LABELS[right_slot]}{right_branch}",
            ),
        )
        identity = {
            "compiler_version": STRUCTURAL_CANDIDATE_COMPILER_VERSION,
            "chart_version_ref": chart_version_ref,
            "relation_fact_ref": fact_ref,
            "relation_type": fact_type,
            "participants": [item.model_dump(mode="json") for item in participants],
        }
        candidate = MingliCandidatePath(
            candidate_ref=stable_ref("v60-structure-candidate", identity),
            chart_version_ref=chart_version_ref,
            path_kind="STRUCTURAL_RELATION_CANDIDATE",
            label=(f"{participants[0].label}与{participants[1].label}的{relation_label}结构候选"),
            relation_fact_ref=fact_ref,
            relation_type=fact_type,
            participants=participants,
            evidence_refs=(fact_ref,),
            source_refs=(source_ref,),
            path_status=CandidatePathStatus.STRUCTURE_CANDIDATE,
            effect_status=CandidateResolutionStatus.UNRESOLVED,
            capacity_status=CandidateResolutionStatus.UNRESOLVED,
            usability_status=CandidateResolutionStatus.UNRESOLVED,
            professional_admission_status=CandidateResolutionStatus.UNRESOLVED,
            selection_qualified=False,
            missing_requirements=_MISSING_REQUIREMENTS,
        )
        receipt = self._qualification_engine.evaluate_structure_evidence(
            candidate=candidate,
            fact=fact,
        )
        return candidate.model_copy(
            update={
                "structure_evidence_status": receipt.status,
                "qualification_receipts": (receipt,),
            }
        )
