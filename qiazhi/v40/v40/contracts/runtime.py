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
    policy_version_used: str = "baseline"
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
        data = dict(data)
        if data.get("runtime_context"):
            data["policy_version_used"] = data.get("policy_version_used") or _policy_version_from_context(data["runtime_context"])
            return data
        role_key = data.get("role_key", "user")
        locale = data.get("locale", "zh-CN")
        client = data.get("client", "web")
        data["runtime_context"] = RuntimeContext(
            locale_context=default_locale_context(locale),
            role_context=default_role_context(role_key),
            client_context=default_client_context(client),
        )
        data["policy_version_used"] = data.get("policy_version_used") or _policy_version_from_context(data["runtime_context"])
        return data


class RuntimeResult(V40Model):
    version: str = "v40.runtime_result.v1"
    reading_id: str
    request: RuntimeRequest
    policy_version_used: str = "baseline"
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

    @model_validator(mode="before")
    @classmethod
    def _sync_policy_version(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        request_policy = _policy_version_from_request(data.get("request"))
        data["policy_version_used"] = data.get("policy_version_used") or request_policy or "baseline"
        return data

    @model_validator(mode="after")
    def _runtime_boundary(self) -> "RuntimeResult":
        if self.chart_fact_mutation_allowed:
            raise ValueError("RuntimeResult cannot mutate chart facts")
        if self.v30_runtime_imported:
            raise ValueError("RuntimeResult cannot import V30 runtime state")
        if not self.policy_version_used.strip():
            raise ValueError("RuntimeResult requires policy_version_used")
        if self.request.policy_version_used and self.policy_version_used != self.request.policy_version_used:
            raise ValueError("RuntimeResult policy_version_used must match request")
        return self


def _policy_version_from_request(request: Any) -> str:
    if isinstance(request, RuntimeRequest):
        return request.policy_version_used
    if isinstance(request, dict):
        value = str(request.get("policy_version_used") or "").strip()
        if value:
            return value
        return _policy_version_from_context(request.get("runtime_context"))
    return ""


def _policy_version_from_context(runtime_context: Any) -> str:
    if isinstance(runtime_context, RuntimeContext):
        return runtime_context.engine_context.engine_policy_version
    if isinstance(runtime_context, dict):
        engine_context = runtime_context.get("engine_context") or {}
        if isinstance(engine_context, dict):
            return str(engine_context.get("engine_policy_version") or "baseline").strip() or "baseline"
        return str(getattr(engine_context, "engine_policy_version", "baseline") or "baseline").strip() or "baseline"
    return str(getattr(getattr(runtime_context, "engine_context", None), "engine_policy_version", "baseline") or "baseline").strip() or "baseline"
