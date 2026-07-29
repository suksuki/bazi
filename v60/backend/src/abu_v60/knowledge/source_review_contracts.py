from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash


class SourceCoordinateReviewRule(BaseModel):
    """Admit one relation membership as a review trigger, never an effect."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    admitted_fact_type: Literal[
        "six_clash_membership",
        "six_harmony_membership",
    ]
    required_authority: Literal["SYSTEM_DETERMINISTIC_BOUNDED"]
    required_boolean_claims: tuple[
        Literal["membership_only", "effect_not_inferred"],
        ...,
    ] = Field(min_length=2, max_length=2)
    review_state: Literal[
        "SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
        "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
    ]
    effect_conclusion_allowed: Literal[False]
    weight_allowed: Literal[False]

    @model_validator(mode="after")
    def claims_and_review_state_are_consistent(
        self,
    ) -> SourceCoordinateReviewRule:
        if set(self.required_boolean_claims) != {
            "membership_only",
            "effect_not_inferred",
        }:
            raise ValueError("source_review_required_claims_incomplete")
        expected = (
            "SIX_CLASH_COORDINATE_REVIEW_REQUIRED"
            if self.admitted_fact_type == "six_clash_membership"
            else "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED"
        )
        if self.review_state != expected:
            raise ValueError("source_review_state_fact_type_mismatch")
        return self

    @property
    def rule_ref(self) -> str:
        return f"{self.rule_id}@{self.rule_version}"


class BaziSourceCoordinateReviewProfile(BaseModel):
    """Hash-locked triage for source coordinates intersected by relations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_AUTHORIZED_EVIDENCE_TRIAGE_ONLY"]
    runtime_scope: Literal["SOURCE_COORDINATE_RELATION_REVIEW"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    rules: tuple[SourceCoordinateReviewRule, ...] = Field(
        min_length=2,
        max_length=2,
    )
    clear_state: Literal["NO_ADMITTED_RELATION_INTERSECTION"]
    unresolved_dimensions: tuple[str, ...] = Field(min_length=1)
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def rule_coverage_and_boundaries_are_complete(
        self,
    ) -> BaziSourceCoordinateReviewProfile:
        fact_types = [rule.admitted_fact_type for rule in self.rules]
        if set(fact_types) != {
            "six_clash_membership",
            "six_harmony_membership",
        } or len(fact_types) != len(set(fact_types)):
            raise ValueError("source_review_rules_must_cover_relations_once")
        if len(self.unresolved_dimensions) != len(set(self.unresolved_dimensions)):
            raise ValueError("source_review_unresolved_dimensions_not_unique")
        if len(self.forbidden_conclusions) != len(set(self.forbidden_conclusions)):
            raise ValueError("source_review_forbidden_conclusions_not_unique")
        required_forbidden = {
            "root_verdict",
            "usable_root",
            "root_strength",
            "relation_effect",
            "mechanism_effectiveness",
            "empirical_probability",
        }
        if not required_forbidden <= set(self.forbidden_conclusions):
            raise ValueError("source_review_forbidden_conclusions_incomplete")
        return self

    @property
    def source_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))
