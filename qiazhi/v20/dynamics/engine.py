from __future__ import annotations

from collections import Counter
from typing import Any

from v20.core.constants import CONTROLS, GENERATES, element_of_stem
from v20.core.schemas import ChartFacts, RelationHit, TimeContext
from v20.dynamics.schema import DynamicChain, DynamicEdge, DynamicNode, StructureDynamics
from v20.features.schema import FeatureLayer


STRUCTURE_DYNAMICS_VERSION = "v20.structure_dynamics.v1"

DESTRUCTIVE_RELATIONS = {"clash", "harm", "break", "punishment"}
STABILIZING_RELATIONS = {"harmony", "three_harmony", "three_meeting"}
CHAIN_ORDER = (
    ("output", ("食神", "伤官")),
    ("wealth", ("正财", "偏财")),
    ("authority", ("正官", "七杀")),
    ("resource", ("正印", "偏印")),
    ("self", ("比肩", "劫财")),
)
CHAIN_SEGMENT_PRIORITY = (
    ("output", "wealth", "self"),
    ("output", "authority", "resource"),
    ("output", "wealth", "authority"),
    ("wealth", "authority", "resource"),
    ("authority", "resource", "self"),
    ("output", "wealth"),
    ("wealth", "authority"),
    ("authority", "resource"),
    ("resource", "self"),
    ("wealth", "self"),
)

CHAIN_NODE_BY_TEN_GOD = {
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

CHAIN_NODE_BY_DOMAIN = {
    "wealth": ("wealth",),
    "career": ("authority", "resource"),
    "strength": ("self",),
    "useful_god": ("resource", "self"),
    "pattern": ("authority", "resource"),
    "ten_god": ("output", "wealth", "authority", "resource", "self"),
}

CHAIN_NODES_BY_RULE_KEY = {
    "wealth.output_capacity": ("output", "wealth", "self"),
    "wealth.output_wealth_capacity_chain": ("output", "wealth", "self"),
    "career.guan_shang_yin": ("output", "authority", "resource"),
    "career.output_authority_resource_chain": ("output", "authority", "resource"),
    "career.structure": ("authority", "resource"),
    "career.resource_buffer": ("authority", "resource"),
    "ten_god.shang_guan_jian_guan": ("output", "authority", "resource"),
    "ten_god.guan_sha_mixed": ("authority",),
    "ten_god.output_to_wealth": ("output", "wealth"),
    "wealth.peer_competition": ("wealth", "self"),
    "wealth.capacity_gate": ("wealth", "self"),
    "wealth.material": ("wealth",),
    "strength.capacity": ("self",),
    "useful_god.candidate_gate": ("resource", "self"),
    "pattern.review_gate": ("authority", "resource"),
}


def build_structure_dynamics(
    chart_facts: ChartFacts,
    feature_layer: FeatureLayer,
    feature_state_model: dict[str, Any],
    time_context: TimeContext,
    decision_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_report = decision_report or {}
    nodes = _unique_nodes(_nodes(chart_facts, feature_layer, time_context))
    edges = _valid_edges(_edges(chart_facts, time_context), {node.node_id for node in nodes})
    dimensions = _dimensions(chart_facts, feature_layer, feature_state_model, time_context)
    chain = _dominant_chain(chart_facts, feature_state_model, time_context, decision_report)
    activated = _activated_structures(feature_state_model, time_context)
    suppressed = _suppressed_structures(feature_state_model, time_context)
    volatility_score = _volatility_score(chart_facts, time_context)
    stability_shift = _stability_shift(dimensions["stability_score"], volatility_score, time_context)
    energy_shift = _energy_shift(dimensions["energy_strength"], time_context)
    status = "ready" if nodes else "empty"
    payload = StructureDynamics(
        version=STRUCTURE_DYNAMICS_VERSION,
        status=status,
        source="ChartFacts+FeatureLayer+FeatureStateModel+DecisionReport+PortraitProjection+TimeContext",
        nodes=nodes,
        edges=edges,
        dynamic_state={
            "energy_strength": dimensions["energy_strength"],
            "stability_score": dimensions["stability_score"],
            "visibility_score": dimensions["visibility_score"],
            "continuity_score": dimensions["continuity_score"],
            "volatility_score": volatility_score,
            "time_layer_status": time_context.status,
            "relation_pressure_count": dimensions["relation_pressure_count"],
            "relation_stabilizer_count": dimensions["relation_stabilizer_count"],
        },
        dominant_chain=chain.to_dict(),
        chain_state=chain.state,
        activated_structures=activated,
        suppressed_structures=suppressed,
        energy_shift=energy_shift,
        stability_shift=stability_shift,
        terminal_node=chain.terminal_node,
        volatility_score=volatility_score,
    )
    return payload.to_dict()


def _nodes(chart_facts: ChartFacts, feature_layer: FeatureLayer, time_context: TimeContext) -> tuple[DynamicNode, ...]:
    rows: list[DynamicNode] = []
    aggregate_elements = sorted({element_of_stem(pillar.stem) for pillar in chart_facts.pillars.values()})
    for element in aggregate_elements:
        rows.append(DynamicNode(f"element.{element}", "ElementNode", element, "natal"))
    for position, pillar in chart_facts.pillars.items():
        rows.append(DynamicNode(f"stem.{position}.{pillar.stem}", "StemNode", pillar.stem, "natal"))
        rows.append(DynamicNode(f"branch.{position}.{pillar.branch}", "BranchNode", pillar.branch, "natal"))
        rows.append(DynamicNode(f"element.{position}.{element_of_stem(pillar.stem)}", "ElementNode", element_of_stem(pillar.stem), "natal"))
    for row in chart_facts.visible_ten_gods:
        rows.append(DynamicNode(f"tengod.visible.{row.pillar}.{row.label}", "TenGodNode", row.label, "natal", row.weight))
    for row in chart_facts.hidden_ten_gods:
        rows.append(DynamicNode(f"hidden.{row.pillar}.{row.stem}", "HiddenStemNode", row.stem, "hidden", row.weight))
    for layer in time_context.layers:
        rows.append(DynamicNode(f"stem.{layer.layer_key}.{layer.pillar.stem}", "StemNode", layer.pillar.stem, "time"))
        rows.append(DynamicNode(f"branch.{layer.layer_key}.{layer.pillar.branch}", "BranchNode", layer.pillar.branch, "time"))
        rows.append(DynamicNode(f"element.{layer.layer_key}.{element_of_stem(layer.pillar.stem)}", "ElementNode", element_of_stem(layer.pillar.stem), "time"))
        rows.append(DynamicNode(f"time.{layer.layer_key}.{layer.pillar.display}", "StructureNode", layer.pillar.display, "time"))
        rows.append(DynamicNode(f"tengod.time.{layer.layer_key}.{layer.ten_god.label}", "TenGodNode", layer.ten_god.label, "time"))
    for feature in feature_layer.features[:12]:
        rows.append(DynamicNode(f"feature.{feature.feature_id}", "StructureNode", feature.title, "feature", float(feature.confidence or 0.0)))
    return tuple(rows)


def _unique_nodes(nodes: tuple[DynamicNode, ...]) -> tuple[DynamicNode, ...]:
    seen: set[str] = set()
    rows: list[DynamicNode] = []
    for node in nodes:
        if node.node_id in seen:
            continue
        seen.add(node.node_id)
        rows.append(node)
    return tuple(rows)


def _edges(chart_facts: ChartFacts, time_context: TimeContext) -> tuple[DynamicEdge, ...]:
    rows: list[DynamicEdge] = []
    for position, pillar in chart_facts.pillars.items():
        stem_node = f"stem.{position}.{pillar.stem}"
        branch_node = f"branch.{position}.{pillar.branch}"
        rows.append(DynamicEdge(f"edge.root.{position}", "root", branch_node, stem_node, "natal", 0.72))
    for hit in tuple(chart_facts.relation_hits) + tuple(time_context.relation_hits):
        rows.append(_relation_edge(hit))
    element_counts = Counter(element_of_stem(pillar.stem) for pillar in chart_facts.pillars.values())
    for source, target in GENERATES.items():
        if element_counts[source] and element_counts[target]:
            rows.append(DynamicEdge(f"edge.generate.{source}.{target}", "generate", f"element.{source}", f"element.{target}", "natal", 0.55))
    for source, target in CONTROLS.items():
        if element_counts[source] and element_counts[target]:
            rows.append(DynamicEdge(f"edge.control.{source}.{target}", "control", f"element.{source}", f"element.{target}", "natal", 0.5))
    for layer in time_context.layers:
        rows.append(DynamicEdge(f"edge.activate.{layer.layer_key}", "activate", f"time.{layer.layer_key}.{layer.pillar.display}", f"tengod.time.{layer.layer_key}.{layer.ten_god.label}", "time", 0.82))
    return tuple(rows)


def _valid_edges(edges: tuple[DynamicEdge, ...], node_ids: set[str]) -> tuple[DynamicEdge, ...]:
    seen: set[str] = set()
    rows: list[DynamicEdge] = []
    for edge in edges:
        if edge.edge_id in seen:
            continue
        if edge.source not in node_ids or edge.target not in node_ids:
            continue
        seen.add(edge.edge_id)
        rows.append(edge)
    return tuple(rows)


def _relation_edge(hit: RelationHit) -> DynamicEdge:
    source = f"branch.{hit.positions[0]}.{hit.branches[0]}" if hit.positions and hit.branches else "branch.unknown"
    target = f"branch.{hit.positions[-1]}.{hit.branches[-1]}" if hit.positions and hit.branches else "branch.unknown"
    weight = 0.78 if hit.relation_type in DESTRUCTIVE_RELATIONS else 0.66
    return DynamicEdge(
        edge_id=f"edge.{hit.layer}.{hit.relation_type}.{'.'.join(hit.positions)}",
        edge_type=hit.relation_type,
        source=source,
        target=target,
        layer=hit.layer,
        weight=weight,
    )


def _dimensions(
    chart_facts: ChartFacts,
    feature_layer: FeatureLayer,
    feature_state_model: dict[str, Any],
    time_context: TimeContext,
) -> dict[str, Any]:
    all_relations = tuple(chart_facts.relation_hits) + tuple(time_context.relation_hits)
    pressure_count = sum(1 for row in all_relations if row.relation_type in DESTRUCTIVE_RELATIONS)
    stabilizer_count = sum(1 for row in all_relations if row.relation_type in STABILIZING_RELATIONS)
    priority_count = len(tuple(feature_state_model.get("priority_features", ())))
    energy = min(0.99, 0.34 + len(feature_layer.features) * 0.018 + len(time_context.layers) * 0.08 + priority_count * 0.025)
    stability = max(0.05, min(0.99, 0.68 + stabilizer_count * 0.07 - pressure_count * 0.09))
    visibility = min(0.99, 0.36 + len(chart_facts.visible_ten_gods) * 0.055 + len(time_context.layers) * 0.12)
    continuity = min(0.99, 0.32 + len(chart_facts.hidden_ten_gods) * 0.025 + len(chart_facts.vault_branches) * 0.04 + stabilizer_count * 0.04)
    return {
        "energy_strength": round(energy, 3),
        "stability_score": round(stability, 3),
        "visibility_score": round(visibility, 3),
        "continuity_score": round(continuity, 3),
        "relation_pressure_count": pressure_count,
        "relation_stabilizer_count": stabilizer_count,
    }


def _dominant_chain(
    chart_facts: ChartFacts,
    feature_state_model: dict[str, Any],
    time_context: TimeContext,
    decision_report: dict[str, Any],
) -> DynamicChain:
    labels = [row.label for row in chart_facts.visible_ten_gods]
    labels.extend(row.label for row in chart_facts.hidden_ten_gods if row.weight >= 0.25)
    labels.extend(layer.ten_god.label for layer in time_context.layers)
    present = tuple(stage for stage, candidates in CHAIN_ORDER if any(label in candidates for label in labels))
    if not present:
        return DynamicChain("empty", (), "empty")
    node_scores, node_evidence, segment_boosts = _chain_signal_scores(
        chart_facts,
        feature_state_model,
        time_context,
        decision_report,
    )
    dominant_nodes = _dominant_chain_segment(present, node_scores, segment_boosts)
    evidence = _chain_evidence(dominant_nodes, labels, node_evidence)
    destructive_time = any(row.relation_type in DESTRUCTIVE_RELATIONS for row in time_context.relation_hits)
    if len(dominant_nodes) >= 3:
        state = "volatile" if destructive_time else "closed"
    elif len(dominant_nodes) >= 2:
        state = "volatile" if destructive_time else "partial"
    else:
        state = "blocked" if destructive_time else "partial"
    terminal = dominant_nodes[-1]
    return DynamicChain(
        chain_key="->".join(dominant_nodes),
        nodes=dominant_nodes,
        state=state,
        terminal_node=terminal,
        evidence=evidence,
    )


def _dominant_chain_segment(
    present: tuple[str, ...],
    node_scores: dict[str, float],
    segment_boosts: dict[tuple[str, ...], float],
) -> tuple[str, ...]:
    present_set = set(present)
    candidates: list[tuple[float, int, tuple[str, ...]]] = []
    for index, segment in enumerate(CHAIN_SEGMENT_PRIORITY):
        if not all(node in present_set for node in segment):
            continue
        if not all(node_scores.get(node, 0.0) >= 0.12 for node in segment):
            continue
        score = sum(node_scores.get(node, 0.0) for node in segment) / len(segment)
        score += segment_boosts.get(segment, 0.0)
        candidates.append((score, -index, segment))
    if candidates:
        return sorted(candidates, reverse=True)[0][2]
    return present[:3]


def _chain_signal_scores(
    chart_facts: ChartFacts,
    feature_state_model: dict[str, Any],
    time_context: TimeContext,
    decision_report: dict[str, Any],
) -> tuple[dict[str, float], dict[str, list[str]], dict[tuple[str, ...], float]]:
    scores: dict[str, float] = {stage: 0.0 for stage, _ in CHAIN_ORDER}
    evidence: dict[str, list[str]] = {stage: [] for stage, _ in CHAIN_ORDER}
    segment_boosts: dict[tuple[str, ...], float] = {}

    def add(node: str, amount: float, reason: str = "") -> None:
        if node not in scores:
            return
        scores[node] = round(min(2.0, scores[node] + amount), 4)
        if reason and reason not in evidence[node]:
            if reason.startswith("系统"):
                evidence[node].insert(0, reason)
            else:
                evidence[node].append(reason)

    def boost_segment(nodes: tuple[str, ...], amount: float, reason: str = "") -> None:
        if not nodes:
            return
        segment = _known_segment(nodes)
        if not segment:
            return
        segment_boosts[segment] = round(min(1.2, segment_boosts.get(segment, 0.0) + amount), 4)
        for node in segment:
            add(node, amount / 2, reason)

    for row in chart_facts.visible_ten_gods:
        add(CHAIN_NODE_BY_TEN_GOD.get(row.label, ""), 0.24, f"明透{row.label}")
    for row in chart_facts.hidden_ten_gods:
        add(CHAIN_NODE_BY_TEN_GOD.get(row.label, ""), 0.08 * float(row.weight or 0.0), f"藏干{row.label}")
    for layer in time_context.layers:
        add(CHAIN_NODE_BY_TEN_GOD.get(layer.ten_god.label, ""), 0.28, f"{layer.layer_key}:{layer.ten_god.label}")

    for state in feature_state_model.get("priority_features", ()):
        if not isinstance(state, dict):
            continue
        amount = 0.18 * float(state.get("priority", 0.0) or 0.0)
        reason = str(state.get("title", "") or state.get("feature_id", ""))
        for node in _nodes_for_domain(str(state.get("domain", ""))):
            add(node, amount, reason)

    _score_decision_rows(decision_report.get("hits", ()), 0.2, scores, evidence, segment_boosts)
    _score_decision_rows(decision_report.get("decisions", ()), 0.34, scores, evidence, segment_boosts)
    _score_decision_rows(decision_report.get("mainlines", ()), 0.52, scores, evidence, segment_boosts)
    _score_decision_rows(decision_report.get("rule_runtime_hits", ()), 0.12, scores, evidence, segment_boosts)

    portrait = decision_report.get("portrait_projection", {})
    axes = portrait.get("axes", ()) if isinstance(portrait, dict) else ()
    for axis in axes:
        if not isinstance(axis, dict):
            continue
        amount = 0.14 * float(axis.get("peak_confidence", 0.0) or 0.0)
        reason = str(axis.get("structural_anchor", "") or axis.get("label", ""))
        for node in _nodes_for_domain(str(axis.get("domain", ""))):
            add(node, amount, reason)

    return scores, evidence, segment_boosts


def _score_decision_rows(
    rows: object,
    factor: float,
    scores: dict[str, float],
    evidence: dict[str, list[str]],
    segment_boosts: dict[tuple[str, ...], float],
) -> None:
    def add(node: str, amount: float, reason: str = "") -> None:
        if node not in scores:
            return
        scores[node] = round(min(2.0, scores[node] + amount), 4)
        if reason and reason not in evidence[node]:
            if reason.startswith("系统"):
                evidence[node].insert(0, reason)
            else:
                evidence[node].append(reason)

    for row in (rows if isinstance(rows, (list, tuple)) else ()):
        if not isinstance(row, dict):
            continue
        score = float(row.get("score", row.get("match_score", 0.0)) or 0.0)
        amount = factor * score
        key = _normalize_rule_key(str(row.get("rule_key", "") or row.get("decision_key", "") or row.get("mainline_key", "")))
        reason = f"系统裁决:{str(row.get('title', '') or row.get('label', '') or key)}"
        nodes = _nodes_for_rule_key(key) or _nodes_for_text(reason, tuple(str(item) for item in row.get("support", ()) if str(item)))
        if not nodes:
            nodes = _nodes_for_domain(str(row.get("domain", "")))
        for node in nodes:
            add(node, amount, reason)
        if len(nodes) >= 2:
            segment = _known_segment(nodes)
            if segment:
                segment_boosts[segment] = round(min(1.2, segment_boosts.get(segment, 0.0) + amount * 0.8), 4)


def _normalize_rule_key(key: str) -> str:
    for prefix in ("decision.rulespec.", "decision.", "rule.", "mainline."):
        if key.startswith(prefix):
            return key[len(prefix):]
    return key


def _nodes_for_domain(domain: str) -> tuple[str, ...]:
    return CHAIN_NODE_BY_DOMAIN.get(domain, ())


def _nodes_for_rule_key(key: str) -> tuple[str, ...]:
    for suffix, nodes in CHAIN_NODES_BY_RULE_KEY.items():
        if key == suffix or key.endswith(f".{suffix}"):
            return nodes
    return ()


def _nodes_for_text(label: str, support: tuple[str, ...] = ()) -> tuple[str, ...]:
    text = " ".join((label, *support))
    nodes = []
    for ten_god, node in CHAIN_NODE_BY_TEN_GOD.items():
        if ten_god in text and node not in nodes:
            nodes.append(node)
    return tuple(nodes)


def _known_segment(nodes: tuple[str, ...]) -> tuple[str, ...]:
    node_set = set(nodes)
    for segment in CHAIN_SEGMENT_PRIORITY:
        if all(node in node_set for node in segment):
            return segment
    ordered = tuple(node for node, _ in CHAIN_ORDER if node in node_set)
    if len(ordered) >= 2:
        return ordered[:3]
    return ()


def _chain_evidence(
    dominant_nodes: tuple[str, ...],
    labels: list[str],
    node_evidence: dict[str, list[str]],
) -> tuple[str, ...]:
    rows: list[str] = []
    for node in dominant_nodes:
        rows.extend(node_evidence.get(node, ())[:2])
    rows.extend(labels)
    return tuple(dict.fromkeys(row for row in rows if row))[:10]


def _activated_structures(feature_state_model: dict[str, Any], time_context: TimeContext) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for state in feature_state_model.get("priority_features", ()):
        if isinstance(state, dict):
            rows.append(
                {
                    "structure_key": state.get("feature_id", ""),
                    "label": state.get("title", ""),
                    "domain": state.get("domain", ""),
                    "activation": "time_layer" if time_context.status == "ready" else "natal_priority",
                    "score": state.get("priority", 0),
                }
            )
    for layer in time_context.layers:
        rows.append(
            {
                "structure_key": f"time.{layer.layer_key}",
                "label": layer.pillar.display,
                "domain": "time",
                "activation": layer.ten_god.label,
                "score": 0.82,
            }
        )
    return tuple(rows[:12])


def _suppressed_structures(feature_state_model: dict[str, Any], time_context: TimeContext) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for state in feature_state_model.get("evidence_gap_features", ()):
        if isinstance(state, dict):
            rows.append(
                {
                    "structure_key": state.get("feature_id", ""),
                    "label": state.get("title", ""),
                    "domain": state.get("domain", ""),
                    "suppression": state.get("state", "evidence_gap"),
                    "score": state.get("priority", 0),
                }
            )
    for hit in time_context.relation_hits:
        if hit.relation_type in DESTRUCTIVE_RELATIONS:
            rows.append(
                {
                    "structure_key": f"time_relation.{hit.relation_type}.{'.'.join(hit.positions)}",
                    "label": hit.relation_type,
                    "domain": "time",
                    "suppression": "stability_pressure",
                    "score": 0.7,
                }
            )
    return tuple(rows[:12])


def _volatility_score(chart_facts: ChartFacts, time_context: TimeContext) -> float:
    all_relations = tuple(chart_facts.relation_hits) + tuple(time_context.relation_hits)
    pressure_count = sum(1 for row in all_relations if row.relation_type in DESTRUCTIVE_RELATIONS)
    time_pressure = sum(1 for row in time_context.relation_hits if row.relation_type in DESTRUCTIVE_RELATIONS)
    score = 0.18 + pressure_count * 0.08 + time_pressure * 0.12 + len(time_context.layers) * 0.05
    return round(min(0.99, score), 3)


def _stability_shift(stability_score: float, volatility_score: float, time_context: TimeContext) -> str:
    if time_context.status != "ready":
        return "natal_baseline"
    if volatility_score >= 0.55 or stability_score < 0.45:
        return "destabilized"
    if stability_score >= 0.72:
        return "stabilized"
    return "activated"


def _energy_shift(energy_strength: float, time_context: TimeContext) -> str:
    if time_context.status != "ready":
        return "baseline"
    if energy_strength >= 0.72:
        return "amplified"
    if energy_strength <= 0.42:
        return "muted"
    return "activated"
