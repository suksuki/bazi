from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from v30.contracts import RoleKey, V30Model
from v30.production.contracts import AssertionLevelHint, SignalPolarity
from v30.ziwei.standards import (
    TWELVE_PALACES,
    ZIWEI_DECISION_WEIGHT_V1,
    ZIWEI_FACT_LAYER_VERSION,
    ZIWEI_SIGNAL_LAYER_VERSION,
    ZIWEI_SYSTEM_STANDARD_VERSION,
)


ZiweiPalaceKey = Literal[
    "life",
    "siblings",
    "spouse",
    "children",
    "wealth",
    "health",
    "travel",
    "friends",
    "career",
    "property",
    "fortune",
    "parents",
]
ZiweiDomainKey = Literal[
    "wealth",
    "career",
    "relationship",
    "mobility",
    "health_pressure",
    "property",
]
ZiweiTransformKey = Literal["lu", "quan", "ke", "ji"]
ZiweiCycleScope = Literal["natal", "major_period", "annual"]
ZiweiSignalManifestation = Literal["observed", "not_yet_manifested", "context_blocked", "unknown"]


class ZiweiPalace(V30Model):
    palace_key: ZiweiPalaceKey
    branch: str = ""
    heavenly_stem: str = ""
    is_life_palace: bool = False
    is_body_palace: bool = False
    notes: list[str] = Field(default_factory=list)


class ZiweiStarPlacement(V30Model):
    star_key: str
    palace_key: ZiweiPalaceKey
    star_group: Literal["main", "auxiliary", "deferred"] = "main"
    brightness: str = ""
    source_method: str = ""


class ZiweiTransform(V30Model):
    transform_key: ZiweiTransformKey
    star_key: str = ""
    palace_key: ZiweiPalaceKey
    source: Literal["birth_year", "major_period", "annual"] = "birth_year"
    source_ref: str = ""


class ZiweiCycle(V30Model):
    scope: ZiweiCycleScope
    palace_key: ZiweiPalaceKey
    start_age: int | None = None
    end_age: int | None = None
    year: int | None = None
    source_ref: str = ""


class ZiweiChart(V30Model):
    version: str = ZIWEI_FACT_LAYER_VERSION
    chart_id: str
    reading_id: str
    standard_version: str = ZIWEI_SYSTEM_STANDARD_VERSION
    palaces: list[ZiweiPalace] = Field(default_factory=list)
    main_stars: list[ZiweiStarPlacement] = Field(default_factory=list)
    auxiliary_stars: list[ZiweiStarPlacement] = Field(default_factory=list)
    transforms: list[ZiweiTransform] = Field(default_factory=list)
    cycles: list[ZiweiCycle] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=lambda: ["ziwei_chart_fact_layer_no_judgment"])

    @model_validator(mode="after")
    def _chart_has_known_palaces(self) -> "ZiweiChart":
        unknown = [row.palace_key for row in self.palaces if row.palace_key not in TWELVE_PALACES]
        if unknown:
            raise ValueError(f"unknown ziwei palaces: {unknown}")
        return self


class ZiweiDomainRule(V30Model):
    version: str = ZIWEI_SIGNAL_LAYER_VERSION
    rule_id: str
    domain: ZiweiDomainKey
    condition: str
    palace_refs: list[ZiweiPalaceKey] = Field(default_factory=list)
    star_refs: list[str] = Field(default_factory=list)
    transform_refs: list[ZiweiTransformKey] = Field(default_factory=list)
    related_palaces: list[ZiweiPalaceKey] = Field(default_factory=list)
    claim: str
    claim_key: str
    probe_trigger: str
    polarity: SignalPolarity = SignalPolarity.SUPPORT
    strength_hint: float = Field(default=0.55, ge=0.0, le=1.0)
    confidence_hint: float = Field(default=0.55, ge=0.0, le=1.0)
    assertion_level_hint: AssertionLevelHint = AssertionLevelHint.WEAK_CANDIDATE
    target_hidden_attributes: list[str] = Field(default_factory=list)
    decision_weight: float = Field(default=ZIWEI_DECISION_WEIGHT_V1, ge=0.0, le=1.0)
    boundary: str = "ziwei_domain_rule_is_auxiliary_signal_not_final_verdict"

    @model_validator(mode="after")
    def _rule_is_observation_only(self) -> "ZiweiDomainRule":
        if self.decision_weight != 0:
            raise ValueError("Ziwei V1 domain rules must keep decision_weight=0")
        if not self.probe_trigger.strip():
            raise ValueError("ZiweiDomainRule requires probe_trigger")
        return self


class ZiweiSignal(V30Model):
    version: str = ZIWEI_SIGNAL_LAYER_VERSION
    signal_id: str
    reading_id: str
    rule_id: str
    source_ref: str
    domain: ZiweiDomainKey
    claim: str
    claim_key: str
    palace_refs: list[ZiweiPalaceKey] = Field(default_factory=list)
    star_refs: list[str] = Field(default_factory=list)
    transform_refs: list[ZiweiTransformKey] = Field(default_factory=list)
    related_palaces: list[ZiweiPalaceKey] = Field(default_factory=list)
    polarity: SignalPolarity = SignalPolarity.SUPPORT
    strength: float = Field(default=0.55, ge=0.0, le=1.0)
    confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    assertion_level_hint: AssertionLevelHint = AssertionLevelHint.WEAK_CANDIDATE
    probe_trigger: str = ""
    target_hidden_attributes: list[str] = Field(default_factory=list)
    manifestation_status: ZiweiSignalManifestation = "unknown"
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["practitioner", "admin", "analyst", "lab"])
    decision_weight: float = Field(default=ZIWEI_DECISION_WEIGHT_V1, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    boundary: str = "ziwei_signal_observation_only_decision_weight_zero"

    @model_validator(mode="after")
    def _signal_is_observation_only(self) -> "ZiweiSignal":
        if self.decision_weight != 0:
            raise ValueError("Ziwei V1 signals must keep decision_weight=0")
        if "user" in self.role_visibility:
            raise ValueError("Ziwei V1 raw signals must not be user-visible by default")
        if not self.evidence_refs:
            raise ValueError("ZiweiSignal requires evidence_refs")
        return self


class ZiweiProbeMapping(V30Model):
    version: str = "v30.ziwei_probe_mapping.v1"
    claim_key: str
    domain: ZiweiDomainKey
    probe_trigger: str
    question_slot_key: str
    answer_signal_key: str
    hidden_attribute_keys: list[str] = Field(default_factory=list)
    user_surface_policy: str = "one_line_auxiliary_hint_only"
    practitioner_surface_policy: str = "show_signal_table_and_conflict_actions"
    boundary: str = "ziwei_probe_mapping_triggers_questions_without_final_verdict_authority"
