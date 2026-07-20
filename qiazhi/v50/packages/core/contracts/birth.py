from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from core.contracts.base import CalendarType, Gender, V50Model, require_non_empty


class BirthInputCanonical(V50Model):
    version: str = "v50.birth_input_canonical.v1"
    birth_input_id: str
    name: str = ""
    gender: Gender = Gender.UNKNOWN
    calendar_type: CalendarType = CalendarType.UNKNOWN
    birth_date: str = ""
    birth_time: str = ""
    birth_location: str = ""
    timezone: str = ""
    true_solar_time_policy: str = "not_applied"
    lunar_leap_month: bool | None = None
    year_pillar: str = ""
    month_pillar: str = ""
    day_pillar: str = ""
    hour_pillar: str = ""
    input_quality: str = "unknown"
    pillar_fact_source: Literal[
        "unknown",
        "calendar_derived_formal",
        "calendar_verified_supplied",
        "structurally_legal_hypothetical",
        "unverified_legacy",
    ] = "unknown"
    warnings: list[str] = Field(default_factory=list)
    boundary: str = "birth_input_is_single_source_and_cannot_be_mutated_by_engines"

    @model_validator(mode="after")
    def _boundary(self) -> "BirthInputCanonical":
        require_non_empty(self.birth_input_id, "birth_input_id")
        require_non_empty(self.birth_date, "birth_date")
        require_non_empty(self.birth_time, "birth_time")
        require_non_empty(self.timezone, "timezone")
        return self


class CalendarNormalizationResult(V50Model):
    version: str = "v50.calendar_normalization_result.v1"
    normalization_id: str
    birth_input_id: str
    solar_date: str = ""
    lunar_date: str = ""
    hour_branch: str = ""
    timezone: str = ""
    true_solar_offset_minutes: int | None = None
    warnings: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    boundary: str = "calendar_normalization_is_deterministic_and_does_not_create_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "CalendarNormalizationResult":
        require_non_empty(self.normalization_id, "normalization_id")
        require_non_empty(self.birth_input_id, "birth_input_id")
        require_non_empty(self.timezone, "timezone")
        return self
