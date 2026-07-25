from __future__ import annotations

import pytest

from core.contracts import Topic
from core.state import (
    FlowState,
    PalaceStateSpace,
    RealityState,
    StateEvolution,
    StateTrendDirection,
    TemporalState,
    UnifiedDomainState,
    UnifiedTheme,
    UnifiedStateBundle,
)


def _flow_state() -> FlowState:
    return FlowState(
        state_id="flow_state.career.001",
        reading_id="reading.unified_state.001",
        mechanism="output_controls_pressure",
        path_refs=["path.bazi.001"],
        node_refs=["node.bazi.ding", "node.bazi.you"],
        mechanism_refs=["mechanism.output_controls_pressure"],
        output_strength=0.82,
        path_score=0.81,
        ablation_sensitivity=0.95,
        evidence_refs=["graph.bazi.001"],
        confidence=0.84,
    )


def _palace_state_space() -> PalaceStateSpace:
    return PalaceStateSpace(
        state_id="palace_state_space.career.001",
        reading_id="reading.unified_state.001",
        palace="官禄",
        domain=Topic.CAREER,
        dimensions={
            "opportunity": 0.58,
            "pressure": 0.72,
            "growth": 0.61,
            "visibility": 0.64,
            "support": 0.42,
            "conflict": 0.68,
            "mobility": 0.55,
            "stability": 0.47,
        },
        behavior_modifier_refs=["star.七杀.behavior_modifier"],
        transformation_refs=["transformation.化忌"],
        palace_refs=["palace.官禄"],
        theme_refs=["theme.career_expansion_under_pressure"],
        evidence_refs=["ziwei.palace.官禄"],
        confidence=0.72,
    )


def _reality_state() -> RealityState:
    return RealityState(
        state_id="reality_state.career.001",
        reading_id="reading.unified_state.001",
        domain=Topic.CAREER,
        geography={"living_abroad": True, "location": "Seoul"},
        profession={"industry": "technology", "role": "founder"},
        event_refs=["event.started_business.2023"],
        evidence_refs=["context.geography.seoul", "context.profession.founder"],
        confidence=0.86,
    )


def _temporal_state() -> TemporalState:
    return TemporalState(
        state_id="temporal_state.career.001",
        reading_id="reading.unified_state.001",
        timing_layer="luck_year",
        activated_paths=["path.bazi.001"],
        weakened_nodes=["node.bazi.ding"],
        rerouted_flows=["flow.resource_backflow"],
        mechanism_shifts={"output_controls_pressure": 0.42},
        state_delta_refs=["state_delta.luck_year.001"],
        evidence_refs=["timing.luck_year.001"],
        confidence=0.69,
    )


def _state_evolution() -> StateEvolution:
    return StateEvolution(
        evolution_id="state_evolution.career.001",
        reading_id="reading.unified_state.001",
        domain=Topic.CAREER,
        current_state_refs=[
            "flow_state.career.001",
            "palace_state_space.career.001",
            "reality_state.career.001",
            "temporal_state.career.001",
        ],
        previous_state_refs=["domain_state.career.previous"],
        delta_by_dimension={"pressure": 0.21, "expansion": -0.12, "visibility": 0.08},
        trend=StateTrendDirection.INCREASING,
        velocity=0.74,
        activated_by=["luck_field", "annual_activation"],
        suppressed_by=["ziwei_hua_ji"],
        reason_codes=["luck_year_pressure_increase", "career_palace_constraint"],
        evidence_refs=["timing.luck_year.001", "ziwei.palace.官禄"],
        confidence=0.73,
    )


def _unified_theme() -> UnifiedTheme:
    return UnifiedTheme(
        theme_id="unified_theme.career.001",
        reading_id="reading.unified_state.001",
        domain=Topic.CAREER,
        theme_code="career_expansion_under_pressure",
        strength=0.82,
        producer_refs=["bazi.flow", "ziwei.palace", "context.reality"],
        state_refs=["flow_state.career.001", "palace_state_space.career.001", "reality_state.career.001"],
        evidence_refs=["graph.bazi.001", "ziwei.palace.官禄", "context.profession.founder"],
        confidence=0.79,
    )


def test_v50_unified_domain_state_accepts_multiple_state_producers_without_judgment() -> None:
    domain_state = UnifiedDomainState(
        domain_state_id="domain_state.career.001",
        reading_id="reading.unified_state.001",
        domain=Topic.CAREER,
        flow_state=_flow_state(),
        palace_state_space=_palace_state_space(),
        reality_state=_reality_state(),
        temporal_state=_temporal_state(),
        state_evolution=_state_evolution(),
        unified_theme=_unified_theme(),
        evidence_refs=["graph.bazi.001", "ziwei.palace.官禄", "context.geography.seoul", "timing.luck_year.001"],
        confidence={"bazi": 0.84, "ziwei": 0.72, "context": 0.86, "timing": 0.69, "overall": 0.78},
        conflict_codes=["bazi_long_term_support_vs_ziwei_short_term_pressure"],
        missing_information_codes=["needs_recent_work_change_probe"],
    )
    bundle = UnifiedStateBundle(
        bundle_id="unified_state_bundle.001",
        reading_id="reading.unified_state.001",
        domain_states=[domain_state],
        evidence_refs=["domain_state.career.001"],
    )

    assert domain_state.creates_judgment is False
    assert domain_state.calls_brain is False
    assert domain_state.calls_llm is False
    assert bundle.creates_judgment is False
    assert bundle.calls_brain is False
    assert bundle.calls_llm is False
    assert domain_state.flow_state is not None
    assert domain_state.palace_state_space is not None
    assert domain_state.reality_state is not None
    assert domain_state.temporal_state is not None
    assert domain_state.state_evolution is not None
    assert domain_state.state_evolution.trend == StateTrendDirection.INCREASING
    assert domain_state.unified_theme is not None
    assert domain_state.unified_theme.theme_code == "career_expansion_under_pressure"
    assert domain_state.confidence["overall"] == 0.78


def test_v50_unified_domain_state_rejects_mixed_domain_or_missing_evidence() -> None:
    with pytest.raises(ValueError, match="cannot mix domains"):
        UnifiedDomainState(
            domain_state_id="domain_state.bad",
            reading_id="reading.unified_state.001",
            domain=Topic.WEALTH,
            palace_state_space=_palace_state_space(),
            evidence_refs=["ziwei.palace.官禄"],
        )

    with pytest.raises(ValueError, match="evidence_refs requires at least one reference"):
        UnifiedDomainState(
            domain_state_id="domain_state.bad_refs",
            reading_id="reading.unified_state.001",
            domain=Topic.CAREER,
            flow_state=_flow_state(),
        )


def test_v50_state_evolution_and_unified_theme_keep_brain_boundary() -> None:
    with pytest.raises(ValueError, match="delta_by_dimension values must be between -1 and 1"):
        StateEvolution(
            evolution_id="state_evolution.bad_delta",
            reading_id="reading.unified_state.001",
            domain=Topic.CAREER,
            current_state_refs=["flow_state.career.001"],
            delta_by_dimension={"pressure": 1.4},
            evidence_refs=["timing.luck_year.001"],
        )

    with pytest.raises(ValueError, match="UnifiedTheme cannot create judgment"):
        UnifiedTheme(
            theme_id="unified_theme.bad",
            reading_id="reading.unified_state.001",
            domain=Topic.CAREER,
            theme_code="career_expansion_under_pressure",
            strength=0.82,
            producer_refs=["bazi.flow"],
            state_refs=["flow_state.career.001"],
            evidence_refs=["graph.bazi.001"],
            creates_judgment=True,
        )


def test_v50_state_producer_contracts_reject_brain_llm_or_judgment_authority() -> None:
    with pytest.raises(ValueError, match="FlowState cannot create judgment"):
        FlowState(
            state_id="flow_state.bad",
            reading_id="reading.unified_state.001",
            mechanism="output_controls_pressure",
            path_refs=["path.bazi.001"],
            node_refs=["node.bazi.ding"],
            evidence_refs=["graph.bazi.001"],
            creates_judgment=True,
        )

    with pytest.raises(ValueError, match="PalaceStateSpace cannot call LLM"):
        PalaceStateSpace(
            state_id="palace_state_space.bad",
            reading_id="reading.unified_state.001",
            palace="官禄",
            domain=Topic.CAREER,
            dimensions={"pressure": 0.72},
            palace_refs=["palace.官禄"],
            evidence_refs=["ziwei.palace.官禄"],
            calls_llm=True,
        )

    with pytest.raises(ValueError, match="RealityState cannot mutate birth input"):
        RealityState(
            state_id="reality_state.bad",
            reading_id="reading.unified_state.001",
            domain=Topic.CAREER,
            evidence_refs=["context.geography.seoul"],
            mutates_birth_input=True,
        )
