from __future__ import annotations

from collections import defaultdict

from core.graph.contracts import (
    MingliGraph,
    MingliGraphNode,
    NodeRoleAssignment,
    NodeRoleClassificationResult,
    NodeRoleType,
    PathExplorationResult,
)


def classify_node_roles(graph: MingliGraph, path_result: PathExplorationResult) -> NodeRoleClassificationResult:
    assignments: list[NodeRoleAssignment] = []
    paths_by_node = _paths_by_node(path_result)
    for node in graph.nodes:
        if node.node_type.value == "hidden_stem":
            continue
        for role, confidence, reason_codes in _roles_for_node(node=node, graph=graph, path_result=path_result):
            path_refs = [path.path_id for path in paths_by_node.get(node.node_id, [])[:5]]
            assignments.append(
                NodeRoleAssignment(
                    assignment_id=f"role:{graph.reading_id}:{node.node_id}:{role.value}",
                    reading_id=graph.reading_id,
                    graph_id=graph.graph_id,
                    node_id=node.node_id,
                    label=node.label,
                    position=node.position,
                    role=role,
                    confidence=confidence,
                    reason_codes=reason_codes,
                    path_refs=path_refs,
                    graph_refs=[graph.graph_id],
                    evidence_refs=[graph.graph_id, *node.evidence_refs, *path_refs],
                )
            )
    roles_by_node: dict[str, list[NodeRoleType]] = defaultdict(list)
    for assignment in assignments:
        roles_by_node[assignment.node_id].append(assignment.role)
    return NodeRoleClassificationResult(
        classification_id=f"role_classification:{graph.reading_id}:{path_result.state_layer.value}",
        reading_id=graph.reading_id,
        graph_id=graph.graph_id,
        state_layer=path_result.state_layer,
        assignments=assignments,
        roles_by_node_id=dict(roles_by_node),
    )


def _paths_by_node(path_result: PathExplorationResult) -> dict[str, list]:
    grouped: defaultdict[str, list] = defaultdict(list)
    for path in path_result.paths:
        for node_id in path.node_ids:
            grouped[node_id].append(path)
    for node_id, paths in grouped.items():
        grouped[node_id] = sorted(paths, key=lambda path: path.path_score, reverse=True)
    return grouped


def _roles_for_node(
    *,
    node: MingliGraphNode,
    graph: MingliGraph,
    path_result: PathExplorationResult,
) -> list[tuple[NodeRoleType, float, list[str]]]:
    roles: list[tuple[NodeRoleType, float, list[str]]] = []
    contribution = path_result.node_path_contribution.get(node.node_id, 0.0)
    if node.position == "month_branch":
        roles.append((NodeRoleType.ENVIRONMENT_NODE, 0.94, ["role.month_branch_initial_environment"]))
        roles.append((NodeRoleType.ACTIVATION_NODE, 0.88, ["role.month_branch_activates_season"]))
    if node.position in {"day_stem", "day_branch"}:
        roles.append((NodeRoleType.ANCHOR_NODE, 0.86, ["role.day_position_anchor"]))
    if node.attributes.get("triple_combination_bridge"):
        roles.append((NodeRoleType.BRIDGE_NODE, 0.95, ["role.triple_combination_bridge", "role.path_bridge"]))
    if node.attributes.get("output_converter"):
        roles.append((NodeRoleType.CONVERTER_NODE, 0.94, ["role.visible_output_converter", "role.flow_converter"]))
    if _is_engine_node(node, graph, contribution):
        roles.append((NodeRoleType.ENGINE_NODE, round(max(0.68, contribution), 3), ["role.high_path_engine", "role.active_element_source"]))
    if _is_buffer_node(node, graph):
        roles.append((NodeRoleType.BUFFER_NODE, 0.72, ["role.storage_or_damp_buffer"]))
    if _is_single_failure_node(node, contribution):
        roles.append((NodeRoleType.SINGLE_FAILURE_NODE, round(max(0.82, contribution), 3), ["role.high_path_contribution", "role.removal_sensitive_candidate"]))
    return roles


def _is_engine_node(node: MingliGraphNode, graph: MingliGraph, contribution: float) -> bool:
    if node.position == "month_branch":
        return True
    if contribution >= 0.70 and node.node_type.value in {"stem", "branch"}:
        return True
    outgoing = [edge for edge in graph.edges if edge.from_node_id == node.node_id]
    return len(outgoing) >= 4


def _is_buffer_node(node: MingliGraphNode, graph: MingliGraph) -> bool:
    if node.label in {"丑", "辰"}:
        return True
    if node.label in {"未", "戌"} and any(str(hidden) in {"丁", "辛", "乙"} for hidden in node.attributes.get("hidden_stems", [])):
        return True
    return False


def _is_single_failure_node(node: MingliGraphNode, contribution: float) -> bool:
    if node.attributes.get("triple_combination_bridge"):
        return True
    if node.attributes.get("output_converter"):
        return True
    return contribution >= 0.86
