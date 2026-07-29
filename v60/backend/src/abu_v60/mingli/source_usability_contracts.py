from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

SOURCE_USABILITY_PREREQUISITE_VERSION = (
    "v60.mingli-source-usability-prerequisite.001"
)
SOURCE_USABILITY_SCOPE_ORDER = (
    "EXACT_IDENTITY_ONLY",
    "ELEMENT_AFFINITY_INCLUDED",
)
SOURCE_USABILITY_REQUIREMENT_ORDER = (
    "MATCH_SCOPE_RULE",
    "RELATION_EFFECT_RULE",
    "SEASONAL_CAPACITY_RULE",
    "MULTI_SOURCE_AGGREGATION_RULE",
    "ROOT_USABILITY_RULE",
    "PROFESSIONAL_ADMISSION",
)
PILLAR_SLOT_ORDER = ("year", "month", "day", "hour")

SourceUsabilityScopeId = Literal[
    "EXACT_IDENTITY_ONLY",
    "ELEMENT_AFFINITY_INCLUDED",
]
SourceUsabilityRequirementId = Literal[
    "MATCH_SCOPE_RULE",
    "RELATION_EFFECT_RULE",
    "SEASONAL_CAPACITY_RULE",
    "MULTI_SOURCE_AGGREGATION_RULE",
    "ROOT_USABILITY_RULE",
    "PROFESSIONAL_ADMISSION",
]
SourceUsabilityRequirementStatus = Literal[
    "NOT_ADMITTED",
    "NOT_TRIGGERED",
    "UNRESOLVED",
]


class SourceUsabilityResearchScope(BaseModel):
    """One unselected source-membership scope for a visible stem carrier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope_ref: str = Field(min_length=1)
    scope_id: SourceUsabilityScopeId
    source_review_refs: tuple[str, ...]
    relation_review_refs: tuple[str, ...]
    intersection_refs: tuple[str, ...]
    source_review_count: int = Field(ge=0)
    clear_count: int = Field(ge=0)
    relation_review_count: int = Field(ge=0)
    intersection_count: int = Field(ge=0)
    relation_effect_status: Literal["UNRESOLVED"]
    root_usability_status: Literal["UNRESOLVED"]
    selection_authority: Literal[False]

    @model_validator(mode="after")
    def refs_and_counts_are_consistent(self) -> SourceUsabilityResearchScope:
        groups = (
            self.source_review_refs,
            self.relation_review_refs,
            self.intersection_refs,
        )
        if any(values != tuple(sorted(set(values))) for values in groups):
            raise ValueError("source_usability_scope_refs_not_sorted_unique")
        if not set(self.relation_review_refs) <= set(self.source_review_refs):
            raise ValueError("source_usability_relation_reviews_not_in_scope")
        expected = {
            "source_review_count": len(self.source_review_refs),
            "clear_count": len(self.source_review_refs)
            - len(self.relation_review_refs),
            "relation_review_count": len(self.relation_review_refs),
            "intersection_count": len(self.intersection_refs),
        }
        if any(getattr(self, key) != value for key, value in expected.items()):
            raise ValueError("source_usability_scope_count_mismatch")
        return self


class SourceUsabilityRequirement(BaseModel):
    """One bounded condition to verify before professional discussion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: SourceUsabilityRequirementId
    status: SourceUsabilityRequirementStatus
    evidence_refs: tuple[str, ...]
    meaning: str = Field(min_length=1)
    next_evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_refs_are_sorted_unique(self) -> SourceUsabilityRequirement:
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError("source_usability_requirement_refs_not_sorted_unique")
        return self


class SourceCarrierUsabilityPrerequisite(BaseModel):
    """Competing scopes and evidence gaps for one visible stem carrier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    carrier_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    scopes: tuple[SourceUsabilityResearchScope, ...] = Field(
        min_length=2,
        max_length=2,
    )
    requirements: tuple[SourceUsabilityRequirement, ...] = Field(
        min_length=6,
        max_length=6,
    )
    discussion_ready: Literal[False]

    @model_validator(mode="after")
    def scope_and_requirement_shape_is_valid(
        self,
    ) -> SourceCarrierUsabilityPrerequisite:
        if tuple(item.scope_id for item in self.scopes) != (
            SOURCE_USABILITY_SCOPE_ORDER
        ):
            raise ValueError("source_usability_scope_order_invalid")
        if tuple(item.requirement_id for item in self.requirements) != (
            SOURCE_USABILITY_REQUIREMENT_ORDER
        ):
            raise ValueError("source_usability_requirement_order_invalid")
        strict, inclusive = self.scopes
        if not set(strict.source_review_refs) <= set(inclusive.source_review_refs):
            raise ValueError("source_usability_strict_scope_not_in_inclusive")
        identity = self.model_dump(mode="json", exclude={"carrier_ref"})
        if self.carrier_ref != stable_ref(
            "v60-source-usability-carrier",
            identity,
        ):
            raise ValueError("source_usability_carrier_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> SourceCarrierUsabilityPrerequisite:
        identity = {
            **values,
            "scopes": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["scopes"]
            ),
            "requirements": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["requirements"]
            ),
            "discussion_ready": False,
        }
        return cls(
            carrier_ref=stable_ref("v60-source-usability-carrier", identity),
            **identity,
        )


class MingliSourceUsabilityPrerequisiteEnvelope(BaseModel):
    """Read-only discussion gate over one persisted source-review vector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prerequisite_ref: str = Field(min_length=1)
    prerequisite_hash: str = Field(min_length=64, max_length=64)
    prerequisite_version: str = SOURCE_USABILITY_PREREQUISITE_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    quant_vector_ref: str = Field(min_length=1)
    quant_vector_hash: str = Field(min_length=64, max_length=64)
    source_review_vector_ref: str = Field(min_length=1)
    source_review_vector_hash: str = Field(min_length=64, max_length=64)
    carriers: tuple[SourceCarrierUsabilityPrerequisite, ...]
    carrier_count: int = Field(ge=0)
    exact_identity_only_clear_count: int = Field(ge=0)
    exact_identity_only_review_required_count: int = Field(ge=0)
    element_affinity_included_clear_count: int = Field(ge=0)
    element_affinity_included_review_required_count: int = Field(ge=0)
    competing_carrier_count: int = Field(ge=0)
    ready_carrier_count: Literal[0]
    projection_semantics: Literal["EVIDENCE_GAPS_AND_COMPETING_SCOPES_ONLY"]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_counts_are_valid(
        self,
    ) -> MingliSourceUsabilityPrerequisiteEnvelope:
        carrier_keys = tuple(
            (PILLAR_SLOT_ORDER.index(item.visible_slot), item.visible_stem)
            for item in self.carriers
        )
        if carrier_keys != tuple(sorted(set(carrier_keys))):
            raise ValueError("source_usability_carriers_not_ordered_unique")
        strict_scopes = tuple(item.scopes[0] for item in self.carriers)
        inclusive_scopes = tuple(item.scopes[1] for item in self.carriers)
        strict_refs = tuple(
            ref for scope in strict_scopes for ref in scope.source_review_refs
        )
        inclusive_refs = tuple(
            ref for scope in inclusive_scopes for ref in scope.source_review_refs
        )
        if len(strict_refs) != len(set(strict_refs)) or len(inclusive_refs) != len(
            set(inclusive_refs)
        ):
            raise ValueError("source_usability_review_assigned_to_multiple_carriers")
        expected = {
            "carrier_count": len(self.carriers),
            "exact_identity_only_clear_count": sum(
                item.clear_count for item in strict_scopes
            ),
            "exact_identity_only_review_required_count": sum(
                item.relation_review_count for item in strict_scopes
            ),
            "element_affinity_included_clear_count": sum(
                item.clear_count for item in inclusive_scopes
            ),
            "element_affinity_included_review_required_count": sum(
                item.relation_review_count for item in inclusive_scopes
            ),
            "competing_carrier_count": sum(
                strict.source_review_refs != inclusive.source_review_refs
                for strict, inclusive in zip(
                    strict_scopes,
                    inclusive_scopes,
                    strict=True,
                )
            ),
            "ready_carrier_count": 0,
        }
        if any(getattr(self, key) != value for key, value in expected.items()):
            raise ValueError("source_usability_prerequisite_count_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"prerequisite_ref", "prerequisite_hash"},
        )
        if self.prerequisite_hash != content_hash(identity):
            raise ValueError("source_usability_prerequisite_hash_mismatch")
        if self.prerequisite_ref != stable_ref(
            "v60-source-usability-prerequisite",
            identity,
        ):
            raise ValueError("source_usability_prerequisite_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliSourceUsabilityPrerequisiteEnvelope:
        identity = {
            "prerequisite_version": SOURCE_USABILITY_PREREQUISITE_VERSION,
            **values,
            "carriers": tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in values["carriers"]
            ),
            "projection_semantics": "EVIDENCE_GAPS_AND_COMPETING_SCOPES_ONLY",
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            prerequisite_ref=stable_ref(
                "v60-source-usability-prerequisite",
                identity,
            ),
            prerequisite_hash=content_hash(identity),
            **identity,
        )
