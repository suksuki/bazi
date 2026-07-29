from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.knowledge.mechanism_contracts import BaziMechanismEvidenceProfile
from abu_v60.knowledge.quant_contracts import BaziQuantFoundationProfile
from abu_v60.knowledge.source_review_contracts import (
    BaziSourceCoordinateReviewProfile,
)
from abu_v60.knowledge.timing_contracts import BaziTimingEvidenceProfile
from abu_v60.provenance import content_hash


class StemDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    stem: str = Field(min_length=1, max_length=1)
    element: Literal["wood", "fire", "earth", "metal", "water"]
    polarity: Literal["yin", "yang"]


class BranchDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    branch: str = Field(min_length=1, max_length=1)
    hidden_stems: tuple[str, ...] = Field(min_length=1)


class BranchRelationDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relation_type: Literal["six_clash_membership", "six_harmony_membership"]
    left_branch: str = Field(min_length=1, max_length=1)
    right_branch: str = Field(min_length=1, max_length=1)

    @model_validator(mode="after")
    def pair_is_not_reflexive(self) -> BranchRelationDefinition:
        if self.left_branch == self.right_branch:
            raise ValueError("knowledge_relation_pair_must_not_be_reflexive")
        return self


class BaziFoundationProfile(BaseModel):
    """Hashable owner-approved boundary for deterministic foundation facts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_CONDITIONALLY_ACCEPTED"]
    runtime_scope: Literal["BOUNDED_DETERMINISTIC_FACTS"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    owner_decision_hash: str = Field(min_length=64, max_length=64)
    stems: tuple[StemDefinition, ...] = Field(min_length=10, max_length=10)
    branches: tuple[BranchDefinition, ...] = Field(min_length=12, max_length=12)
    relations: tuple[BranchRelationDefinition, ...] = Field(
        min_length=12,
        max_length=12,
    )
    forbidden_inferences: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def canonical_membership_is_complete(self) -> BaziFoundationProfile:
        stems = [item.stem for item in self.stems]
        branches = [item.branch for item in self.branches]
        if len(stems) != len(set(stems)):
            raise ValueError("knowledge_profile_stems_must_be_unique")
        if len(branches) != len(set(branches)):
            raise ValueError("knowledge_profile_branches_must_be_unique")
        if any(hidden not in set(stems) for item in self.branches for hidden in item.hidden_stems):
            raise ValueError("knowledge_profile_hidden_stem_not_registered")
        relation_keys = [
            (item.relation_type, frozenset((item.left_branch, item.right_branch)))
            for item in self.relations
        ]
        if len(relation_keys) != len(set(relation_keys)):
            raise ValueError("knowledge_profile_relations_must_be_unique")
        if any(
            item.left_branch not in set(branches) or item.right_branch not in set(branches)
            for item in self.relations
        ):
            raise ValueError("knowledge_profile_relation_branch_not_registered")
        return self

    @property
    def source_ref(self) -> str:
        return (
            f"{self.profile_id}@{self.profile_version}"
            f"#owner-decision-sha256:{self.owner_decision_hash}"
        )

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class CandidateQualificationRule(BaseModel):
    """Owner-bounded rule that can qualify one evidence dimension only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    dimension: Literal["STRUCTURE_EVIDENCE"]
    admitted_fact_types: tuple[str, ...] = Field(min_length=1)
    required_authority: Literal["SYSTEM_DETERMINISTIC_BOUNDED"]
    required_boolean_claims: tuple[str, ...] = Field(min_length=1)
    required_source_refs: tuple[str, ...] = Field(min_length=1)
    conclusion: Literal["STRUCTURE_EVIDENCE_SATISFIED"]
    selection_authority: Literal[False]
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def refs_and_claims_are_unique(self) -> CandidateQualificationRule:
        groups = (
            self.admitted_fact_types,
            self.required_boolean_claims,
            self.required_source_refs,
            self.forbidden_conclusions,
        )
        if any(len(values) != len(set(values)) for values in groups):
            raise ValueError("candidate_qualification_rule_values_must_be_unique")
        return self

    @property
    def rule_ref(self) -> str:
        return f"{self.rule_id}@{self.rule_version}"

    @property
    def rule_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class BaziCandidateQualificationProfile(BaseModel):
    """Hash-locked executable rules that cannot promote professional meaning."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_CONDITIONALLY_ACCEPTED"]
    runtime_scope: Literal["STRUCTURE_VISIBILITY_ONLY"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    rules: tuple[CandidateQualificationRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def rule_identity_is_unique(self) -> BaziCandidateQualificationProfile:
        identities = [(rule.rule_id, rule.rule_version) for rule in self.rules]
        if len(identities) != len(set(identities)):
            raise ValueError("candidate_qualification_rule_identity_must_be_unique")
        return self

    @property
    def source_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))


class KnowledgeProfileSelection(BaseModel):
    """Explicit deployment choice among already admitted profile versions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    selection_version: Literal["v60.knowledge-profile-selection.005"] = (
        "v60.knowledge-profile-selection.005"
    )
    foundation_profile_id: str = Field(min_length=1)
    foundation_profile_version: str = Field(min_length=1)
    foundation_profile_hash: str = Field(min_length=64, max_length=64)
    candidate_rule_profile_id: str = Field(min_length=1)
    candidate_rule_profile_version: str = Field(min_length=1)
    candidate_rule_profile_hash: str = Field(min_length=64, max_length=64)
    quant_foundation_profile_id: str = Field(min_length=1)
    quant_foundation_profile_version: str = Field(min_length=1)
    quant_foundation_profile_hash: str = Field(min_length=64, max_length=64)
    source_review_profile_id: str = Field(min_length=1)
    source_review_profile_version: str = Field(min_length=1)
    source_review_profile_hash: str = Field(min_length=64, max_length=64)
    mechanism_evidence_profile_id: str = Field(min_length=1)
    mechanism_evidence_profile_version: str = Field(min_length=1)
    mechanism_evidence_profile_hash: str = Field(min_length=64, max_length=64)
    timing_evidence_profile_id: str = Field(min_length=1)
    timing_evidence_profile_version: str = Field(min_length=1)
    timing_evidence_profile_hash: str = Field(min_length=64, max_length=64)

    @classmethod
    def from_profiles(
        cls,
        *,
        foundation: BaziFoundationProfile,
        candidate_rules: BaziCandidateQualificationProfile,
        quant_foundation: BaziQuantFoundationProfile,
        source_review: BaziSourceCoordinateReviewProfile | None = None,
        mechanism_evidence: BaziMechanismEvidenceProfile | None = None,
        timing_evidence: BaziTimingEvidenceProfile | None = None,
    ) -> KnowledgeProfileSelection:
        if mechanism_evidence is None:
            from abu_v60.knowledge.mechanism_bazi import (
                bazi_mechanism_evidence_profile,
            )

            mechanism_evidence = bazi_mechanism_evidence_profile()
        if source_review is None:
            from abu_v60.knowledge.source_review_bazi import (
                bazi_source_coordinate_review_profile,
            )

            source_review = bazi_source_coordinate_review_profile()
        if timing_evidence is None:
            from abu_v60.knowledge.timing_bazi import (
                bazi_timing_evidence_profile,
            )

            timing_evidence = bazi_timing_evidence_profile()
        return cls(
            foundation_profile_id=foundation.profile_id,
            foundation_profile_version=foundation.profile_version,
            foundation_profile_hash=foundation.profile_hash,
            candidate_rule_profile_id=candidate_rules.profile_id,
            candidate_rule_profile_version=candidate_rules.profile_version,
            candidate_rule_profile_hash=candidate_rules.profile_hash,
            quant_foundation_profile_id=quant_foundation.profile_id,
            quant_foundation_profile_version=quant_foundation.profile_version,
            quant_foundation_profile_hash=quant_foundation.profile_hash,
            source_review_profile_id=source_review.profile_id,
            source_review_profile_version=source_review.profile_version,
            source_review_profile_hash=source_review.profile_hash,
            mechanism_evidence_profile_id=mechanism_evidence.profile_id,
            mechanism_evidence_profile_version=mechanism_evidence.profile_version,
            mechanism_evidence_profile_hash=mechanism_evidence.profile_hash,
            timing_evidence_profile_id=timing_evidence.profile_id,
            timing_evidence_profile_version=timing_evidence.profile_version,
            timing_evidence_profile_hash=timing_evidence.profile_hash,
        )

    @property
    def selection_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))

    def public_manifest(self) -> dict[str, object]:
        return {
            **self.model_dump(mode="json"),
            "selection_hash": self.selection_hash,
        }
