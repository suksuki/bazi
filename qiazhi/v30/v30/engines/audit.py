from __future__ import annotations

from v30.engines.contracts import EngineAuditEntry, EngineRunResult


def build_engine_audit_entry(result: EngineRunResult, *, registered_signal_ids: list[str] | None = None) -> EngineAuditEntry:
    registered = set(registered_signal_ids or [])
    signal_ids = [signal.signal_id for signal in result.signals]
    return EngineAuditEntry(
        engine=result.engine,
        mode=result.mode,
        status=result.status,
        fact_count=len(result.facts),
        feature_count=len(result.features),
        signal_count=len(result.signals),
        registered_signal_count=sum(1 for signal_id in signal_ids if signal_id in registered),
        probe_candidate_count=len(result.probe_candidates),
        signal_ids=signal_ids,
        warnings=list(result.warnings),
    )
