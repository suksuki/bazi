from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DynamicNode:
    node_id: str
    node_type: str
    label: str
    layer: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicEdge:
    edge_id: str
    edge_type: str
    source: str
    target: str
    layer: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicChain:
    chain_key: str
    nodes: tuple[str, ...]
    state: str
    terminal_node: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructureDynamics:
    version: str
    status: str
    source: str
    nodes: tuple[DynamicNode, ...]
    edges: tuple[DynamicEdge, ...]
    dynamic_state: dict[str, Any]
    legacy_dynamic_chain: dict[str, Any]
    chain_state: str
    activated_structures: tuple[dict[str, Any], ...]
    suppressed_structures: tuple[dict[str, Any], ...]
    energy_shift: str
    stability_shift: str
    terminal_node: str
    volatility_score: float
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "SDE_IS_DETERMINISTIC_STRUCTURE_FACT_LAYER",
        "SDE_DOES_NOT_CALL_LLM",
        "SDE_DOES_NOT_MUTATE_RULES_OR_PROFILE",
        "SDE_OUTPUT_IS_DYNAMIC_CONTEXT_NOT_FINAL_VERDICT",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": [row.to_dict() for row in self.nodes],
            "edges": [row.to_dict() for row in self.edges],
            "dynamic_state": self.dynamic_state,
            "legacy_dynamic_chain": self.legacy_dynamic_chain,
            "chain_state": self.chain_state,
            "activated_structures": list(self.activated_structures),
            "suppressed_structures": list(self.suppressed_structures),
            "energy_shift": self.energy_shift,
            "stability_shift": self.stability_shift,
            "terminal_node": self.terminal_node,
            "volatility_score": self.volatility_score,
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }
