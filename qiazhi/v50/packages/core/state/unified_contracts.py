from __future__ import annotations

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.state.foundation_contracts import (
    OpportunityField,
    RiskField,
    StateDimension,
    StateProducerType,
    TimingStateSummary,
    UncertaintyProfile,
    _validate_score_map,
)
from core.state.producer_contracts import (
    FlowState,
    PalaceStateSpace,
    RealityState,
    StateEvolution,
    TemporalState,
    UnifiedTheme,
)


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

