from __future__ import annotations

from core.contracts.base import Topic
from core.state.contracts import FlowState, StateEvolution, StateTrendDirection, TemporalState


def build_state_evolution(
    *,
    reading_id: str,
    domain: Topic,
    current_flow_state: FlowState,
    temporal_state: TemporalState | None = None,
    previous_flow_state: FlowState | None = None,
) -> StateEvolution:
    """Build StateEvolution from current state plus optional timing overlay."""

    if current_flow_state.reading_id != reading_id:
        raise ValueError("State Delta builder cannot mix readings")
    if temporal_state is not None and temporal_state.reading_id != reading_id:
        raise ValueError("State Delta builder cannot mix readings")
    if previous_flow_state is not None and previous_flow_state.reading_id != reading_id:
        raise ValueError("State Delta builder cannot mix readings")

    delta_by_dimension = _delta_by_dimension(current_flow_state, previous_flow_state=previous_flow_state, temporal_state=temporal_state)
    trend = _trend(delta_by_dimension)
    velocity = _velocity(delta_by_dimension)
    current_state_refs = [current_flow_state.state_id]
    evidence_refs = [*current_flow_state.evidence_refs, current_flow_state.state_id]
    activated_by: list[str] = []
    suppressed_by: list[str] = []
    reason_codes = [f"state_delta.flow.{current_flow_state.mechanism}"]

    if temporal_state is not None:
        current_state_refs.append(temporal_state.state_id)
        evidence_refs.extend([*temporal_state.evidence_refs, temporal_state.state_id])
        activated_by.extend(_activation_sources(temporal_state))
        suppressed_by.extend(_suppression_sources(temporal_state))
        reason_codes.extend(_temporal_reason_codes(temporal_state))

    previous_refs = [previous_flow_state.state_id] if previous_flow_state else []
    confidence = _confidence(current_flow_state, temporal_state=temporal_state)

    return StateEvolution(
        evolution_id=f"state_evolution:{reading_id}:{domain.value}:{current_flow_state.mechanism}",
        reading_id=reading_id,
        domain=domain,
        current_state_refs=_unique(current_state_refs),
        previous_state_refs=previous_refs,
        delta_by_dimension=delta_by_dimension,
        trend=trend,
        velocity=velocity,
        activated_by=_unique(activated_by),
        suppressed_by=_unique(suppressed_by),
        reason_codes=_unique(reason_codes),
        evidence_refs=_unique(evidence_refs),
        confidence=confidence,
    )


def _delta_by_dimension(
    current_flow_state: FlowState,
    *,
    previous_flow_state: FlowState | None,
    temporal_state: TemporalState | None,
) -> dict[str, float]:
    baseline_strength = previous_flow_state.output_strength if previous_flow_state else 0.5
    output_delta = _clamp_delta(current_flow_state.output_strength - baseline_strength)
    path_delta = _clamp_delta(current_flow_state.path_score - (previous_flow_state.path_score if previous_flow_state else 0.5))
    sensitivity_delta = _clamp_delta(current_flow_state.ablation_sensitivity - (previous_flow_state.ablation_sensitivity if previous_flow_state else 0.5))

    deltas = {
        "output_strength": output_delta,
        "path_activation": path_delta,
        "structural_sensitivity": sensitivity_delta,
    }

    if temporal_state is not None:
        mechanism_shift = temporal_state.mechanism_shifts.get(current_flow_state.mechanism)
        if mechanism_shift is None:
            mechanism_shift = temporal_state.mechanism_shifts.get(f"mechanism.{current_flow_state.mechanism}")
        if mechanism_shift is not None:
            deltas["timing_mechanism_shift"] = _clamp_delta(mechanism_shift - current_flow_state.output_strength)
        if temporal_state.activated_paths:
            deltas["timing_activation"] = max(deltas.get("timing_activation", 0.0), 0.18)
        if temporal_state.weakened_nodes:
            deltas["timing_pressure"] = max(deltas.get("timing_pressure", 0.0), 0.16)
        if temporal_state.rerouted_flows:
            deltas["flow_reroute"] = max(deltas.get("flow_reroute", 0.0), 0.14)
    return deltas


def _trend(delta_by_dimension: dict[str, float]) -> StateTrendDirection:
    if not delta_by_dimension:
        return StateTrendDirection.UNKNOWN
    positive = sum(value for value in delta_by_dimension.values() if value > 0.05)
    negative = abs(sum(value for value in delta_by_dimension.values() if value < -0.05))
    if positive > 0.18 and negative > 0.18:
        return StateTrendDirection.VOLATILE
    if positive > negative and positive > 0.08:
        return StateTrendDirection.INCREASING
    if negative > positive and negative > 0.08:
        return StateTrendDirection.DECREASING
    return StateTrendDirection.STABLE


def _velocity(delta_by_dimension: dict[str, float]) -> float:
    if not delta_by_dimension:
        return 0.0
    return round(min(1.0, sum(abs(value) for value in delta_by_dimension.values()) / len(delta_by_dimension)), 3)


def _activation_sources(temporal_state: TemporalState) -> list[str]:
    sources: list[str] = []
    if temporal_state.activated_paths:
        sources.append(f"{temporal_state.timing_layer}.path_activation")
    if temporal_state.mechanism_shifts:
        sources.append(f"{temporal_state.timing_layer}.mechanism_shift")
    return sources


def _suppression_sources(temporal_state: TemporalState) -> list[str]:
    sources: list[str] = []
    if temporal_state.weakened_nodes:
        sources.append(f"{temporal_state.timing_layer}.weakened_nodes")
    if temporal_state.rerouted_flows:
        sources.append(f"{temporal_state.timing_layer}.rerouted_flow")
    return sources


def _temporal_reason_codes(temporal_state: TemporalState) -> list[str]:
    reason_codes: list[str] = []
    if temporal_state.activated_paths:
        reason_codes.append("state_delta.timing.activated_paths")
    if temporal_state.weakened_nodes:
        reason_codes.append("state_delta.timing.weakened_nodes")
    if temporal_state.rerouted_flows:
        reason_codes.append("state_delta.timing.rerouted_flows")
    if temporal_state.mechanism_shifts:
        reason_codes.append("state_delta.timing.mechanism_shift")
    return reason_codes


def _confidence(current_flow_state: FlowState, *, temporal_state: TemporalState | None) -> float:
    if temporal_state is None:
        return current_flow_state.confidence
    return round((current_flow_state.confidence + temporal_state.confidence) / 2, 3)


def _clamp_delta(value: float) -> float:
    return round(max(-1.0, min(1.0, value)), 3)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
