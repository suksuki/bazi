from __future__ import annotations

from v30.core.chart_context import build_chart_context_from_displays
from v30.evidence import compile_feature_evidence
from v30.structure import build_dynamic_graph, select_structure_state


def _parts():
    context = build_chart_context_from_displays(
        reading_id="dynamic-graph",
        year="甲子",
        month="乙丑",
        day="甲寅",
        hour="丁卯",
    )
    evidence = compile_feature_evidence(context)
    return context, evidence


def test_dynamic_graph_v2_builds_nodes_edges_and_paths() -> None:
    _context, evidence = _parts()
    nodes, edges, paths = build_dynamic_graph(evidence)
    assert nodes
    assert edges
    assert paths
    assert any(node.family == "output" for node in nodes)
    assert any(edge.edge_type in {"generate", "control", "support_day_master"} for edge in edges)
    assert paths[0].score > 0
    assert paths[0].competition_rank == 1
    assert paths[0].score_reasons
    assert any(reason.startswith("node_score:") for reason in paths[0].score_reasons)
    assert any(path.suppression > 0 for path in paths)
    assert any(
        "competition_suppression:" in reason
        for path in paths
        for reason in path.score_reasons
    )
    assert any(path.conflict_families for path in paths)
    assert any(path.resolution_families for path in paths)
    assert any(
        reason.startswith("conflict_family:")
        for path in paths
        for reason in path.score_reasons
    )


def test_structure_state_exposes_dynamic_graph_v2_scores() -> None:
    context, evidence = _parts()
    structure = select_structure_state(context, evidence)
    assert "dynamic_graph_review" in structure.primary_chain
    assert structure.path_scores["dynamic_graph_node_count"] > 0
    assert structure.path_scores["dynamic_graph_edge_count"] > 0
    assert structure.path_scores["dynamic_path_count"] > 0
    assert structure.path_scores["top_dynamic_path_score"] > 0
    assert structure.path_scores["dynamic_competing_path_count"] > 0
    assert structure.path_scores["dynamic_suppressed_path_count"] > 0
    assert structure.path_scores["dynamic_conflict_family_count"] > 0
    assert structure.path_scores["dynamic_path_resolution_family_count"] > 0
    assert structure.path_scores["dynamic_branch_conflict_edge_count"] > 0
    assert structure.path_scores["dynamic_branch_alignment_edge_count"] > 0
    assert structure.path_scores["strength_pattern_review_count"] > 0
    assert structure.path_scores["dynamic_wealth_path_count"] > 0
    assert structure.path_scores["dynamic_wealth_competition_path_count"] > 0
    assert structure.path_scores["dynamic_wealth_output_generation_path_count"] > 0
    assert structure.path_scores["dynamic_wealth_authority_bridge_path_count"] > 0
    assert structure.path_scores["dynamic_career_path_count"] > 0
    assert structure.path_scores["dynamic_career_authority_pressure_path_count"] > 0
    assert structure.path_scores["dynamic_career_resource_resolution_path_count"] > 0
    assert structure.path_scores["dynamic_relationship_path_count"] > 0
    assert structure.path_scores["dynamic_relationship_conflict_path_count"] > 0
    assert structure.path_scores["dynamic_relationship_alignment_path_count"] > 0
    assert structure.path_scores["dynamic_relationship_marker_path_count"] > 0
    assert structure.path_scores["dynamic_health_review_path_count"] > 0
    assert structure.path_scores["dynamic_health_element_excess_review_count"] > 0
    assert structure.path_scores["dynamic_health_conflict_pressure_review_count"] > 0
    assert structure.path_scores["dynamic_useful_god_candidate_path_count"] > 0
    assert structure.path_scores["dynamic_useful_god_ranked_candidate_count"] > 0
    assert structure.path_scores["dynamic_tongguan_path_count"] > 0
    assert structure.path_scores["dynamic_tongguan_resource_mediator_path_count"] > 0
    assert structure.path_scores["dynamic_tongguan_output_wealth_bridge_path_count"] > 0
    assert structure.path_scores["dynamic_zhihua_path_count"] > 0
    assert structure.path_scores["dynamic_zhihua_output_authority_path_count"] > 0
    assert structure.path_scores["dynamic_zhihua_wealth_authority_resource_path_count"] > 0
    assert any(node["kind"] == "dynamic_path" for node in structure.graph_nodes)
    assert any(node.get("score_reasons") for node in structure.graph_nodes if node["kind"] == "dynamic_path")
    assert any(node.get("conflict_families") for node in structure.graph_nodes if node["kind"] == "dynamic_path")
    assert any(node.get("resolution_families") for node in structure.graph_nodes if node["kind"] == "dynamic_path")
    assert any(
        any(str(family).startswith(("tongguan", "zhihua")) for family in node.get("resolution_families", []))
        for node in structure.graph_nodes
        if node["kind"] == "dynamic_path"
    )


def test_structure_policy_weights_dynamic_graph_v2_scores() -> None:
    _context, evidence = _parts()
    baseline = build_dynamic_graph(evidence)[2]
    weighted = build_dynamic_graph(evidence, {"weights": {"dynamic_graph.v2": 0.5}})[2]
    assert weighted[0].score < baseline[0].score
    assert any(
        "structure_policy.dynamic_graph.v2:0.5" in reason
        for reason in weighted[0].score_reasons
    )


def test_structure_policy_weights_competition_suppression() -> None:
    _context, evidence = _parts()
    weighted = build_dynamic_graph(evidence, {"weights": {"dynamic_graph.competition_suppression": 1.5}})[2]
    suppressed = next(path for path in weighted if path.suppression > 0)
    assert suppressed.suppression > 0.035
    assert any(
        "structure_policy.dynamic_graph.competition_suppression:1.5" in reason
        for reason in suppressed.score_reasons
    )


def test_structure_policy_weights_conflict_family_explanations() -> None:
    _context, evidence = _parts()
    weighted = build_dynamic_graph(evidence, {"weights": {"dynamic_graph.conflict_family": 1.4}})[2]
    assert any(
        "structure_policy.dynamic_graph.conflict_family:1.4" in reason
        for path in weighted
        for reason in path.score_reasons
    )


def test_structure_policy_weights_path_resolution_explanations() -> None:
    _context, evidence = _parts()
    weighted = build_dynamic_graph(evidence, {"weights": {"dynamic_graph.path_resolution": 1.2}})[2]
    assert any(
        "structure_policy.dynamic_graph.path_resolution:1.2" in reason
        for path in weighted
        for reason in path.score_reasons
    )


def test_structure_policy_weights_tongguan_zhihua_explanations() -> None:
    _context, evidence = _parts()
    weighted = build_dynamic_graph(evidence, {"weights": {"dynamic_graph.tongguan_zhihua": 1.2}})[2]
    assert any(
        "structure_policy.dynamic_graph.tongguan_zhihua:1.2" in reason
        for path in weighted
        for reason in path.score_reasons
    )
