from __future__ import annotations

from typing import Dict, List, Sequence

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, ten_god_from_stems
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import PillarEdge, PillarNode, SixPillarGraph
from v17_rebirth.backend.logic.core_engine.work_path_row_protocol import clamp_value


def node_lookup(graph: SixPillarGraph) -> Dict[str, List[PillarNode]]:
    out: Dict[str, List[PillarNode]] = {}
    for node in graph.nodes:
        out.setdefault(node.symbol, []).append(node)
    return out


def edge_lookup(graph: SixPillarGraph) -> Dict[tuple[str, str], PillarEdge]:
    return {(edge.source, edge.target): edge for edge in graph.edges}


def nodes_for_members(graph: SixPillarGraph, *, members: Sequence[str], layer: str) -> List[PillarNode]:
    if not members:
        return []
    lookup = node_lookup(graph)
    wanted_kinds = {"branch"} if layer == "branch" else {"stem"} if layer == "stem" else {"stem", "branch"}
    out: List[PillarNode] = []
    for member in members:
        for node in lookup.get(str(member).strip(), []):
            if node.kind in wanted_kinds:
                out.append(node)
    return out


def nodes_for_gods(graph: SixPillarGraph, *, gods: Sequence[str], day_master: str) -> List[PillarNode]:
    wanted = {str(god).strip() for god in gods if str(god).strip()}
    if not wanted or not day_master:
        return []
    out: List[PillarNode] = []
    for node in graph.nodes:
        if node.kind == "stem":
            try:
                if ten_god_from_stems(day_master, node.symbol) in wanted:
                    out.append(node)
            except Exception:
                continue
        if node.kind != "branch":
            continue
        for hidden_stem, _hidden_weight in BRANCH_HIDDEN.get(node.symbol, []):
            try:
                if ten_god_from_stems(day_master, hidden_stem) in wanted:
                    out.append(node)
                    break
            except Exception:
                continue
    return out


def avg_position_weight(nodes: Sequence[PillarNode]) -> float:
    if not nodes:
        return 0.48
    return sum(float(node.position_weight) for node in nodes) / max(len(nodes), 1)


def avg_edge_weight(nodes: Sequence[PillarNode], edges: Dict[tuple[str, str], PillarEdge]) -> float:
    if len(nodes) <= 1:
        return 0.72
    weights: List[float] = []
    for left in nodes:
        for right in nodes:
            if left.node_id == right.node_id:
                continue
            edge = edges.get((left.node_id, right.node_id))
            if edge:
                weights.append(float(edge.weight))
    if not weights:
        return 0.58
    return sum(weights) / max(len(weights), 1)


def avg_directed_edge_weight(
    source_nodes: Sequence[PillarNode],
    target_nodes: Sequence[PillarNode],
    edges: Dict[tuple[str, str], PillarEdge],
) -> float:
    if not source_nodes or not target_nodes:
        return 0.72
    weights: List[float] = []
    for source in source_nodes:
        for target in target_nodes:
            if source.node_id == target.node_id:
                weights.append(1.0)
                continue
            edge = edges.get((source.node_id, target.node_id))
            if edge:
                weights.append(float(edge.weight))
    if not weights:
        return 0.58
    return sum(weights) / max(len(weights), 1)


def directional_factor(
    *,
    actor_nodes: Sequence[PillarNode],
    receiver_nodes: Sequence[PillarNode],
    edges: Dict[tuple[str, str], PillarEdge],
) -> tuple[float, float, float, float, float]:
    if not actor_nodes or not receiver_nodes:
        return 1.0, 0.0, 0.0, 0.0, 0.0
    actor_position = avg_position_weight(actor_nodes)
    receiver_position = avg_position_weight(receiver_nodes)
    directed_edge = avg_directed_edge_weight(actor_nodes, receiver_nodes, edges)
    factor = clamp_value(
        0.72 + actor_position * 0.16 + receiver_position * 0.12 + directed_edge * 0.18,
        0.84,
        1.28,
    )
    return factor, actor_position, receiver_position, directed_edge, (actor_position + receiver_position) / 2.0


def dynamic_factor(nodes: Sequence[PillarNode]) -> float:
    if not nodes:
        return 1.0
    boost = 1.0
    if any(node.pillar == "luck" for node in nodes):
        boost += 0.16
    if any(node.pillar == "flow" for node in nodes):
        boost += 0.08
    return boost


__all__ = [
    "avg_edge_weight",
    "avg_position_weight",
    "directional_factor",
    "dynamic_factor",
    "edge_lookup",
    "node_lookup",
    "nodes_for_gods",
    "nodes_for_members",
]
