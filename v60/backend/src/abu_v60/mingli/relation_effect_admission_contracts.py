from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.knowledge.relation_effect_contracts import (
    RELATION_EFFECT_RULE_DIMENSIONS,
    BaziRelationEffectAdmissionPolicy,
    BaziRelationEffectRuleProposal,
    RelationEffectProposalDimensionStatus,
    RelationEffectRuleDimension,
)
from abu_v60.mingli.relation_effect_frontier_contracts import (
    MingliRelationEffectResearchFrontierEnvelope,
)
from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_ADMISSION_REVIEW_VERSION = "v60.mingli-relation-rule-admission-review.001"

RelationEffectInterpretationId = Literal[
    "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
    "SOURCE_OPEN_OR_EXPOSE",
    "SOURCE_DAMAGE_OR_REMOVE",
]


class RelationEffectCompetingInterpretation(BaseModel):
    """One visible hypothesis with no selection or effect authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    interpretation_ref: str = Field(min_length=1)
    interpretation_id: RelationEffectInterpretationId
    summary: str = Field(min_length=1)
    status: Literal["HELD"]
    selected: Literal[False]
    effect_atom_created: Literal[False]

    @model_validator(mode="after")
    def identity_is_valid(
        self,
    ) -> RelationEffectCompetingInterpretation:
        identity = self.model_dump(
            mode="json",
            exclude={"interpretation_ref"},
        )
        if self.interpretation_ref != stable_ref(
            "v60-relation-effect-competing-interpretation",
            identity,
        ):
            raise ValueError("relation_effect_interpretation_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        interpretation_id: RelationEffectInterpretationId,
        summary: str,
    ) -> RelationEffectCompetingInterpretation:
        identity = {
            "interpretation_id": interpretation_id,
            "summary": summary,
            "status": "HELD",
            "selected": False,
            "effect_atom_created": False,
        }
        return cls(
            interpretation_ref=stable_ref(
                "v60-relation-effect-competing-interpretation",
                identity,
            ),
            **identity,
        )


class RelationEffectDimensionAssessment(BaseModel):
    """Runtime assessment of one submitted professional-rule dimension."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension_id: RelationEffectRuleDimension
    submission_status: RelationEffectProposalDimensionStatus
    current_basis_refs: tuple[str, ...]
    gap: str = Field(min_length=1)
    satisfied: Literal[False]

    @model_validator(mode="after")
    def basis_is_unique(
        self,
    ) -> RelationEffectDimensionAssessment:
        if len(self.current_basis_refs) != len(set(self.current_basis_refs)):
            raise ValueError("relation_effect_dimension_basis_refs_not_unique")
        return self


class RelationEffectRuleAdmissionAssessment(BaseModel):
    """One rejected pre-admission shortcut bound to one exact demand."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assessment_ref: str = Field(min_length=1)
    assessment_hash: str = Field(min_length=64, max_length=64)
    demand_ref: str = Field(min_length=1)
    source_review_ref: str = Field(min_length=1)
    source_evidence_ref: str = Field(min_length=1)
    intersection_ref: str = Field(min_length=1)
    relation_fact_ref: str = Field(min_length=1)
    carrier_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: Literal["午"]
    peer_slot: Literal["year", "month", "day", "hour"]
    peer_branch: Literal["子"]
    relation_type: Literal["six_clash_membership"]
    source_match_kind: Literal["EXACT_IDENTITY"]
    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    proposal_claim: str = Field(min_length=1)
    interpretations: tuple[
        RelationEffectCompetingInterpretation,
        ...,
    ] = Field(min_length=3, max_length=3)
    dimension_assessments: tuple[
        RelationEffectDimensionAssessment,
        ...,
    ] = Field(min_length=6, max_length=6)
    disposition: Literal["REJECTED_PRE_ADMISSION"]
    candidate_truth_status: Literal["NOT_EVALUATED_AS_TRUE_OR_FALSE"]
    rejection_codes: tuple[
        Literal[
            "APPLICABILITY_AUTHORITY_INCOMPLETE",
            "EFFECT_DIRECTION_COMPETING",
            "COMPLETION_CONDITIONS_MISSING",
            "BLOCKING_CONDITIONS_MISSING",
            "COUNTER_EVIDENCE_MISSING",
            "PROFESSIONAL_PROVENANCE_MISSING",
        ],
        ...,
    ] = Field(min_length=6, max_length=6)
    blocked_claims: tuple[
        Literal[
            "AUTOMATIC_RELATION_DAMAGE",
            "AUTOMATIC_SOURCE_UNUSABLE",
        ],
        ...,
    ] = Field(min_length=2, max_length=2)
    admitted_effect_atom_refs: tuple[str, ...]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]

    @model_validator(mode="after")
    def contract_and_identity_are_valid(
        self,
    ) -> RelationEffectRuleAdmissionAssessment:
        if tuple(item.interpretation_id for item in self.interpretations) != (
            "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
            "SOURCE_OPEN_OR_EXPOSE",
            "SOURCE_DAMAGE_OR_REMOVE",
        ):
            raise ValueError("relation_effect_assessment_interpretations_invalid")
        if (
            tuple(item.dimension_id for item in self.dimension_assessments)
            != RELATION_EFFECT_RULE_DIMENSIONS
        ):
            raise ValueError("relation_effect_assessment_dimensions_invalid")
        if any(item.satisfied for item in self.dimension_assessments):
            raise ValueError("relation_effect_assessment_dimension_cannot_be_satisfied")
        if self.rejection_codes != (
            "APPLICABILITY_AUTHORITY_INCOMPLETE",
            "EFFECT_DIRECTION_COMPETING",
            "COMPLETION_CONDITIONS_MISSING",
            "BLOCKING_CONDITIONS_MISSING",
            "COUNTER_EVIDENCE_MISSING",
            "PROFESSIONAL_PROVENANCE_MISSING",
        ):
            raise ValueError("relation_effect_assessment_rejection_codes_invalid")
        if self.blocked_claims != (
            "AUTOMATIC_RELATION_DAMAGE",
            "AUTOMATIC_SOURCE_UNUSABLE",
        ):
            raise ValueError("relation_effect_assessment_blocked_claims_invalid")
        if self.admitted_effect_atom_refs:
            raise ValueError("relation_effect_assessment_effect_atom_not_allowed")
        identity = self.model_dump(
            mode="json",
            exclude={"assessment_ref", "assessment_hash"},
        )
        if self.assessment_hash != content_hash(identity):
            raise ValueError("relation_effect_assessment_hash_mismatch")
        if self.assessment_ref != stable_ref(
            "v60-relation-effect-admission-assessment",
            identity,
        ):
            raise ValueError("relation_effect_assessment_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> RelationEffectRuleAdmissionAssessment:
        identity = {
            **values,
            "interpretations": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["interpretations"]
            ),
            "dimension_assessments": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["dimension_assessments"]
            ),
            "disposition": "REJECTED_PRE_ADMISSION",
            "candidate_truth_status": ("NOT_EVALUATED_AS_TRUE_OR_FALSE"),
            "rejection_codes": (
                "APPLICABILITY_AUTHORITY_INCOMPLETE",
                "EFFECT_DIRECTION_COMPETING",
                "COMPLETION_CONDITIONS_MISSING",
                "BLOCKING_CONDITIONS_MISSING",
                "COUNTER_EVIDENCE_MISSING",
                "PROFESSIONAL_PROVENANCE_MISSING",
            ),
            "blocked_claims": (
                "AUTOMATIC_RELATION_DAMAGE",
                "AUTOMATIC_SOURCE_UNUSABLE",
            ),
            "admitted_effect_atom_refs": (),
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
        }
        return cls(
            assessment_ref=stable_ref(
                "v60-relation-effect-admission-assessment",
                identity,
            ),
            assessment_hash=content_hash(identity),
            **identity,
        )


class MingliRelationEffectAdmissionReviewEnvelope(BaseModel):
    """Read-only preflight proving a shortcut cannot be admitted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    review_ref: str = Field(min_length=1)
    review_hash: str = Field(min_length=64, max_length=64)
    review_version: Literal["v60.mingli-relation-rule-admission-review.001"] = (
        RELATION_EFFECT_ADMISSION_REVIEW_VERSION
    )
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    frontier_ref: str = Field(min_length=1)
    frontier_hash: str = Field(min_length=64, max_length=64)
    frontier_scope_invariant_demand_refs: tuple[str, ...]
    frontier_match_scope_demand_refs: tuple[str, ...]
    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    assessments: tuple[RelationEffectRuleAdmissionAssessment, ...]
    reviewed_demand_count: int = Field(ge=0)
    rejected_pre_admission_count: int = Field(ge=0)
    admitted_effect_rule_count: Literal[0]
    deferred_match_scope_demand_refs: tuple[str, ...]
    unreviewed_scope_invariant_demand_refs: tuple[str, ...]
    disposition: Literal[
        "REJECTED_PRE_ADMISSION",
        "NOT_TRIGGERED",
    ]
    review_semantics: Literal["SHORTCUT_ADMISSION_REJECTION_NOT_EFFECT_NEGATION"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    provider_invoked: Literal[False]
    owner_professional_review_invoked: Literal[False]
    knowledge_promotion_request_created: Literal[False]
    gate_invoked: Literal[False]
    decision_created: Literal[False]
    selection_authority: Literal[False]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def counts_boundaries_and_identity_are_valid(
        self,
    ) -> MingliRelationEffectAdmissionReviewEnvelope:
        assessment_refs = tuple(item.assessment_ref for item in self.assessments)
        if assessment_refs != tuple(sorted(set(assessment_refs))):
            raise ValueError("relation_effect_review_assessments_not_ordered_unique")
        assessed_demand_refs = tuple(item.demand_ref for item in self.assessments)
        if len(assessed_demand_refs) != len(set(assessed_demand_refs)):
            raise ValueError("relation_effect_review_assessed_demands_not_unique")
        if self.reviewed_demand_count != len(self.assessments):
            raise ValueError("relation_effect_review_demand_count_mismatch")
        if self.rejected_pre_admission_count != len(self.assessments):
            raise ValueError("relation_effect_review_rejected_count_mismatch")
        expected_disposition = "REJECTED_PRE_ADMISSION" if self.assessments else "NOT_TRIGGERED"
        if self.disposition != expected_disposition:
            raise ValueError("relation_effect_review_disposition_mismatch")
        if any(
            item.policy_ref != self.policy_ref
            or item.policy_hash != self.policy_hash
            or item.proposal_ref != self.proposal_ref
            or item.proposal_hash != self.proposal_hash
            for item in self.assessments
        ):
            raise ValueError("relation_effect_review_policy_proposal_mismatch")
        if len(self.deferred_match_scope_demand_refs) != len(
            set(self.deferred_match_scope_demand_refs)
        ):
            raise ValueError("relation_effect_review_deferred_refs_not_unique")
        if len(self.unreviewed_scope_invariant_demand_refs) != len(
            set(self.unreviewed_scope_invariant_demand_refs)
        ):
            raise ValueError("relation_effect_review_unreviewed_refs_not_unique")
        if len(self.frontier_scope_invariant_demand_refs) != len(
            set(self.frontier_scope_invariant_demand_refs)
        ):
            raise ValueError("relation_effect_review_scope_inventory_not_unique")
        if len(self.frontier_match_scope_demand_refs) != len(
            set(self.frontier_match_scope_demand_refs)
        ):
            raise ValueError("relation_effect_review_match_inventory_not_unique")
        scope_inventory = set(self.frontier_scope_invariant_demand_refs)
        match_inventory = set(self.frontier_match_scope_demand_refs)
        assessed = set(assessed_demand_refs)
        unreviewed = set(self.unreviewed_scope_invariant_demand_refs)
        deferred = set(self.deferred_match_scope_demand_refs)
        if scope_inventory & match_inventory:
            raise ValueError("relation_effect_review_frontier_inventory_overlap")
        if assessed & unreviewed or assessed & deferred or unreviewed & deferred:
            raise ValueError("relation_effect_review_demand_partition_overlap")
        if assessed | unreviewed != scope_inventory:
            raise ValueError("relation_effect_review_scope_inventory_not_covered")
        if (
            self.deferred_match_scope_demand_refs != self.frontier_match_scope_demand_refs
            or deferred != match_inventory
        ):
            raise ValueError("relation_effect_review_match_inventory_not_covered")
        expected_unreviewed = tuple(
            demand_ref
            for demand_ref in self.frontier_scope_invariant_demand_refs
            if demand_ref not in assessed
        )
        if self.unreviewed_scope_invariant_demand_refs != expected_unreviewed:
            raise ValueError("relation_effect_review_unreviewed_order_invalid")
        identity = self.model_dump(
            mode="json",
            exclude={"review_ref", "review_hash"},
        )
        if self.review_hash != content_hash(identity):
            raise ValueError("relation_effect_review_hash_mismatch")
        if self.review_ref != stable_ref(
            "v60-relation-effect-admission-review",
            identity,
        ):
            raise ValueError("relation_effect_review_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        frontier: MingliRelationEffectResearchFrontierEnvelope,
        policy: BaziRelationEffectAdmissionPolicy,
        proposal: BaziRelationEffectRuleProposal,
        assessments: tuple[RelationEffectRuleAdmissionAssessment, ...],
    ) -> MingliRelationEffectAdmissionReviewEnvelope:
        from abu_v60.mingli.relation_effect_admission_review_issuer import (
            issue_relation_effect_admission_review,
        )

        return issue_relation_effect_admission_review(
            model_cls=cls,
            frontier=frontier,
            policy=policy,
            proposal=proposal,
            assessments=assessments,
        )
