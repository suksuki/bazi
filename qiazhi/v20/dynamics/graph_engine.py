from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from v20.core.constants import CONTROLS, GENERATES
from v20.core.schemas import ChartFacts, TenGodPosition, TimeContext
from v20.knowledge.structure_mechanisms import match_structure_path_mechanisms
from v20.storage.local_jsonl import local_jsonl_store_from_env


SDE_GRAPH_VERSION = "v20.structure_dynamics_graph.v2"

TEN_GOD_FAMILY = {
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "authority",
    "七杀": "authority",
    "正印": "resource",
    "偏印": "resource",
    "比肩": "self",
    "劫财": "self",
}

FAMILY_LABEL = {
    "output": "食伤",
    "wealth": "财星",
    "authority": "官杀",
    "resource": "印星",
    "self": "比劫",
    "day_master": "日主",
}

EDGE_LABEL = {
    "generate": "相生",
    "control": "制约",
    "support_day_master": "承接日主",
    "pressure_day_master": "压向日主",
    "same_family": "同气",
    "time_activate": "岁运引动",
}

STRUCTURE_DYNAMICS_ACTIVE_POINTER_VERSION = "v20.structure_dynamics_runtime_active_pointer.v1"
STRUCTURE_DYNAMICS_POINTER_RELATIVE_PATH = "training/structure_dynamics_policy_versions/active_pointer.json"


@dataclass(frozen=True)
class RuntimeStructurePolicy:
    active_policy_version: str = "v20.structure_dynamics_policy.baseline.v1"
    source: str = "baseline"
    runtime_applied: bool = False
    direct_action_priority_weight: float = 0.0
    continuity_bonus_weight: float = 0.08
    blockage_penalty_weight: float = 0.18
    terminal_convergence_weight: float = 0.12
    semantic_match_threshold: float = 0.0

    def to_report(self) -> dict[str, Any]:
        return {
            "version": "v20.structure_dynamics_runtime_policy_consumption.v1",
            "status": "active_policy_applied" if self.runtime_applied else "baseline",
            "active_policy_version": self.active_policy_version,
            "source": self.source,
            "runtime_applied": self.runtime_applied,
            "weights": {
                "direct_action_priority_weight": self.direct_action_priority_weight,
                "continuity_bonus_weight": self.continuity_bonus_weight,
                "blockage_penalty_weight": self.blockage_penalty_weight,
                "terminal_convergence_weight": self.terminal_convergence_weight,
                "semantic_match_threshold": self.semantic_match_threshold,
            },
            "runtime_mutation": False,
        }


@dataclass(frozen=True)
class DynamicGraphNode:
    node_id: str
    label: str
    family: str
    element: str
    layer: str
    source: str
    weight: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicGraphEdge:
    source: str
    target: str
    edge_type: str
    label: str
    weight: float
    role: str = "continuity"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicGraphPath:
    path_id: str
    node_ids: tuple[str, ...]
    node_labels: tuple[str, ...]
    family_chain: tuple[str, ...]
    edge_types: tuple[str, ...]
    edge_labels: tuple[str, ...]
    score: float
    state: str
    terminal: str
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_structure_dynamic_graph_report(chart_facts: ChartFacts, time_context: TimeContext) -> dict[str, Any]:
    runtime_policy = _load_runtime_structure_policy()
    nodes = _build_nodes(chart_facts, time_context)
    edges = _build_edges(nodes, chart_facts, time_context)
    paths = _extract_paths(nodes, edges, runtime_policy=runtime_policy)
    dominant = paths[0] if paths else None
    semantics = _semantic_candidates(paths, runtime_policy=runtime_policy)
    dominant_chain = _dominant_chain_candidate(paths, semantics)
    semantics = _semantic_candidates_with_primary_chain(semantics, dominant_chain, runtime_policy=runtime_policy)
    return {
        "version": SDE_GRAPH_VERSION,
        "algorithm": "weighted_dynamic_graph_path_extraction_v2_primary",
        "runtime_policy": runtime_policy.to_report(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "path_count": len(paths),
        "nodes": [node.to_dict() for node in nodes],
        "edges": [edge.to_dict() for edge in edges],
        "dominant_path": dominant.to_dict() if dominant else {},
        "dominant_chain_candidate": dominant_chain,
        "candidate_paths": [path.to_dict() for path in paths[:5]],
        "semantic_candidates": semantics,
        "path_diagnostics": _path_diagnostics(paths, edges, semantics, time_context),
        "guardrails": [
            "SDE_V2_GRAPH_IS_DETERMINISTIC",
            "SDE_V2_GRAPH_DOES_NOT_CALL_LLM",
            "SDE_V2_GRAPH_USES_CURRENT_BAZI_AND_TIME_CONTEXT_ONLY",
            "SDE_V2_SEMANTICS_NAME_EXTRACTED_PATHS_ONLY",
        ],
        "runtime_mutation": False,
    }


def _build_nodes(chart_facts: ChartFacts, time_context: TimeContext) -> tuple[DynamicGraphNode, ...]:
    rows: list[DynamicGraphNode] = [
        DynamicGraphNode(
            node_id="day_master",
            label=f"{chart_facts.day_master}日主",
            family="day_master",
            element=chart_facts.day_master_element,
            layer="natal",
            source="day_master",
            weight=1.0,
        )
    ]
    for row in chart_facts.visible_ten_gods:
        rows.append(_node_from_ten_god(row, prefix="visible", base_weight=0.9))
    for row in chart_facts.hidden_ten_gods:
        if float(row.weight or 0.0) < 0.15:
            continue
        rows.append(_node_from_ten_god(row, prefix="hidden", base_weight=0.42 * float(row.weight or 0.0)))
    for layer in time_context.layers:
        rows.append(_node_from_ten_god(layer.ten_god, prefix=f"time.{layer.layer_key}", base_weight=0.76))
    return tuple(_dedupe_nodes(rows))


def _node_from_ten_god(row: TenGodPosition, *, prefix: str, base_weight: float) -> DynamicGraphNode:
    family = TEN_GOD_FAMILY.get(row.label, "unknown")
    source = f"{row.layer}:{row.pillar}:{row.stem}"
    return DynamicGraphNode(
        node_id=f"{prefix}.{row.pillar}.{row.stem}.{row.label}",
        label=f"{row.stem}{row.label}",
        family=family,
        element=row.element,
        layer=row.layer,
        source=source,
        weight=round(min(1.0, base_weight), 4),
    )


def _dedupe_nodes(nodes: list[DynamicGraphNode]) -> list[DynamicGraphNode]:
    seen: set[str] = set()
    rows: list[DynamicGraphNode] = []
    for node in nodes:
        if node.node_id in seen:
            continue
        seen.add(node.node_id)
        rows.append(node)
    return rows


def _build_edges(
    nodes: tuple[DynamicGraphNode, ...],
    chart_facts: ChartFacts,
    time_context: TimeContext,
) -> tuple[DynamicGraphEdge, ...]:
    rows: list[DynamicGraphEdge] = []
    action_nodes = tuple(node for node in nodes if node.family not in {"day_master", "unknown"})
    for source in action_nodes:
        for target in action_nodes:
            if source.node_id == target.node_id:
                continue
            edge = _element_edge(source, target)
            if edge:
                rows.append(edge)
        if source.element == chart_facts.day_master_element:
            rows.append(DynamicGraphEdge(source.node_id, "day_master", "same_family", EDGE_LABEL["same_family"], 0.5, "continuity"))
        if GENERATES.get(source.element) == chart_facts.day_master_element:
            rows.append(
                DynamicGraphEdge(source.node_id, "day_master", "support_day_master", EDGE_LABEL["support_day_master"], 0.72, "continuity")
            )
        if CONTROLS.get(source.element) == chart_facts.day_master_element:
            rows.append(
                DynamicGraphEdge(source.node_id, "day_master", "pressure_day_master", EDGE_LABEL["pressure_day_master"], 0.58, "pressure")
            )
    for layer in time_context.layers:
        time_id = f"time.{layer.layer_key}.{layer.ten_god.pillar}.{layer.ten_god.stem}.{layer.ten_god.label}"
        for node in action_nodes:
            if node.node_id == time_id:
                continue
            if node.family == TEN_GOD_FAMILY.get(layer.ten_god.label, "") or node.element == layer.ten_god.element:
                rows.append(DynamicGraphEdge(time_id, node.node_id, "time_activate", EDGE_LABEL["time_activate"], 0.62, "activation"))
    return tuple(_dedupe_edges(rows))


def _element_edge(source: DynamicGraphNode, target: DynamicGraphNode) -> DynamicGraphEdge | None:
    if GENERATES.get(source.element) == target.element:
        return DynamicGraphEdge(source.node_id, target.node_id, "generate", EDGE_LABEL["generate"], 0.68, "continuity")
    if CONTROLS.get(source.element) == target.element:
        return DynamicGraphEdge(
            source.node_id,
            target.node_id,
            "control",
            EDGE_LABEL["control"],
            0.64,
            _control_role(source.family, target.family),
        )
    return None


def _control_role(source_family: str, target_family: str) -> str:
    if source_family == "output" and target_family == "authority":
        return "continuity"
    if source_family == "authority" and target_family in {"self", "day_master"}:
        return "pressure"
    return "blockage"


def _dedupe_edges(edges: list[DynamicGraphEdge]) -> list[DynamicGraphEdge]:
    seen: set[tuple[str, str, str]] = set()
    rows: list[DynamicGraphEdge] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.edge_type)
        if key in seen:
            continue
        seen.add(key)
        rows.append(edge)
    return rows


def _extract_paths(
    nodes: tuple[DynamicGraphNode, ...],
    edges: tuple[DynamicGraphEdge, ...],
    *,
    runtime_policy: RuntimeStructurePolicy,
) -> tuple[DynamicGraphPath, ...]:
    by_id = {node.node_id: node for node in nodes}
    adjacency: dict[str, list[DynamicGraphEdge]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source, []).append(edge)
    starts = tuple(
        node for node in nodes
        if node.family not in {"day_master", "unknown"} and (node.layer in {"visible", "time"} or node.weight >= 0.25)
    )
    raw_paths: list[tuple[str, ...]] = []
    for start in starts:
        _walk_paths(start.node_id, adjacency, ("day_master",), (start.node_id,), raw_paths, max_depth=4)
    scored = [_path_from_ids(index + 1, ids, by_id, adjacency, runtime_policy=runtime_policy) for index, ids in enumerate(raw_paths)]
    scored = [path for path in scored if len(path.family_chain) >= 2]
    scored.sort(key=lambda row: (row.score, _path_action_priority(row), _state_priority(row.state), len(row.node_ids)), reverse=True)
    return tuple(_dedupe_paths(scored)[:8])


def _walk_paths(
    current: str,
    adjacency: dict[str, list[DynamicGraphEdge]],
    terminals: tuple[str, ...],
    path: tuple[str, ...],
    output: list[tuple[str, ...]],
    *,
    max_depth: int,
) -> None:
    if len(path) >= 2 and (current in terminals or len(path) >= max_depth):
        output.append(path)
    if len(path) >= max_depth or current in terminals:
        return
    for edge in sorted(adjacency.get(current, ()), key=lambda row: row.weight, reverse=True)[:8]:
        if edge.target in path:
            continue
        _walk_paths(edge.target, adjacency, terminals, (*path, edge.target), output, max_depth=max_depth)


def _path_from_ids(
    index: int,
    ids: tuple[str, ...],
    by_id: dict[str, DynamicGraphNode],
    adjacency: dict[str, list[DynamicGraphEdge]],
    *,
    runtime_policy: RuntimeStructurePolicy,
) -> DynamicGraphPath:
    nodes = tuple(by_id[node_id] for node_id in ids)
    edge_rows = tuple(_find_edge(left, right, adjacency) for left, right in zip(ids, ids[1:]))
    edge_rows = tuple(row for row in edge_rows if row)
    family_chain = tuple(_compact_families(node.family for node in nodes))
    node_strength = sum(node.weight for node in nodes) / max(1, len(nodes))
    edge_strength = sum(edge.weight for edge in edge_rows) / max(1, len(edge_rows))
    visibility = 0.08 * sum(1 for node in nodes if node.layer in {"visible", "time"})
    terminal_bonus = runtime_policy.terminal_convergence_weight if ids[-1] == "day_master" else 0.04
    continuity = 0.04 * max(0, len(edge_rows) - 1)
    continuity_bonus = runtime_policy.continuity_bonus_weight * sum(1 for edge in edge_rows if edge.role == "continuity")
    blockage_penalty = runtime_policy.blockage_penalty_weight * sum(1 for edge in edge_rows if edge.role == "blockage")
    pressure_penalty = 0.04 * sum(1 for edge in edge_rows if edge.role == "pressure" and ids[-1] != "day_master")
    direct_action_bonus = runtime_policy.direct_action_priority_weight if _has_direct_action_pair(_compact_families(node.family for node in nodes)) else 0.0
    score = round(
        max(
            0.0,
            min(
                1.0,
                node_strength * 0.34
                + edge_strength * 0.28
                + visibility
                + terminal_bonus
                + continuity
                + continuity_bonus
                + direct_action_bonus
                - blockage_penalty
                - pressure_penalty,
            ),
        ),
        4,
    )
    return DynamicGraphPath(
        path_id=f"dynamic_path.{index}",
        node_ids=ids,
        node_labels=tuple(node.label for node in nodes),
        family_chain=family_chain,
        edge_types=tuple(edge.edge_type for edge in edge_rows),
        edge_labels=tuple(edge.label for edge in edge_rows),
        score=score,
        state=_path_state(ids, edge_rows),
        terminal=nodes[-1].label,
        evidence=tuple(_path_evidence(nodes, edge_rows)),
    )


def _compact_families(families: Any) -> tuple[str, ...]:
    rows: list[str] = []
    for family in families:
        if family == "unknown":
            continue
        if rows and rows[-1] == family:
            continue
        rows.append(family)
    return tuple(rows)


def _find_edge(source: str, target: str, adjacency: dict[str, list[DynamicGraphEdge]]) -> DynamicGraphEdge | None:
    for edge in adjacency.get(source, ()):
        if edge.target == target:
            return edge
    return None


def _path_state(ids: tuple[str, ...], edges: tuple[DynamicGraphEdge, ...]) -> str:
    if any(edge.role == "blockage" for edge in edges):
        return "blocked"
    if any(edge.edge_type == "time_activate" for edge in edges):
        return "volatile"
    if ids[-1] == "day_master" and len(ids) >= 3:
        return "closed"
    if ids[-1] == "day_master":
        return "partial"
    if any(edge.edge_type == "control" for edge in edges):
        return "partial"
    return "leaking"


def _state_priority(state: str) -> int:
    return {
        "closed": 5,
        "volatile": 4,
        "partial": 3,
        "leaking": 2,
        "blocked": 1,
        "collapsed": 0,
    }.get(state, 0)


def _path_action_priority(path: DynamicGraphPath) -> int:
    pairs = set(zip(path.family_chain, path.family_chain[1:]))
    if ("output", "authority") in pairs:
        return 7
    if ("output", "wealth") in pairs:
        return 6
    if ("wealth", "authority") in pairs:
        return 5
    if ("authority", "resource") in pairs:
        return 4
    if ("self", "wealth") in pairs:
        return 4
    if ("wealth", "resource") in pairs:
        return 4
    if ("resource", "output") in pairs:
        return 4
    if ("resource", "self") in pairs:
        return 3
    if ("self", "output") in pairs:
        return 2
    return 1


def _has_direct_action_pair(family_chain: tuple[str, ...]) -> bool:
    pairs = set(zip(family_chain, family_chain[1:]))
    return bool(
        {
            ("output", "authority"),
            ("output", "wealth"),
            ("wealth", "authority"),
            ("authority", "resource"),
            ("self", "wealth"),
            ("wealth", "resource"),
            ("resource", "output"),
        } & pairs
    )


def _path_evidence(nodes: tuple[DynamicGraphNode, ...], edges: tuple[DynamicGraphEdge, ...]) -> list[str]:
    rows = [f"{node.label}:{FAMILY_LABEL.get(node.family, node.family)}:{node.layer}" for node in nodes]
    rows.extend(f"{edge.label}:{edge.edge_type}:{edge.role}" for edge in edges)
    return rows


def _dedupe_paths(paths: list[DynamicGraphPath]) -> list[DynamicGraphPath]:
    seen: set[tuple[str, ...]] = set()
    rows: list[DynamicGraphPath] = []
    for path in paths:
        key = path.family_chain
        if key in seen:
            continue
        seen.add(key)
        rows.append(path)
    return rows


def _semantic_candidates(paths: tuple[DynamicGraphPath, ...], *, runtime_policy: RuntimeStructurePolicy) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths[:5]:
        candidates = _semantics_for_path(path)
        for candidate in candidates:
            if float(candidate.get("confidence", 0.0) or 0.0) < runtime_policy.semantic_match_threshold:
                continue
            candidate["path_id"] = path.path_id
            candidate["path_score"] = path.score
            candidate["runtime_semantic_threshold"] = runtime_policy.semantic_match_threshold
            rows.append(candidate)
    rows.sort(
        key=lambda row: (
            float(row.get("confidence", 0.0)),
            int(row.get("priority", 0) or 0),
            float(row.get("path_score", 0.0)),
        ),
        reverse=True,
    )
    return rows[:8]


def _semantic_candidates_with_primary_chain(
    semantics: list[dict[str, Any]],
    dominant_chain: dict[str, Any],
    *,
    runtime_policy: RuntimeStructurePolicy,
) -> list[dict[str, Any]]:
    label = str(dominant_chain.get("pattern_label", "") or "")
    path_id = str(dominant_chain.get("path_id", "") or "")
    if not label or label in {"核心做功链", "暂未形成清晰结构主链"}:
        return semantics
    for row in semantics:
        if str(row.get("label", "") or "") == label and str(row.get("path_id", "") or "") == path_id:
            return semantics
    primary_row = {
        "semantic_key": str(dominant_chain.get("pattern_key", "knowledge.semantic.dynamic_path") or "knowledge.semantic.dynamic_path"),
        "label": label,
        "confidence": float(dominant_chain.get("confidence", 0.0) or 0.0),
        "matched_path": list(dominant_chain.get("node_labels", ()) or ()),
        "boundary": str(dominant_chain.get("pattern_summary", "") or "由结构动态图提取的核心通路候选。"),
        "mechanism_source": "knowledge.structure_mechanisms",
        "priority": 0,
        "path_id": path_id,
        "path_score": float(dominant_chain.get("path_score", 0.0) or 0.0),
        "runtime_semantic_threshold": runtime_policy.semantic_match_threshold,
        "below_runtime_threshold_primary": dominant_chain.get("selection_basis") == "dominant_path_mechanism_below_runtime_threshold",
    }
    return [primary_row, *semantics][:8]


def _dominant_chain_candidate(paths: tuple[DynamicGraphPath, ...], semantics: list[dict[str, Any]]) -> dict[str, Any]:
    if not paths:
        return {
            "chain_key": "empty",
            "nodes": [],
            "state": "empty",
            "terminal_node": "",
            "pattern_key": "empty",
            "pattern_label": "暂未形成清晰结构主链",
            "path_id": "",
            "selection_basis": "no_path",
            "confidence": 0.0,
            "evidence": [],
        }
    by_path = {path.path_id: path for path in paths}
    dominant = paths[0]
    semantic = next((row for row in semantics if row.get("path_id") == dominant.path_id), None)
    selection_basis = "dominant_path_semantic"
    if semantic is not None and semantics:
        top_semantic = semantics[0]
        semantic_confidence = float(semantic.get("confidence", 0.0) or 0.0)
        top_confidence = float(top_semantic.get("confidence", 0.0) or 0.0)
        semantic_priority = int(semantic.get("priority", 0) or 0)
        top_priority = int(top_semantic.get("priority", 0) or 0)
        if top_confidence > semantic_confidence or (top_confidence == semantic_confidence and top_priority > semantic_priority):
            semantic = top_semantic
            dominant = by_path.get(str(semantic.get("path_id", "")), dominant)
            selection_basis = "top_specific_semantic_candidate"
    if semantic is None:
        raw_semantics = _semantics_for_path(dominant)
        if raw_semantics:
            semantic = raw_semantics[0]
            selection_basis = "dominant_path_mechanism_below_runtime_threshold"
    if semantic is None and semantics:
        semantic = semantics[0]
        dominant = by_path.get(str(semantic.get("path_id", "")), dominant)
        selection_basis = "top_semantic_candidate"
    nodes = _compat_chain_nodes(dominant.family_chain)
    return {
        "chain_key": "->".join(nodes) if nodes else "empty",
        "nodes": list(nodes),
        "state": dominant.state,
        "terminal_node": nodes[-1] if nodes else "",
        "pattern_key": str(semantic.get("semantic_key", "knowledge.semantic.dynamic_path")) if semantic else "knowledge.semantic.dynamic_path",
        "pattern_label": str(semantic.get("label", "核心做功链")) if semantic else "核心做功链",
        "pattern_summary": str(semantic.get("boundary", "由结构动态图提取的核心通路候选。")) if semantic else "由结构动态图提取的核心通路候选。",
        "path_id": dominant.path_id,
        "path_score": dominant.score,
        "confidence": float(semantic.get("confidence", dominant.score)) if semantic else dominant.score,
        "selection_basis": selection_basis,
        "node_labels": list(dominant.node_labels),
        "edge_labels": list(dominant.edge_labels),
        "evidence": list(dominant.evidence[:10]),
    }


def _path_diagnostics(
    paths: tuple[DynamicGraphPath, ...],
    edges: tuple[DynamicGraphEdge, ...],
    semantics: list[dict[str, Any]],
    time_context: TimeContext,
) -> dict[str, Any]:
    blockers = _time_relation_blockers(time_context)
    return {
        "candidate_path_count": len(paths),
        "blocked_edge_count": sum(1 for edge in edges if edge.role == "blockage"),
        "activation_edge_count": sum(1 for edge in edges if edge.role == "activation"),
        "continuity_edge_count": sum(1 for edge in edges if edge.role == "continuity"),
        "time_relation_blocker_count": len(blockers),
        "time_relation_blockers": blockers,
        "top_path_states": [
            {"path_id": path.path_id, "state": path.state, "score": path.score}
            for path in paths[:5]
        ],
        "top_semantics": [
            {
                "path_id": str(row.get("path_id", "")),
                "label": str(row.get("label", "")),
                "confidence": row.get("confidence", 0.0),
            }
            for row in semantics[:5]
        ],
    }


def _time_relation_blockers(time_context: TimeContext) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for hit in time_context.relation_hits:
        if hit.relation_type not in {"clash", "break", "punishment", "harm"}:
            continue
        time_positions = tuple(position for position in hit.positions if str(position).startswith("flow_") or position == "luck")
        if not time_positions:
            continue
        rows.append(
            {
                "relation_type": hit.relation_type,
                "branches": list(hit.branches),
                "positions": list(hit.positions),
                "time_positions": list(time_positions),
                "boundary": "岁运关系只作为结构波动和阻断证据，不直接推出具体事件或吉凶。",
            }
        )
    return rows


def _compat_chain_nodes(family_chain: tuple[str, ...]) -> tuple[str, ...]:
    nodes = tuple(family for family in family_chain if family not in {"day_master", "unknown"})
    if len(nodes) <= 3:
        return nodes
    if "resource" in nodes and "self" in nodes:
        nodes = tuple(family for family in nodes if family != "self")
    return nodes[:3]


def _semantics_for_path(path: DynamicGraphPath) -> list[dict[str, Any]]:
    return match_structure_path_mechanisms(
        family_chain=path.family_chain,
        node_labels=path.node_labels,
        path_score=path.score,
    )


def _load_runtime_structure_policy() -> RuntimeStructurePolicy:
    if os.getenv("V20_STRUCTURE_DYNAMICS_DISABLE_RUNTIME_POLICY") == "1":
        return RuntimeStructurePolicy(source="runtime_policy_disabled_for_validation")
    pointer = _read_active_structure_pointer()
    payload = pointer.get("policy_payload", {}) if isinstance(pointer.get("policy_payload"), dict) else {}
    dynamic_policy = payload.get("dynamic_path_weight_policy", {}) if isinstance(payload.get("dynamic_path_weight_policy"), dict) else {}
    semantic_policy = payload.get("semantic_match_policy", {}) if isinstance(payload.get("semantic_match_policy"), dict) else {}
    if not payload:
        return RuntimeStructurePolicy()
    return RuntimeStructurePolicy(
        active_policy_version=str(pointer.get("active_policy_version", "")) or "v20.structure_dynamics_policy.baseline.v1",
        source=str(pointer.get("source", "")) or "active_pointer",
        runtime_applied=True,
        direct_action_priority_weight=_bounded_float(dynamic_policy.get("direct_action_priority_weight"), 0.0, 0.0, 0.16),
        continuity_bonus_weight=_bounded_float(dynamic_policy.get("continuity_bonus_weight"), 0.08, 0.0, 0.16),
        blockage_penalty_weight=_bounded_float(dynamic_policy.get("blockage_penalty_weight"), 0.18, 0.02, 0.32),
        terminal_convergence_weight=_bounded_float(dynamic_policy.get("terminal_convergence_weight"), 0.12, 0.0, 0.20),
        semantic_match_threshold=_bounded_float(semantic_policy.get("semantic_match_threshold"), 0.0, 0.0, 0.96),
    )


def _read_active_structure_pointer() -> dict[str, Any]:
    try:
        path = local_jsonl_store_from_env().runtime_dir / STRUCTURE_DYNAMICS_POINTER_RELATIVE_PATH
    except Exception:
        return {}
    if not Path(path).exists():
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != STRUCTURE_DYNAMICS_ACTIVE_POINTER_VERSION or payload.get("status") != "candidate_active":
        return {}
    if not isinstance(payload.get("policy_payload"), dict):
        return {}
    return payload


def _bounded_float(value: object, fallback: float, low: float, high: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = fallback
    return round(max(low, min(high, number)), 4)
