from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from core.contracts.base import Topic, V50Model, require_non_empty, require_refs
from core.state.foundation_contracts import UncertaintyProfile


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



