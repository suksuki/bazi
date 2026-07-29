from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash

Element = Literal["wood", "fire", "earth", "metal", "water"]
TenGodRelationship = Literal[
    "same_element",
    "day_master_generates",
    "day_master_controls",
    "other_controls_day_master",
    "other_generates_day_master",
]
TenGodLabel = Literal[
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


class ElementCycleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    element: Element
    generates: Element
    controls: Element

    @model_validator(mode="after")
    def relations_are_not_reflexive(self) -> ElementCycleDefinition:
        if self.element in {self.generates, self.controls}:
            raise ValueError("quant_element_cycle_must_not_be_reflexive")
        return self


class TenGodDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relationship: TenGodRelationship
    same_polarity: bool
    label: TenGodLabel


class BaziQuantFoundationProfile(BaseModel):
    """Owner-bounded deterministic measurements, never strength or probability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_AUTHORIZED_MEASUREMENT_ONLY"]
    runtime_scope: Literal["DETERMINISTIC_STRUCTURE_MEASUREMENTS"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    element_cycles: tuple[ElementCycleDefinition, ...] = Field(
        min_length=5,
        max_length=5,
    )
    ten_god_definitions: tuple[TenGodDefinition, ...] = Field(
        min_length=10,
        max_length=10,
    )
    source_evidence_states: tuple[str, ...] = Field(min_length=1)
    source_match_kinds: tuple[
        Literal["EXACT_IDENTITY", "SAME_ELEMENT_DIFFERENT_IDENTITY"],
        ...,
    ] = Field(min_length=2, max_length=2)
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)
    calibration_status: Literal["NOT_CALIBRATED"]

    @model_validator(mode="after")
    def deterministic_tables_are_complete(self) -> BaziQuantFoundationProfile:
        elements = [item.element for item in self.element_cycles]
        expected_elements = {"wood", "fire", "earth", "metal", "water"}
        if set(elements) != expected_elements or len(elements) != len(set(elements)):
            raise ValueError("quant_element_cycle_must_cover_five_elements_once")
        generated = [item.generates for item in self.element_cycles]
        controlled = [item.controls for item in self.element_cycles]
        if set(generated) != expected_elements or set(controlled) != expected_elements:
            raise ValueError("quant_element_cycle_targets_must_be_complete")

        keys = {(item.relationship, item.same_polarity) for item in self.ten_god_definitions}
        expected_keys = {
            (relationship, same_polarity)
            for relationship in (
                "same_element",
                "day_master_generates",
                "day_master_controls",
                "other_controls_day_master",
                "other_generates_day_master",
            )
            for same_polarity in (False, True)
        }
        if keys != expected_keys:
            raise ValueError("quant_ten_god_definitions_must_cover_all_relations")
        labels = [item.label for item in self.ten_god_definitions]
        if len(labels) != len(set(labels)):
            raise ValueError("quant_ten_god_labels_must_be_unique")
        if len(self.source_evidence_states) != len(set(self.source_evidence_states)):
            raise ValueError("quant_source_evidence_states_must_be_unique")
        if len(self.forbidden_conclusions) != len(set(self.forbidden_conclusions)):
            raise ValueError("quant_forbidden_conclusions_must_be_unique")
        return self

    @property
    def source_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))
