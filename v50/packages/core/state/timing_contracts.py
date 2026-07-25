from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.state.foundation_contracts import (
    OpportunityField,
    RiskField,
    StateDimension,
    TimingStateSummary,
    UncertaintyProfile,
)


class TimingStrategyBiasValue(str, Enum):
    ADVANCE = "advance"
    HOLD = "hold"
    ACCUMULATE = "accumulate"
    REDUCE_RISK = "reduce_risk"
    WAIT = "wait"
    UNKNOWN = "unknown"


class TimingLayerEffect(V50Model):
    version: str = "v50.timing_layer_effect.v1"
    layer: str
    stem: str = ""
    branch: str = ""
    model_candidate_ref: str
    effect_summary: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "TimingLayerEffect":
        require_non_empty(self.layer, "timing_layer_effect layer")
        require_non_empty(self.model_candidate_ref, "timing_layer_effect model_candidate_ref")
        require_non_empty(self.effect_summary, "timing_layer_effect effect_summary")
        require_refs(self.evidence_refs, "timing_layer_effect evidence_refs")
        return self


class TimingStateDimensionDelta(V50Model):
    version: str = "v50.timing_state_dimension_delta.v1"
    delta_id: str
    reading_id: str
    domain: Topic
    dimension_id: str
    dimension_name: str
    before_score: float = Field(ge=0.0, le=1.0)
    after_score: float = Field(ge=0.0, le=1.0)
    delta: float = Field(ge=-1.0, le=1.0)
    activated_by: list[str] = Field(default_factory=list)
    weakened_by: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile

    @model_validator(mode="after")
    def _boundary(self) -> "TimingStateDimensionDelta":
        require_non_empty(self.delta_id, "delta_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.dimension_id, "dimension_id")
        require_non_empty(self.dimension_name, "dimension_name")
        if self.delta > 0 and not self.activated_by:
            raise ValueError("positive timing delta requires activated_by")
        if self.delta < 0 and not self.weakened_by:
            raise ValueError("negative timing delta requires weakened_by")
        require_refs(self.evidence_refs, "timing_state_dimension_delta evidence_refs")
        return self


class TimingActivatedPath(V50Model):
    version: str = "v50.timing_activated_path.v1"
    path_ref: str
    activation_reason: str
    timing_layer: str
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "TimingActivatedPath":
        require_non_empty(self.path_ref, "path_ref")
        require_non_empty(self.activation_reason, "activation_reason")
        require_non_empty(self.timing_layer, "timing_layer")
        require_refs(self.evidence_refs, "timing_activated_path evidence_refs")
        return self


class TimingWindow(V50Model):
    version: str = "v50.timing_window.v1"
    window_id: str
    reading_id: str
    domain: Topic
    timing_label: str
    window_type: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile

    @model_validator(mode="after")
    def _boundary(self) -> "TimingWindow":
        require_non_empty(self.window_id, "window_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.timing_label, "timing_label")
        require_non_empty(self.window_type, "window_type")
        require_refs(self.evidence_refs, "timing_window evidence_refs")
        return self


class TimingStrategyBias(V50Model):
    version: str = "v50.timing_strategy_bias.v1"
    value: TimingStrategyBiasValue = TimingStrategyBiasValue.UNKNOWN
    reason: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "TimingStrategyBias":
        require_non_empty(self.reason, "timing_strategy_bias reason")
        if self.value != TimingStrategyBiasValue.UNKNOWN:
            require_refs(self.evidence_refs, "timing_strategy_bias evidence_refs")
        return self


class TimingStateEvolution(V50Model):
    version: str = "v50.timing_state_evolution.v1"
    evolution_id: str
    reading_id: str
    domain: Topic
    domain_supported: bool = True
    domain_gap: bool = False
    luck: TimingLayerEffect | None = None
    year: TimingLayerEffect | None = None
    month: TimingLayerEffect | None = None
    activated_state_dimensions: list[TimingStateDimensionDelta] = Field(default_factory=list)
    weakened_state_dimensions: list[TimingStateDimensionDelta] = Field(default_factory=list)
    activated_paths: list[TimingActivatedPath] = Field(default_factory=list)
    risk_windows: list[TimingWindow] = Field(default_factory=list)
    opportunity_windows: list[TimingWindow] = Field(default_factory=list)
    strategy_bias: TimingStrategyBias
    unsupported_domains: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_natal_structure: bool = False
    boundary: str = "timing_state_evolution_shifts_state_without_event_prediction"

    @model_validator(mode="after")
    def _boundary(self) -> "TimingStateEvolution":
        require_non_empty(self.evolution_id, "evolution_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("TimingStateEvolution requires a concrete or supported general domain")
        if not self.domain_supported and not self.domain_gap:
            raise ValueError("unsupported TimingStateEvolution must set domain_gap")
        if not self.domain_supported:
            if self.activated_state_dimensions or self.weakened_state_dimensions or self.risk_windows or self.opportunity_windows:
                raise ValueError("unsupported TimingStateEvolution cannot create timing effects")
        require_refs(self.evidence_refs, "timing_state_evolution evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "timing_state_evolution theory_refs")
        if self.creates_judgment:
            raise ValueError("TimingStateEvolution cannot create judgment")
        if self.calls_brain:
            raise ValueError("TimingStateEvolution cannot call Brain")
        if self.calls_llm:
            raise ValueError("TimingStateEvolution cannot call LLM")
        if self.mutates_natal_structure:
            raise ValueError("TimingStateEvolution cannot mutate natal structure")
        return self


class DomainStateEnrichment(V50Model):
    version: str = "v50.domain_state_enrichment.v1"
    enrichment_id: str
    reading_id: str
    domain: Topic
    domain_supported: bool = True
    domain_gap: bool = False
    state_dimensions: list[StateDimension] = Field(default_factory=list)
    risk_field: RiskField | None = None
    opportunity_field: OpportunityField | None = None
    timing_state_summary: TimingStateSummary | None = None
    uncertainty_profile: UncertaintyProfile
    missing_state_dimensions: list[str] = Field(default_factory=list)
    unsupported_reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "domain_state_enrichment_is_semantic_projection_of_existing_runtime_evidence"

    @model_validator(mode="after")
    def _boundary(self) -> "DomainStateEnrichment":
        require_non_empty(self.enrichment_id, "enrichment_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("DomainStateEnrichment requires a concrete or supported general domain")
        if not self.domain_supported:
            if not self.domain_gap:
                raise ValueError("unsupported DomainStateEnrichment must set domain_gap")
            if self.state_dimensions:
                raise ValueError("unsupported DomainStateEnrichment cannot create state_dimensions")
        for dimension in self.state_dimensions:
            if dimension.reading_id != self.reading_id:
                raise ValueError("DomainStateEnrichment cannot mix dimension readings")
            if dimension.domain != self.domain:
                raise ValueError("DomainStateEnrichment cannot mix dimension domains")
        for field in [self.risk_field, self.opportunity_field, self.timing_state_summary]:
            if field is not None:
                if field.reading_id != self.reading_id:
                    raise ValueError("DomainStateEnrichment cannot mix field readings")
                if field.domain != self.domain:
                    raise ValueError("DomainStateEnrichment cannot mix field domains")
        require_refs(self.evidence_refs, "domain_state_enrichment evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "domain_state_enrichment theory_refs")
        if self.creates_judgment:
            raise ValueError("DomainStateEnrichment cannot create judgment")
        if self.calls_brain:
            raise ValueError("DomainStateEnrichment cannot call Brain")
        if self.calls_llm:
            raise ValueError("DomainStateEnrichment cannot call LLM")
        return self



