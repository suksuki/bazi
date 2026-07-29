from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

TIMING_VECTOR_VERSION = "v60.mingli-timing-evidence-vector.001"


class TimingCoordinate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    coordinate_ref: str = Field(min_length=1)
    layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    pillar: str = Field(min_length=2, max_length=2)
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    ten_god_label: str = Field(min_length=1)
    start_year: int | None = None
    end_year: int | None = None
    calculation_status: Literal["DETERMINISTIC_COORDINATE"]

    @model_validator(mode="after")
    def period_bounds_match_layer(self) -> TimingCoordinate:
        if self.pillar != f"{self.stem}{self.branch}":
            raise ValueError("timing_coordinate_pillar_mismatch")
        if self.layer == "DAYUN":
            if self.start_year is None or self.end_year is None:
                raise ValueError("timing_dayun_requires_year_bounds")
            if self.start_year > self.end_year:
                raise ValueError("timing_dayun_year_bounds_invalid")
        elif self.start_year is not None or self.end_year is not None:
            raise ValueError("timing_calendar_coordinate_cannot_claim_year_bounds")
        return self


class TimingRelationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    timing_coordinate_ref: str = Field(min_length=1)
    timing_layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    timing_branch: str = Field(min_length=1, max_length=1)
    natal_slot: Literal["year", "month", "day", "hour"]
    natal_branch: str = Field(min_length=1, max_length=1)
    relation_type: Literal[
        "same_branch_membership",
        "six_clash_membership",
        "six_harmony_membership",
    ]
    evidence_refs: tuple[str, ...] = Field(min_length=2)
    rule_ref: str = Field(min_length=1)
    relation_status: Literal["MEMBERSHIP_PRESENT"]
    effect_status: Literal["UNRESOLVED"]


class TimingCandidateOverlap(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    overlap_ref: str = Field(min_length=1)
    timing_coordinate_ref: str = Field(min_length=1)
    timing_layer: Literal["DAYUN", "ANNUAL", "MONTHLY"]
    timing_ten_god_label: str = Field(min_length=1)
    candidate_ref: str = Field(min_length=1)
    matching_role_ids: tuple[str, ...] = Field(min_length=1)
    overlap_status: Literal["LABEL_OVERLAP_ONLY"]
    activation_status: Literal["UNRESOLVED"]
    effect_status: Literal["UNRESOLVED"]


class MingliTimingEvidenceVector(BaseModel):
    """Frozen Dayun/year/month coordinates that stop before effect judgment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_ref: str = Field(min_length=1)
    vector_hash: str = Field(min_length=64, max_length=64)
    vector_version: str = TIMING_VECTOR_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    birth_input_hash: str = Field(min_length=64, max_length=64)
    timing_profile_ref: str = Field(min_length=1)
    timing_profile_hash: str = Field(min_length=64, max_length=64)
    foundation_profile_ref: str = Field(min_length=1)
    foundation_profile_hash: str = Field(min_length=64, max_length=64)
    calendar_engine_version: str = Field(min_length=1)
    analysis_date: date
    timezone: str = Field(min_length=1)
    day_master_stem: str = Field(min_length=1, max_length=1)
    coordinates: tuple[TimingCoordinate, ...] = Field(min_length=3, max_length=3)
    relation_evidence: tuple[TimingRelationEvidence, ...] = ()
    candidate_overlaps: tuple[TimingCandidateOverlap, ...] = ()
    timing_semantics: Literal["COORDINATE_AND_MEMBERSHIP_ONLY"]
    activation_status: Literal["UNRESOLVED"]
    effect_status: Literal["UNRESOLVED"]
    calibration_status: Literal["NOT_CALIBRATED"]
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_shape_are_valid(self) -> MingliTimingEvidenceVector:
        if tuple(item.layer for item in self.coordinates) != (
            "DAYUN",
            "ANNUAL",
            "MONTHLY",
        ):
            raise ValueError("timing_vector_coordinate_order_invalid")
        if len({item.coordinate_ref for item in self.coordinates}) != len(self.coordinates):
            raise ValueError("timing_vector_coordinate_not_unique")
        if len({item.evidence_ref for item in self.relation_evidence}) != len(
            self.relation_evidence
        ):
            raise ValueError("timing_vector_relation_evidence_not_unique")
        if len({item.overlap_ref for item in self.candidate_overlaps}) != len(
            self.candidate_overlaps
        ):
            raise ValueError("timing_vector_candidate_overlap_not_unique")
        identity = self.model_dump(
            mode="json",
            exclude={"vector_ref", "vector_hash"},
        )
        if self.vector_hash != content_hash(identity):
            raise ValueError("timing_vector_hash_mismatch")
        if self.vector_ref != stable_ref("v60-mingli-timing-vector", identity):
            raise ValueError("timing_vector_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliTimingEvidenceVector:
        identity = {
            "vector_version": TIMING_VECTOR_VERSION,
            **values,
            "read_only": True,
        }
        for key in ("coordinates", "relation_evidence", "candidate_overlaps"):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        return cls(
            vector_ref=stable_ref("v60-mingli-timing-vector", identity),
            vector_hash=content_hash(identity),
            **identity,
        )
