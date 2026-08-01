from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.provenance import content_hash, stable_ref

MINGLI_STAGE_PROJECTION_VERSION = "v60.mingli-stage-projection.003"


class MingliStageMode(StrEnum):
    NATAL_4 = "NATAL_4"
    NATAL_DAYUN_YEAR_6 = "NATAL_DAYUN_YEAR_6"


class MingliStageColumn(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    column_ref: str = Field(min_length=1)
    slot: Literal[
        "NATAL_YEAR",
        "NATAL_MONTH",
        "NATAL_DAY",
        "NATAL_HOUR",
        "DAYUN",
        "ANNUAL",
    ]
    label: str = Field(min_length=1)
    source_layer: Literal["NATAL", "DAYUN", "ANNUAL"]
    pillar: str = Field(min_length=2, max_length=2)
    stem: str = Field(min_length=1, max_length=1)
    branch: str = Field(min_length=1, max_length=1)
    coordinate_ref: str = Field(min_length=1)
    start_year: int | None = None
    end_year: int | None = None
    start_date: date | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    end_date: date | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    calculation_status: Literal["DETERMINISTIC_COORDINATE"]

    @model_validator(mode="after")
    def coordinate_shape_is_valid(self) -> MingliStageColumn:
        if self.pillar != f"{self.stem}{self.branch}":
            raise ValueError("mingli_stage_column_pillar_mismatch")
        if self.source_layer == "DAYUN":
            if (
                self.start_year is None
                or self.end_year is None
                or self.start_date is None
                or self.end_date is None
            ):
                raise ValueError("mingli_stage_dayun_bounds_required")
            if self.start_date >= self.end_date:
                raise ValueError("mingli_stage_dayun_date_bounds_invalid")
            if self.start_year != self.start_date.year or self.end_year != self.end_date.year - 1:
                raise ValueError("mingli_stage_dayun_year_date_bounds_mismatch")
        elif (
            self.start_year is not None
            or self.end_year is not None
            or self.start_date is not None
            or self.end_date is not None
        ):
            raise ValueError("mingli_stage_non_dayun_bounds_forbidden")
        return self


class MingliStageBody(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    body_ref: str = Field(min_length=1)
    column_ref: str = Field(min_length=1)
    role: Literal["STEM", "BRANCH"]
    glyph: str = Field(min_length=1, max_length=1)
    order: int = Field(ge=0)


class MingliStageRelationMembership(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    relation_ref: str = Field(min_length=1)
    relation_type: Literal["six_clash_membership", "six_harmony_membership"]
    label: str = Field(min_length=1)
    left_column_ref: str = Field(min_length=1)
    right_column_ref: str = Field(min_length=1)
    left_branch: str = Field(min_length=1, max_length=1)
    right_branch: str = Field(min_length=1, max_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    rule_ref: str = Field(min_length=1)
    rule_hash: str = Field(min_length=64, max_length=64)
    relation_status: Literal["MEMBERSHIP_PRESENT"]
    effect_status: Literal["UNRESOLVED"]
    usable_source_status: Literal["UNRESOLVED"]


class MingliStageProjection(BaseModel):
    """Four/six-column presentation contract that cannot promote effects."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    projection_ref: str = Field(min_length=1)
    projection_hash: str = Field(min_length=64, max_length=64)
    projection_version: Literal["v60.mingli-stage-projection.003"] = MINGLI_STAGE_PROJECTION_VERSION
    subject_id: str = Field(min_length=1)
    case_ref: str = Field(min_length=1)
    chart_version_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    reading_ref: str | None = None
    reading_hash: str | None = Field(default=None, min_length=64, max_length=64)
    display_name: str = Field(min_length=1)
    subject_kind: Literal[
        "HUMAN_OWNER",
        "HUMAN_REFERENCE",
        "CANONICAL_SYNTHETIC",
    ]
    identity_badge: Literal["私密真实档案", "真实参考档案", "角色合成设定"]
    privacy_scope: Literal[
        "PRIVATE_OWNER",
        "PRIVATE_REFERENCE",
        "PUBLIC_SYNTHETIC_SHOWCASE",
    ]
    stage_mode: MingliStageMode
    selected_year: int | None = None
    available_years: tuple[int, ...] = Field(min_length=1)
    current_dayun_label: str = Field(min_length=1)
    current_dayun_start_year: int
    current_dayun_end_year: int
    current_dayun_start_date: date
    current_dayun_end_date: date
    dayun_boundary_precision: Literal["START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY"]
    dayun_calculation_policy: Literal["LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES"]
    dayun_resolution_status: Literal["RESOLVED_OUTSIDE_BOUNDARY_DAY"]
    annual_label_semantics: Literal["SELECTED_SOLAR_YEAR_GANZHI"]
    foundation_profile_ref: str = Field(min_length=1)
    foundation_profile_hash: str = Field(min_length=64, max_length=64)
    timing_profile_ref: str = Field(min_length=1)
    timing_profile_hash: str = Field(min_length=64, max_length=64)
    columns: tuple[MingliStageColumn, ...]
    bodies: tuple[MingliStageBody, ...]
    relations: tuple[MingliStageRelationMembership, ...] = ()
    narrator_actor_id: Literal["ABU_NARRATOR_V1", "DUODUO_NARRATOR_V1"]
    narration_voice_status: Literal["OWNER_SELECTED", "AUDITION_CANDIDATE"]
    stage_semantics: Literal["COORDINATES_AND_MEMBERSHIP_ONLY"]
    relation_effect_status: Literal["UNRESOLVED"]
    usable_source_status: Literal["UNRESOLVED"]
    professional_verdict_allowed: Literal[False]
    forbidden_conclusions: tuple[str, ...] = Field(min_length=1)
    source_refs: tuple[str, ...] = Field(min_length=1)
    read_only: Literal[True]

    @model_validator(mode="after")
    def stage_identity_and_shape_are_valid(self) -> MingliStageProjection:
        expected_columns = 4 if self.stage_mode == MingliStageMode.NATAL_4 else 6
        expected_bodies = expected_columns * 2
        if len(self.columns) != expected_columns or len(self.bodies) != expected_bodies:
            raise ValueError("mingli_stage_shape_invalid")
        expected_slots = (
            "NATAL_YEAR",
            "NATAL_MONTH",
            "NATAL_DAY",
            "NATAL_HOUR",
        )
        if self.stage_mode == MingliStageMode.NATAL_DAYUN_YEAR_6:
            expected_slots += ("DAYUN", "ANNUAL")
            if self.selected_year is None:
                raise ValueError("mingli_stage_six_timing_required")
        elif self.selected_year is not None:
            raise ValueError("mingli_stage_four_timing_forbidden")
        if (self.reading_ref is None) != (self.reading_hash is None):
            raise ValueError("mingli_stage_reading_binding_incomplete")
        required_source_refs = {
            self.foundation_profile_ref,
            self.timing_profile_ref,
            self.chart_version_ref,
            self.life_case_revision_ref,
        }
        if self.reading_ref is not None:
            required_source_refs.add(self.reading_ref)
        if not required_source_refs.issubset(self.source_refs):
            raise ValueError("mingli_stage_required_source_ref_missing")
        if tuple(column.slot for column in self.columns) != expected_slots:
            raise ValueError("mingli_stage_column_order_invalid")
        if len({column.column_ref for column in self.columns}) != len(self.columns):
            raise ValueError("mingli_stage_column_identity_not_unique")
        if len({body.body_ref for body in self.bodies}) != len(self.bodies):
            raise ValueError("mingli_stage_body_identity_not_unique")
        if self.current_dayun_start_date >= self.current_dayun_end_date:
            raise ValueError("mingli_stage_dayun_date_bounds_invalid")
        if (
            self.current_dayun_start_year != self.current_dayun_start_date.year
            or self.current_dayun_end_year != self.current_dayun_end_date.year - 1
        ):
            raise ValueError("mingli_stage_dayun_year_date_bounds_mismatch")
        expected_years = tuple(
            range(
                self.current_dayun_start_date.year,
                self.current_dayun_end_date.year + 1,
            )
        )
        if self.available_years != expected_years:
            raise ValueError("mingli_stage_available_years_not_exact_boundary_span")
        if self.selected_year is not None and self.selected_year not in self.available_years:
            raise ValueError("mingli_stage_selected_year_outside_dayun")
        identity = self.model_dump(
            mode="json",
            exclude={"projection_ref", "projection_hash"},
        )
        if self.projection_hash != content_hash(identity):
            raise ValueError("mingli_stage_projection_hash_mismatch")
        if self.projection_ref != stable_ref("v60-mingli-stage", identity):
            raise ValueError("mingli_stage_projection_ref_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> MingliStageProjection:
        identity = {
            **values,
            "projection_version": MINGLI_STAGE_PROJECTION_VERSION,
            "read_only": True,
        }
        for key in ("columns", "bodies", "relations"):
            identity[key] = tuple(
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in identity[key]
            )
        return cls(
            projection_ref=stable_ref("v60-mingli-stage", identity),
            projection_hash=content_hash(identity),
            **identity,
        )
