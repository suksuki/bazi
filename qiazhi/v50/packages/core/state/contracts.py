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


class FlowState(V50Model):
    version: str = "v50.flow_state.v1"
    state_id: str
    reading_id: str
    source: StateProducerType = StateProducerType.BAZI_FLOW
    mechanism: str
    path_refs: list[str] = Field(default_factory=list)
    node_refs: list[str] = Field(default_factory=list)
    mechanism_refs: list[str] = Field(default_factory=list)
    output_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    path_score: float = Field(default=0.0, ge=0.0, le=1.0)
    ablation_sensitivity: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "flow_state_is_bazi_computational_state_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "FlowState":
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.mechanism, "mechanism")
        require_refs(self.path_refs, "path_refs")
        require_refs(self.node_refs, "node_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.source != StateProducerType.BAZI_FLOW:
            raise ValueError("FlowState source must be bazi_flow")
        if self.creates_judgment:
            raise ValueError("FlowState cannot create judgment")
        if self.calls_brain:
            raise ValueError("FlowState cannot call Brain")
        if self.calls_llm:
            raise ValueError("FlowState cannot call LLM")
        return self


class PalaceStateSpace(V50Model):
    version: str = "v50.palace_state_space.v1"
    state_id: str
    reading_id: str
    source: StateProducerType = StateProducerType.ZIWEI_PALACE
    palace: str
    domain: Topic
    dimensions: dict[str, float] = Field(default_factory=dict)
    behavior_modifier_refs: list[str] = Field(default_factory=list)
    transformation_refs: list[str] = Field(default_factory=list)
    palace_refs: list[str] = Field(default_factory=list)
    theme_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "palace_state_space_is_ziwei_state_vector_not_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "PalaceStateSpace":
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.palace, "palace")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("PalaceStateSpace requires a concrete life domain")
        if self.source != StateProducerType.ZIWEI_PALACE:
            raise ValueError("PalaceStateSpace source must be ziwei_palace")
        if not self.dimensions:
            raise ValueError("PalaceStateSpace requires dimensions")
        _validate_score_map(self.dimensions, "dimensions")
        require_refs(self.palace_refs, "palace_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.creates_judgment:
            raise ValueError("PalaceStateSpace cannot create judgment")
        if self.calls_brain:
            raise ValueError("PalaceStateSpace cannot call Brain")
        if self.calls_llm:
            raise ValueError("PalaceStateSpace cannot call LLM")
        return self


class RealityState(V50Model):
    version: str = "v50.reality_state.v1"
    state_id: str
    reading_id: str
    source: StateProducerType = StateProducerType.CONTEXT_REALITY
    domain: Topic
    geography: dict[str, Any] = Field(default_factory=dict)
    profession: dict[str, Any] = Field(default_factory=dict)
    family: dict[str, Any] = Field(default_factory=dict)
    event_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_birth_input: bool = False
    boundary: str = "reality_state_contextualizes_domain_without_mutating_mingli_facts"

    @model_validator(mode="after")
    def _boundary(self) -> "RealityState":
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("RealityState requires a concrete life domain")
        if self.source != StateProducerType.CONTEXT_REALITY:
            raise ValueError("RealityState source must be context_reality")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.creates_judgment:
            raise ValueError("RealityState cannot create judgment")
        if self.calls_brain:
            raise ValueError("RealityState cannot call Brain")
        if self.calls_llm:
            raise ValueError("RealityState cannot call LLM")
        if self.mutates_birth_input:
            raise ValueError("RealityState cannot mutate birth input")
        return self


class TemporalState(V50Model):
    version: str = "v50.temporal_state.v1"
    state_id: str
    reading_id: str
    source: StateProducerType = StateProducerType.TIMING_TEMPORAL
    timing_layer: str
    activated_paths: list[str] = Field(default_factory=list)
    weakened_nodes: list[str] = Field(default_factory=list)
    rerouted_flows: list[str] = Field(default_factory=list)
    mechanism_shifts: dict[str, float] = Field(default_factory=dict)
    state_delta_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_natal_structure: bool = False
    boundary: str = "temporal_state_is_timing_overlay_not_natal_rewrite"

    @model_validator(mode="after")
    def _boundary(self) -> "TemporalState":
        require_non_empty(self.state_id, "state_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.timing_layer, "timing_layer")
        if self.source != StateProducerType.TIMING_TEMPORAL:
            raise ValueError("TemporalState source must be timing_temporal")
        require_refs(self.evidence_refs, "evidence_refs")
        _validate_score_map(self.mechanism_shifts, "mechanism_shifts")
        if self.creates_judgment:
            raise ValueError("TemporalState cannot create judgment")
        if self.calls_brain:
            raise ValueError("TemporalState cannot call Brain")
        if self.calls_llm:
            raise ValueError("TemporalState cannot call LLM")
        if self.mutates_natal_structure:
            raise ValueError("TemporalState cannot mutate natal structure")
        return self


class StateEvolution(V50Model):
    version: str = "v50.state_evolution.v1"
    evolution_id: str
    reading_id: str
    domain: Topic
    current_state_refs: list[str] = Field(default_factory=list)
    previous_state_refs: list[str] = Field(default_factory=list)
    delta_by_dimension: dict[str, float] = Field(default_factory=dict)
    trend: StateTrendDirection = StateTrendDirection.UNKNOWN
    velocity: float = Field(default=0.0, ge=0.0, le=1.0)
    activated_by: list[str] = Field(default_factory=list)
    suppressed_by: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "state_evolution_describes_change_without_deciding_outcome"

    @model_validator(mode="after")
    def _boundary(self) -> "StateEvolution":
        require_non_empty(self.evolution_id, "evolution_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("StateEvolution requires a concrete life domain")
        require_refs(self.current_state_refs, "current_state_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        _validate_delta_map(self.delta_by_dimension, "delta_by_dimension")
        if self.creates_judgment:
            raise ValueError("StateEvolution cannot create judgment")
        if self.calls_brain:
            raise ValueError("StateEvolution cannot call Brain")
        if self.calls_llm:
            raise ValueError("StateEvolution cannot call LLM")
        return self


class UnifiedTheme(V50Model):
    version: str = "v50.unified_theme.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_code: str
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    producer_refs: list[str] = Field(default_factory=list)
    state_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "unified_theme_is_cross_producer_pattern_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedTheme":
        require_non_empty(self.theme_id, "theme_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.theme_code, "theme_code")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("UnifiedTheme requires a concrete life domain")
        require_refs(self.producer_refs, "producer_refs")
        require_refs(self.state_refs, "state_refs")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.creates_judgment:
            raise ValueError("UnifiedTheme cannot create judgment")
        if self.calls_brain:
            raise ValueError("UnifiedTheme cannot call Brain")
        if self.calls_llm:
            raise ValueError("UnifiedTheme cannot call LLM")
        return self


class ThemeType(str, Enum):
    CREATION = "creation"
    ACCUMULATION = "accumulation"
    PRESSURE_TRANSFORMATION = "pressure_transformation"
    MANAGEMENT = "management"
    MOBILITY = "mobility"
    COMPETITION = "competition"
    STABILITY = "stability"
    RISK_CONTROL = "risk_control"
    RESOURCE_SUPPORT = "resource_support"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ThemeStability(str, Enum):
    STABLE = "stable"
    TIMING_SENSITIVE = "timing_sensitive"
    UNSTABLE = "unstable"
    UNKNOWN = "unknown"


class ThemeSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ThemeCompleteness(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    WEAK = "weak"
    UNKNOWN = "unknown"


class ThemeActivationSource(str, Enum):
    LUCK = "luck"
    YEAR = "year"
    MONTH = "month"
    TIMING_STATE = "timing_state"
    STATE_DELTA = "state_delta"
    UNKNOWN = "unknown"


class ThemeTransitionType(str, Enum):
    STABLE = "stable"
    TIMING_ACTIVATED = "timing_activated"
    RISK_SHIFT = "risk_shift"
    OPPORTUNITY_SHIFT = "opportunity_shift"
    CONFLICT_SHIFT = "conflict_shift"
    UNKNOWN = "unknown"


class ThemeCandidate(V50Model):
    version: str = "v50.theme_candidate.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_name: str
    theme_type: ThemeType = ThemeType.UNKNOWN
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    stability: ThemeStability = ThemeStability.UNKNOWN
    timing_sensitivity: ThemeSensitivity = ThemeSensitivity.MEDIUM
    active_now: bool | None = None
    opportunity_link: list[str] = Field(default_factory=list)
    risk_link: list[str] = Field(default_factory=list)
    strategy_link: str = "unknown"
    source_mechanism_refs: list[str] = Field(default_factory=list)
    source_state_dimension_refs: list[str] = Field(default_factory=list)
    source_timing_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    counter_theme: str = ""
    uncertainty: UncertaintyProfile
    completeness: ThemeCompleteness = ThemeCompleteness.UNKNOWN
    label_is_presentation_only: bool = True
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "theme_candidate_is_structural_life_theme_not_judgment_or_copy"

    @model_validator(mode="after")
    def _boundary(self) -> "ThemeCandidate":
        require_non_empty(self.theme_id, "theme_id")
        require_non_empty(self.reading_id, "reading_id")
        require_non_empty(self.theme_name, "theme_name")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("ThemeCandidate requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            require_refs(self.source_mechanism_refs, "theme_candidate source_mechanism_refs")
            require_refs(self.source_state_dimension_refs, "theme_candidate source_state_dimension_refs")
            require_refs(self.evidence_refs, "theme_candidate evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "theme_candidate theory_refs")
        if not self.label_is_presentation_only:
            raise ValueError("ThemeCandidate label must remain presentation-only")
        if self.creates_judgment:
            raise ValueError("ThemeCandidate cannot create judgment")
        if self.calls_brain:
            raise ValueError("ThemeCandidate cannot call Brain")
        if self.calls_llm:
            raise ValueError("ThemeCandidate cannot call LLM")
        return self


class BaseTheme(V50Model):
    version: str = "v50.base_theme.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_type: ThemeType = ThemeType.UNKNOWN
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    stability: ThemeStability = ThemeStability.UNKNOWN
    source_mechanism_refs: list[str] = Field(default_factory=list)
    source_state_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    timing_can_mutate: bool = False
    boundary: str = "base_theme_is_natal_structural_theme_and_cannot_be_rewritten_by_timing"

    @model_validator(mode="after")
    def _boundary(self) -> "BaseTheme":
        require_non_empty(self.theme_id, "base_theme theme_id")
        require_non_empty(self.reading_id, "base_theme reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("BaseTheme requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            require_refs(self.source_mechanism_refs, "base_theme source_mechanism_refs")
            require_refs(self.source_state_refs, "base_theme source_state_refs")
            require_refs(self.evidence_refs, "base_theme evidence_refs")
        if self.timing_can_mutate:
            raise ValueError("Timing cannot mutate BaseTheme")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("BaseTheme cannot create judgment or call Brain/LLM")
        return self


class ActiveTheme(V50Model):
    version: str = "v50.active_theme.v1"
    theme_id: str
    reading_id: str
    domain: Topic
    theme_type: ThemeType = ThemeType.UNKNOWN
    activation_source: ThemeActivationSource = ThemeActivationSource.UNKNOWN
    activation_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    active_now: bool = False
    opportunity_link: list[str] = Field(default_factory=list)
    risk_link: list[str] = Field(default_factory=list)
    strategy_link: str = "unknown"
    source_timing_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    mutates_base_theme: bool = False
    boundary: str = "active_theme_is_timing_activation_and_cannot_rewrite_base_theme"

    @model_validator(mode="after")
    def _boundary(self) -> "ActiveTheme":
        require_non_empty(self.theme_id, "active_theme theme_id")
        require_non_empty(self.reading_id, "active_theme reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("ActiveTheme requires a concrete or supported general domain")
        if self.theme_type != ThemeType.UNKNOWN:
            if self.activation_source == ThemeActivationSource.UNKNOWN:
                raise ValueError("concrete ActiveTheme requires activation_source")
            require_refs(self.source_timing_refs, "active_theme source_timing_refs")
            require_refs(self.evidence_refs, "active_theme evidence_refs")
        if self.mutates_base_theme:
            raise ValueError("ActiveTheme cannot mutate BaseTheme")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("ActiveTheme cannot create judgment or call Brain/LLM")
        return self


class ThemeTransition(V50Model):
    version: str = "v50.theme_transition.v1"
    transition_id: str
    reading_id: str
    domain: Topic
    base_theme: BaseTheme
    active_theme: ActiveTheme
    transition_type: ThemeTransitionType = ThemeTransitionType.UNKNOWN
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)
    timing_changed_base_theme: bool = False
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "theme_transition_explains_timing_activation_without_rewriting_natal_theme"

    @model_validator(mode="after")
    def _boundary(self) -> "ThemeTransition":
        require_non_empty(self.transition_id, "theme_transition transition_id")
        require_non_empty(self.reading_id, "theme_transition reading_id")
        require_non_empty(self.reason, "theme_transition reason")
        if self.base_theme.reading_id != self.reading_id or self.active_theme.reading_id != self.reading_id:
            raise ValueError("ThemeTransition cannot mix readings")
        if self.base_theme.domain != self.domain or self.active_theme.domain != self.domain:
            raise ValueError("ThemeTransition cannot mix domains")
        if self.timing_changed_base_theme:
            raise ValueError("ThemeTransition cannot change BaseTheme")
        require_refs(self.evidence_refs, "theme_transition evidence_refs")
        if self.creates_judgment or self.calls_brain or self.calls_llm:
            raise ValueError("ThemeTransition cannot create judgment or call Brain/LLM")
        return self


class UnifiedThemeBundle(V50Model):
    version: str = "v50.unified_theme_bundle.v2"
    bundle_id: str
    reading_id: str
    domain: Topic
    domain_supported: bool = True
    domain_gap: bool = False
    base_theme: BaseTheme
    active_theme: ActiveTheme
    theme_transition: ThemeTransition
    primary_theme: ThemeCandidate
    primary_theme_legacy_derived: bool = True
    secondary_themes: list[ThemeCandidate] = Field(default_factory=list)
    counter_themes: list[ThemeCandidate] = Field(default_factory=list)
    theme_conflicts: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    missing_theme_inputs: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "unified_theme_bundle_collects_theme_candidates_without_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedThemeBundle":
        require_non_empty(self.bundle_id, "bundle_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("UnifiedThemeBundle requires a concrete or supported general domain")
        if self.primary_theme.reading_id != self.reading_id or self.primary_theme.domain != self.domain:
            raise ValueError("UnifiedThemeBundle primary_theme must match reading/domain")
        if self.base_theme.reading_id != self.reading_id or self.active_theme.reading_id != self.reading_id:
            raise ValueError("UnifiedThemeBundle base/active themes must match reading")
        if self.base_theme.domain != self.domain or self.active_theme.domain != self.domain:
            raise ValueError("UnifiedThemeBundle base/active themes must match domain")
        if self.theme_transition.reading_id != self.reading_id or self.theme_transition.domain != self.domain:
            raise ValueError("UnifiedThemeBundle transition must match reading/domain")
        if not self.primary_theme_legacy_derived:
            raise ValueError("UnifiedThemeBundle primary_theme must remain legacy/derived")
        for theme in [*self.secondary_themes, *self.counter_themes]:
            if theme.reading_id != self.reading_id or theme.domain != self.domain:
                raise ValueError("UnifiedThemeBundle cannot mix theme readings or domains")
        if not self.domain_supported and not self.domain_gap:
            raise ValueError("unsupported UnifiedThemeBundle must set domain_gap")
        require_refs(self.evidence_refs, "unified_theme_bundle evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "unified_theme_bundle theory_refs")
        if self.creates_judgment:
            raise ValueError("UnifiedThemeBundle cannot create judgment")
        if self.calls_brain:
            raise ValueError("UnifiedThemeBundle cannot call Brain")
        if self.calls_llm:
            raise ValueError("UnifiedThemeBundle cannot call LLM")
        return self


class DecisionConfidenceBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NOT_AVAILABLE = "not_available"


class DecisionStrategySource(str, Enum):
    THEME = "theme"
    TIMING = "timing"
    STATE = "state"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DecisionConfidenceScore(V50Model):
    version: str = "v50.decision_confidence_score.v1"
    value: float = Field(default=0.0, ge=0.0, le=1.0)
    band: DecisionConfidenceBand = DecisionConfidenceBand.LOW
    calibrated: bool = False


class DecisionConfidenceComponent(V50Model):
    version: str = "v50.decision_confidence_component.v1"
    component_id: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    source_theme_refs: list[str] = Field(default_factory=list)
    source_state_refs: list[str] = Field(default_factory=list)
    source_timing_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "DecisionConfidenceComponent":
        require_non_empty(self.component_id, "component_id")
        require_refs(self.reasons, "decision_confidence_component reasons")
        require_refs(self.evidence_refs, "decision_confidence_component evidence_refs")
        return self


class ConfidenceDriver(V50Model):
    version: str = "v50.confidence_driver.v1"
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "ConfidenceDriver":
        require_non_empty(self.reason, "confidence_driver reason")
        require_refs(self.evidence_refs, "confidence_driver evidence_refs")
        return self


class ConfidenceLimiter(V50Model):
    version: str = "v50.confidence_limiter.v1"
    reason: str
    missing_input: str = ""
    uncertainty_ref: str = ""

    @model_validator(mode="after")
    def _boundary(self) -> "ConfidenceLimiter":
        require_non_empty(self.reason, "confidence_limiter reason")
        if not self.missing_input and not self.uncertainty_ref:
            raise ValueError("ConfidenceLimiter requires missing_input or uncertainty_ref")
        return self


class ConfidenceProbeGain(V50Model):
    version: str = "v50.confidence_probe_gain.v1"
    probe_question: str
    reason: str
    expected_information_gain: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _boundary(self) -> "ConfidenceProbeGain":
        require_non_empty(self.probe_question, "confidence_probe_gain probe_question")
        require_non_empty(self.reason, "confidence_probe_gain reason")
        require_refs(self.evidence_refs, "confidence_probe_gain evidence_refs")
        return self


class DecisionConfidenceProfile(V50Model):
    version: str = "v50.decision_confidence_profile.v1"
    profile_id: str
    reading_id: str
    domain: Topic
    domain_supported: bool = True
    domain_gap: bool = False
    decision_context: dict[str, str] = Field(default_factory=dict)
    score: DecisionConfidenceScore
    components: dict[str, DecisionConfidenceComponent] = Field(default_factory=dict)
    confidence_drivers: list[ConfidenceDriver] = Field(default_factory=list)
    confidence_limiters: list[ConfidenceLimiter] = Field(default_factory=list)
    what_would_increase_confidence: list[ConfidenceProbeGain] = Field(default_factory=list)
    must_not_say: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    theory_refs: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    predicts_exact_event: bool = False
    calibrated_by_user_feedback: bool = False
    boundary: str = "decision_confidence_profile_supports_decision_without_new_judgment"

    @model_validator(mode="after")
    def _boundary(self) -> "DecisionConfidenceProfile":
        require_non_empty(self.profile_id, "profile_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("DecisionConfidenceProfile requires a concrete or supported general domain")
        if not self.domain_supported and not self.domain_gap:
            raise ValueError("unsupported DecisionConfidenceProfile must set domain_gap")
        if self.domain_supported:
            require_refs(list(self.components.keys()), "decision_confidence components")
            require_refs(self.confidence_drivers, "decision_confidence confidence_drivers")
        else:
            if self.score.band != DecisionConfidenceBand.NOT_AVAILABLE:
                raise ValueError("unsupported DecisionConfidenceProfile must use not_available band")
        require_refs(self.confidence_limiters, "decision_confidence confidence_limiters")
        require_refs(self.must_not_say, "decision_confidence must_not_say")
        require_refs(self.evidence_refs, "decision_confidence evidence_refs")
        if self.theory_refs:
            require_refs(self.theory_refs, "decision_confidence theory_refs")
        if self.creates_judgment:
            raise ValueError("DecisionConfidenceProfile cannot create judgment")
        if self.calls_brain:
            raise ValueError("DecisionConfidenceProfile cannot call Brain")
        if self.calls_llm:
            raise ValueError("DecisionConfidenceProfile cannot call LLM")
        if self.predicts_exact_event:
            raise ValueError("DecisionConfidenceProfile cannot predict exact events")
        if self.calibrated_by_user_feedback:
            raise ValueError("DecisionConfidenceProfile v1 is not calibrated by user feedback")
        return self


class UnifiedDomainState(V50Model):
    version: str = "v50.unified_domain_state.v1"
    domain_state_id: str
    reading_id: str
    domain: Topic
    flow_state: FlowState | None = None
    palace_state_space: PalaceStateSpace | None = None
    reality_state: RealityState | None = None
    temporal_state: TemporalState | None = None
    state_evolution: StateEvolution | None = None
    unified_theme: UnifiedTheme | None = None
    state_dimensions: list[StateDimension] = Field(default_factory=list)
    risk_field: RiskField | None = None
    opportunity_field: OpportunityField | None = None
    timing_state_summary: TimingStateSummary | None = None
    uncertainty_profile: UncertaintyProfile | None = None
    domain_supported: bool = True
    domain_gap: bool = False
    missing_state_dimensions: list[str] = Field(default_factory=list)
    unsupported_reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: dict[str, float] = Field(default_factory=dict)
    conflict_codes: list[str] = Field(default_factory=list)
    missing_information_codes: list[str] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "unified_domain_state_is_brain_input_not_verdict"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedDomainState":
        require_non_empty(self.domain_state_id, "domain_state_id")
        require_non_empty(self.reading_id, "reading_id")
        if self.domain in {Topic.UNKNOWN, Topic.OVERVIEW, Topic.STRUCTURE}:
            raise ValueError("UnifiedDomainState requires a concrete life domain")
        states = [self.flow_state, self.palace_state_space, self.reality_state, self.temporal_state]
        if not any(states) and self.domain_supported:
            raise ValueError("UnifiedDomainState requires at least one producer state")
        for state in [*states, self.state_evolution, self.unified_theme]:
            if state is not None:
                if state.reading_id != self.reading_id:
                    raise ValueError("UnifiedDomainState cannot mix readings")
                state_domain = getattr(state, "domain", self.domain)
                if state_domain != self.domain:
                    raise ValueError("UnifiedDomainState cannot mix domains")
        for dimension in self.state_dimensions:
            if dimension.reading_id != self.reading_id:
                raise ValueError("UnifiedDomainState cannot mix dimension readings")
            if dimension.domain != self.domain:
                raise ValueError("UnifiedDomainState cannot mix dimension domains")
        for field in [self.risk_field, self.opportunity_field, self.timing_state_summary]:
            if field is not None:
                if field.reading_id != self.reading_id:
                    raise ValueError("UnifiedDomainState cannot mix field readings")
                if field.domain != self.domain:
                    raise ValueError("UnifiedDomainState cannot mix field domains")
        if self.uncertainty_profile is not None and not set(self.uncertainty_profile.evidence_refs).issubset(set(self.evidence_refs)):
            raise ValueError("UnifiedDomainState uncertainty_profile evidence_refs must come from domain evidence_refs")
        if not self.domain_supported and not self.domain_gap:
            raise ValueError("unsupported domain must set domain_gap")
        if self.domain_gap and not self.unsupported_reason and not self.missing_state_dimensions:
            raise ValueError("domain_gap requires unsupported_reason or missing_state_dimensions")
        require_refs(self.evidence_refs, "evidence_refs")
        _validate_score_map(self.confidence, "confidence")
        if self.creates_judgment:
            raise ValueError("UnifiedDomainState cannot create judgment")
        if self.calls_brain:
            raise ValueError("UnifiedDomainState cannot call Brain")
        if self.calls_llm:
            raise ValueError("UnifiedDomainState cannot call LLM")
        return self


class UnifiedStateBundle(V50Model):
    version: str = "v50.unified_state_bundle.v1"
    bundle_id: str
    reading_id: str
    domain_states: list[UnifiedDomainState] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    producer_types: list[StateProducerType] = Field(default_factory=list)
    creates_judgment: bool = False
    calls_brain: bool = False
    calls_llm: bool = False
    boundary: str = "unified_state_bundle_is_common_state_language_for_brain_input"

    @model_validator(mode="after")
    def _boundary(self) -> "UnifiedStateBundle":
        require_non_empty(self.bundle_id, "bundle_id")
        require_non_empty(self.reading_id, "reading_id")
        if not self.domain_states:
            raise ValueError("UnifiedStateBundle requires domain_states")
        if any(state.reading_id != self.reading_id for state in self.domain_states):
            raise ValueError("UnifiedStateBundle cannot mix readings")
        require_refs(self.evidence_refs, "evidence_refs")
        if self.creates_judgment:
            raise ValueError("UnifiedStateBundle cannot create judgment")
        if self.calls_brain:
            raise ValueError("UnifiedStateBundle cannot call Brain")
        if self.calls_llm:
            raise ValueError("UnifiedStateBundle cannot call LLM")
        return self
