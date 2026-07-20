from __future__ import annotations

import pytest

from core.contracts import Topic
from core.state import FlowState, StateTrendDirection, TemporalState, build_state_evolution


def _flow_state(strength: float = 0.82, path_score: float = 0.81, sensitivity: float = 0.95) -> FlowState:
    return FlowState(
        state_id=f"flow_state.career.{strength}",
        reading_id="reading.state_delta.001",
        mechanism="output_controls_pressure",
        path_refs=["path.bazi.001"],
        node_refs=["node.bazi.ding", "node.bazi.you"],
        mechanism_refs=["mechanism.output_controls_pressure"],
        output_strength=strength,
        path_score=path_score,
        ablation_sensitivity=sensitivity,
        evidence_refs=["graph.bazi.001"],
        confidence=0.84,
    )


def _temporal_state() -> TemporalState:
    return TemporalState(
        state_id="temporal_state.career.luck_year",
        reading_id="reading.state_delta.001",
        timing_layer="luck_year",
        activated_paths=["path.bazi.001"],
        weakened_nodes=["node.bazi.ding"],
        rerouted_flows=["flow.resource_backflow"],
        mechanism_shifts={"output_controls_pressure": 0.42},
        state_delta_refs=["state_delta.luck_year.001"],
        evidence_refs=["timing.luck_year.001"],
        confidence=0.7,
    )


def test_v50_state_delta_builder_creates_evolution_from_flow_and_timing_without_judgment() -> None:
    evolution = build_state_evolution(
        reading_id="reading.state_delta.001",
        domain=Topic.CAREER,
        current_flow_state=_flow_state(),
        temporal_state=_temporal_state(),
    )

    assert evolution.creates_judgment is False
    assert evolution.calls_brain is False
    assert evolution.calls_llm is False
    assert evolution.trend == StateTrendDirection.VOLATILE
    assert evolution.velocity > 0.1
    assert evolution.delta_by_dimension["output_strength"] > 0.0
    assert evolution.delta_by_dimension["timing_mechanism_shift"] < 0.0
    assert "luck_year.path_activation" in evolution.activated_by
    assert "luck_year.weakened_nodes" in evolution.suppressed_by
    assert "state_delta.timing.mechanism_shift" in evolution.reason_codes
    assert "flow_state.career.0.82" in evolution.current_state_refs
    assert "temporal_state.career.luck_year" in evolution.current_state_refs


def test_v50_state_delta_builder_compares_against_previous_flow_state() -> None:
    evolution = build_state_evolution(
        reading_id="reading.state_delta.001",
        domain=Topic.CAREER,
        current_flow_state=_flow_state(strength=0.72, path_score=0.76, sensitivity=0.8),
        previous_flow_state=_flow_state(strength=0.82, path_score=0.81, sensitivity=0.95),
    )

    assert evolution.trend == StateTrendDirection.DECREASING
    assert evolution.delta_by_dimension["output_strength"] == -0.1
    assert evolution.delta_by_dimension["structural_sensitivity"] == -0.15
    assert evolution.previous_state_refs == ["flow_state.career.0.82"]


def test_v50_state_delta_builder_rejects_mixed_readings() -> None:
    bad_temporal = _temporal_state().model_copy(update={"reading_id": "reading.other"})

    with pytest.raises(ValueError, match="cannot mix readings"):
        build_state_evolution(
            reading_id="reading.state_delta.001",
            domain=Topic.CAREER,
            current_flow_state=_flow_state(),
            temporal_state=bad_temporal,
        )
