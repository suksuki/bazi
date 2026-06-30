from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import AssertionLevel, Polarity, RoleKey, Topic, V40Model


class SignalSource(str, Enum):
    BAZI_ENGINE = "bazi_engine"
    ZIWEI_ENGINE = "ziwei_engine"
    REALITY_PROBE = "reality_probe"
    PRACTITIONER_FEEDBACK = "practitioner_feedback"
    USER_FEEDBACK = "user_feedback"
    GOLDEN_CASE = "golden_case"
    TRAINING_OVERLAY = "training_overlay"
    LLM_HYPOTHESIS = "llm_hypothesis"


class RuntimeSignal(V40Model):
    version: str = "v40.runtime_signal.v1"
    signal_id: str
    reading_id: str
    source: SignalSource
    source_ref: str = ""
    topic: Topic = Topic.UNKNOWN
    claim: str
    claim_key: str = ""
    polarity: Polarity = Polarity.NEUTRAL
    strength: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    assertion_hint: AssertionLevel = AssertionLevel.WEAK_CANDIDATE
    evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    branch_group_id: str = ""
    role_visibility: list[RoleKey] = Field(default_factory=lambda: ["user", "practitioner", "admin"])
    trainable_targets: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    decision_authority: bool = False
    boundary: str = "runtime_signal_is_material_for_decision_not_verdict_authority"

    @model_validator(mode="after")
    def _signal_boundary(self) -> "RuntimeSignal":
        if not self.signal_id.strip():
            raise ValueError("RuntimeSignal requires signal_id")
        if not self.reading_id.strip():
            raise ValueError("RuntimeSignal requires reading_id")
        if not self.claim.strip():
            raise ValueError("RuntimeSignal requires claim")
        if not self.role_visibility:
            raise ValueError("RuntimeSignal requires role_visibility")
        if self.chart_fact_mutation_allowed:
            raise ValueError("RuntimeSignal cannot mutate chart facts")
        if self.decision_authority:
            raise ValueError("RuntimeSignal cannot have decision authority")
        return self


class SignalRegistrySnapshot(V40Model):
    version: str = "v40.signal_registry_snapshot.v1"
    registry_id: str
    reading_id: str
    signals: list[RuntimeSignal] = Field(default_factory=list)
    validation_issues: list[str] = Field(default_factory=list)
    decision_engine_mutated: bool = False
    boundary: str = "signal_registry_snapshot_collects_signals_without_replacing_decision_engine"

    @model_validator(mode="after")
    def _registry_boundary(self) -> "SignalRegistrySnapshot":
        if not self.registry_id.strip():
            raise ValueError("SignalRegistrySnapshot requires registry_id")
        if self.decision_engine_mutated:
            raise ValueError("SignalRegistrySnapshot cannot mutate DecisionEngine")
        return self

    def by_topic(self, topic: Topic) -> list[RuntimeSignal]:
        return [signal for signal in self.signals if signal.topic == topic]

    def by_role(self, role_key: RoleKey) -> list[RuntimeSignal]:
        return [signal for signal in self.signals if role_key in signal.role_visibility]
