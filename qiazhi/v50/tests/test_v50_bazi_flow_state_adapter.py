from __future__ import annotations

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import analyze_mingli_graph, build_mingli_graph_from_material_store, classify_node_roles, explore_mingli_paths
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation
from core.state import build_bazi_flow_states


def _birth() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth.flow_state_adapter.001",
        name="flow_state_adapter_case",
        gender="male",
        calendar_type="solar",
        birth_date="1977-05-20",
        birth_time="18:00",
        birth_location="Guangzhou",
        timezone="Asia/Shanghai",
        input_quality="complete",
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
    )


def test_v50_bazi_flow_state_adapter_turns_simulation_evidence_into_unified_state() -> None:
    birth = _birth()
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id="reading.flow_state_adapter.001", birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    analysis = analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)
    state = build_mingli_state_from_graph_analysis(analysis)
    simulation_report = run_ablation_simulation(state)

    flow_states = build_bazi_flow_states(
        analysis=analysis,
        path_result=path_result,
        state=state,
        simulation_report=simulation_report,
    )

    output_control = next(flow_state for flow_state in flow_states if flow_state.mechanism == "output_controls_pressure")
    top_labels = {
        metric.label
        for metric in analysis.node_metrics
        if metric.node_id in output_control.node_refs
    }

    assert output_control.creates_judgment is False
    assert output_control.calls_brain is False
    assert output_control.calls_llm is False
    assert output_control.path_refs
    assert output_control.node_refs
    assert output_control.evidence_refs
    assert output_control.output_strength > 0.8
    assert output_control.path_score > 0.0
    assert output_control.ablation_sensitivity >= 0.9
    assert output_control.confidence >= output_control.output_strength
    assert {"酉", "丁"}.issubset(top_labels)


def test_v50_bazi_flow_state_adapter_rejects_mixed_readings() -> None:
    birth = _birth()
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id="reading.flow_state_adapter.001", birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    analysis = analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)
    state = build_mingli_state_from_graph_analysis(analysis)

    bad_state = state.model_copy(update={"reading_id": "reading.other"})

    try:
        build_bazi_flow_states(analysis=analysis, path_result=path_result, state=bad_state)
    except ValueError as exc:
        assert "cannot mix readings" in str(exc)
    else:
        raise AssertionError("expected mixed reading rejection")
