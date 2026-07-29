from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MECHANISM_QUALIFICATION_VERSION = "v60.mingli-mechanism-qualification.001"
MECHANISM_QUALIFICATION_DIMENSIONS = (
    "STRUCTURAL_ROLES",
    "SOURCE_MANIFESTATION",
    "TIMING_OVERLAP",
    "COUNTER_EVIDENCE",
    "EFFECT",
    "CAPACITY",
    "USABILITY",
    "PROFESSIONAL_ADMISSION",
)

MechanismQualificationDimension = Literal[
    "STRUCTURAL_ROLES",
    "SOURCE_MANIFESTATION",
    "TIMING_OVERLAP",
    "COUNTER_EVIDENCE",
    "EFFECT",
    "CAPACITY",
    "USABILITY",
    "PROFESSIONAL_ADMISSION",
]
MechanismQualificationStatus = Literal[
    "PRESENT",
    "PARTIAL",
    "MISSING",
    "NOT_ADMITTED",
    "UNRESOLVED",
]


class MechanismQualificationCheck(BaseModel):
    """One inspectable requirement without a hidden score or verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension: MechanismQualificationDimension
    label: str = Field(min_length=1)
    status: MechanismQualificationStatus
    evidence_refs: tuple[str, ...]
    meaning: str = Field(min_length=1)
    next_evidence: str = Field(min_length=1)
    falsifier: str = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_refs_are_sorted_unique(self) -> MechanismQualificationCheck:
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError("mechanism_qualification_evidence_refs_not_sorted_unique")
        return self


class CandidateMechanismQualification(BaseModel):
    """Qualification state for one mechanism candidate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_ref: str = Field(min_length=1)
    pattern_ref: str = Field(min_length=1)
    pattern_label: str = Field(min_length=1)
    checks: tuple[MechanismQualificationCheck, ...] = Field(min_length=8, max_length=8)
    evidence_present_count: int = Field(ge=0, le=8)
    unresolved_or_unadmitted_count: int = Field(ge=0, le=8)
    readiness: Literal["STRUCTURE_CANDIDATE_ONLY"]
    professional_admission: Literal[False]

    @model_validator(mode="after")
    def check_shape_is_valid(self) -> CandidateMechanismQualification:
        if tuple(item.dimension for item in self.checks) != (
            MECHANISM_QUALIFICATION_DIMENSIONS
        ):
            raise ValueError("mechanism_qualification_dimension_order_invalid")
        evidence_present_count = sum(
            item.status in {"PRESENT", "PARTIAL"} for item in self.checks
        )
        if self.evidence_present_count != evidence_present_count:
            raise ValueError("mechanism_qualification_present_count_mismatch")
        if self.unresolved_or_unadmitted_count != len(self.checks) - evidence_present_count:
            raise ValueError("mechanism_qualification_gap_count_mismatch")
        return self


class MingliMechanismQualificationEnvelope(BaseModel):
    """Read-only evidence completeness projection for one Mingli Reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    qualification_ref: str = Field(min_length=1)
    qualification_hash: str = Field(min_length=64, max_length=64)
    qualification_version: str = MECHANISM_QUALIFICATION_VERSION
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    quant_vector_ref: str = Field(min_length=1)
    quant_vector_hash: str = Field(min_length=64, max_length=64)
    mechanism_vector_ref: str = Field(min_length=1)
    mechanism_vector_hash: str = Field(min_length=64, max_length=64)
    timing_vector_ref: str = Field(min_length=1)
    timing_vector_hash: str = Field(min_length=64, max_length=64)
    candidates: tuple[CandidateMechanismQualification, ...]
    summary: str = Field(min_length=1)
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_candidate_order_are_valid(
        self,
    ) -> MingliMechanismQualificationEnvelope:
        refs = tuple(item.candidate_ref for item in self.candidates)
        if refs != tuple(sorted(set(refs))):
            raise ValueError("mechanism_qualification_candidates_not_sorted_unique")
        identity = self.model_dump(
            mode="json",
            exclude={"qualification_ref", "qualification_hash"},
        )
        if self.qualification_hash != content_hash(identity):
            raise ValueError("mechanism_qualification_hash_mismatch")
        if self.qualification_ref != stable_ref(
            "v60-mingli-mechanism-qualification",
            identity,
        ):
            raise ValueError("mechanism_qualification_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliMechanismQualificationEnvelope:
        candidates = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["candidates"]
        )
        identity = {
            "qualification_version": MECHANISM_QUALIFICATION_VERSION,
            **values,
            "candidates": candidates,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            qualification_ref=stable_ref(
                "v60-mingli-mechanism-qualification",
                identity,
            ),
            qualification_hash=content_hash(identity),
            **identity,
        )
