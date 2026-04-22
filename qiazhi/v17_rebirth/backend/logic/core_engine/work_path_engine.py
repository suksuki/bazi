from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import branches_and_stems_from_runtime_pillars
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import (
    BRANCH_HIDDEN,
    BRANCH_ELEMENT,
    ELEMENT_CYCLE,
    STEM_ELEMENT,
    ten_god_from_stems,
)
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import PillarEdge, PillarNode, SixPillarGraph
from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import WORK_EVIDENCE_KEY


@dataclass(frozen=True)
class WorkPath:
    path_id: str
    target_god: str
    path_type: str
    path_family: str
    path_role: str
    participants: List[str]
    origin_scope: str
    activation: float
    transmission: float
    loss: float
    stability: float
    net_effect: float
    evidence: Dict[str, object] = field(default_factory=dict)


_PATH_FAMILY_BY_RELATION: Dict[str, str] = {
    "sanhui": "convergence",
    "sanhe": "convergence",
    "banhe": "convergence",
    "gonghe": "convergence",
    "liuhe": "convergence",
    "stem_fusion": "transmuter",
    "liu_chong": "conflict",
    "liu_po": "conflict",
    "liu_hai": "conflict",
    "muku": "drain",
    "risk_matrix": "risk",
    "status_machine": "risk",
    "owl_food": "drain",
    "blade_clash": "conflict",
    "officer_hurt": "intercept",
    "sanxing": "dynamic_work",
}

_RELATION_FAMILY_ALIASES: Dict[str, str] = {
    "san_hui": "sanhui",
    "sanhui": "sanhui",
    "san_he": "sanhe",
    "sanxing": "sanxing",
    "liu_he": "liuhe",
    "liu_po": "liu_po",
    "liupo": "liu_po",
    "liu_hai": "liu_hai",
    "liuhai": "liu_hai",
    "liu_chong": "liu_chong",
    "ban_he": "banhe",
    "banhe": "banhe",
    "banhe_shengwang": "banhe",
    "banhe_muwang": "banhe",
    "gong_he": "gonghe",
    "gonghe": "gonghe",
    "risk_blade_clash": "blade_clash",
    "risk_owl_food": "owl_food",
    "risk_officer_hurt_contest": "officer_hurt",
    "risk_officer_crush": "officer_hurt",
    "status_machine": "status_machine",
    "officer_hurt": "officer_hurt",
}

_RELATION_DEFAULT_FAMILY = "dynamic_work"

_FAMILY_FACTOR: Dict[str, float] = {
    "convergence": 1.08,
    "conflict": 0.96,
    "drain": 0.93,
    "transmuter": 1.12,
    "bridge": 1.06,
    "risk": 0.9,
    "intercept": 0.88,
    "dynamic_work": 1.0,
    "static": 1.0,
}

_ROLE_FACTOR: Dict[str, Tuple[float, float]] = {
    "promote": (1.06, 0.96),
    "restrain": (0.96, 1.04),
    "transfer": (1.0, 0.9),
    "intercept": (0.9, 1.08),
    "bridge": (1.06, 0.92),
    "unknown": (0.98, 0.98),
}


def _classify_path_family_and_role(*, relation_family: str, effect_type: str) -> Tuple[str, str]:
    normalized_relation = _normalize_relation_family(relation_family)
    normalized_effect = str(effect_type or "").strip().lower()
    family = _PATH_FAMILY_BY_RELATION.get(normalized_relation, _RELATION_DEFAULT_FAMILY)
    if normalized_relation.startswith("tongguan"):
        return "bridge", "bridge"
    if normalized_effect in {"transform", "release", "support", "bind"}:
        if family in {"drain", "risk", "intercept"}:
            return family, "transfer"
        if family == "conflict":
            return family, "restrain"
        return family, "promote"
    if normalized_effect in {"harm", "storage", "stuck", "disrupt", "clash", "block"}:
        if family == "transmuter":
            return family, "transfer"
        if family == "bridge":
            return family, "bridge"
        return family, "restrain"
    return family, "unknown"


def _normalize_relation_family(raw_relation: str) -> str:
    normalized = str(raw_relation or "").strip().lower().replace("-", "_")
    normalized = normalized.replace("  ", " ").replace(" ", "_")
    if not normalized:
        return _RELATION_DEFAULT_FAMILY
    if normalized in _RELATION_FAMILY_ALIASES:
        return _RELATION_FAMILY_ALIASES[normalized]
    if normalized.startswith("risk_"):
        stripped = normalized[5:]
        if stripped in _RELATION_FAMILY_ALIASES:
            return _RELATION_FAMILY_ALIASES[stripped]
        if stripped in _PATH_FAMILY_BY_RELATION:
            return stripped
    return normalized


def _family_and_role_factor(path_family: str, path_role: str) -> Tuple[float, float]:
    family = _FAMILY_FACTOR.get(str(path_family or "").strip().lower(), 1.0)
    promote_factor, restrain_factor = _ROLE_FACTOR.get(str(path_role or "").strip().lower(), _ROLE_FACTOR["unknown"])
    return family, (promote_factor, restrain_factor)


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
    family = _normalize_relation_family(str(relation_family or ""))
    effect = str(effect_type or "").strip().lower()
    family_weights = {
        "sanhui": 1.44,
        "sanhe": 1.32,
        "banhe": 1.18,
        "gonghe": 1.08,
        "liuhe": 1.12,
        "liu_chong": 1.18,
        "liu_po": 1.08,
        "liu_hai": 1.06,
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


def _nodes_for_gods(graph: SixPillarGraph, *, gods: Sequence[str], day_master: str) -> List[PillarNode]:
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


def _avg_directed_edge_weight(
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


def _directional_factor(
    *,
    actor_nodes: Sequence[PillarNode],
    receiver_nodes: Sequence[PillarNode],
    edges: Dict[tuple[str, str], PillarEdge],
) -> tuple[float, float, float, float, float]:
    if not actor_nodes or not receiver_nodes:
        return 1.0, 0.0, 0.0, 0.0, 0.0
    actor_position = _avg_position_weight(actor_nodes)
    receiver_position = _avg_position_weight(receiver_nodes)
    directed_edge = _avg_directed_edge_weight(actor_nodes, receiver_nodes, edges)
    factor = _clamp(
        0.72 + actor_position * 0.16 + receiver_position * 0.12 + directed_edge * 0.18,
        0.84,
        1.28,
    )
    return factor, actor_position, receiver_position, directed_edge, (actor_position + receiver_position) / 2.0


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
    relation_family_raw = str(
        work.get("relation_family")
        or impact.get("relation_family")
        or row.get("source")
        or row.get("plugin_id")
        or "unknown"
    ).strip()
    relation_family = _normalize_relation_family(relation_family_raw)
    impact_ratio = _safe_float(work.get("impact_ratio", impact.get("impact_ratio", 0.0)))
    match_ratio = _clamp(_safe_float(work.get("match_ratio", impact.get("match_ratio", 0.0))), 0.0, 1.0)
    condition_state = str(work.get("condition_state") or impact.get("condition_state") or "").strip()
    layer = str(work.get("layer") or impact.get("interaction_layer") or "unknown").strip()
    origin_scope = str(work.get("origin_scope") or impact.get("origin_type") or "natal").strip()
    effect_type = str(work.get("effect_type") or "").strip()
    significance = _safe_float(impact.get("significance_weight", 1.0), 1.0)
    decision_id = str(row.get("id") or "").strip()
    plugin_id = str(row.get("plugin_id") or row.get("source") or relation_family).strip()
    source_label = str(
        row.get("source_label")
        or row.get("display_name")
        or row.get("definition_text")
        or row.get("title")
        or row.get("label")
        or plugin_id
        or relation_family
    ).strip()
    decision_label = str(
        row.get("label")
        or row.get("title")
        or row.get("summary")
        or row.get("reason")
        or source_label
    ).strip()
    path_strength = _safe_float(
        work.get("path_strength"),
        abs(impact_ratio) * max(0.45, match_ratio) * max(0.75, significance),
    )
    return {
        "row_id": decision_id,
        "decision_id": decision_id,
        "plugin_id": plugin_id,
        "source_label": source_label,
        "decision_label": decision_label,
        "target_god": target,
        "relation_family_raw": relation_family_raw,
        "relation_family": relation_family,
        "effect_type": effect_type,
        "members": _legacy_members(impact),
        "actor_members": [
            str(item).strip()
            for item in (
                work.get("actor_members")
                if isinstance(work.get("actor_members"), list)
                else impact.get("actor_members")
                if isinstance(impact.get("actor_members"), list)
                else row.get("actor_members")
                if isinstance(row.get("actor_members"), list)
                else []
            )
            if str(item).strip()
        ],
        "receiver_members": [
            str(item).strip()
            for item in (
                work.get("receiver_members")
                if isinstance(work.get("receiver_members"), list)
                else impact.get("receiver_members")
                if isinstance(impact.get("receiver_members"), list)
                else row.get("receiver_members")
                if isinstance(row.get("receiver_members"), list)
                else []
            )
            if str(item).strip()
        ],
        "origin_scope": origin_scope,
        "layer": layer,
        "condition_state": condition_state,
        "impact_ratio": impact_ratio,
        "match_ratio": match_ratio,
        "path_strength": max(0.0, path_strength),
        "significance_weight": significance,
        "actor_gods": [
            str(item).strip()
            for item in (
                work.get("actor_gods")
                if isinstance(work.get("actor_gods"), list)
                else impact.get("actor_gods")
                if isinstance(impact.get("actor_gods"), list)
                else row.get("actor_gods")
                if isinstance(row.get("actor_gods"), list)
                else []
            )
            if str(item).strip()
        ],
        "receiver_gods": [
            str(item).strip()
            for item in (
                work.get("receiver_gods")
                if isinstance(work.get("receiver_gods"), list)
                else impact.get("receiver_gods")
                if isinstance(impact.get("receiver_gods"), list)
                else row.get("receiver_gods")
                if isinstance(row.get("receiver_gods"), list)
                else []
            )
            if str(item).strip()
        ],
        "source": str(row.get("source") or row.get("plugin_id") or relation_family).strip(),
        "work": dict(work) if isinstance(work, dict) else {},
        "impact": dict(impact) if isinstance(impact, dict) else {},
    }


def _extract_counterpart_gods(
    *,
    row: Dict[str, Any],
    work: Dict[str, Any],
    impact: Dict[str, Any],
    relation_family: str,
    target_god: str,
    day_master: str,
) -> List[str]:
    candidates: list[str] = []
    raw_sources = [
        row.get("counterpart_gods"),
        row.get("interaction_gods"),
        row.get("interaction_pair"),
        work.get("counterpart_gods"),
        work.get("interaction_gods"),
        work.get("interaction_pair"),
        work.get("interplay"),
        impact.get("counterpart_gods"),
        impact.get("interaction_gods"),
    ]
    for raw in raw_sources:
        if isinstance(raw, list):
            candidates.extend([str(item).strip() for item in raw if str(item).strip()])
        elif isinstance(raw, str):
            candidates.append(raw.strip())

    members = row.get("members") if isinstance(row.get("members"), list) else work.get("members")
    if isinstance(members, list):
        for member in members:
            name = str(member).strip()
            if len(name) == 1 and STEM_ELEMENT.get(name):
                try:
                    candidates.append(ten_god_from_stems(day_master, name))
                except Exception:
                    continue

    normalized_family = str(relation_family or "").lower().strip()
    if normalized_family.startswith("risk_officer") and target_god in {"正官", "七杀"}:
        candidates.append("伤官")
    if normalized_family.startswith("risk_officer") and target_god == "伤官":
        candidates.append("正官")

    out: list[str] = []
    for candidate in candidates:
        name = str(candidate or "").strip()
        if not name or name == target_god:
            continue
        if name not in out:
            out.append(name)
    return out


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
        path_family="static",
        path_role="promote",
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


def _day_master_from_graph(graph: SixPillarGraph) -> str:
    for node in graph.nodes:
        if node.node_id == "day_stem":
            return str(node.symbol or "").strip()
    for node in graph.nodes:
        if node.pillar == "day" and node.kind == "stem":
            return str(node.symbol or "").strip()
    return ""


def _god_element_maps(day_master: str) -> tuple[Dict[str, str], Dict[str, List[str]]]:
    god_to_element: Dict[str, str] = {}
    element_to_gods: Dict[str, List[str]] = {element: [] for element in ELEMENT_CYCLE}
    seen: set[str] = set()
    for stem, element in STEM_ELEMENT.items():
        god = ten_god_from_stems(day_master, stem)
        god_to_element[god] = element
        marker = f"{element}:{god}"
        if marker in seen:
            continue
        element_to_gods.setdefault(element, []).append(god)
        seen.add(marker)
    return god_to_element, element_to_gods


def _element_strengths(day_master: str, deity_scores: Dict[str, float]) -> Dict[str, float]:
    god_to_element, _ = _god_element_maps(day_master)
    strengths: Dict[str, float] = {element: 0.0 for element in ELEMENT_CYCLE}
    for god, score in deity_scores.items():
        element = god_to_element.get(str(god).strip())
        if not element:
            continue
        strengths[element] = strengths.get(element, 0.0) + max(float(score or 0.0), 0.0)
    return strengths


def _element_nodes(graph: SixPillarGraph, element: str) -> List[PillarNode]:
    out: List[PillarNode] = []
    for node in graph.nodes:
        if node.kind == "stem" and STEM_ELEMENT.get(node.symbol) == element:
            out.append(node)
        elif node.kind == "branch" and BRANCH_ELEMENT.get(node.symbol) == element:
            out.append(node)
    return out


def _infer_tongguan_paths(
    *,
    graph: SixPillarGraph,
    deity_scores: Dict[str, float],
) -> List[WorkPath]:
    day_master = _day_master_from_graph(graph)
    if not day_master:
        return []

    god_to_element, element_to_gods = _god_element_maps(day_master)
    element_strengths = _element_strengths(day_master, deity_scores)
    max_element_strength = max([float(value or 0.0) for value in element_strengths.values()] or [1.0])
    max_god_score = max([float(value or 0.0) for value in deity_scores.values()] or [1.0])
    edge_index = _edge_lookup(graph)

    pair_candidates: List[Dict[str, float | str]] = []
    for index, controller in enumerate(ELEMENT_CYCLE):
        controlled = ELEMENT_CYCLE[(index + 2) % 5]
        mediator = ELEMENT_CYCLE[(index + 1) % 5]
        controller_strength = float(element_strengths.get(controller, 0.0) or 0.0)
        controlled_strength = float(element_strengths.get(controlled, 0.0) or 0.0)
        if controller_strength < max_element_strength * 0.18 or controlled_strength < max_element_strength * 0.18:
            continue
        balance_ratio = min(controller_strength, controlled_strength) / max(controller_strength, controlled_strength, 1.0)
        war_tension = (
            min(controller_strength, controlled_strength) / max(max_element_strength, 1.0)
        ) * (0.64 + balance_ratio * 0.36)
        if war_tension < 0.2:
            continue
        pair_candidates.append(
            {
                "controller": controller,
                "controlled": controlled,
                "mediator": mediator,
                "controller_strength": controller_strength,
                "controlled_strength": controlled_strength,
                "balance_ratio": balance_ratio,
                "war_tension": war_tension,
            }
        )

    pair_candidates.sort(key=lambda item: float(item["war_tension"]), reverse=True)
    out: List[WorkPath] = []
    for pair_index, pair in enumerate(pair_candidates[:2]):
        controller = str(pair["controller"])
        controlled = str(pair["controlled"])
        mediator = str(pair["mediator"])
        controller_strength = float(pair["controller_strength"])
        controlled_strength = float(pair["controlled_strength"])
        balance_ratio = float(pair["balance_ratio"])
        war_tension = float(pair["war_tension"])
        mediator_strength = float(element_strengths.get(mediator, 0.0) or 0.0)
        mediator_presence_ratio = mediator_strength / max(max_element_strength, 1.0)
        mediator_nodes = _element_nodes(graph, mediator)
        controller_nodes = _element_nodes(graph, controller)
        controlled_nodes = _element_nodes(graph, controlled)
        cluster_nodes = controller_nodes + controlled_nodes + mediator_nodes
        position_weight = _avg_position_weight(cluster_nodes or mediator_nodes)
        edge_weight = _avg_edge_weight(cluster_nodes or mediator_nodes, edge_index)
        mediator_present = mediator_presence_ratio >= 0.12 or bool(mediator_nodes)
        target_gods = sorted(
            element_to_gods.get(mediator, []),
            key=lambda god: float(deity_scores.get(god, 0.0) or 0.0),
            reverse=True,
        )[:2]
        for god_index, target_god in enumerate(target_gods):
            target_score = max(float(deity_scores.get(target_god, 0.0) or 0.0), 0.0)
            target_ratio = target_score / max(max_god_score, 1.0)
            activation = _clamp(
                0.18
                + war_tension * 0.44
                + balance_ratio * 0.16
                + (mediator_presence_ratio * 0.22 if mediator_present else 0.0)
                + target_ratio * 0.12
                - god_index * 0.03,
                0.08,
                1.12,
            )
            transmission = _clamp(
                position_weight * (0.68 + edge_weight * 0.24 + war_tension * 0.18 + (0.12 if mediator_present else 0.0)),
                0.12,
                1.28,
            )
            loss = _clamp(
                0.11
                - mediator_presence_ratio * 0.05
                - balance_ratio * 0.03
                + (0.03 if not mediator_present else 0.0),
                0.02,
                0.28,
            )
            stability = _clamp(
                0.34
                + balance_ratio * 0.22
                + position_weight * 0.16
                + (0.08 if mediator_present else -0.02)
                - loss * 0.18,
                0.12,
                0.96,
            )
            projection_bonus = war_tension * (0.04 if mediator_present else 0.12)
            net_effect = activation * transmission * stability * (1.0 - loss) + projection_bonus
            out.append(
                WorkPath(
                    path_id=f"tongguan_{pair_index}_{god_index}_{controller}_{mediator}_{controlled}",
                    target_god=target_god,
                    path_type="tongguan_present" if mediator_present else "tongguan_external",
                    path_family="bridge",
                    path_role="bridge",
                    participants=[controller, mediator, controlled, target_god],
                    origin_scope="natal_projection" if mediator_present else "external_projection",
                    activation=round(activation, 4),
                    transmission=round(transmission, 4),
                    loss=round(loss, 4),
                    stability=round(stability, 4),
                    net_effect=round(net_effect, 4),
                    evidence={
                        "controller_element": controller,
                        "controlled_element": controlled,
                        "mediator_element": mediator,
                        "controller_strength": round(controller_strength, 4),
                        "controlled_strength": round(controlled_strength, 4),
                        "mediator_strength": round(mediator_strength, 4),
                        "balance_ratio": round(balance_ratio, 4),
                        "war_tension": round(war_tension, 4),
                        "position_weight": round(position_weight, 4),
                        "edge_weight": round(edge_weight, 4),
                        "candidate_gods": target_gods,
                        "external_candidate": not mediator_present,
                        "decision_id": "",
                        "plugin_id": "core_engine.tongguan",
                        "source_label": "通关神传导",
                        "decision_label": "核心推导通关神",
                        "condition_state": "manifested" if mediator_present else "projected",
                        "layer": "cross_layer",
                        "source": "core_engine.tongguan",
                        "path_family": "bridge",
                        "path_role": "bridge",
                    },
                )
            )
    return out


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
    day_master = _day_master_from_graph(graph)

    out: List[WorkPath] = []
    for row in rows:
        normalized = _normalize_row_evidence(row)
        target_god = str(normalized.get("target_god") or "").strip()
        if not target_god:
            continue
        normalized["counterpart_gods"] = _extract_counterpart_gods(
            row=normalized,
            work=normalized.get("work", {}) if isinstance(normalized.get("work"), dict) else {},
            impact=normalized.get("impact", {}) if isinstance(normalized.get("impact"), dict) else {},
            relation_family=str(normalized.get("relation_family") or ""),
            target_god=target_god,
            day_master=day_master,
        )
        base_score = max(float(deity_scores.get(target_god, 0.0) or 0.0), 0.0)
        base_activation = base_score / max(max_score, 1.0)
        member_nodes = _nodes_for_members(
            graph,
            members=list(normalized.get("members") or []),
            layer=str(normalized.get("layer") or "unknown"),
        )
        actor_nodes = _nodes_for_members(
            graph,
            members=list(normalized.get("actor_members") or []),
            layer=str(normalized.get("layer") or "unknown"),
        ) or _nodes_for_gods(
            graph,
            gods=list(normalized.get("actor_gods") or []),
            day_master=day_master,
        )
        receiver_nodes = _nodes_for_members(
            graph,
            members=list(normalized.get("receiver_members") or []),
            layer=str(normalized.get("layer") or "unknown"),
        ) or _nodes_for_gods(
            graph,
            gods=list(normalized.get("receiver_gods") or []),
            day_master=day_master,
        )
        member_position = _avg_position_weight(member_nodes)
        member_edges = _avg_edge_weight(member_nodes, edge_index)
        directional_factor, actor_position, receiver_position, directed_edge, directed_position = _directional_factor(
            actor_nodes=actor_nodes,
            receiver_nodes=receiver_nodes,
            edges=edge_index,
        )
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
        path_family, path_role = _classify_path_family_and_role(
            relation_family=str(normalized.get("relation_family") or ""),
            effect_type=str(normalized.get("effect_type") or ""),
        )
        family_factor, role_factors = _family_and_role_factor(path_family, path_role)
        role_factor = role_factors[0] if sign >= 0 else role_factors[1]

        activation = _clamp(
            base_activation * (0.7 + path_strength * 0.65) * dynamic_factor * family_factor,
            0.02,
            1.3,
        )
        transmission = _clamp(
            member_position * member_edges * origin_factor * layer_factor * relation_factor * role_factor * directional_factor,
            0.08,
            1.45,
        )
        loss = _clamp(
            (abs(impact_ratio) * 0.55 if sign < 0 else 0.0)
            + max(0.0, 1.0 - condition_factor) * 0.18,
            0.0,
            0.88,
        )
        stability = _clamp(
            0.32
            + match_ratio * 0.46
            + condition_factor * 0.24
            - loss * 0.16
            - (0.04 if path_role == "restrain" and sign < 0 else 0.0),
            0.08,
            1.0,
        )
        magnitude = activation * transmission * stability + path_strength * 0.58
        net_effect = magnitude if sign >= 0 else -magnitude
        if path_role == "bridge":
            net_effect *= 1.04
        out.append(
            WorkPath(
                path_id=str(normalized.get("row_id") or f"path_{target_god}_{len(out)}"),
                target_god=target_god,
                path_type=str(normalized.get("relation_family") or "dynamic_work"),
                path_family=path_family,
                path_role=path_role,
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
                    "counterpart_gods": list(normalized.get("counterpart_gods") or []),
                    "member_nodes": [node.node_id for node in member_nodes],
                    "member_position_weight": round(member_position, 4),
                    "member_edge_weight": round(member_edges, 4),
                    "actor_nodes": [node.node_id for node in actor_nodes],
                    "receiver_nodes": [node.node_id for node in receiver_nodes],
                    "actor_position_weight": round(actor_position, 4),
                    "receiver_position_weight": round(receiver_position, 4),
                    "directed_edge_weight": round(directed_edge, 4),
                    "directed_position_weight": round(directed_position, 4),
                    "directional_factor": round(directional_factor, 4),
                    "relation_factor": round(relation_factor, 4),
                    "dynamic_factor": round(dynamic_factor, 4),
                    "path_family": path_family,
                    "path_role": path_role,
                    "family_factor": round(family_factor, 4),
                    "role_factor": round(role_factor, 4),
                    "decision_id": normalized.get("decision_id"),
                    "plugin_id": normalized.get("plugin_id"),
                    "source_label": normalized.get("source_label"),
                    "decision_label": normalized.get("decision_label"),
                    "condition_state": normalized.get("condition_state"),
                    "layer": normalized.get("layer"),
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

    out.extend(_infer_tongguan_paths(graph=graph, deity_scores=deity_scores))

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
