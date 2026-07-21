from __future__ import annotations

from dataclasses import dataclass

from core.graph.contracts import (
    MingliGraph,
    MingliGraphEdgeType,
    PathEligibility,
)
from core.graph.provenance import RelationDirectionality


PATH_QUALIFICATION_POLICY_VERSION = "deepbazi.path-qualification.ra2.v1"

_ELIGIBLE_RELATIONS = {
    MingliGraphEdgeType.GENERATES,
    MingliGraphEdgeType.CONTROLS,
    MingliGraphEdgeType.SAME_ELEMENT_SUPPORT,
    MingliGraphEdgeType.STORES,
    MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION,
}

_EVIDENCE_ONLY_RELATIONS = {
    MingliGraphEdgeType.ROOTS,
    MingliGraphEdgeType.POSITION_LINK,
}


@dataclass(frozen=True)
class WholePathValidation:
    passed: bool
    reason_codes: tuple[str, ...]


def qualify_relation_for_path(
    relation_type: MingliGraphEdgeType,
) -> tuple[PathEligibility, list[str]]:
    if relation_type in _ELIGIBLE_RELATIONS:
        return PathEligibility.ELIGIBLE, [
            PATH_QUALIFICATION_POLICY_VERSION,
            f"path.relation.eligible:{relation_type.value}",
        ]
    if relation_type in _EVIDENCE_ONLY_RELATIONS:
        return PathEligibility.EVIDENCE_ONLY, [
            PATH_QUALIFICATION_POLICY_VERSION,
            f"path.relation.evidence_only:{relation_type.value}",
        ]
    return PathEligibility.NOT_YET_QUALIFIED, [
        PATH_QUALIFICATION_POLICY_VERSION,
        f"path.relation.requires_mechanism:{relation_type.value}",
    ]


def validate_whole_path_candidate(
    graph: MingliGraph,
    *,
    node_ids: tuple[str, ...] | list[str],
    edge_ids: tuple[str, ...] | list[str],
) -> WholePathValidation:
    reasons: list[str] = []
    nodes = list(node_ids)
    edges = list(edge_ids)
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    edges_by_id = {edge.edge_id: edge for edge in graph.edges}

    if len(nodes) < 2:
        reasons.append("path.requires_two_nodes")
    if len(edges) != max(0, len(nodes) - 1):
        reasons.append("path.edge_count_not_contiguous")
    if len(set(nodes)) != len(nodes):
        reasons.append("path.repeated_node")
    if any(node_id not in nodes_by_id for node_id in nodes):
        reasons.append("path.unknown_node")
    if any(edge_id not in edges_by_id for edge_id in edges):
        reasons.append("path.unknown_edge")
    if reasons:
        return WholePathValidation(False, tuple(dict.fromkeys(reasons)))

    for index, edge_id in enumerate(edges):
        edge = edges_by_id[edge_id]
        source = nodes[index]
        target = nodes[index + 1]
        if edge.path_eligibility != PathEligibility.ELIGIBLE:
            reasons.append(f"path.edge_not_eligible:{edge_id}")
            continue
        if edge.directionality == RelationDirectionality.SYMMETRIC:
            participants = set(edge.participant_node_ids)
            if source not in participants or target not in participants:
                reasons.append(f"path.symmetric_edge_not_contiguous:{edge_id}")
        elif edge.from_node_id != source or edge.to_node_id != target:
            reasons.append(f"path.directed_edge_reversed_or_disconnected:{edge_id}")

    return WholePathValidation(not reasons, tuple(dict.fromkeys(reasons)))
