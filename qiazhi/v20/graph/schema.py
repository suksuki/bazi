from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChartGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    feature_tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [row.to_dict() for row in self.nodes],
            "edges": [row.to_dict() for row in self.edges],
            "feature_tags": list(self.feature_tags),
        }


@dataclass(frozen=True)
class RulePath:
    path_id: str
    domain: str
    title: str
    score: float
    evidence_refs: tuple[str, ...]
    boundary: str
    runtime_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
