from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence

from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import branches_and_stems_from_runtime_pillars
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import PillarEdge, PillarNode, SixPillarGraph
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import WORK_EVIDENCE_KEY


@dataclass(frozen=True)
class WorkPath:
    path_id: str
    target_god: str
    path_type: str
    participants: List[str]
    origin_scope: str
    activation: float
    transmission: float
    loss: float
    stability: float
    net_effect: float
    evidence: Dict[str, object] = field(default_factory=dict)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(fallback)


def _sign_from_effect(effect_type: str, impact_ratio: float) -> int:
    normalized = str(effect_type or "").strip().lower()
    if impact_ratio > 0:
        return 1
    if impact_ratio < 0:
        return -1
    if normalized in {"benefit", "release", "transform", "support", "bind"}:
        return 1
    if normalized in {"harm", "storage", "stuck", "disrupt", "clash"}:
        return -1
    return 0


def _relation_factor(relation_family: str, effect_type: str) -> float:
    family = str(relation_family or "").strip().lower()
    effect = str(effect_type or "").strip().lower()
    family_weights = {
        "sanhe": 1.32,
        "banhe": 1.18,
        "liuhe": 1.12,
        "liu_chong": 1.18,
        "liupo": 1.08,
        "liuhai": 1.06,
        "muku": 1.04,
        "stem_fusion": 1.16,
    }
    factor = family_weights.get(family, 1.0)
    if effect in {"transform", "release"}:
        factor += 0.08
    if effect in {"harm", "stuck", "storage"}:
        factor += 0.04
    return factor


def _origin_factor(origin_scope: str) -> float:
    normalized = str(origin_scope or "").strip().lower()
    if normalized == "luck":
        return 1.16
    if normalized == "flow":
        return 0.84
    if normalized in {"runtime", "mixed"}:
        return 1.08
    return 1.0


def _layer_factor(layer: str) -> float:
    normalized = str(layer or "").strip().lower()
    if normalized == "branch":
        return 1.0
    if normalized == "stem":
        return 0.84
    if normalized == "cross_layer":
        return 0.76
    if normalized == "hidden":
        return 0.68
    return 0.74


def _condition_factor(condition_state: str) -> float:
    normalized = str(condition_state or "").strip().lower()
    if normalized in {"formed", "supported", "manifested", "open"}:
        return 1.12
    if normalized in {"latent"}:
        return 0.82
    if normalized in {"contested", "blocked"}:
        return 0.72
    if normalized in {"stuck", "closed"}:
        return 0.76
    return 0.92


def _node_lookup(graph: SixPillarGraph) -> Dict[str, List[PillarNode]]:
    out: Dict[str, List[PillarNode]] = {}
    for node in graph.nodes:
        out.setdefault(node.symbol, []).append(node)
    return out


def _edge_lookup(graph: SixPillarGraph) -> Dict[tuple[str, str], PillarEdge]:
    return {(edge.source, edge.target): edge for edge in graph.edges}


def _nodes_for_members(graph: SixPillarGraph, *, members: Sequence[str], layer: str) -> List[PillarNode]:
    if not members:
        return []
    lookup = _node_lookup(graph)
    wanted_kinds = {"branch"} if layer == "branch" else {"stem"} if layer == "stem" else {"stem", "branch"}
    out: List[PillarNode] = []
    for member in members:
        for node in lookup.get(str(member).strip(), []):
            if node.kind in wanted_kinds:
                out.append(node)
    return out


def _avg_position_weight(nodes: Sequence[PillarNode]) -> float:
    if not nodes:
        return 0.48
    return sum(float(node.position_weight) for node in nodes) / max(len(nodes), 1)


def _avg_edge_weight(nodes: Sequence[PillarNode], edges: Dict[tuple[str, str], PillarEdge]) -> float:
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


def _dynamic_factor(nodes: Sequence[PillarNode]) -> float:
    if not nodes:
        return 1.0
    boost = 1.0
    if any(node.pillar == "luck" for node in nodes):
        boost += 0.16
    if any(node.pillar == "flow" for node in nodes):
        boost += 0.08
    return boost


def _legacy_members(impact: Dict[str, Any]) -> List[str]:
    work = impact.get(WORK_EVIDENCE_KEY) if isinstance(impact.get(WORK_EVIDENCE_KEY), dict) else {}
    members = work.get("members") if isinstance(work, dict) else None
    if isinstance(members, list):
        cleaned = [str(item).strip() for item in members if str(item).strip()]
        if cleaned:
            return cleaned
    pair = impact.get("clash_pair")
    if isinstance(pair, list):
        cleaned = [str(item).strip() for item in pair if str(item).strip()]
        if cleaned:
            return cleaned
    return []


def _normalize_row_evidence(row: Dict[str, Any]) -> Dict[str, Any]:
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    work = impact.get(WORK_EVIDENCE_KEY) if isinstance(impact.get(WORK_EVIDENCE_KEY), dict) else {}
    target = str(row.get("target_god") or impact.get("target_god") or work.get("target_god") or "").strip()
    relation_family = str(
        work.get("relation_family")
        or impact.get("relation_family")
        or row.get("source")
        or row.get("plugin_id")
        or "unknown"
    ).strip()
    impact_ratio = _safe_float(work.get("impact_ratio", impact.get("impact_ratio", 0.0)))
    match_ratio = _clamp(_safe_float(work.get("match_ratio", impact.get("match_ratio", 0.0))), 0.0, 1.0)
    condition_state = str(work.get("condition_state") or impact.get("condition_state") or "").strip()
    layer = str(work.get("layer") or impact.get("interaction_layer") or "unknown").strip()
    origin_scope = str(work.get("origin_scope") or impact.get("origin_type") or "natal").strip()
    effect_type = str(work.get("effect_type") or "").strip()
    significance = _safe_float(impact.get("significance_weight", 1.0), 1.0)
    path_strength = _safe_float(
        work.get("path_strength"),
        abs(impact_ratio) * max(0.45, match_ratio) * max(0.75, significance),
    )
    return {
        "row_id": str(row.get("id") or "").strip(),
        "target_god": target,
        "relation_family": relation_family,
        "effect_type": effect_type,
        "members": _legacy_members(impact),
        "origin_scope": origin_scope,
        "layer": layer,
        "condition_state": condition_state,
        "impact_ratio": impact_ratio,
        "match_ratio": match_ratio,
        "path_strength": max(0.0, path_strength),
        "significance_weight": significance,
        "source": str(row.get("source") or row.get("plugin_id") or relation_family).strip(),
    }


def _basis_path(
    *,
    graph: SixPillarGraph,
    god: str,
    score: float,
    max_score: float,
    positive_hint: float,
    negative_hint: float,
) -> WorkPath:
    graph_density = min(1.0, len(graph.edges) / max(len(graph.nodes), 1) / 8.0)
    activation = max(float(score or 0.0), 0.0) / max(max_score, 1.0)
    transmission = 0.46 + graph_density * 0.22
    loss = min(0.66, max(0.0, negative_hint * 0.32))
    stability = _clamp(0.52 + positive_hint * 0.08 - negative_hint * 0.1, 0.2, 1.0)
    net_effect = activation * transmission * stability * (1.0 - loss) + positive_hint * 0.45 - negative_hint * 0.55
    return WorkPath(
        path_id=f"basis_{god}",
        target_god=god,
        path_type="static_basis",
        participants=[god],
        origin_scope="natal_basis",
        activation=round(activation, 4),
        transmission=round(transmission, 4),
        loss=round(loss, 4),
        stability=round(stability, 4),
        net_effect=round(net_effect, 4),
        evidence={
            "positive_hint": round(positive_hint, 4),
            "negative_hint": round(negative_hint, 4),
            "graph_edges": len(graph.edges),
        },
    )


def build_work_paths(
    *,
    graph: SixPillarGraph,
    deity_scores: Dict[str, float],
    decision_rows: Iterable[Dict[str, object]] | None = None,
) -> List[WorkPath]:
    rows = [dict(row) for row in (decision_rows or []) if isinstance(row, dict)]
    positive_hint, negative_hint = collect_effect_maps(rows)
    max_score = max([float(v or 0.0) for v in deity_scores.values()] or [1.0])
    edge_index = _edge_lookup(graph)

    out: List[WorkPath] = []
    for row in rows:
        normalized = _normalize_row_evidence(row)
        target_god = str(normalized.get("target_god") or "").strip()
        if not target_god:
            continue
        base_score = max(float(deity_scores.get(target_god, 0.0) or 0.0), 0.0)
        base_activation = base_score / max(max_score, 1.0)
        member_nodes = _nodes_for_members(
            graph,
            members=list(normalized.get("members") or []),
            layer=str(normalized.get("layer") or "unknown"),
        )
        member_position = _avg_position_weight(member_nodes)
        member_edges = _avg_edge_weight(member_nodes, edge_index)
        relation_factor = _relation_factor(
            relation_family=str(normalized.get("relation_family") or ""),
            effect_type=str(normalized.get("effect_type") or ""),
        )
        origin_factor = _origin_factor(str(normalized.get("origin_scope") or "natal"))
        layer_factor = _layer_factor(str(normalized.get("layer") or "unknown"))
        condition_factor = _condition_factor(str(normalized.get("condition_state") or ""))
        dynamic_factor = _dynamic_factor(member_nodes)
        path_strength = _safe_float(normalized.get("path_strength"), 0.0)
        match_ratio = _clamp(_safe_float(normalized.get("match_ratio"), 0.0), 0.0, 1.0)
        impact_ratio = _safe_float(normalized.get("impact_ratio"), 0.0)
        sign = _sign_from_effect(str(normalized.get("effect_type") or ""), impact_ratio)

        activation = _clamp(base_activation * (0.7 + path_strength * 0.65) * dynamic_factor, 0.02, 1.3)
        transmission = _clamp(member_position * member_edges * origin_factor * layer_factor * relation_factor, 0.08, 1.45)
        loss = _clamp(
            (abs(impact_ratio) * 0.55 if sign < 0 else 0.0)
            + max(0.0, 1.0 - condition_factor) * 0.18,
            0.0,
            0.88,
        )
        stability = _clamp(0.32 + match_ratio * 0.46 + condition_factor * 0.24 - loss * 0.16, 0.08, 1.0)
        magnitude = activation * transmission * stability + path_strength * 0.58
        net_effect = magnitude if sign >= 0 else -magnitude
        out.append(
            WorkPath(
                path_id=str(normalized.get("row_id") or f"path_{target_god}_{len(out)}"),
                target_god=target_god,
                path_type=str(normalized.get("relation_family") or "dynamic_work"),
                participants=list(normalized.get("members") or [target_god]),
                origin_scope=str(normalized.get("origin_scope") or "natal"),
                activation=round(activation, 4),
                transmission=round(transmission, 4),
                loss=round(loss, 4),
                stability=round(stability, 4),
                net_effect=round(net_effect, 4),
                evidence={
                    "effect_type": normalized.get("effect_type"),
                    "impact_ratio": round(impact_ratio, 4),
                    "match_ratio": round(match_ratio, 4),
                    "path_strength": round(path_strength, 4),
                    "member_nodes": [node.node_id for node in member_nodes],
                    "member_position_weight": round(member_position, 4),
                    "member_edge_weight": round(member_edges, 4),
                    "relation_factor": round(relation_factor, 4),
                    "dynamic_factor": round(dynamic_factor, 4),
                    "source": normalized.get("source"),
                },
            )
        )

    for god, score in deity_scores.items():
        out.append(
            _basis_path(
                graph=graph,
                god=god,
                score=float(score or 0.0),
                max_score=max_score,
                positive_hint=float(positive_hint.get(god, 0.0) or 0.0),
                negative_hint=float(negative_hint.get(god, 0.0) or 0.0),
            )
        )

    return sorted(out, key=lambda item: (item.net_effect, item.activation, item.transmission), reverse=True)


def collect_effect_maps(decision_rows: Iterable[Dict[str, object]]) -> tuple[Dict[str, float], Dict[str, float]]:
    positive: Dict[str, float] = {}
    negative: Dict[str, float] = {}
    for row in decision_rows:
        normalized = _normalize_row_evidence(dict(row))
        god = str(normalized.get("target_god") or "").strip()
        if not god:
            continue
        ratio = _safe_float(normalized.get("impact_ratio"), 0.0)
        path_strength = _safe_float(normalized.get("path_strength"), abs(ratio))
        sign = _sign_from_effect(str(normalized.get("effect_type") or ""), ratio)
        if sign > 0:
            positive[god] = positive.get(god, 0.0) + max(path_strength, ratio, 0.0)
        elif sign < 0:
            negative[god] = negative.get(god, 0.0) + max(path_strength, abs(ratio))
    return positive, negative


def pillar_symbol_maps(
    four_pillars: Dict[str, str],
    *,
    luck_pillar: str = "",
    flow_pillar: str = "",
) -> Dict[str, Dict[str, str]]:
    branches, stems = branches_and_stems_from_runtime_pillars(
        four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
    )
    return {"branches": branches, "stems": stems}
