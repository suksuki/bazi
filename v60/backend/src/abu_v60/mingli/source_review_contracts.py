from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

SOURCE_REVIEW_VECTOR_VERSION = "v60.mingli-source-coordinate-review-vector.001"
SOURCE_REVIEW_STATE_ORDER = (
    "NO_ADMITTED_RELATION_INTERSECTION",
    "SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
    "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
)


class SourceRelationIntersection(BaseModel):
    """One admitted relation fact touching a source coordinate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intersection_ref: str = Field(min_length=1)
    relation_fact_ref: str = Field(min_length=1)
    relation_type: Literal[
        "six_clash_membership",
        "six_harmony_membership",
    ]
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: str = Field(min_length=1, max_length=1)
    peer_slot: Literal["year", "month", "day", "hour"]
    peer_branch: str = Field(min_length=1, max_length=1)
    rule_ref: str = Field(min_length=1)
    review_state: Literal[
        "SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
        "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
    ]
    effect_status: Literal["UNRESOLVED"]


class SourceCoordinateReviewEvidence(BaseModel):
    """Review state for one existing source/manifestation evidence item."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    review_ref: str = Field(min_length=1)
    source_evidence_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: str = Field(min_length=1, max_length=1)
    hidden_stem: str = Field(min_length=1, max_length=1)
    source_match_kind: Literal[
        "EXACT_IDENTITY",
        "SAME_ELEMENT_DIFFERENT_IDENTITY",
    ]
    relation_intersections: tuple[SourceRelationIntersection, ...]
    review_states: tuple[
        Literal[
            "NO_ADMITTED_RELATION_INTERSECTION",
            "SIX_CLASH_COORDINATE_REVIEW_REQUIRED",
            "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED",
        ],
        ...,
    ] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    relation_effect_status: Literal["UNRESOLVED"]
    root_usability_status: Literal["UNRESOLVED"]

    @model_validator(mode="after")
    def review_state_matches_intersections(
        self,
    ) -> SourceCoordinateReviewEvidence:
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError("source_review_evidence_refs_not_sorted_unique")
        intersection_refs = tuple(item.intersection_ref for item in self.relation_intersections)
        if intersection_refs != tuple(sorted(set(intersection_refs))):
            raise ValueError("source_review_intersections_not_sorted_unique")
        expected_states = (
            tuple(
                state
                for state in SOURCE_REVIEW_STATE_ORDER
                if state in {item.review_state for item in self.relation_intersections}
            )
            if self.relation_intersections
            else ("NO_ADMITTED_RELATION_INTERSECTION",)
        )
        if self.review_states != expected_states:
            raise ValueError("source_review_state_intersection_mismatch")
        return self


class MingliSourceCoordinateReviewVector(BaseModel):
    """Append-only relation triage without a root or effect verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_ref: str = Field(min_length=1)
    vector_hash: str = Field(min_length=64, max_length=64)
    vector_version: str = SOURCE_REVIEW_VECTOR_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    quant_vector_ref: str = Field(min_length=1)
    quant_vector_hash: str = Field(min_length=64, max_length=64)
    source_review_profile_ref: str = Field(min_length=1)
    source_review_profile_hash: str = Field(min_length=64, max_length=64)
    reviews: tuple[SourceCoordinateReviewEvidence, ...]
    source_evidence_count: int = Field(ge=0)
    exact_identity_count: int = Field(ge=0)
    elemental_affinity_count: int = Field(ge=0)
    clear_coordinate_count: int = Field(ge=0)
    review_required_count: int = Field(ge=0)
    six_clash_intersection_count: int = Field(ge=0)
    six_harmony_intersection_count: int = Field(ge=0)
    review_semantics: Literal["SOURCE_COORDINATE_RELATION_TRIAGE_ONLY"]
    professional_verdict_allowed: Literal[False]
    probability_claim_allowed: Literal[False]
    canonical_write_allowed: Literal[False]
    unresolved_dimensions: tuple[str, ...] = Field(min_length=1)
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_counts_are_valid(
        self,
    ) -> MingliSourceCoordinateReviewVector:
        refs = tuple(item.review_ref for item in self.reviews)
        if refs != tuple(sorted(set(refs))):
            raise ValueError("source_review_items_not_sorted_unique")
        expected_counts = {
            "source_evidence_count": len(self.reviews),
            "exact_identity_count": sum(
                item.source_match_kind == "EXACT_IDENTITY" for item in self.reviews
            ),
            "elemental_affinity_count": sum(
                item.source_match_kind == "SAME_ELEMENT_DIFFERENT_IDENTITY" for item in self.reviews
            ),
            "clear_coordinate_count": sum(not item.relation_intersections for item in self.reviews),
            "review_required_count": sum(
                bool(item.relation_intersections) for item in self.reviews
            ),
            "six_clash_intersection_count": sum(
                item.relation_type == "six_clash_membership"
                for review in self.reviews
                for item in review.relation_intersections
            ),
            "six_harmony_intersection_count": sum(
                item.relation_type == "six_harmony_membership"
                for review in self.reviews
                for item in review.relation_intersections
            ),
        }
        if any(getattr(self, key) != value for key, value in expected_counts.items()):
            raise ValueError("source_review_vector_count_mismatch")
        identity = self.model_dump(
            mode="json",
            exclude={"vector_ref", "vector_hash"},
        )
        if self.vector_hash != content_hash(identity):
            raise ValueError("source_review_vector_hash_mismatch")
        if self.vector_ref != stable_ref("v60-mingli-source-review-vector", identity):
            raise ValueError("source_review_vector_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliSourceCoordinateReviewVector:
        reviews = tuple(
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in values["reviews"]
        )
        identity = {
            "vector_version": SOURCE_REVIEW_VECTOR_VERSION,
            **values,
            "reviews": reviews,
            "review_semantics": "SOURCE_COORDINATE_RELATION_TRIAGE_ONLY",
            "professional_verdict_allowed": False,
            "probability_claim_allowed": False,
            "canonical_write_allowed": False,
            "read_only": True,
        }
        return cls(
            vector_ref=stable_ref("v60-mingli-source-review-vector", identity),
            vector_hash=content_hash(identity),
            **identity,
        )
