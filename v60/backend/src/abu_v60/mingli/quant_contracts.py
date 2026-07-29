from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

QUANT_VECTOR_VERSION = "v60.mingli-quant-foundation-vector.001"


class ElementMembershipMeasurement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    element: Literal["wood", "fire", "earth", "metal", "water"]
    visible_stem_count: int = Field(ge=0, le=4)
    hidden_stem_membership_count: int = Field(ge=0, le=12)
    total_membership_count: int = Field(ge=0, le=16)
    total_membership_share: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def count_is_additive(self) -> ElementMembershipMeasurement:
        if self.total_membership_count != (
            self.visible_stem_count + self.hidden_stem_membership_count
        ):
            raise ValueError("quant_element_membership_count_mismatch")
        return self


class PolarityMembershipMeasurement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    polarity: Literal["yin", "yang"]
    visible_stem_count: int = Field(ge=0, le=4)
    hidden_stem_membership_count: int = Field(ge=0, le=12)
    total_membership_count: int = Field(ge=0, le=16)

    @model_validator(mode="after")
    def count_is_additive(self) -> PolarityMembershipMeasurement:
        if self.total_membership_count != (
            self.visible_stem_count + self.hidden_stem_membership_count
        ):
            raise ValueError("quant_polarity_membership_count_mismatch")
        return self


class TenGodOccurrence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    occurrence_ref: str = Field(min_length=1)
    pillar_slot: Literal["year", "month", "day", "hour"]
    layer: Literal["VISIBLE_STEM", "HIDDEN_STEM"]
    stem: str = Field(min_length=1, max_length=1)
    branch: str | None = Field(default=None, min_length=1, max_length=1)
    membership_order: int | None = Field(default=None, ge=0, le=2)
    label: Literal[
        "日主",
        "比肩",
        "劫财",
        "食神",
        "伤官",
        "偏财",
        "正财",
        "七杀",
        "正官",
        "偏印",
        "正印",
    ]
    evidence_refs: tuple[str, ...] = Field(min_length=1)


class TenGodCount(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: Literal[
        "比肩",
        "劫财",
        "食神",
        "伤官",
        "偏财",
        "正财",
        "七杀",
        "正官",
        "偏印",
        "正印",
    ]
    visible_count: int = Field(ge=0, le=3)
    hidden_membership_count: int = Field(ge=0, le=12)


class SourceManifestationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    visible_slot: Literal["year", "month", "day", "hour"]
    visible_stem: str = Field(min_length=1, max_length=1)
    source_slot: Literal["year", "month", "day", "hour"]
    source_branch: str = Field(min_length=1, max_length=1)
    hidden_stem: str = Field(min_length=1, max_length=1)
    source_match_kind: Literal[
        "EXACT_IDENTITY",
        "SAME_ELEMENT_DIFFERENT_IDENTITY",
    ]
    evidence_states: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    effect_status: Literal["EFFECT_UNRESOLVED"]


class MingliQuantFoundationVector(BaseModel):
    """Exact chart measurements that deliberately stop before interpretation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_ref: str = Field(min_length=1)
    vector_hash: str = Field(min_length=64, max_length=64)
    vector_version: str = QUANT_VECTOR_VERSION
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    quant_profile_ref: str = Field(min_length=1)
    quant_profile_hash: str = Field(min_length=64, max_length=64)
    day_master_stem: str = Field(min_length=1, max_length=1)
    day_master_element: Literal["wood", "fire", "earth", "metal", "water"]
    day_master_polarity: Literal["yin", "yang"]
    visible_stem_total: Literal[4]
    hidden_stem_membership_total: int = Field(ge=4, le=12)
    element_measurements: tuple[ElementMembershipMeasurement, ...] = Field(
        min_length=5,
        max_length=5,
    )
    polarity_measurements: tuple[PolarityMembershipMeasurement, ...] = Field(
        min_length=2,
        max_length=2,
    )
    ten_god_occurrences: tuple[TenGodOccurrence, ...] = Field(min_length=4)
    ten_god_counts: tuple[TenGodCount, ...] = Field(min_length=10, max_length=10)
    source_manifestation_evidence: tuple[SourceManifestationEvidence, ...]
    measurement_semantics: Literal["DETERMINISTIC_UNWEIGHTED_STRUCTURE"]
    calibration_status: Literal["NOT_CALIBRATED"]
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)
    read_only: Literal[True]

    @model_validator(mode="after")
    def identity_and_measurement_shape_are_valid(
        self,
    ) -> MingliQuantFoundationVector:
        if [item.element for item in self.element_measurements] != [
            "wood",
            "fire",
            "earth",
            "metal",
            "water",
        ]:
            raise ValueError("quant_vector_element_order_invalid")
        if [item.polarity for item in self.polarity_measurements] != ["yang", "yin"]:
            raise ValueError("quant_vector_polarity_order_invalid")
        if len({item.occurrence_ref for item in self.ten_god_occurrences}) != len(
            self.ten_god_occurrences
        ):
            raise ValueError("quant_vector_ten_god_occurrence_not_unique")
        if len({item.evidence_ref for item in self.source_manifestation_evidence}) != len(
            self.source_manifestation_evidence
        ):
            raise ValueError("quant_vector_source_evidence_not_unique")
        identity = self.model_dump(
            mode="json",
            exclude={"vector_ref", "vector_hash"},
        )
        if self.vector_hash != content_hash(identity):
            raise ValueError("quant_vector_hash_mismatch")
        if self.vector_ref != stable_ref("v60-mingli-quant-vector", identity):
            raise ValueError("quant_vector_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliQuantFoundationVector:
        identity = {
            "vector_version": QUANT_VECTOR_VERSION,
            **values,
            "read_only": True,
        }
        for key in (
            "element_measurements",
            "polarity_measurements",
            "ten_god_occurrences",
            "ten_god_counts",
            "source_manifestation_evidence",
        ):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        return cls(
            vector_ref=stable_ref("v60-mingli-quant-vector", identity),
            vector_hash=content_hash(identity),
            **identity,
        )
