from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.mingli.source_usability_contracts import PILLAR_SLOT_ORDER
from abu_v60.provenance import content_hash, stable_ref

RELATION_EFFECT_RESEARCH_FRONTIER_VERSION = (
    "v60.mingli-relation-effect-research-frontier.001"
)
RELATION_EFFECT_REQUIRED_RULE_DIMENSIONS = (
    "APPLICABILITY_CONTEXT",
    "EFFECT_DIRECTION",
    "COMPLETION_CONDITIONS",
    "BLOCKING_CONDITIONS",
    "COUNTER_EVIDENCE",
    "PROFESSIONAL_PROVENANCE",
)

RelationEffectDependencyStatus = Literal[
    "SCOPE_INVARIANT_RULE_DEMAND",
    "MATCH_SCOPE_RULE_FIRST",
]
RelationEffectResearchScope = Literal[
    "EXACT_IDENTITY_ONLY",
    "ELEMENT_AFFINITY_INCLUDED",
]
RelationEffectRuleDimension = Literal[
    "APPLICABILITY_CONTEXT",
    "EFFECT_DIRECTION",
    "COMPLETION_CONDITIONS",
    "BLOCKING_CONDITIONS",
    "COUNTER_EVIDENCE",
    "PROFESSIONAL_PROVENANCE",
]


class RelationEffectRuleDemand(BaseModel):
    """One relation hit classified only by its upstream scope dependency."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    demand_ref: str = Field(min_length=1)
    carrier_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    source_review_ref: str = Field(min_length=1)
    source_evidence_ref: str = Field(min_length=1)
    intersection_ref: str = Field(min_length=1)
    relation_fact_ref: str = Field(min_length=1)
    relation_type: Literal[
        "six_clash_membership",
        "six_harmony_membership",
    ]
    source_match_kind: Literal[
        "EXACT_IDENTITY",
        "SAME_ELEMENT_DIFFERENT_IDENTITY",
    ]
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: str = Field(min_length=1, max_length=1)
    peer_slot: Literal["year", "month", "day", "hour"]
    peer_branch: str = Field(min_length=1, max_length=1)
    scope_presence: tuple[RelationEffectResearchScope, ...] = Field(
        min_length=1,
        max_length=2,
    )
    dependency_status: RelationEffectDependencyStatus
    required_rule_dimensions: tuple[
        RelationEffectRuleDimension,
        ...,
    ] = Field(min_length=6, max_length=6)
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    selection_authority: Literal[False]

    @model_validator(mode="after")
    def dependency_and_identity_are_valid(
        self,
    ) -> RelationEffectRuleDemand:
        expected_scope_presence = (
            ("EXACT_IDENTITY_ONLY", "ELEMENT_AFFINITY_INCLUDED")
            if self.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
            else ("ELEMENT_AFFINITY_INCLUDED",)
        )
        if self.scope_presence != expected_scope_presence:
            raise ValueError("relation_effect_frontier_scope_dependency_mismatch")
        expected_match_kind = (
            "EXACT_IDENTITY"
            if self.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
            else "SAME_ELEMENT_DIFFERENT_IDENTITY"
        )
        if self.source_match_kind != expected_match_kind:
            raise ValueError("relation_effect_frontier_match_dependency_mismatch")
        if (
            self.required_rule_dimensions
            != RELATION_EFFECT_REQUIRED_RULE_DIMENSIONS
        ):
            raise ValueError("relation_effect_frontier_rule_dimensions_invalid")
        identity = self.model_dump(mode="json", exclude={"demand_ref"})
        if self.demand_ref != stable_ref(
            "v60-relation-effect-rule-demand",
            identity,
        ):
            raise ValueError("relation_effect_frontier_demand_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> RelationEffectRuleDemand:
        identity = {
            **values,
            "required_rule_dimensions": (
                RELATION_EFFECT_REQUIRED_RULE_DIMENSIONS
            ),
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
            "selection_authority": False,
        }
        return cls(
            demand_ref=stable_ref(
                "v60-relation-effect-rule-demand",
                identity,
            ),
            **identity,
        )


class MingliRelationEffectResearchFrontierEnvelope(BaseModel):
    """Read-only map of which authority dependency blocks each relation hit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    frontier_ref: str = Field(min_length=1)
    frontier_hash: str = Field(min_length=64, max_length=64)
    frontier_version: Literal[
        "v60.mingli-relation-effect-research-frontier.001"
    ] = RELATION_EFFECT_RESEARCH_FRONTIER_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    reading_ref: str = Field(min_length=1)
    reading_hash: str = Field(min_length=64, max_length=64)
    source_review_vector_ref: str = Field(min_length=1)
    source_review_vector_hash: str = Field(min_length=64, max_length=64)
    prerequisite_ref: str = Field(min_length=1)
    prerequisite_hash: str = Field(min_length=64, max_length=64)
    refusal_receipt_ref: str = Field(min_length=1)
    refusal_receipt_hash: str = Field(min_length=64, max_length=64)
    demands: tuple[RelationEffectRuleDemand, ...]
    demand_count: int = Field(ge=0)
    scope_invariant_rule_demand_count: int = Field(ge=0)
    match_scope_rule_first_count: int = Field(ge=0)
    admitted_effect_rule_count: Literal[0]
    research_semantics: Literal[
        "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY"
    ]
    source_discussion_disposition: Literal["ABSTAIN"]
    effect_status: Literal["UNRESOLVED"]
    usability_status: Literal["UNRESOLVED"]
    provider_invoked: Literal[False]
    decision_created: Literal[False]
    gate_invoked: Literal[False]
    selection_authority: Literal[False]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_counts_and_order_are_valid(
        self,
    ) -> MingliRelationEffectResearchFrontierEnvelope:
        demand_keys = tuple(
            (
                PILLAR_SLOT_ORDER.index(item.visible_slot),
                item.visible_stem,
                PILLAR_SLOT_ORDER.index(item.source_slot),
                item.source_branch,
                PILLAR_SLOT_ORDER.index(item.peer_slot),
                item.peer_branch,
                item.relation_type,
                item.intersection_ref,
            )
            for item in self.demands
        )
        if demand_keys != tuple(sorted(set(demand_keys))):
            raise ValueError("relation_effect_frontier_demands_not_ordered_unique")
        expected_counts = {
            "demand_count": len(self.demands),
            "scope_invariant_rule_demand_count": sum(
                item.dependency_status == "SCOPE_INVARIANT_RULE_DEMAND"
                for item in self.demands
            ),
            "match_scope_rule_first_count": sum(
                item.dependency_status == "MATCH_SCOPE_RULE_FIRST"
                for item in self.demands
            ),
            "admitted_effect_rule_count": 0,
        }
        if any(getattr(self, key) != value for key, value in expected_counts.items()):
            raise ValueError("relation_effect_frontier_count_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"frontier_ref", "frontier_hash"},
        )
        if self.frontier_hash != content_hash(identity):
            raise ValueError("relation_effect_frontier_hash_mismatch")
        if self.frontier_ref != stable_ref(
            "v60-relation-effect-research-frontier",
            identity,
        ):
            raise ValueError("relation_effect_frontier_ref_mismatch")
        return self

    @classmethod
    def issue(
        cls,
        **values: Any,
    ) -> MingliRelationEffectResearchFrontierEnvelope:
        identity = {
            "frontier_version": RELATION_EFFECT_RESEARCH_FRONTIER_VERSION,
            **values,
            "demands": tuple(
                item.model_dump(mode="json")
                if isinstance(item, BaseModel)
                else item
                for item in values["demands"]
            ),
            "research_semantics": (
                "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY"
            ),
            "source_discussion_disposition": "ABSTAIN",
            "effect_status": "UNRESOLVED",
            "usability_status": "UNRESOLVED",
            "provider_invoked": False,
            "decision_created": False,
            "gate_invoked": False,
            "selection_authority": False,
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            frontier_ref=stable_ref(
                "v60-relation-effect-research-frontier",
                identity,
            ),
            frontier_hash=content_hash(identity),
            **identity,
        )
