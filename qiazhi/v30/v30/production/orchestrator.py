from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from v30.contracts import FeatureEvidence
from v30.production.adapters import (
    signals_from_diagnosis,
    signals_from_feature_evidence,
    signals_from_macro_dimensions,
    signals_from_ranked_decisions,
    signals_from_stage_points,
)
from v30.production.contracts import ProductionSidecar
from v30.production.module_audit import (
    build_module_audit,
    build_usage_audit,
    summarize_production_audit,
)
from v30.production.signal_registry import build_signal_registry


def build_production_sidecar(
    *,
    reading_id: str,
    feature_evidence: Sequence[FeatureEvidence | Mapping[str, Any]] | None = None,
    macro_signals: Sequence[Mapping[str, Any]] | None = None,
    ranked_decisions: Mapping[str, Any] | None = None,
    practical_context: Mapping[str, Any] | None = None,
    diagnosis: Mapping[str, Any] | None = None,
    central_state: Mapping[str, Any] | None = None,
    decision_result: Mapping[str, Any] | None = None,
    final_synthesis: Mapping[str, Any] | None = None,
    reading_surface: Mapping[str, Any] | None = None,
    thinking_projection: Mapping[str, Any] | None = None,
    training_artifacts: Sequence[Mapping[str, Any]] | None = None,
) -> ProductionSidecar:
    central = _dict(central_state)
    decision_payload = _dict(decision_result) or _dict(central.get("decision_result"))
    final_payload = _dict(final_synthesis) or _dict(central.get("final_synthesis"))
    signals = []
    signals.extend(signals_from_feature_evidence(list(feature_evidence or [])))
    signals.extend(signals_from_macro_dimensions(_dict_rows(macro_signals)))
    signals.extend(signals_from_ranked_decisions(_dict(ranked_decisions)))
    signals.extend(signals_from_diagnosis(_dict(diagnosis)))
    signals.extend(signals_from_stage_points(_stage_points(thinking_projection)))

    registry = build_signal_registry(reading_id=reading_id, signals=signals)
    usage_audit = build_usage_audit(
        registry,
        decision_result=decision_payload,
        final_synthesis=final_payload,
        reading_surface=reading_surface,
        thinking_projection=thinking_projection,
        training_artifacts=training_artifacts,
    )
    module_audit = build_module_audit(registry, usage_audit)
    summary = summarize_production_audit(
        reading_id=reading_id,
        registry=registry,
        usage_audit=usage_audit,
        module_audit=module_audit,
    )
    return ProductionSidecar(
        reading_id=reading_id,
        registry=registry,
        usage_audit=usage_audit,
        module_audit=module_audit,
        summary=summary,
    )


def _stage_points(thinking_projection: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    thinking = _dict(thinking_projection)
    rows: list[dict[str, Any]] = []
    for container_key in ("steps", "journey_steps"):
        for step in _dict_rows(thinking.get(container_key)):
            for point_key in ("stage_points", "selected_points", "points"):
                rows.extend(_dict_rows(step.get(point_key)))
            point_set = _dict(step.get("stage_point_set"))
            rows.extend(_dict_rows(point_set.get("selected_points")))
            rows.extend(_dict_rows(point_set.get("points")))
    deduped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows, start=1):
        key = str(row.get("point_id") or row.get("source_point_id") or f"stage-point:{index}")
        deduped.setdefault(key, row)
    return list(deduped.values())


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dict_rows(value: object) -> list[dict[str, Any]]:
    return [dict(row) for row in value if isinstance(row, Mapping)] if isinstance(value, list) else []
