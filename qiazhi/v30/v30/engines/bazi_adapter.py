from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.engines.contracts import EngineKey, EngineMode, EngineRunRequest, EngineRunResult, EngineRunStatus
from v30.production.contracts import BaziSignal


BAZI_ENGINE_ADAPTER_VERSION = "v30.bazi_engine_adapter.v1"


def run_bazi_engine(request: EngineRunRequest, *, runtime: CoreRuntimeResult | None = None) -> EngineRunResult:
    if runtime is None:
        return EngineRunResult(
            result_id=f"{request.reading_id}:engine:bazi:blocked",
            reading_id=request.reading_id,
            engine=EngineKey.BAZI,
            mode=request.mode,
            status=EngineRunStatus.BLOCKED,
            engine_version=BAZI_ENGINE_ADAPTER_VERSION,
            warnings=["bazi_engine_requires_existing_runtime_payload_v1"],
            decision_weight=1.0,
        )
    policy_effect = runtime.question_plan.policy_effect
    registry_payload = _dict(policy_effect.get("production_signal_registry"))
    signal_rows = _list(registry_payload.get("signals"))
    signals = [BaziSignal.model_validate(row) for row in signal_rows]
    facts = [
        {"fact_type": "chart_context", "payload": runtime.chart_context.model_dump(mode="json")},
        {"fact_type": "structure_state", "payload": runtime.structure_state.model_dump(mode="json")},
        {"fact_type": "mainline_state", "payload": runtime.mainline_state.model_dump(mode="json")},
    ]
    if isinstance(policy_effect.get("ten_god_energy_model"), dict):
        facts.append({"fact_type": "ten_god_energy_model", "payload": policy_effect["ten_god_energy_model"]})
    diagnosis = _dict(policy_effect.get("real_bazi_diagnosis"))
    features = [
        {"feature_type": "feature_evidence", "payload": row.model_dump(mode="json")}
        for row in runtime.feature_evidence
    ]
    for key in ("features", "paths", "portraits", "claims", "matched_rules"):
        rows = _list(diagnosis.get(key))
        features.extend({"feature_type": f"diagnosis_{key}", "payload": row} for row in rows)
    return EngineRunResult(
        result_id=f"{request.reading_id}:engine:bazi:{request.mode.value}",
        reading_id=request.reading_id,
        engine=EngineKey.BAZI,
        mode=request.mode,
        status=EngineRunStatus.READY,
        engine_version=BAZI_ENGINE_ADAPTER_VERSION,
        standard_version="v30.bazi_existing_runtime_wrapped.v1",
        facts=facts,
        features=features,
        signals=signals,
        probe_candidates=_list(policy_effect.get("hidden_factor_probes")),
        diagnostics={
            "wrapped_runtime_trace_id": runtime.trace_id,
            "feature_evidence_count": len(runtime.feature_evidence),
            "production_signal_count": len(signals),
            "decision_verdict_count": len(_list(_dict(_dict(policy_effect.get("central_reading_state")).get("decision_result")).get("verdicts"))),
        },
        decision_weight=1.0,
        boundary="bazi_engine_adapter_wraps_existing_runtime_without_rewriting_bazi_modules",
    )


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []
