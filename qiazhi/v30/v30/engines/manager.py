from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.engines.audit import build_engine_audit_entry
from v30.engines.bazi_adapter import run_bazi_engine
from v30.engines.contracts import (
    EngineKey,
    EnginePlan,
    EngineRunRequest,
    EngineRunResult,
    MultiEngineRunResult,
)
from v30.engines.reality_probe_adapter import run_reality_probe_engine
from v30.engines.ziwei_adapter import run_ziwei_engine
from v30.production.signal_registry import build_signal_registry


def run_engine_plan(
    plan: EnginePlan,
    *,
    runtime: CoreRuntimeResult | None = None,
    engine_contexts: dict[str | EngineKey, dict[str, Any]] | None = None,
) -> MultiEngineRunResult:
    engine_contexts = engine_contexts or {}
    results: list[EngineRunResult] = []
    for item in plan.items:
        request = EngineRunRequest(
            request_id=f"{plan.reading_id}:engine-request:{item.engine.value}:{item.mode.value}",
            reading_id=plan.reading_id,
            engine=item.engine,
            mode=item.mode,
            topic=plan.topic,
            domain=plan.domain,
            user_question=plan.user_question,
            chart_context_ref=(runtime.chart_context.context_id if runtime is not None else ""),
            role=plan.role,
            engine_context=_engine_context(engine_contexts, item.engine),
        )
        if item.engine == EngineKey.BAZI:
            results.append(run_bazi_engine(request, runtime=runtime))
        elif item.engine == EngineKey.ZIWEI:
            results.append(run_ziwei_engine(request))
        elif item.engine == EngineKey.REALITY_PROBE:
            results.append(run_reality_probe_engine(request, runtime=runtime))
    registry = build_signal_registry(
        reading_id=plan.reading_id,
        signals=[signal for result in results for signal in result.signals],
        registry_id=f"{plan.reading_id}:multi-engine-signal-registry",
    )
    registered_ids = [signal.signal_id for signal in registry.signals]
    audit = [build_engine_audit_entry(result, registered_signal_ids=registered_ids) for result in results]
    return MultiEngineRunResult(
        reading_id=plan.reading_id,
        plan=plan,
        results=results,
        signal_registry=registry,
        audit=audit,
    )


def _engine_context(contexts: dict[str | EngineKey, dict[str, Any]], engine: EngineKey) -> dict[str, Any]:
    return contexts.get(engine) or contexts.get(engine.value) or {}
