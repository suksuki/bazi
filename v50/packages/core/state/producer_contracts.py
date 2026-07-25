from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.state.foundation_contracts import (
    StateProducerType,
    StateTrendDirection,
    _validate_delta_map,
    _validate_score_map,
)


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



