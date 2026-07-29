from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MECHANISM_EVIDENCE_DEPTH_VERSION = "v60.mingli-mechanism-evidence-depth.001"
MECHANISM_EVIDENCE_CHANNEL_ORDER = (
    "STRUCTURAL_ROLES",
    "VISIBLE_CARRIERS",
    "HIDDEN_MEMBERS",
    "SOURCE_MANIFESTATION",
    "MONTH_BRANCH_CONTEXT",
    "TIMING_ROLE_OVERLAP",
    "TIMING_RELATION_CONTEXT",
    "SHARED_PARTICIPANT_COMPETITION",
)
MECHANISM_UNRESOLVED_DIMENSIONS = (
    "ROOT_USABILITY",
    "SEASONAL_CAPACITY",
    "RELATION_EFFECT",
    "TIMING_ACTIVATION",
    "COUNTER_EVIDENCE",
    "MECHANISM_EFFECT",
    "PROFESSIONAL_ADMISSION",
)

MechanismAttentionStatus = Literal[
    "PRIMARY_ATTENTION",
    "DIRECT_COMPETITOR",
    "UNRANKED",
]
MechanismCarrierState = Literal[
    "VISIBLE_AND_HIDDEN",
    "VISIBLE_ONLY",
    "HIDDEN_ONLY",
]
MechanismEvidenceChannel = Literal[
    "STRUCTURAL_ROLES",
    "VISIBLE_CARRIERS",
    "HIDDEN_MEMBERS",
    "SOURCE_MANIFESTATION",
    "MONTH_BRANCH_CONTEXT",
    "TIMING_ROLE_OVERLAP",
    "TIMING_RELATION_CONTEXT",
    "SHARED_PARTICIPANT_COMPETITION",
]
MechanismUnresolvedDimension = Literal[
    "ROOT_USABILITY",
    "SEASONAL_CAPACITY",
    "RELATION_EFFECT",
    "TIMING_ACTIVATION",
    "COUNTER_EVIDENCE",
    "MECHANISM_EFFECT",
    "PROFESSIONAL_ADMISSION",
]


class MechanismRoleEvidenceDepth(BaseModel):
    """Traceable carrier and source coordinates for one candidate role."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: Literal["SOURCE", "BRIDGE", "TARGET"]
    accepted_labels: tuple[str, ...] = Field(min_length=1)
    visible_labels: tuple[str, ...]
    hidden_labels: tuple[str, ...]
    carrier_state: MechanismCarrierState
    visible_occurrence_refs: tuple[str, ...]
    hidden_occurrence_refs: tuple[str, ...]
    month_branch_occurrence_refs: tuple[str, ...]
    exact_source_evidence_refs: tuple[str, ...]
    elemental_source_evidence_refs: tuple[str, ...]
    same_pillar_source_evidence_refs: tuple[str, ...]
    month_branch_source_evidence_refs: tuple[str, ...]
    direct_evidence_refs: tuple[str, ...] = Field(min_length=1)
    source_effect_status: Literal["UNRESOLVED"]

    @model_validator(mode="after")
    def refs_and_carrier_state_are_consistent(self) -> MechanismRoleEvidenceDepth:
        groups = (
            self.visible_labels,
            self.hidden_labels,
            self.visible_occurrence_refs,
            self.hidden_occurrence_refs,
            self.month_branch_occurrence_refs,
            self.exact_source_evidence_refs,
            self.elemental_source_evidence_refs,
            self.same_pillar_source_evidence_refs,
            self.month_branch_source_evidence_refs,
            self.direct_evidence_refs,
        )
        if any(values != tuple(sorted(set(values))) for values in groups):
            raise ValueError("mechanism_depth_role_values_must_be_sorted_unique")
        expected_state: MechanismCarrierState
        if self.visible_occurrence_refs and self.hidden_occurrence_refs:
            expected_state = "VISIBLE_AND_HIDDEN"
        elif self.visible_occurrence_refs:
            expected_state = "VISIBLE_ONLY"
        else:
            expected_state = "HIDDEN_ONLY"
        if self.carrier_state != expected_state:
            raise ValueError("mechanism_depth_role_carrier_state_mismatch")
        return self


class MechanismTimingOverlapDepth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    overlap_ref: str = Field(min_length=1)
    timing_coordinate_ref: str = Field(min_length=1)
    timing_layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    timing_ten_god_label: str = Field(min_length=1)
    matching_role_ids: tuple[str, ...] = Field(min_length=1)
    activation_status: Literal["UNRESOLVED"]


class MechanismTimingRelationDepth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    timing_coordinate_ref: str = Field(min_length=1)
    timing_layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    natal_slot: Literal["year", "month", "day", "hour"]
    relation_type: Literal[
        "same_branch_membership",
        "six_clash_membership",
        "six_harmony_membership",
    ]
    matching_role_ids: tuple[str, ...] = Field(min_length=1)
    rule_ref: str = Field(min_length=1)
    effect_status: Literal["UNRESOLVED"]


class MechanismSharedParticipantDepth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    competing_candidate_ref: str = Field(min_length=1)
    shared_occurrence_refs: tuple[str, ...] = Field(min_length=1)
    shared_labels: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def shared_values_are_sorted_unique(self) -> MechanismSharedParticipantDepth:
        if self.shared_occurrence_refs != tuple(sorted(set(self.shared_occurrence_refs))):
            raise ValueError("mechanism_depth_shared_occurrences_not_unique")
        if self.shared_labels != tuple(sorted(set(self.shared_labels))):
            raise ValueError("mechanism_depth_shared_labels_not_unique")
        return self


class CandidateMechanismEvidenceDepth(BaseModel):
    """Evidence channels for one candidate, without score or professional verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_ref: str = Field(min_length=1)
    pattern_ref: str = Field(min_length=1)
    pattern_label: str = Field(min_length=1)
    attention_status: MechanismAttentionStatus
    roles: tuple[MechanismRoleEvidenceDepth, ...] = Field(min_length=2, max_length=3)
    timing_overlaps: tuple[MechanismTimingOverlapDepth, ...]
    timing_relations: tuple[MechanismTimingRelationDepth, ...]
    shared_participants: tuple[MechanismSharedParticipantDepth, ...]
    evidence_channels: tuple[MechanismEvidenceChannel, ...] = Field(min_length=1)
    unresolved_dimensions: tuple[MechanismUnresolvedDimension, ...] = Field(min_length=1)
    evidence_score_status: Literal["NOT_COMPUTED"]
    professional_admission: Literal[False]

    @model_validator(mode="after")
    def candidate_shape_is_valid(self) -> CandidateMechanismEvidenceDepth:
        expected_channels = tuple(
            item for item in MECHANISM_EVIDENCE_CHANNEL_ORDER if item in set(self.evidence_channels)
        )
        if self.evidence_channels != expected_channels:
            raise ValueError("mechanism_depth_channel_order_invalid")
        if self.unresolved_dimensions != MECHANISM_UNRESOLVED_DIMENSIONS:
            raise ValueError("mechanism_depth_unresolved_dimensions_invalid")
        competitor_refs = tuple(item.competing_candidate_ref for item in self.shared_participants)
        if competitor_refs != tuple(sorted(set(competitor_refs))):
            raise ValueError("mechanism_depth_competitors_not_sorted_unique")
        return self


class MingliMechanismEvidenceDepthEnvelope(BaseModel):
    """Read-only evidence contrast tied to one immutable Mingli Reading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    depth_ref: str = Field(min_length=1)
    depth_hash: str = Field(min_length=64, max_length=64)
    depth_version: str = MECHANISM_EVIDENCE_DEPTH_VERSION
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
    selected_attention_candidate_ref: str | None = None
    candidates: tuple[CandidateMechanismEvidenceDepth, ...]
    semantics: Literal["EVIDENCE_CHANNEL_CONTRAST_ONLY"]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_attention_are_valid(
        self,
    ) -> MingliMechanismEvidenceDepthEnvelope:
        candidate_refs = tuple(item.candidate_ref for item in self.candidates)
        if candidate_refs != tuple(sorted(set(candidate_refs))):
            raise ValueError("mechanism_depth_candidates_not_sorted_unique")
        primary_refs = tuple(
            item.candidate_ref
            for item in self.candidates
            if item.attention_status == "PRIMARY_ATTENTION"
        )
        expected_primary = (
            (self.selected_attention_candidate_ref,)
            if self.selected_attention_candidate_ref is not None
            else ()
        )
        if primary_refs != expected_primary:
            raise ValueError("mechanism_depth_primary_attention_mismatch")
        identity = self.model_dump(mode="json", exclude={"depth_ref", "depth_hash"})
        if self.depth_hash != content_hash(identity):
            raise ValueError("mechanism_depth_hash_mismatch")
        if self.depth_ref != stable_ref("v60-mingli-mechanism-depth", identity):
            raise ValueError("mechanism_depth_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliMechanismEvidenceDepthEnvelope:
        candidates = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["candidates"]
        )
        identity = {
            "depth_version": MECHANISM_EVIDENCE_DEPTH_VERSION,
            **values,
            "candidates": candidates,
            "semantics": "EVIDENCE_CHANNEL_CONTRAST_ONLY",
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            depth_ref=stable_ref("v60-mingli-mechanism-depth", identity),
            depth_hash=content_hash(identity),
            **identity,
        )
