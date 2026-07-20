from __future__ import annotations

from collections import Counter

from core.engines.bazi.knowledge import CONTROLS, GENERATES
from core.graph.contracts import (
    GraphAnalysisResult,
    MingliGraph,
    MingliGraphEdgeType,
    MingliGraphNode,
    NodeImportanceMetric,
    NodeRoleClassificationResult,
    NodeRoleType,
    PathExplorationResult,
)


NODE_IMPORTANCE_POLICY_V2 = {
    "policy_version": "node_importance_policy_v2",
    "season_weight": 0.10,
    "centrality_weight": 0.12,
    "bridge_weight": 0.24,
    "criticality_weight": 0.20,
    "flow_weight": 0.22,
    "perturbation_weight": 0.16,
    "redundancy_weight": 0.10,
}

NODE_IMPORTANCE_POLICY_V1 = NODE_IMPORTANCE_POLICY_V2


def analyze_mingli_graph(
    graph: MingliGraph,
    *,
    path_result: PathExplorationResult | None = None,
    role_result: NodeRoleClassificationResult | None = None,
) -> GraphAnalysisResult:
    if not graph.nodes:
        return GraphAnalysisResult(
            analysis_id=f"graph_analysis:{graph.reading_id}",
            reading_id=graph.reading_id,
            graph_id=graph.graph_id,
            policy_version=NODE_IMPORTANCE_POLICY_V2["policy_version"],
            node_metrics=[],
            ranked_node_ids=[],
        )

    month_branch = _month_branch_node(graph)
    month_element = month_branch.element if month_branch else ""
    degree_scores = _degree_scores(graph)
    duplicate_scores = _duplicate_label_scores(graph)
    path_contribution = path_result.node_path_contribution if path_result else {}
    roles_by_node = role_result.roles_by_node_id if role_result else {}
    metrics: list[NodeImportanceMetric] = []
    for node in graph.nodes:
        if node.node_type.value == "hidden_stem":
            continue
        roles = set(roles_by_node.get(node.node_id, []))
        season_score = _season_score(node, month_branch=month_branch, month_element=month_element)
        centrality_score = degree_scores.get(node.node_id, 0.0)
        bridge_score = max(_bridge_score(node, graph), _role_bridge_score(roles))
        criticality_score = max(_criticality_score(node, graph), _role_criticality_score(roles))
        flow_contribution = max(_flow_contribution(node, graph), path_contribution.get(node.node_id, 0.0))
        perturbation_sensitivity = max(_perturbation_sensitivity(node, graph), _role_perturbation_score(roles))
        redundancy_score = duplicate_scores.get(node.label, 0.0)
        final_importance = _importance(
            season_score=season_score,
            centrality_score=centrality_score,
            bridge_score=bridge_score,
            criticality_score=criticality_score,
            flow_contribution=flow_contribution,
            perturbation_sensitivity=perturbation_sensitivity,
            redundancy_score=redundancy_score,
        )
        metrics.append(
            NodeImportanceMetric(
                metric_id=f"metric:{graph.reading_id}:node_importance:{node.node_id}",
                reading_id=graph.reading_id,
                graph_id=graph.graph_id,
                node_id=node.node_id,
                label=node.label,
                position=node.position,
                policy_version=NODE_IMPORTANCE_POLICY_V2["policy_version"],
                season_score=season_score,
                centrality_score=centrality_score,
                bridge_score=bridge_score,
                criticality_score=criticality_score,
                flow_contribution=flow_contribution,
                perturbation_sensitivity=perturbation_sensitivity,
                redundancy_score=redundancy_score,
                final_importance=final_importance,
                explanation_codes=_explanation_codes(
                    node,
                    roles=roles,
                    bridge_score=bridge_score,
                    criticality_score=criticality_score,
                    flow_contribution=flow_contribution,
                    perturbation_sensitivity=perturbation_sensitivity,
                ),
                graph_refs=[graph.graph_id],
                evidence_refs=[*node.evidence_refs, graph.graph_id],
            )
        )

    metrics = sorted(metrics, key=lambda metric: metric.final_importance, reverse=True)
    return GraphAnalysisResult(
        analysis_id=f"graph_analysis:{graph.reading_id}",
        reading_id=graph.reading_id,
        graph_id=graph.graph_id,
        policy_version=NODE_IMPORTANCE_POLICY_V2["policy_version"],
        node_metrics=metrics,
        ranked_node_ids=[metric.node_id for metric in metrics],
    )


def _month_branch_node(graph: MingliGraph) -> MingliGraphNode | None:
    for node in graph.nodes:
        if node.position == "month_branch":
            return node
    return None


def _degree_scores(graph: MingliGraph) -> dict[str, float]:
    degrees: Counter[str] = Counter()
    for edge in graph.edges:
        degrees[edge.from_node_id] += 1
        degrees[edge.to_node_id] += 1
    max_degree = max(degrees.values() or [1])
    return {node_id: round(min(1.0, degree / max_degree), 3) for node_id, degree in degrees.items()}


def _duplicate_label_scores(graph: MingliGraph) -> dict[str, float]:
    counts = Counter(node.label for node in graph.nodes if node.node_type.value in {"stem", "branch"})
    return {label: min(0.45, max(0, count - 1) * 0.18) for label, count in counts.items()}


def _season_score(node: MingliGraphNode, *, month_branch: MingliGraphNode | None, month_element: str) -> float:
    if not month_branch or not month_element:
        return 0.45
    if node.node_id == month_branch.node_id:
        return 0.96
    if node.element == month_element:
        return 0.78 if node.node_type.value == "branch" else 0.70
    if GENERATES.get(month_element) == node.element:
        return 0.58
    if CONTROLS.get(month_element) == node.element:
        return 0.35
    if GENERATES.get(node.element) == month_element:
        return 0.48
    return 0.42


def _bridge_score(node: MingliGraphNode, graph: MingliGraph) -> float:
    if node.attributes.get("triple_combination_bridge"):
        return 0.95
    if node.attributes.get("output_converter"):
        return 0.58
    if node.position == "month_branch":
        return 0.48
    if any(edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION and node.node_id in {edge.from_node_id, edge.to_node_id} for edge in graph.edges):
        return 0.62
    return 0.28


def _criticality_score(node: MingliGraphNode, graph: MingliGraph) -> float:
    if node.attributes.get("triple_combination_bridge"):
        return 0.90
    if node.attributes.get("output_converter"):
        return 0.87
    if node.position == "month_branch":
        return 0.62
    if _controls_pressure_target(node, graph):
        return 0.76
    if node.position == "day_stem":
        return 0.70
    return 0.38


def _flow_contribution(node: MingliGraphNode, graph: MingliGraph) -> float:
    if node.attributes.get("output_converter"):
        return 0.93
    if node.attributes.get("triple_combination_bridge"):
        return 0.88
    if node.position == "month_branch":
        return 0.74
    if _controls_pressure_target(node, graph):
        return 0.72
    if node.position == "day_stem":
        return 0.66
    return 0.36


def _perturbation_sensitivity(node: MingliGraphNode, graph: MingliGraph) -> float:
    if node.attributes.get("output_converter"):
        return 0.90
    if node.attributes.get("triple_combination_bridge"):
        return 0.82
    if node.position == "month_branch":
        return 0.55
    if _controls_pressure_target(node, graph):
        return 0.70
    return 0.34


def _role_bridge_score(roles: set[NodeRoleType]) -> float:
    return 0.95 if NodeRoleType.BRIDGE_NODE in roles else 0.0


def _role_criticality_score(roles: set[NodeRoleType]) -> float:
    if NodeRoleType.SINGLE_FAILURE_NODE in roles:
        return 0.90
    if NodeRoleType.CONVERTER_NODE in roles:
        return 0.87
    if NodeRoleType.ANCHOR_NODE in roles:
        return 0.74
    return 0.0


def _role_perturbation_score(roles: set[NodeRoleType]) -> float:
    if NodeRoleType.CONVERTER_NODE in roles:
        return 0.90
    if NodeRoleType.BRIDGE_NODE in roles:
        return 0.82
    if NodeRoleType.ANCHOR_NODE in roles:
        return 0.62
    if NodeRoleType.ACTIVATION_NODE in roles:
        return 0.55
    return 0.0


def _controls_pressure_target(node: MingliGraphNode, graph: MingliGraph) -> bool:
    if node.element != "metal":
        return False
    return any(edge.edge_type == MingliGraphEdgeType.CONTROLS and edge.to_node_id == node.node_id for edge in graph.edges)


def _importance(
    *,
    season_score: float,
    centrality_score: float,
    bridge_score: float,
    criticality_score: float,
    flow_contribution: float,
    perturbation_sensitivity: float,
    redundancy_score: float,
) -> float:
    score = (
        NODE_IMPORTANCE_POLICY_V2["season_weight"] * season_score
        + NODE_IMPORTANCE_POLICY_V2["centrality_weight"] * centrality_score
        + NODE_IMPORTANCE_POLICY_V2["bridge_weight"] * bridge_score
        + NODE_IMPORTANCE_POLICY_V2["criticality_weight"] * criticality_score
        + NODE_IMPORTANCE_POLICY_V2["flow_weight"] * flow_contribution
        + NODE_IMPORTANCE_POLICY_V2["perturbation_weight"] * perturbation_sensitivity
        - NODE_IMPORTANCE_POLICY_V2["redundancy_weight"] * redundancy_score
    )
    return round(max(0.0, min(1.0, score)), 3)


def _explanation_codes(
    node: MingliGraphNode,
    *,
    roles: set[NodeRoleType],
    bridge_score: float,
    criticality_score: float,
    flow_contribution: float,
    perturbation_sensitivity: float,
) -> list[str]:
    codes: list[str] = []
    if node.attributes.get("triple_combination_bridge"):
        codes.append("node.is_triple_combination_bridge")
    if node.attributes.get("output_converter"):
        codes.append("node.is_output_converter")
    if node.position == "month_branch":
        codes.append("node.is_month_environment")
    for role in sorted(roles, key=lambda item: item.value):
        codes.append(f"role.{role.value}")
    if bridge_score >= 0.8:
        codes.append("metric.high_bridge_score")
    if criticality_score >= 0.8:
        codes.append("metric.high_single_failure_risk")
    if flow_contribution >= 0.8:
        codes.append("metric.high_flow_contribution")
    if perturbation_sensitivity >= 0.8:
        codes.append("metric.high_perturbation_sensitivity")
    return codes or ["metric.baseline_structural_node"]
