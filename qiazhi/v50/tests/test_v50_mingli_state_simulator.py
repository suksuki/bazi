from __future__ import annotations

import json
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import analyze_mingli_graph, build_mingli_graph_from_material_store, classify_node_roles, explore_mingli_paths
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "data" / "validation" / "fixtures" / "mingli_state_simulator_v1.json"
SYNTHETIC_WORK_PATH = Path(__file__).resolve().parents[1] / "data" / "validation" / "fixtures" / "synthetic_work_system_v1.json"


def _fixture_case() -> dict[str, object]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload["cases"][0]


def _analysis_for_synthetic_case(case_id: str):
    payload = json.loads(SYNTHETIC_WORK_PATH.read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == case_id)
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=f"reading.policy_v2.{case_id}", birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    return analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)


def test_v50_mingli_graph_builds_computational_evidence_without_judgment() -> None:
    case = _fixture_case()
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=str(case["reading_id"]), birth_input=birth, calendar=calendar)

    graph = build_mingli_graph_from_material_store(store)

    assert graph.creates_judgment is False
    assert graph.calls_brain is False
    assert graph.calls_llm is False
    assert any(node.label == "酉" and node.position == "hour_branch" for node in graph.nodes)
    assert any(node.label == "丁" and node.position == "year_stem" and node.attributes.get("output_converter") for node in graph.nodes)
    assert any(node.label == "酉" and node.attributes.get("triple_combination_bridge") for node in graph.nodes)
    assert any(edge.relation_label == "si_you_chou_metal" for edge in graph.edges)


def test_v50_path_explorer_and_role_classifier_find_paths_before_importance_scoring() -> None:
    case = _fixture_case()
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=str(case["reading_id"]), birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)

    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)

    assert path_result.creates_judgment is False
    assert path_result.calls_brain is False
    assert path_result.calls_llm is False
    assert role_result.creates_judgment is False
    assert role_result.calls_brain is False
    assert role_result.calls_llm is False
    assert len(path_result.paths) > 10
    assert set(case["expected_path_hints"]).issubset({hint for path in path_result.paths for hint in path.mechanism_hints})

    roles_by_label_position = {}
    for assignment in role_result.assignments:
        key = f"{assignment.label}:{assignment.position}"
        roles_by_label_position.setdefault(key, set()).add(assignment.role.value)

    for key, expected_roles in case["expected_roles"].items():
        assert set(expected_roles).issubset(roles_by_label_position[key])


def test_v50_node_importance_ranks_bridge_and_converter_before_month_environment() -> None:
    case = _fixture_case()
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=str(case["reading_id"]), birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)

    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    analysis = analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)
    top = analysis.node_metrics[:3]
    top_pairs = [(metric.label, metric.position) for metric in top]

    assert analysis.creates_judgment is False
    assert analysis.calls_brain is False
    assert analysis.calls_llm is False
    assert top_pairs == [("酉", "hour_branch"), ("丁", "year_stem"), ("巳", "month_branch")]
    assert top[0].final_importance > top[1].final_importance > top[2].final_importance
    assert top[0].policy_version == "node_importance_policy_v2"
    assert "node.is_triple_combination_bridge" in top[0].explanation_codes
    assert "role.bridge_node" in top[0].explanation_codes
    assert "node.is_output_converter" in top[1].explanation_codes
    assert "role.converter_node" in top[1].explanation_codes
    assert "node.is_month_environment" in top[2].explanation_codes
    assert "role.environment_node" in top[2].explanation_codes


def test_v50_node_importance_policy_v2_supports_different_structural_winners() -> None:
    bridge_analysis = _analysis_for_synthetic_case("bridge_node_si_you_chou_complete")
    month_analysis = _analysis_for_synthetic_case("month_command_dominant_without_bridge")
    anchor_analysis = _analysis_for_synthetic_case("day_branch_anchor_type")

    bridge_top = bridge_analysis.node_metrics[0]
    month_top = month_analysis.node_metrics[0]
    anchor_top = anchor_analysis.node_metrics[0]

    assert bridge_analysis.policy_version == "node_importance_policy_v2"
    assert (bridge_top.label, bridge_top.position) == ("酉", "hour_branch")
    assert bridge_top.bridge_score >= 0.9
    assert bridge_top.final_importance > next(
        metric.final_importance for metric in bridge_analysis.node_metrics if metric.label == "巳" and metric.position == "month_branch"
    )

    assert (month_top.label, month_top.position) == ("午", "month_branch")
    assert month_top.season_score >= 0.9
    assert month_top.bridge_score < bridge_top.bridge_score

    assert (anchor_top.label, anchor_top.position) == ("巳", "day_branch")
    assert anchor_top.criticality_score >= 0.9
    assert anchor_top.final_importance > next(
        metric.final_importance for metric in anchor_analysis.node_metrics if metric.label == "卯" and metric.position == "month_branch"
    )


def test_v50_ablation_simulation_confirms_critical_node_order_without_brain_or_llm() -> None:
    case = _fixture_case()
    birth = BirthInputCanonical(**case["birth_input"])
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(reading_id=str(case["reading_id"]), birth_input=birth, calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    path_result = explore_mingli_paths(graph)
    role_result = classify_node_roles(graph, path_result)
    analysis = analyze_mingli_graph(graph, path_result=path_result, role_result=role_result)
    state = build_mingli_state_from_graph_analysis(analysis)

    expected_targets = [
        next(metric.node_id for metric in analysis.node_metrics if metric.label == expected["label"] and metric.position == expected["position"])
        for expected in case["expected_top_nodes"]
    ]
    report = run_ablation_simulation(state, target_node_ids=expected_targets)
    labels = [result.target_label for result in report.ablation_results]

    assert state.creates_judgment is False
    assert state.calls_brain is False
    assert state.calls_llm is False
    assert case["expected_active_flow"] in state.active_flows
    assert report.creates_judgment is False
    assert report.calls_brain is False
    assert report.calls_llm is False
    assert labels == case["expected_ablation_order"]
    assert report.ablation_results[0].state_delta > report.ablation_results[1].state_delta > report.ablation_results[2].state_delta
    assert "flow.output_controls_pressure" in report.ablation_results[0].affected_flows
