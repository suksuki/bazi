from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from v40.contracts.base import ClientKey, LocaleKey, RoleKey, Topic, V40Model
from v40.contracts.context import RuntimeContext, default_client_context, default_locale_context, default_role_context
from v40.contracts.decision import AdvicePlan, BranchCandidate, DecisionInputBundle, DecisionVerdict, ProbeCandidate
from v40.contracts.engine import MultiEngineRunResult
from v40.contracts.output import (
    AcceptanceResult,
    ConversationSeed,
    ExpressionTelemetry,
    LLMExpressionResult,
    LLMExpressionTask,
    ProductProjectionBundle,
    SurfaceBundle,
)
from v40.contracts.signal import SignalRegistrySnapshot


class RuntimeRequest(V40Model):
    version: str = "v40.runtime_request.v1"
    request_id: str
    reading_id: str
    role_key: RoleKey = "user"
    locale: LocaleKey = "zh"
    client: ClientKey = "web"
    runtime_context: RuntimeContext = Field(default_factory=RuntimeContext)
    user_question: str = ""
    topic: Topic = Topic.OVERVIEW
    birth_input_ref: str = ""
    imported_case_ref: str = ""
    boundary: str = "runtime_request_starts_v40_runtime_without_reading_v30_state"

    @model_validator(mode="before")
    @classmethod
    def _sync_runtime_context(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("runtime_context"):
            return data
        role_key = data.get("role_key", "user")
        locale = data.get("locale", "zh-CN")
        client = data.get("client", "web")
        data = dict(data)
        data["runtime_context"] = RuntimeContext(
            locale_context=default_locale_context(locale),
            role_context=default_role_context(role_key),
            client_context=default_client_context(client),
        )
        return data


class RuntimeResult(V40Model):
    version: str = "v40.runtime_result.v1"
    reading_id: str
    request: RuntimeRequest
    engine_result: MultiEngineRunResult | None = None
    signal_registry: SignalRegistrySnapshot | None = None
    decision_input: DecisionInputBundle | None = None
    branches: list[BranchCandidate] = Field(default_factory=list)
    verdicts: list[DecisionVerdict] = Field(default_factory=list)
    advice_plans: list[AdvicePlan] = Field(default_factory=list)
    probes: list[ProbeCandidate] = Field(default_factory=list)
    product_projection: ProductProjectionBundle | None = None
    expression_task: LLMExpressionTask | None = None
    expression_result: LLMExpressionResult | None = None
    acceptance_result: AcceptanceResult | None = None
    expression_telemetry: ExpressionTelemetry | None = None
    conversation_seeds: list[ConversationSeed] = Field(default_factory=list)
    surface_bundle: SurfaceBundle | None = None
    chart_fact_mutation_allowed: bool = False
    v30_runtime_imported: bool = False
    boundary: str = "runtime_result_keeps_v40_state_independent_from_v30_runtime"

    @model_validator(mode="after")
    def _runtime_boundary(self) -> "RuntimeResult":
        if self.chart_fact_mutation_allowed:
            raise ValueError("RuntimeResult cannot mutate chart facts")
        if self.v30_runtime_imported:
            raise ValueError("RuntimeResult cannot import V30 runtime state")
        return self
