from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from v30.contracts import RoleKey, V30Model
from v30.production.contracts import BaziDomain, BaziSignal, BaziTopic, SignalRegistry


ENGINE_RUNTIME_VERSION = "v30.multi_engine_runtime.v1"


class EngineKey(str, Enum):
    BAZI = "bazi"
    ZIWEI = "ziwei"
    REALITY_PROBE = "reality_probe"


class EngineMode(str, Enum):
    FACT_ONLY = "fact_only"
    SIGNAL_SIDECAR = "signal_sidecar"
    DECISION_AUX = "decision_aux"
    PROBE_TRIGGER = "probe_trigger"
    EXPLANATION_CONTEXT = "explanation_context"


class EngineRunStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class EngineCapability(V30Model):
    version: str = "v30.engine_capability.v1"
    engine: EngineKey
    modes: list[EngineMode] = Field(default_factory=list)
    topics: list[BaziTopic] = Field(default_factory=list)
    domains: list[BaziDomain] = Field(default_factory=list)
    emits_facts: bool = False
    emits_features: bool = False
    emits_signals: bool = False
    emits_probe_candidates: bool = False
    decision_authority: bool = False
    user_verdict_authority: bool = False
    boundary: str = "engine_capability_describes_outputs_not_final_verdict_authority"

    @model_validator(mode="after")
    def _engine_cannot_claim_verdict_authority(self) -> "EngineCapability":
        if self.decision_authority or self.user_verdict_authority:
            raise ValueError("Engine capability cannot claim verdict authority")
        return self


class EnginePlanItem(V30Model):
    version: str = "v30.engine_plan_item.v1"
    engine: EngineKey
    mode: EngineMode
    required: bool = False
    reason: str = ""
    topics: list[BaziTopic] = Field(default_factory=list)
    domains: list[BaziDomain] = Field(default_factory=list)
    decision_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    output_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    boundary: str = "engine_plan_item_schedules_engine_without_granting_verdict_authority"

    @model_validator(mode="after")
    def _planned_engine_has_reason(self) -> "EnginePlanItem":
        if not self.reason.strip():
            raise ValueError("EnginePlanItem requires reason")
        if self.engine == EngineKey.ZIWEI and self.decision_weight != 0:
            raise ValueError("ZiweiEngine V1 decision_weight must be 0")
        return self


class EnginePlan(V30Model):
    version: str = "v30.engine_plan.v1"
    plan_id: str
    reading_id: str
    role: RoleKey = "user"
    user_question: str = ""
    topic: BaziTopic = BaziTopic.UNKNOWN
    domain: BaziDomain = BaziDomain.UNKNOWN
    time_scope: str = "natal"
    items: list[EnginePlanItem] = Field(default_factory=list)
    decision_policy: dict[str, float] = Field(default_factory=dict)
    central_brain_verdict_authority: bool = False
    boundary: str = "central_brain_generates_engine_plan_not_verdict"

    @model_validator(mode="after")
    def _plan_has_primary_engine_and_no_brain_verdict_authority(self) -> "EnginePlan":
        if not self.plan_id.strip():
            raise ValueError("EnginePlan requires plan_id")
        if not self.items:
            raise ValueError("EnginePlan requires items")
        if not any(item.engine == EngineKey.BAZI for item in self.items):
            raise ValueError("EnginePlan requires BaziEngine as primary engine")
        if self.central_brain_verdict_authority:
            raise ValueError("CentralBrain cannot claim verdict authority")
        if self.decision_policy.get("ziwei", 0.0) != 0.0:
            raise ValueError("ZiweiEngine V1 decision policy weight must be 0")
        return self


class EngineRunRequest(V30Model):
    version: str = "v30.engine_run_request.v1"
    request_id: str
    reading_id: str
    engine: EngineKey
    mode: EngineMode
    topic: BaziTopic = BaziTopic.UNKNOWN
    domain: BaziDomain = BaziDomain.UNKNOWN
    user_question: str = ""
    birth_input_ref: str = ""
    chart_context_ref: str = ""
    role: RoleKey = "user"
    policy_version: str = ENGINE_RUNTIME_VERSION
    engine_context: dict[str, Any] = Field(default_factory=dict)
    boundary: str = "engine_run_request_invokes_engine_without_verdict_authority"


class EngineRunResult(V30Model):
    version: str = "v30.engine_run_result.v1"
    result_id: str
    reading_id: str
    engine: EngineKey
    mode: EngineMode
    status: EngineRunStatus = EngineRunStatus.READY
    engine_version: str
    standard_version: str = ""
    facts: list[dict[str, Any]] = Field(default_factory=list)
    features: list[dict[str, Any]] = Field(default_factory=list)
    signals: list[BaziSignal] = Field(default_factory=list)
    probe_candidates: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    decision_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_authority: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "engine_run_result_outputs_material_not_final_verdict"

    @model_validator(mode="after")
    def _engine_result_cannot_decide(self) -> "EngineRunResult":
        if self.verdict_authority:
            raise ValueError("EngineRunResult cannot have verdict authority")
        if self.chart_fact_mutation_allowed:
            raise ValueError("EngineRunResult cannot mutate chart facts")
        if self.engine == EngineKey.ZIWEI and self.decision_weight != 0:
            raise ValueError("ZiweiEngine V1 decision_weight must be 0")
        return self


class EngineAuditEntry(V30Model):
    version: str = "v30.engine_audit_entry.v1"
    engine: EngineKey
    mode: EngineMode
    status: EngineRunStatus
    fact_count: int = Field(default=0, ge=0)
    feature_count: int = Field(default=0, ge=0)
    signal_count: int = Field(default=0, ge=0)
    registered_signal_count: int = Field(default=0, ge=0)
    probe_candidate_count: int = Field(default=0, ge=0)
    verdict_consumed_count: int = Field(default=0, ge=0)
    advice_consumed_count: int = Field(default=0, ge=0)
    ui_consumed_count: int = Field(default=0, ge=0)
    signal_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    boundary: str = "engine_audit_observes_outputs_without_runtime_mutation"


class MultiEngineRunResult(V30Model):
    version: str = ENGINE_RUNTIME_VERSION
    reading_id: str
    plan: EnginePlan
    results: list[EngineRunResult] = Field(default_factory=list)
    signal_registry: SignalRegistry
    audit: list[EngineAuditEntry] = Field(default_factory=list)
    decision_engine_mutated: bool = False
    verdict_mutated: bool = False
    final_synthesis_mutated: bool = False
    boundary: str = "multi_engine_runtime_is_sidecar_before_decision_engine_integration"

    @model_validator(mode="after")
    def _multi_engine_sidecar_does_not_mutate_decision(self) -> "MultiEngineRunResult":
        if self.decision_engine_mutated or self.verdict_mutated or self.final_synthesis_mutated:
            raise ValueError("MultiEngineRunResult V1 cannot mutate decision/verdict/final synthesis")
        if self.plan.reading_id != self.reading_id:
            raise ValueError("MultiEngineRunResult reading id must match plan")
        return self
