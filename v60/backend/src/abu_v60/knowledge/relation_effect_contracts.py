from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_RULE_DIMENSIONS = (
    "APPLICABILITY_CONTEXT",
    "EFFECT_DIRECTION",
    "COMPLETION_CONDITIONS",
    "BLOCKING_CONDITIONS",
    "COUNTER_EVIDENCE",
    "PROFESSIONAL_PROVENANCE",
)

RelationEffectRuleDimension = Literal[
    "APPLICABILITY_CONTEXT",
    "EFFECT_DIRECTION",
    "COMPLETION_CONDITIONS",
    "BLOCKING_CONDITIONS",
    "COUNTER_EVIDENCE",
    "PROFESSIONAL_PROVENANCE",
]
RelationEffectProposalDimensionStatus = Literal[
    "VERIFIED",
    "PARTIAL",
    "COMPETING",
    "UNSUPPORTED",
    "MISSING",
]


class RelationEffectProposalDimension(BaseModel):
    """One submitted rule dimension before professional admission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension_id: RelationEffectRuleDimension
    status: RelationEffectProposalDimensionStatus
    statement: str | None = None
    evidence_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def evidence_shape_matches_status(
        self,
    ) -> RelationEffectProposalDimension:
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("relation_effect_proposal_dimension_evidence_not_unique")
        if self.status == "MISSING" and (self.statement is not None or self.evidence_refs):
            raise ValueError("relation_effect_missing_dimension_cannot_claim_evidence")
        if self.status != "MISSING" and not self.statement:
            raise ValueError("relation_effect_non_missing_dimension_statement_required")
        if self.status == "VERIFIED" and not self.evidence_refs:
            raise ValueError("relation_effect_verified_dimension_evidence_required")
        return self


class BaziRelationEffectAdmissionPolicy(BaseModel):
    """Knowledge-owned boundary for rule admission preflight only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_ref: str = Field(min_length=1)
    policy_hash: str = Field(min_length=64, max_length=64)
    policy_version: Literal["v60.knowledge-relation-effect-admission-policy.001"]
    governance_status: Literal["OWNER_AUTHORIZED_ADMISSION_BOUNDARY"]
    runtime_scope: Literal["RELATION_EFFECT_RULE_PREFLIGHT"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    required_dimensions: tuple[
        RelationEffectRuleDimension,
        ...,
    ] = Field(min_length=6, max_length=6)
    forbidden_shortcuts: tuple[
        Literal[
            "AUTOMATIC_RELATION_DAMAGE",
            "AUTOMATIC_SOURCE_UNUSABLE",
        ],
        ...,
    ] = Field(min_length=2, max_length=2)
    professional_source_manifest_required: Literal[True]
    owner_professional_review_required: Literal[True]
    effect_conclusion_allowed: Literal[False]
    source_usability_conclusion_allowed: Literal[False]
    admitted_effect_rule_profile_refs: tuple[str, ...]

    @model_validator(mode="after")
    def identity_and_boundary_are_valid(
        self,
    ) -> BaziRelationEffectAdmissionPolicy:
        if self.required_dimensions != RELATION_EFFECT_RULE_DIMENSIONS:
            raise ValueError("relation_effect_admission_policy_dimensions_invalid")
        if self.forbidden_shortcuts != (
            "AUTOMATIC_RELATION_DAMAGE",
            "AUTOMATIC_SOURCE_UNUSABLE",
        ):
            raise ValueError("relation_effect_admission_policy_shortcuts_invalid")
        if self.admitted_effect_rule_profile_refs:
            raise ValueError("relation_effect_admission_policy_unreviewed_rule_profile")
        identity = self.model_dump(
            mode="json",
            exclude={"policy_ref", "policy_hash"},
        )
        if self.policy_hash != content_hash(identity):
            raise ValueError("relation_effect_admission_policy_hash_mismatch")
        if self.policy_ref != stable_ref(
            "v60-relation-effect-admission-policy",
            identity,
        ):
            raise ValueError("relation_effect_admission_policy_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        source_refs: tuple[str, ...],
    ) -> BaziRelationEffectAdmissionPolicy:
        identity = {
            "policy_version": ("v60.knowledge-relation-effect-admission-policy.001"),
            "governance_status": "OWNER_AUTHORIZED_ADMISSION_BOUNDARY",
            "runtime_scope": "RELATION_EFFECT_RULE_PREFLIGHT",
            "professionally_reviewed": False,
            "source_refs": source_refs,
            "required_dimensions": RELATION_EFFECT_RULE_DIMENSIONS,
            "forbidden_shortcuts": (
                "AUTOMATIC_RELATION_DAMAGE",
                "AUTOMATIC_SOURCE_UNUSABLE",
            ),
            "professional_source_manifest_required": True,
            "owner_professional_review_required": True,
            "effect_conclusion_allowed": False,
            "source_usability_conclusion_allowed": False,
            "admitted_effect_rule_profile_refs": (),
        }
        return cls(
            policy_ref=stable_ref(
                "v60-relation-effect-admission-policy",
                identity,
            ),
            policy_hash=content_hash(identity),
            **identity,
        )


class BaziRelationEffectRuleProposal(BaseModel):
    """A research proposal that is not an admitted professional rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    proposal_ref: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    proposal_version: Literal["v60.knowledge-relation-effect-rule-proposal.001"]
    claim_code: Literal["AUTOMATIC_SOURCE_DAMAGE_FROM_SIX_CLASH"]
    claim: str = Field(min_length=1)
    relation_type: Literal["six_clash_membership"]
    exact_branch_pair: tuple[str, str] = Field(min_length=2, max_length=2)
    temporal_scope: Literal["NATAL"]
    source_match_scope: Literal["EXACT_IDENTITY_ONLY"]
    requested_effect_atom: Literal["AUTOMATIC_SOURCE_DAMAGE"]
    dimension_submissions: tuple[
        RelationEffectProposalDimension,
        ...,
    ] = Field(min_length=6, max_length=6)
    professional_source_manifest: tuple[str, ...]
    owner_review_receipt_ref: str | None
    owner_review_receipt_hash: str | None
    professionally_reviewed: Literal[False]
    research_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_submission_are_valid(
        self,
    ) -> BaziRelationEffectRuleProposal:
        if self.exact_branch_pair != ("子", "午"):
            raise ValueError("relation_effect_proposal_branch_pair_invalid")
        if (
            tuple(item.dimension_id for item in self.dimension_submissions)
            != RELATION_EFFECT_RULE_DIMENSIONS
        ):
            raise ValueError("relation_effect_proposal_dimensions_invalid")
        if self.professional_source_manifest:
            raise ValueError("relation_effect_unreviewed_proposal_source_manifest_invalid")
        if self.owner_review_receipt_ref is not None or self.owner_review_receipt_hash is not None:
            raise ValueError("relation_effect_unreviewed_proposal_receipt_invalid")
        identity = self.model_dump(
            mode="json",
            exclude={"proposal_ref", "proposal_hash"},
        )
        if self.proposal_hash != content_hash(identity):
            raise ValueError("relation_effect_proposal_hash_mismatch")
        if self.proposal_ref != stable_ref(
            "v60-relation-effect-rule-proposal",
            identity,
        ):
            raise ValueError("relation_effect_proposal_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        *,
        claim: str,
        dimension_submissions: tuple[
            RelationEffectProposalDimension,
            ...,
        ],
    ) -> BaziRelationEffectRuleProposal:
        identity: dict[str, Any] = {
            "proposal_version": ("v60.knowledge-relation-effect-rule-proposal.001"),
            "claim_code": "AUTOMATIC_SOURCE_DAMAGE_FROM_SIX_CLASH",
            "claim": claim,
            "relation_type": "six_clash_membership",
            "exact_branch_pair": ("子", "午"),
            "temporal_scope": "NATAL",
            "source_match_scope": "EXACT_IDENTITY_ONLY",
            "requested_effect_atom": "AUTOMATIC_SOURCE_DAMAGE",
            "dimension_submissions": tuple(
                item.model_dump(mode="json") for item in dimension_submissions
            ),
            "professional_source_manifest": (),
            "owner_review_receipt_ref": None,
            "owner_review_receipt_hash": None,
            "professionally_reviewed": False,
            "research_only": True,
        }
        return cls(
            proposal_ref=stable_ref(
                "v60-relation-effect-rule-proposal",
                identity,
            ),
            proposal_hash=content_hash(identity),
            **identity,
        )
