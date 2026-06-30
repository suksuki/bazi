from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from v40.contracts.base import V40Model


class BirthInputCanonical(V40Model):
    version: str = "v40.birth_input_canonical.v1"
    input_id: str
    calendar_type: Literal["solar", "lunar"] = "solar"
    birth_date: str = ""
    birth_time: str = ""
    gender: str = ""
    timezone: str = ""
    location: str = ""
    leap_month: bool = False
    source: str = "user_supplied_birth_input"
    immutable: bool = True
    boundary: str = "birth_input_canonical_enables_chart_engines_without_training_birth_facts"

    @model_validator(mode="after")
    def _birth_input_boundary(self) -> "BirthInputCanonical":
        if not self.input_id.strip():
            raise ValueError("BirthInputCanonical requires input_id")
        if not self.immutable:
            raise ValueError("BirthInputCanonical must be immutable in V40 runtime")
        return self

    @property
    def can_run_ziwei(self) -> bool:
        return bool(self.birth_date.strip() and self.birth_time.strip() and self.gender.strip())

    @property
    def ziwei_input_quality(self) -> str:
        if self.can_run_ziwei:
            return "complete"
        if self.birth_date.strip() or self.birth_time.strip() or self.gender.strip():
            return "partial"
        return "unavailable"


class BaziChartFacts(V40Model):
    version: str = "v40.bazi_chart_facts.v1"
    chart_id: str
    gender: str = ""
    year_stem: str
    year_branch: str
    month_stem: str
    month_branch: str
    day_stem: str
    day_branch: str
    hour_stem: str = ""
    hour_branch: str = ""
    current_luck: str = ""
    current_year: str = ""
    source: str = "user_supplied_or_imported_chart_facts"
    immutable: bool = True
    boundary: str = "bazi_chart_facts_are_input_facts_not_trainable_policy"

    @model_validator(mode="after")
    def _chart_fact_boundary(self) -> "BaziChartFacts":
        required = [
            self.chart_id,
            self.year_stem,
            self.year_branch,
            self.month_stem,
            self.month_branch,
            self.day_stem,
            self.day_branch,
        ]
        if not all(value.strip() for value in required):
            raise ValueError("BaziChartFacts requires chart_id and at least year/month/day pillars")
        if not self.immutable:
            raise ValueError("BaziChartFacts must be immutable in V40 runtime")
        return self

    @property
    def pillars_text(self) -> str:
        pillars = [
            f"{self.year_stem}{self.year_branch}",
            f"{self.month_stem}{self.month_branch}",
            f"{self.day_stem}{self.day_branch}",
        ]
        if self.hour_stem and self.hour_branch:
            pillars.append(f"{self.hour_stem}{self.hour_branch}")
        return " ".join(pillars)


class ZiweiChartFacts(V40Model):
    version: str = "v40.ziwei_chart_facts.v1"
    chart_id: str
    life_palace: str = ""
    body_palace: str = ""
    palaces: dict[str, dict[str, object]] = Field(default_factory=dict)
    major_stars: dict[str, list[str]] = Field(default_factory=dict)
    annual_transformations: dict[str, str] = Field(default_factory=dict)
    decade_luck: str = ""
    flow_year: str = ""
    palace_notes: dict[str, str] = Field(default_factory=dict)
    domain_lenses: dict[str, str] = Field(default_factory=dict)
    source: str = "user_supplied_or_imported_ziwei_facts"
    immutable: bool = True
    boundary: str = "ziwei_chart_facts_are_sidecar_facts_not_trainable_policy"

    @model_validator(mode="after")
    def _ziwei_fact_boundary(self) -> "ZiweiChartFacts":
        if not self.chart_id.strip():
            raise ValueError("ZiweiChartFacts requires chart_id")
        if not self.immutable:
            raise ValueError("ZiweiChartFacts must be immutable in V40 runtime")
        return self


class SyntheticCaseSeed(V40Model):
    version: str = "v40.synthetic_case_seed.v1"
    seed_id: str
    question: str
    topic: str = "career"
    chart_facts: BaziChartFacts
    expected_keywords: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    boundary: str = "synthetic_case_seed_generates_evaluation_case_without_claiming_real_world_truth"

    @model_validator(mode="after")
    def _seed_boundary(self) -> "SyntheticCaseSeed":
        if not self.seed_id.strip():
            raise ValueError("SyntheticCaseSeed requires seed_id")
        if not self.question.strip():
            raise ValueError("SyntheticCaseSeed requires question")
        if not self.expected_keywords:
            raise ValueError("SyntheticCaseSeed requires expected_keywords")
        if not self.forbidden_assertions:
            raise ValueError("SyntheticCaseSeed requires forbidden_assertions")
        return self
