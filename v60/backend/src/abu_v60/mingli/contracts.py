from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref


class EpistemicStatus(StrEnum):
    FACT = "FACT"
    COMMITTED = "COMMITTED"
    CANDIDATE = "CANDIDATE"
    HYPOTHESIS = "HYPOTHESIS"
    UNRESOLVED = "UNRESOLVED"


class MingliFactRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    fact_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    fact_type: str = Field(min_length=1)
    epistemic_status: EpistemicStatus
    source_refs: tuple[str, ...] = ()


class MingliContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_ref: str
    chart_version_ref: str
    life_case_revision_ref: str | None = None
    fact_refs: tuple[MingliFactRef, ...] = ()
    selected_semantic_refs: tuple[str, ...] = ()


class CandidatePathStatus(StrEnum):
    STRUCTURE_CANDIDATE = "STRUCTURE_CANDIDATE"


class CandidateResolutionStatus(StrEnum):
    UNRESOLVED = "UNRESOLVED"


class CandidateQualificationDimension(StrEnum):
    STRUCTURE_EVIDENCE = "STRUCTURE_EVIDENCE"


class CandidateQualificationStatus(StrEnum):
    SATISFIED = "SATISFIED"
    REJECTED = "REJECTED"
    NOT_ADMITTED = "NOT_ADMITTED"


class CandidateQualificationReceipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_ref: str = Field(min_length=1)
    evaluator_version: str = Field(min_length=1)
    candidate_ref: str = Field(min_length=1)
    dimension: CandidateQualificationDimension
    status: CandidateQualificationStatus
    rule_ref: str | None = None
    rule_hash: str | None = Field(default=None, min_length=64, max_length=64)
    evidence_refs: tuple[str, ...] = ()
    evaluated_claims: tuple[str, ...] = ()
    missing_claims: tuple[str, ...] = ()
    forbidden_conclusions: tuple[str, ...] = ()
    reason: str = Field(min_length=1)
    selection_authority: bool = False
    receipt_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def receipt_identity_is_valid(self) -> CandidateQualificationReceipt:
        identity = self.model_dump(
            mode="json",
            exclude={"receipt_ref", "receipt_hash"},
        )
        if self.receipt_hash != content_hash(identity):
            raise ValueError("candidate_qualification_receipt_hash_mismatch")
        if self.receipt_ref != stable_ref("v60-candidate-qualification", identity):
            raise ValueError("candidate_qualification_receipt_ref_mismatch")
        if self.selection_authority:
            raise ValueError("candidate_qualification_receipt_cannot_select")
        return self


class CandidatePathParticipant(BaseModel):
    model_config = ConfigDict(frozen=True)

    participant_ref: str = Field(min_length=1)
    slot: str = Field(min_length=1)
    branch: str = Field(min_length=1)
    label: str = Field(min_length=1)


class MingliCandidatePath(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    path_kind: str = Field(min_length=1)
    label: str = Field(min_length=1)
    relation_fact_ref: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    participants: tuple[CandidatePathParticipant, ...] = Field(min_length=2)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)
    path_status: CandidatePathStatus
    structure_evidence_status: CandidateQualificationStatus = (
        CandidateQualificationStatus.NOT_ADMITTED
    )
    qualification_receipts: tuple[CandidateQualificationReceipt, ...] = ()
    effect_status: CandidateResolutionStatus
    capacity_status: CandidateResolutionStatus
    usability_status: CandidateResolutionStatus
    professional_admission_status: CandidateResolutionStatus
    selection_qualified: bool = False
    missing_requirements: tuple[str, ...] = Field(min_length=1)
