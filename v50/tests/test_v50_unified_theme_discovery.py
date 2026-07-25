from __future__ import annotations

import pytest

from core.contracts import Topic
from core.state import FlowState, PalaceStateSpace, RealityState, StateTrendDirection, TemporalState, StateEvolution, discover_unified_theme


def _flow_state(*, reading_id: str = "reading.theme.001", mechanism: str = "output_controls_pressure") -> FlowState:
    return FlowState(
        state_id=f"flow_state.{mechanism}",
        reading_id=reading_id,
        mechanism=mechanism,
        path_refs=[f"path.{mechanism}"],
        node_refs=["node.output", "node.target"],
        mechanism_refs=[f"mechanism.{mechanism}"],
        output_strength=0.82,
        path_score=0.78,
        ablation_sensitivity=0.74,
        evidence_refs=[f"evidence.flow.{mechanism}"],
        confidence=0.8,
    )


def _palace_state(*, reading_id: str = "reading.theme.001", pressure: float = 0.72) -> PalaceStateSpace:
    return PalaceStateSpace(
        state_id="palace_state.career",
        reading_id=reading_id,
        palace="官禄",
        domain=Topic.CAREER,
        dimensions={"pressure": pressure, "opportunity": 0.58, "visibility": 0.62, "conflict": 0.66},
        behavior_modifier_refs=["star.七杀"],
        transformation_refs=["transformation.化忌"],
        palace_refs=["palace.官禄"],
        evidence_refs=["evidence.ziwei.career"],
        confidence=0.72,
    )


def _reality_state(*, reading_id: str = "reading.theme.001", domain: Topic = Topic.WEALTH) -> RealityState:
    return RealityState(
        state_id=f"reality_state.{domain.value}",
        reading_id=reading_id,
        domain=domain,
        geography={"living_abroad": True, "location": "Seoul"},
        profession={"role": "founder", "industry": "technology"},
        evidence_refs=["evidence.context.reality"],
        confidence=0.86,
    )


def _temporal_state(*, reading_id: str = "reading.theme.001") -> TemporalState:
    return TemporalState(
        state_id="temporal_state.career",
        reading_id=reading_id,
        timing_layer="luck",
        weakened_nodes=["node.output"],
        rerouted_flows=["flow.resource_backflow"],
        mechanism_shifts={"output_controls_pressure": 0.42},
        evidence_refs=["evidence.timing.luck"],
        confidence=0.7,
    )


def _state_evolution(*, reading_id: str = "reading.theme.001") -> StateEvolution:
    return StateEvolution(
        evolution_id="state_evolution.career",
        reading_id=reading_id,
        domain=Topic.CAREER,
        current_state_refs=["flow_state.output_controls_pressure", "temporal_state.career"],
        delta_by_dimension={"pressure": 0.21, "timing_mechanism_shift": -0.4},
        trend=StateTrendDirection.VOLATILE,
        activated_by=["luck.mechanism_shift"],
        suppressed_by=["luck.weakened_nodes"],
        reason_codes=["state_delta.timing.mechanism_shift"],
        evidence_refs=["evidence.state_evolution"],
        confidence=0.73,
    )


def test_v50_unified_theme_discovery_combines_bazi_ziwei_timing_without_judgment() -> None:
    theme = discover_unified_theme(
        reading_id="reading.theme.001",
        domain=Topic.CAREER,
        flow_state=_flow_state(),
        palace_state_space=_palace_state(),
        temporal_state=_temporal_state(),
        state_evolution=_state_evolution(),
    )

    assert theme.theme_code == "career_output_under_structural_pressure"
    assert theme.strength > 0.0
    assert "producer.bazi_flow" in theme.producer_refs
    assert "producer.ziwei_palace" in theme.producer_refs
    assert "producer.timing_temporal" in theme.producer_refs
    assert "producer.state_evolution" in theme.producer_refs
    assert theme.evidence_refs
    assert theme.creates_judgment is False
    assert theme.calls_brain is False
    assert theme.calls_llm is False


def test_v50_unified_theme_discovery_detects_wealth_and_context_theme() -> None:
    theme = discover_unified_theme(
        reading_id="reading.theme.001",
        domain=Topic.WEALTH,
        flow_state=_flow_state(mechanism="output_to_wealth"),
        reality_state=_reality_state(domain=Topic.WEALTH),
    )

    assert theme.theme_code == "wealth_from_output_with_cross_border_context"
    assert "producer.bazi_flow" in theme.producer_refs
    assert "producer.context_reality" in theme.producer_refs


def test_v50_unified_theme_discovery_detects_competition_theme() -> None:
    theme = discover_unified_theme(
        reading_id="reading.theme.001",
        domain=Topic.WEALTH,
        flow_state=_flow_state(mechanism="peer_competes_for_wealth"),
    )

    assert theme.theme_code == "wealth_competition_and_resource_division"


def test_v50_unified_theme_discovery_rejects_mixed_reading_or_missing_producer() -> None:
    with pytest.raises(ValueError, match="requires at least one state producer"):
        discover_unified_theme(reading_id="reading.theme.001", domain=Topic.CAREER)

    with pytest.raises(ValueError, match="cannot mix readings"):
        discover_unified_theme(
            reading_id="reading.theme.001",
            domain=Topic.CAREER,
            flow_state=_flow_state(reading_id="reading.other"),
        )
