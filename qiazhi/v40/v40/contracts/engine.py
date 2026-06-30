from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from v40.contracts.base import EngineKey, EngineMode, RoleKey, Topic, V40Model
from v40.contracts.signal import RuntimeSignal, SignalRegistrySnapshot


class EngineRunStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class EnginePlanItem(V40Model):
    version: str = "v40.engine_plan_item.v1"
    engine: EngineKey
    mode: EngineMode
    required: bool = False
    reason: str
    topics: list[Topic] = Field(default_factory=list)
    decision_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    output_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    boundary: str = "engine_plan_item_schedules_engine_without_granting_verdict_authority"

    @model_validator(mode="after")
    def _plan_item_boundary(self) -> "EnginePlanItem":
        if not self.reason.strip():
            raise ValueError("EnginePlanItem requires reason")
        if self.engine == EngineKey.ZIWEI and self.decision_weight != 0.0:
            raise ValueError("ZiweiEngine V1 decision_weight must be 0")
        return self


class EnginePlan(V40Model):
    version: str = "v40.engine_plan.v1"
    plan_id: str
    reading_id: str
    role_key: RoleKey = "user"
    user_question: str = ""
    topic: Topic = Topic.UNKNOWN
    items: list[EnginePlanItem] = Field(default_factory=list)
    central_brain_verdict_authority: bool = False
    boundary: str = "central_brain_generates_engine_plan_not_verdict"

    @model_validator(mode="after")
    def _plan_boundary(self) -> "EnginePlan":
        if not self.plan_id.strip():
            raise ValueError("EnginePlan requires plan_id")
        if not self.items:
            raise ValueError("EnginePlan requires items")
        if not any(item.engine == EngineKey.BAZI for item in self.items):
            raise ValueError("EnginePlan requires BaziEngine as primary engine")
        if self.central_brain_verdict_authority:
            raise ValueError("CentralBrain cannot claim verdict authority")
        return self


class EngineRunRequest(V40Model):
    version: str = "v40.engine_run_request.v1"
    request_id: str
    reading_id: str
    engine: EngineKey
    mode: EngineMode
    topic: Topic = Topic.UNKNOWN
    role_key: RoleKey = "user"
    user_question: str = ""
    input_refs: list[str] = Field(default_factory=list)
    engine_context: dict[str, object] = Field(default_factory=dict)
    boundary: str = "engine_run_request_invokes_engine_without_verdict_authority"


class EngineRunResult(V40Model):
    version: str = "v40.engine_run_result.v1"
    result_id: str
    reading_id: str
    engine: EngineKey
    mode: EngineMode
    status: EngineRunStatus = EngineRunStatus.READY
    engine_version: str = ""
    facts: list[dict[str, object]] = Field(default_factory=list)
    features: list[dict[str, object]] = Field(default_factory=list)
    signals: list[RuntimeSignal] = Field(default_factory=list)
    probe_candidates: list[dict[str, object]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    decision_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_authority: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "engine_run_result_outputs_material_not_final_verdict"

    @model_validator(mode="after")
    def _result_boundary(self) -> "EngineRunResult":
        if self.verdict_authority:
            raise ValueError("EngineRunResult cannot have verdict authority")
        if self.chart_fact_mutation_allowed:
            raise ValueError("EngineRunResult cannot mutate chart facts")
        if self.engine == EngineKey.ZIWEI and self.decision_weight != 0.0:
            raise ValueError("ZiweiEngine V1 decision_weight must be 0")
        return self


class MultiEngineRunResult(V40Model):
    version: str = "v40.multi_engine_run_result.v1"
    reading_id: str
    plan: EnginePlan
    results: list[EngineRunResult] = Field(default_factory=list)
    signal_registry: SignalRegistrySnapshot
    decision_engine_mutated: bool = False
    chart_fact_mutation_allowed: bool = False
    boundary: str = "multi_engine_result_collects_engine_outputs_without_decision_mutation"

    @model_validator(mode="after")
    def _multi_engine_boundary(self) -> "MultiEngineRunResult":
        if self.decision_engine_mutated:
            raise ValueError("MultiEngineRunResult cannot mutate DecisionEngine")
        if self.chart_fact_mutation_allowed:
            raise ValueError("MultiEngineRunResult cannot mutate chart facts")
        return self
