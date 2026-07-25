from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs


class StateProducerType(str, Enum):
    BAZI_FLOW = "bazi_flow"
    ZIWEI_PALACE = "ziwei_palace"
    CONTEXT_REALITY = "context_reality"
    TIMING_TEMPORAL = "timing_temporal"
    FUTURE_ENGINE = "future_engine"


class StateTrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class StatePolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class StateDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    UNKNOWN = "unknown"


class UncertaintyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SemanticStateDeltaStatus(str, Enum):
    REAL = "real"
    INFERRED = "inferred"
    MISSING = "missing"


def _validate_score_map(values: dict[str, float], field_name: str) -> None:
    for key, value in values.items():
        require_non_empty(str(key), f"{field_name} key")
        if value < 0.0 or value > 1.0:
            raise ValueError(f"{field_name} values must be between 0 and 1")


def _validate_delta_map(values: dict[str, float], field_name: str) -> None:
    for key, value in values.items():
        require_non_empty(str(key), f"{field_name} key")
        if value < -1.0 or value > 1.0:
            raise ValueError(f"{field_name} values must be between -1 and 1")


class UncertaintyProfile(V50Model):
    version: str = "v50.uncertainty_profile.v1"
    level: UncertaintyLevel = UncertaintyLevel.MEDIUM
    reasons: list[str] = Field(default_factory=list)
    missing_dimensions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "UncertaintyProfile":
        if not self.reasons and not self.missing_dimensions:
            raise ValueError("UncertaintyProfile requires reasons or missing_dimensions")
        require_refs(self.evidence_refs, "uncertainty_profile evidence_refs")
        return self


class StateDimension(V50Model):
    version: str = "v50.state_dimension.v1"
    dimension_id: str
    reading_id: str
    domain: Topic
    name: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    polarity: StatePolarity = StatePolarity.NEUTRAL
    direction: StateDirection = StateDirection.UNKNOWN
    source_mechanism_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    state_delta_status: SemanticStateDeltaStatus = SemanticStateDeltaStatus.MISSING
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "state_dimension_expresses_existing_semantics_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "StateDimension":
        require_non_empty(self.dimension_id, "dimension_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.name, "name")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("StateDimension requires a concrete or supported general domain")
        require_refs(self.source_mechanism_refs, "state_dimension source_mechanism_refs")
        require_refs(self.evidence_refs, "state_dimension evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "state_dimension theory_refs")
        if self.creates_judgment:
            raise ValueError("StateDimension cannot create judgment")
        if self.calls_brain:
            raise ValueError("StateDimension cannot call Brain")
        if self.calls_llm:
            raise ValueError("StateDimension cannot call LLM")
        return self


class RiskField(V50Model):
    version: str = "v50.risk_field.v1"
    field_id: str
    reading_id: str
    domain: Topic
    dimension_refs: list[str] = Field(default_factory=list)
    risk_codes: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "RiskField":
        require_non_empty(self.field_id, "field_id")
        require_non_empty(self.reading_id, "reading_id")
        require_refs(self.dimension_refs, "risk_field dimension_refs")
        require_refs(self.risk_codes, "risk_field risk_codes")
        require_refs(self.evidence_refs, "risk_field evidence_refs")
        return self


class OpportunityField(V50Model):
    version: str = "v50.opportunity_field.v1"
    field_id: str
    reading_id: str
    domain: Topic
    dimension_refs: list[str] = Field(default_factory=list)
    opportunity_codes: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "OpportunityField":
        require_non_empty(self.field_id, "field_id")
        require_non_empty(self.reading_id, "reading_id")
        require_refs(self.dimension_refs, "opportunity_field dimension_refs")
        require_refs(self.opportunity_codes, "opportunity_field opportunity_codes")
        require_refs(self.evidence_refs, "opportunity_field evidence_refs")
        return self


class TimingStateSummary(V50Model):
    version: str = "v50.timing_state_summary.v1"
    summary_id: str
    reading_id: str
    domain: Topic
    activated_by: list[str] = Field(default_factory=list)
    state_delta_status: SemanticStateDeltaStatus = SemanticStateDeltaStatus.MISSING
    direction: StateDirection = StateDirection.UNKNOWN
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "TimingStateSummary":
        require_non_empty(self.summary_id, "summary_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.state_delta_status == SemanticStateDeltaStatus.MISSING:
            raise ValueError("TimingStateSummary cannot be created from missing state delta")
        require_refs(self.activated_by, "timing_state_summary activated_by")
        require_refs(self.evidence_refs, "timing_state_summary evidence_refs")
        return self



