from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash


class YunGenderCode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    gender: Literal["male", "female"]
    lunar_python_code: Literal[0, 1]


class BaziTimingEvidenceProfile(BaseModel):
    """Owner-bounded rules for deterministic timing coordinates only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    governance_status: Literal["OWNER_AUTHORIZED_COORDINATES_ONLY"]
    runtime_scope: Literal["DETERMINISTIC_TIMING_COORDINATES"]
    professionally_reviewed: Literal[False]
    source_refs: tuple[str, ...] = Field(min_length=1)
    calendar_engine_version: str = Field(min_length=1)
    yun_gender_codes: tuple[YunGenderCode, ...] = Field(min_length=2, max_length=2)
    timing_layers: tuple[Literal["DAYUN", "ANNUAL", "MONTHLY"], ...] = Field(
        min_length=3,
        max_length=3,
    )
    admitted_relation_types: tuple[
        Literal[
            "same_branch_membership",
            "six_clash_membership",
            "six_harmony_membership",
        ],
        ...,
    ] = Field(min_length=3, max_length=3)
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def profile_values_are_complete(self) -> BaziTimingEvidenceProfile:
        if {item.gender for item in self.yun_gender_codes} != {"male", "female"}:
            raise ValueError("timing_profile_gender_codes_incomplete")
        if len({item.lunar_python_code for item in self.yun_gender_codes}) != 2:
            raise ValueError("timing_profile_gender_codes_not_unique")
        if self.timing_layers != ("DAYUN", "ANNUAL", "MONTHLY"):
            raise ValueError("timing_profile_layer_order_invalid")
        if len(self.admitted_relation_types) != len(set(self.admitted_relation_types)):
            raise ValueError("timing_profile_relation_types_not_unique")
        if len(self.forbidden_conclusions) != len(set(self.forbidden_conclusions)):
            raise ValueError("timing_profile_forbidden_conclusions_not_unique")
        return self

    @property
    def source_ref(self) -> str:
        return f"{self.profile_id}@{self.profile_version}"

    @property
    def profile_hash(self) -> str:
        return content_hash(self.model_dump(mode="json"))
