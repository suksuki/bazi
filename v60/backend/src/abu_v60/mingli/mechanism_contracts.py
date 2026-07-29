from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MECHANISM_VECTOR_VERSION = "v60.mingli-mechanism-evidence-vector.001"


class MechanismRoleEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: Literal["SOURCE", "BRIDGE", "TARGET"]
    accepted_labels: tuple[str, ...] = Field(min_length=1)
    occurrence_refs: tuple[str, ...] = Field(min_length=1)
    occurrence_labels: tuple[str, ...] = Field(min_length=1)
    participant_slots: tuple[str, ...] = Field(min_length=1)
    direct_evidence_refs: tuple[str, ...] = Field(min_length=1)
    manifestation_evidence_refs: tuple[str, ...] = ()
    visible_occurrence_count: int = Field(ge=0)
    hidden_occurrence_count: int = Field(ge=0)

    @model_validator(mode="after")
    def evidence_is_consistent(self) -> MechanismRoleEvidence:
        groups = (
            self.occurrence_refs,
            self.participant_slots,
            self.direct_evidence_refs,
            self.manifestation_evidence_refs,
        )
        if any(values != tuple(sorted(set(values))) for values in groups):
            raise ValueError("mechanism_role_evidence_refs_must_be_sorted_unique")
        if self.visible_occurrence_count + self.hidden_occurrence_count != len(
            self.occurrence_refs
        ):
            raise ValueError("mechanism_role_occurrence_count_mismatch")
        return self


class MechanismCandidateEvidence(BaseModel):
    """One inspectable candidate that remains below professional admission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_ref: str = Field(min_length=1)
    pattern_ref: str = Field(min_length=1)
    pattern_label: str = Field(min_length=1)
    structural_statement: str = Field(min_length=1)
    forbidden_shortcut: str = Field(min_length=1)
    roles: tuple[MechanismRoleEvidence, ...] = Field(min_length=2, max_length=3)
    support_evidence_refs: tuple[str, ...] = Field(min_length=1)
    context_evidence_refs: tuple[str, ...] = ()
    counter_evidence_refs: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = Field(min_length=1)
    competing_candidate_refs: tuple[str, ...] = ()
    structural_presence: Literal["PRESENT"]
    effect_status: Literal["UNRESOLVED"]
    capacity_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    timing_activation_status: Literal["UNRESOLVED"]
    counter_evidence_status: Literal["NOT_ADMITTED"]
    professional_admission_status: Literal["UNRESOLVED"]
    comparison_eligible: Literal[True]
    professional_selection_qualified: Literal[False]
    support_score_status: Literal["NOT_COMPUTED_NO_ADMITTED_WEIGHTS"]

    @model_validator(mode="after")
    def candidate_refs_are_consistent(self) -> MechanismCandidateEvidence:
        groups = (
            self.support_evidence_refs,
            self.context_evidence_refs,
            self.counter_evidence_refs,
            self.blocker_codes,
            self.competing_candidate_refs,
        )
        if any(values != tuple(sorted(set(values))) for values in groups):
            raise ValueError("mechanism_candidate_refs_must_be_sorted_unique")
        return self


class MingliMechanismEvidenceVector(BaseModel):
    """Persisted candidate evidence compiled from one real chart vector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_ref: str = Field(min_length=1)
    vector_hash: str = Field(min_length=64, max_length=64)
    vector_version: str = MECHANISM_VECTOR_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    quant_vector_ref: str = Field(min_length=1)
    quant_vector_hash: str = Field(min_length=64, max_length=64)
    mechanism_profile_ref: str = Field(min_length=1)
    mechanism_profile_hash: str = Field(min_length=64, max_length=64)
    candidates: tuple[MechanismCandidateEvidence, ...]
    evidence_refs: tuple[str, ...]
    comparison_status: Literal[
        "NO_CANDIDATE",
        "ONE_CANDIDATE",
        "MULTIPLE_CANDIDATES",
    ]
    interpretation_authority: Literal["BOUNDED_REASONER_ATTENTION_ONLY"]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_shape_are_valid(self) -> MingliMechanismEvidenceVector:
        candidate_refs = tuple(candidate.candidate_ref for candidate in self.candidates)
        if candidate_refs != tuple(sorted(set(candidate_refs))):
            raise ValueError("mechanism_vector_candidates_must_be_sorted_unique")
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError("mechanism_vector_evidence_refs_must_be_sorted_unique")
        expected_status = (
            "NO_CANDIDATE"
            if not self.candidates
            else "ONE_CANDIDATE"
            if len(self.candidates) == 1
            else "MULTIPLE_CANDIDATES"
        )
        if self.comparison_status != expected_status:
            raise ValueError("mechanism_vector_comparison_status_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"vector_ref", "vector_hash"},
        )
        if self.vector_hash != content_hash(identity):
            raise ValueError("mechanism_vector_hash_mismatch")
        if self.vector_ref != stable_ref("v60-mingli-mechanism-vector", identity):
            raise ValueError("mechanism_vector_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliMechanismEvidenceVector:
        candidates = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["candidates"]
        )
        identity = {
            "vector_version": MECHANISM_VECTOR_VERSION,
            **values,
            "candidates": candidates,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            vector_ref=stable_ref("v60-mingli-mechanism-vector", identity),
            vector_hash=content_hash(identity),
            **identity,
        )
