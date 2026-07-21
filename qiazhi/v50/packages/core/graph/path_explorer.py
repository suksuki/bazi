from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass

from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphEdgeType, MingliGraphNode, MingliPath, MingliStateLayer, PathExplorationResult
from core.graph.provenance import stable_candidate_path_key


VALID_PATH_EDGE_TYPES = {
    MingliGraphEdgeType.GENERATES,
    MingliGraphEdgeType.CONTROLS,
    MingliGraphEdgeType.SAME_ELEMENT_SUPPORT,
    MingliGraphEdgeType.STORES,
    MingliGraphEdgeType.ROOTS,
    MingliGraphEdgeType.FORMS_HALF_COMBINATION,
    MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION,
    MingliGraphEdgeType.CLASHES,
    MingliGraphEdgeType.HARMONIZES,
    MingliGraphEdgeType.POSITION_LINK,
}

PATH_SCORE_POLICY_V2 = {
    "policy_version": "path_score_policy_v2",
    "source_weight": 0.10,
    "edge_weight": 0.16,
    "season_weight": 0.08,
    "root_weight": 0.12,
    "converter_weight": 0.22,
    "bridge_weight": 0.22,
    "target_weight": 0.10,
}


@dataclass(frozen=True)
class _PathDraft:
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


def explore_mingli_paths(
    graph: MingliGraph,
    *,
    state_layer: MingliStateLayer = MingliStateLayer.NATAL,
    max_edges: int = 3,
    limit: int = 80,
) -> PathExplorationResult:
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    edges_by_id = {edge.edge_id: edge for edge in graph.edges}
    adjacency = _adjacency(graph)
    drafts: dict[tuple[tuple[str, ...], tuple[str, ...]], _PathDraft] = {}
    for node in graph.nodes:
        _walk(
            node_id=node.node_id,
            adjacency=adjacency,
            node_path=(node.node_id,),
            edge_path=(),
            drafts=drafts,
            max_edges=max_edges,
        )
    paths = [_build_path(graph=graph, state_layer=state_layer, nodes_by_id=nodes_by_id, edges_by_id=edges_by_id, draft=draft) for draft in drafts.values()]
    paths = sorted(paths, key=lambda path: path.path_score, reverse=True)[:limit]
    paths = [_attach_candidate_path_key(path, edges_by_id=edges_by_id) for path in paths]
    contribution = _node_path_contribution(paths)
    return PathExplorationResult(
        exploration_id=f"path_exploration:{graph.reading_id}:{state_layer.value}",
        reading_id=graph.reading_id,
        graph_id=graph.graph_id,
        state_layer=state_layer,
        paths=paths,
        ranked_path_ids=[path.path_id for path in paths],
        node_path_contribution=contribution,
    )


def _attach_candidate_path_key(
    path: MingliPath,
    *,
    edges_by_id: dict[str, MingliGraphEdge],
) -> MingliPath:
    relation_keys = [edges_by_id[edge_id].relation_key for edge_id in path.edge_ids]
    return path.model_copy(update={
        "path_key": stable_candidate_path_key(
            reading_id=path.reading_id,
            state_layer=path.state_layer.value,
            node_keys=list(path.node_ids),
            relation_keys=relation_keys,
        ),
        "relation_keys": relation_keys,
    })


def _adjacency(graph: MingliGraph) -> dict[str, list[MingliGraphEdge]]:
    adjacency: dict[str, list[MingliGraphEdge]] = defaultdict(list)
    for edge in graph.edges:
        if edge.edge_type not in VALID_PATH_EDGE_TYPES:
            continue
        if edge.attributes.get("path_eligibility") == "not_yet_qualified":
            continue
        if (
            edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
            and len(edge.participant_node_ids) > 2
        ):
            bridge_node_id = str(edge.attributes.get("bridge_node_id", ""))
            if bridge_node_id in edge.participant_node_ids:
                for participant_node_id in edge.participant_node_ids:
                    if participant_node_id == bridge_node_id:
                        continue
                    adjacency[participant_node_id].append(
                        edge.model_copy(
                            update={
                                "from_node_id": participant_node_id,
                                "to_node_id": bridge_node_id,
                            }
                        )
                    )
                    adjacency[bridge_node_id].append(
                        edge.model_copy(
                            update={
                                "from_node_id": bridge_node_id,
                                "to_node_id": participant_node_id,
                            }
                        )
                    )
                continue
        adjacency[edge.from_node_id].append(edge)
        if edge.edge_type in {
            MingliGraphEdgeType.SAME_ELEMENT_SUPPORT,
            MingliGraphEdgeType.FORMS_HALF_COMBINATION,
            MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION,
            MingliGraphEdgeType.CLASHES,
            MingliGraphEdgeType.HARMONIZES,
            MingliGraphEdgeType.POSITION_LINK,
        }:
            adjacency[edge.to_node_id].append(edge.model_copy(update={"from_node_id": edge.to_node_id, "to_node_id": edge.from_node_id}))
    return adjacency


def _walk(
    *,
    node_id: str,
    adjacency: dict[str, list[MingliGraphEdge]],
    node_path: tuple[str, ...],
    edge_path: tuple[str, ...],
    drafts: dict[tuple[tuple[str, ...], tuple[str, ...]], _PathDraft],
    max_edges: int,
) -> None:
    if edge_path:
        drafts[(node_path, edge_path)] = _PathDraft(node_ids=node_path, edge_ids=edge_path)
    if len(edge_path) >= max_edges:
        return
    for edge in adjacency.get(node_id, []):
        if edge.to_node_id in node_path:
            continue
        _walk(
            node_id=edge.to_node_id,
            adjacency=adjacency,
            node_path=(*node_path, edge.to_node_id),
            edge_path=(*edge_path, edge.edge_id),
            drafts=drafts,
            max_edges=max_edges,
        )


def _build_path(
    *,
    graph: MingliGraph,
    state_layer: MingliStateLayer,
    nodes_by_id: dict[str, MingliGraphNode],
    edges_by_id: dict[str, MingliGraphEdge],
    draft: _PathDraft,
) -> MingliPath:
    nodes = [nodes_by_id[node_id] for node_id in draft.node_ids]
    edges = [edges_by_id[edge_id] for edge_id in draft.edge_ids]
    source_strength = _source_strength(nodes[0])
    edge_strength = _edge_strength(edges)
    season_bias = _season_bias(nodes)
    root_support = _root_support(nodes, edges)
    converter_capacity = _converter_capacity(nodes)
    bridge_stability = _bridge_stability(nodes, edges)
    target_receptivity = _target_receptivity(nodes[-1], edges[-1])
    path_score = _path_score(
        source_strength=source_strength,
        edge_strength=edge_strength,
        season_bias=season_bias,
        root_support=root_support,
        converter_capacity=converter_capacity,
        bridge_stability=bridge_stability,
        target_receptivity=target_receptivity,
    )
    relation_types = [edge.edge_type.value for edge in edges]
    signature = hashlib.sha256(
        "\x1f".join([*draft.node_ids, "\x1e", *draft.edge_ids]).encode("utf-8")
    ).hexdigest()[:16]
    return MingliPath(
        path_id=f"path:{graph.reading_id}:{state_layer.value}:{len(draft.node_ids)}:{signature}",
        reading_id=graph.reading_id,
        graph_id=graph.graph_id,
        state_layer=state_layer,
        node_ids=list(draft.node_ids),
        edge_ids=list(draft.edge_ids),
        relation_types=relation_types,
        source_strength=source_strength,
        edge_strength=edge_strength,
        season_bias=season_bias,
        root_support=root_support,
        converter_capacity=converter_capacity,
        bridge_stability=bridge_stability,
        target_receptivity=target_receptivity,
        path_score=path_score,
        mechanism_hints=_mechanism_hints(nodes, edges),
        graph_refs=[graph.graph_id],
        evidence_refs=[graph.graph_id, *[ref for node in nodes for ref in node.evidence_refs], *[ref for edge in edges for ref in edge.evidence_refs]],
    )


def _source_strength(node: MingliGraphNode) -> float:
    if node.position == "month_branch":
        return 0.90
    if node.position == "day_stem":
        return 0.78
    if node.attributes.get("output_converter"):
        return 0.86
    if node.attributes.get("triple_combination_bridge"):
        return 0.88
    if node.node_type.value == "branch":
        return 0.68
    if node.node_type.value == "stem":
        return 0.66
    return 0.42


def _edge_strength(edges: list[MingliGraphEdge]) -> float:
    if not edges:
        return 0.0
    return round(sum(edge.strength for edge in edges) / len(edges), 3)


def _season_bias(nodes: list[MingliGraphNode]) -> float:
    scores = []
    for node in nodes:
        if node.position == "month_branch":
            scores.append(0.96)
        elif node.element == "fire":
            scores.append(0.76)
        elif node.element == "earth":
            scores.append(0.58)
        elif node.element == "metal":
            scores.append(0.42)
        else:
            scores.append(0.48)
    return round(sum(scores) / len(scores), 3)


def _root_support(nodes: list[MingliGraphNode], edges: list[MingliGraphEdge]) -> float:
    score = 0.35
    if any(edge.edge_type == MingliGraphEdgeType.STORES for edge in edges):
        score += 0.22
    if any(node.position == "day_branch" for node in nodes):
        score += 0.12
    if any(node.node_type.value == "hidden_stem" for node in nodes):
        score += 0.10
    return round(min(1.0, score), 3)


def _converter_capacity(nodes: list[MingliGraphNode]) -> float:
    if any(node.attributes.get("output_converter") for node in nodes):
        return 0.90
    if any(node.ten_god in {"shi_shen", "shang_guan"} for node in nodes):
        return 0.72
    return 0.35


def _bridge_stability(nodes: list[MingliGraphNode], edges: list[MingliGraphEdge]) -> float:
    if any(node.attributes.get("triple_combination_bridge") for node in nodes):
        return 0.94
    if any(edge.edge_type in {MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION, MingliGraphEdgeType.FORMS_HALF_COMBINATION} for edge in edges):
        return 0.78
    return 0.36


def _target_receptivity(node: MingliGraphNode, last_edge: MingliGraphEdge) -> float:
    if node.attributes.get("triple_combination_bridge"):
        return 0.88
    if last_edge.edge_type == MingliGraphEdgeType.CONTROLS and node.element == "metal":
        return 0.78
    if node.node_type.value == "branch":
        return 0.70
    if node.node_type.value == "hidden_stem":
        return 0.48
    return 0.58


def _path_score(
    *,
    source_strength: float,
    edge_strength: float,
    season_bias: float,
    root_support: float,
    converter_capacity: float,
    bridge_stability: float,
    target_receptivity: float,
) -> float:
    score = (
        source_strength * PATH_SCORE_POLICY_V2["source_weight"]
        + edge_strength * PATH_SCORE_POLICY_V2["edge_weight"]
        + season_bias * PATH_SCORE_POLICY_V2["season_weight"]
        + root_support * PATH_SCORE_POLICY_V2["root_weight"]
        + converter_capacity * PATH_SCORE_POLICY_V2["converter_weight"]
        + bridge_stability * PATH_SCORE_POLICY_V2["bridge_weight"]
        + target_receptivity * PATH_SCORE_POLICY_V2["target_weight"]
    )
    return round(max(0.0, min(1.0, score)), 3)


def _mechanism_hints(nodes: list[MingliGraphNode], edges: list[MingliGraphEdge]) -> list[str]:
    hints: list[str] = []
    relation_types = {edge.edge_type for edge in edges}
    output_nodes = [node for node in nodes if node.attributes.get("output_converter") or node.ten_god in {"shi_shen", "shang_guan"}]
    wealth_nodes = [node for node in nodes if node.ten_god in {"zheng_cai", "pian_cai"}]
    output_node_ids = {node.node_id for node in output_nodes}
    wealth_node_ids = {node.node_id for node in wealth_nodes}
    nodes_by_id = {node.node_id: node for node in nodes}
    direct_output_control = any(
        edge.edge_type == MingliGraphEdgeType.CONTROLS
        and nodes_by_id.get(edge.from_node_id) is not None
        and nodes_by_id.get(edge.to_node_id) is not None
        and nodes_by_id[edge.from_node_id].ten_god == "shi_shen"
        and nodes_by_id[edge.to_node_id].ten_god == "qi_sha"
        for edge in edges
    )
    bridge_output_control = any(node.attributes.get("output_converter") for node in nodes) and any(
        node.attributes.get("triple_combination_bridge") for node in nodes
    )
    if direct_output_control or bridge_output_control:
        hints.append("mechanism_hint.output_controls_pressure")
    if any(
        edge.edge_type == MingliGraphEdgeType.GENERATES
        and edge.from_node_id in output_node_ids
        and edge.to_node_id in wealth_node_ids
        for edge in edges
    ):
        hints.append("mechanism_hint.output_to_wealth")
    if MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION in relation_types:
        hints.append("mechanism_hint.combination_bridge")
    return hints or ["mechanism_hint.structural_path"]


def _node_path_contribution(paths: list[MingliPath]) -> dict[str, float]:
    contribution: defaultdict[str, float] = defaultdict(float)
    for path in paths:
        share = path.path_score / max(1, len(path.node_ids))
        for node_id in path.node_ids:
            contribution[node_id] += share
    max_value = max(contribution.values() or [1.0])
    return {node_id: round(value / max_value, 3) for node_id, value in contribution.items()}
