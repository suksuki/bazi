from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

from v17_rebirth.backend.logic.runtime_field_protocol import (
    CORE_GRAPH_DISTANCE_WEIGHTS,
    CORE_GRAPH_POSITION_WEIGHTS,
    DEFAULT_DYNAMIC_EDGE_MODES,
    DEFAULT_DYNAMIC_EDGE_WEIGHTS,
    dynamic_edge_metadata,
)


PillarName = Literal["year", "month", "day", "hour", "luck", "flow"]
NodeKind = Literal["stem", "branch", "hidden_stem"]
EdgeKind = Literal["intra_pillar", "adjacent_pillar", "skip_pillar", "dynamic_trigger", "projection_bridge"]


DEFAULT_POSITION_WEIGHTS: Dict[PillarName, float] = dict(CORE_GRAPH_POSITION_WEIGHTS)

DEFAULT_DISTANCE_WEIGHTS: Dict[int, float] = dict(CORE_GRAPH_DISTANCE_WEIGHTS)


@dataclass(frozen=True)
class PillarNode:
    node_id: str
    pillar: PillarName
    kind: NodeKind
    symbol: str
    position_weight: float


@dataclass(frozen=True)
class PillarEdge:
    source: str
    target: str
    kind: EdgeKind
    weight: float
    distance: int = 0
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class SixPillarGraph:
    nodes: List[PillarNode]
    edges: List[PillarEdge]
    position_weights: Dict[PillarName, float]
    distance_weights: Dict[int, float]


def pillar_distance(a: PillarName, b: PillarName) -> int:
    order = ["year", "month", "day", "hour"]
    if a in {"luck", "flow"} or b in {"luck", "flow"}:
        return 1 if a == b else 2
    return abs(order.index(a) - order.index(b))


def _dynamic_distance(a: PillarName, b: PillarName) -> int:
    pair = (a, b)
    if pair in {
        ("luck", "day"), ("day", "luck"),
        ("luck", "month"), ("month", "luck"),
        ("flow", "day"), ("day", "flow"),
        ("flow", "month"), ("month", "flow"),
        ("luck", "flow"), ("flow", "luck"),
    }:
        return 1
    if pair in {
        ("luck", "hour"), ("hour", "luck"),
        ("flow", "hour"), ("hour", "flow"),
    }:
        return 2
    return 3


def _edge_weight_and_metadata(
    *,
    source: PillarName,
    target: PillarName,
    distance_weights: Dict[int, float],
) -> tuple[float, int, Dict[str, object]]:
    if source in {"luck", "flow"} or target in {"luck", "flow"}:
        dist = _dynamic_distance(source, target)
        weight = float(DEFAULT_DYNAMIC_EDGE_WEIGHTS.get((source, target), distance_weights.get(min(dist, 3), distance_weights[3])))
        metadata = dynamic_edge_metadata(source, target)
        if "coupling_mode" not in metadata:
            metadata["coupling_mode"] = str(DEFAULT_DYNAMIC_EDGE_MODES.get((source, target), "dynamic_trigger"))
        return weight, dist, metadata
    dist = pillar_distance(source, target)
    weight = float(distance_weights.get(min(dist, 3), distance_weights[3]))
    return weight, dist, {}


def build_six_pillar_graph(
    *,
    four_pillars: Dict[str, str],
    luck_pillar: str = "",
    flow_pillar: str = "",
    position_weights: Dict[PillarName, float] | None = None,
    distance_weights: Dict[int, float] | None = None,
) -> SixPillarGraph:
    p_weights = dict(DEFAULT_POSITION_WEIGHTS)
    if position_weights:
        p_weights.update(position_weights)
    d_weights = dict(DEFAULT_DISTANCE_WEIGHTS)
    if distance_weights:
        d_weights.update(distance_weights)

    raw: Dict[PillarName, str] = {
        "year": str(four_pillars.get("year") or "").strip(),
        "month": str(four_pillars.get("month") or "").strip(),
        "day": str(four_pillars.get("day") or "").strip(),
        "hour": str(four_pillars.get("hour") or "").strip(),
        "luck": str(luck_pillar or "").strip(),
        "flow": str(flow_pillar or "").strip(),
    }

    nodes: List[PillarNode] = []
    for pillar, gz in raw.items():
        if len(gz) < 2:
            continue
        nodes.append(PillarNode(node_id=f"{pillar}_stem", pillar=pillar, kind="stem", symbol=gz[0], position_weight=p_weights[pillar]))
        nodes.append(PillarNode(node_id=f"{pillar}_branch", pillar=pillar, kind="branch", symbol=gz[1], position_weight=p_weights[pillar]))

    edges: List[PillarEdge] = []
    stem_nodes = [n for n in nodes if n.kind == "stem"]
    branch_nodes = [n for n in nodes if n.kind == "branch"]

    by_pillar = {n.pillar: n for n in stem_nodes}
    by_branch_pillar = {n.pillar: n for n in branch_nodes}
    for pillar in raw.keys():
        stem = by_pillar.get(pillar)
        branch = by_branch_pillar.get(pillar)
        if stem and branch:
            edges.append(PillarEdge(source=stem.node_id, target=branch.node_id, kind="intra_pillar", weight=1.0, distance=0))
            edges.append(PillarEdge(source=branch.node_id, target=stem.node_id, kind="intra_pillar", weight=1.0, distance=0))

    pillars = [p for p in ("year", "month", "day", "hour", "luck", "flow") if p in by_pillar and p in by_branch_pillar]
    for source in pillars:
        for target in pillars:
            if source == target:
                continue
            weight, dist, metadata = _edge_weight_and_metadata(source=source, target=target, distance_weights=d_weights)
            edge_kind: EdgeKind = "dynamic_trigger" if source in {"luck", "flow"} or target in {"luck", "flow"} else ("adjacent_pillar" if dist == 1 else "skip_pillar")
            edges.append(PillarEdge(source=f"{source}_stem", target=f"{target}_stem", kind=edge_kind, weight=weight, distance=dist, metadata=dict(metadata)))
            edges.append(PillarEdge(source=f"{source}_branch", target=f"{target}_branch", kind=edge_kind, weight=weight, distance=dist, metadata=dict(metadata)))

    return SixPillarGraph(
        nodes=nodes,
        edges=edges,
        position_weights=p_weights,
        distance_weights=d_weights,
    )
