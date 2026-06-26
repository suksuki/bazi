from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model
from v30.core.constants import CONTROLS, GENERATES


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

FAMILY_ELEMENT = {
    "self": "wood",
    "output": "fire",
    "wealth": "earth",
    "authority": "metal",
    "resource": "water",
}


class DynamicGraphNode(V30Model):
    node_id: str
    label: str
    family: str
    element: str
    layer: str
    weight: float
    evidence_ids: list[str] = Field(default_factory=list)


class DynamicGraphEdge(V30Model):
    source: str
    target: str
    edge_type: str
    role: str
    weight: float


class DynamicGraphPath(V30Model):
    path_id: str
    node_ids: list[str]
    family_chain: list[str]
    edge_types: list[str]
    score: float
    state: str
    evidence_ids: list[str] = Field(default_factory=list)
    competition_rank: int = 0
    suppression: float = 0.0
    conflict_families: list[str] = Field(default_factory=list)
    resolution_families: list[str] = Field(default_factory=list)
    score_reasons: list[str] = Field(default_factory=list)


def build_dynamic_graph(
    evidence: list[FeatureEvidence],
    structure_policy: dict[str, object] | None = None,
) -> tuple[list[DynamicGraphNode], list[DynamicGraphEdge], list[DynamicGraphPath]]:
    nodes = _build_nodes(evidence)
    edges = _build_edges(nodes, evidence)
    paths = _extract_paths(nodes, edges, structure_policy)
    return nodes, edges, paths


def dynamic_graph_nodes(nodes: list[DynamicGraphNode]) -> list[dict[str, object]]:
    return [
        {
            "node_id": node.node_id,
            "kind": "dynamic_graph_node",
            "label": node.label,
            "family": node.family,
            "element": node.element,
            "layer": node.layer,
            "weight": node.weight,
        }
        for node in nodes
    ]


def dynamic_graph_edges(edges: list[DynamicGraphEdge]) -> list[dict[str, object]]:
    return [
        {
            "from": edge.source,
            "to": edge.target,
            "relation": f"dynamic_{edge.edge_type}",
            "role": edge.role,
            "weight": edge.weight,
        }
        for edge in edges
    ]


def dynamic_path_nodes(paths: list[DynamicGraphPath]) -> list[dict[str, object]]:
    return [
        {
            "node_id": path.path_id,
            "kind": "dynamic_path",
            "family_chain": path.family_chain,
            "edge_types": path.edge_types,
            "score": path.score,
            "path_state": path.state,
            "competition_rank": path.competition_rank,
            "suppression": path.suppression,
            "conflict_families": path.conflict_families,
            "resolution_families": path.resolution_families,
            "score_reasons": path.score_reasons,
        }
        for path in paths
    ]


def dynamic_path_edges(paths: list[DynamicGraphPath]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        for evidence_id in path.evidence_ids:
            rows.append({"from": evidence_id, "to": path.path_id, "relation": "supports_dynamic_path"})
        for node_id in path.node_ids:
            rows.append({"from": node_id, "to": path.path_id, "relation": "participates_dynamic_path"})
    return rows


def _build_nodes(evidence: list[FeatureEvidence]) -> list[DynamicGraphNode]:
    rows: list[DynamicGraphNode] = []
    ten_god_rows = [row for row in evidence if row.domain == "ten_god"]
    for item in ten_god_rows:
        for family, labels in _families_from_label(item.label).items():
            rows.append(
                DynamicGraphNode(
                    node_id=f"dynamic.{item.kind}.{family}",
                    label=",".join(labels),
                    family=family,
                    element=FAMILY_ELEMENT.get(family, ""),
                    layer=item.kind,
                    weight=round(item.confidence, 3),
                    evidence_ids=[item.evidence_id],
                )
            )
    if any(row.domain == "chart" for row in evidence):
        rows.append(
            DynamicGraphNode(
                node_id="dynamic.day_master",
                label="day_master",
                family="day_master",
                element="wood",
                layer="chart",
                weight=1.0,
                evidence_ids=[row.evidence_id for row in evidence if row.domain == "chart"],
            )
        )
    return _dedupe_nodes(rows)


def _families_from_label(label: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for ten_god, family in TEN_GOD_FAMILY.items():
        if ten_god in label:
            rows.setdefault(family, []).append(ten_god)
    return rows


def _dedupe_nodes(nodes: list[DynamicGraphNode]) -> list[DynamicGraphNode]:
    by_id: dict[str, DynamicGraphNode] = {}
    for node in nodes:
        current = by_id.get(node.node_id)
        if current is None or node.weight > current.weight:
            by_id[node.node_id] = node
    return list(by_id.values())


def _build_edges(nodes: list[DynamicGraphNode], evidence: list[FeatureEvidence]) -> list[DynamicGraphEdge]:
    rows: list[DynamicGraphEdge] = []
    action_nodes = [node for node in nodes if node.family not in {"day_master", ""}]
    day_master = next((node for node in nodes if node.family == "day_master"), None)
    for source in action_nodes:
        for target in action_nodes:
            if source.node_id == target.node_id:
                continue
            edge = _element_edge(source, target)
            if edge:
                rows.append(edge)
        if day_master is not None:
            if source.element == day_master.element:
                rows.append(DynamicGraphEdge(source=source.node_id, target=day_master.node_id, edge_type="same_family", role="continuity", weight=0.5))
            if GENERATES.get(source.element) == day_master.element:
                rows.append(DynamicGraphEdge(source=source.node_id, target=day_master.node_id, edge_type="support_day_master", role="continuity", weight=0.72))
            if CONTROLS.get(source.element) == day_master.element:
                rows.append(DynamicGraphEdge(source=source.node_id, target=day_master.node_id, edge_type="pressure_day_master", role="pressure", weight=0.58))
    for rule in [row for row in evidence if row.domain == "rule"]:
        state = _rule_state(rule)
        if state in {"blocked", "countered"}:
            role = "countered" if state == "countered" else "blockage"
            rows.extend(
                DynamicGraphEdge(source=node.node_id, target="dynamic.day_master", edge_type=f"rule_{state}", role=role, weight=0.42)
                for node in action_nodes
                if node.family in _families_for_rule(rule)
            )
    branch_relation_types = _branch_relation_types(evidence)
    for relation_type in branch_relation_types:
        edge_type = f"branch_{relation_type}"
        role = _branch_relation_role(relation_type)
        weight = 0.54 if role == "continuity" else 0.57
        rows.extend(
            DynamicGraphEdge(
                source=node.node_id,
                target="dynamic.day_master",
                edge_type=edge_type,
                role=role,
                weight=weight,
            )
            for node in action_nodes
        )
    return _dedupe_edges(rows)


def _element_edge(source: DynamicGraphNode, target: DynamicGraphNode) -> DynamicGraphEdge | None:
    if GENERATES.get(source.element) == target.element:
        return DynamicGraphEdge(source=source.node_id, target=target.node_id, edge_type="generate", role="continuity", weight=0.68)
    if CONTROLS.get(source.element) == target.element:
        return DynamicGraphEdge(source=source.node_id, target=target.node_id, edge_type="control", role="pressure", weight=0.64)
    return None


def _dedupe_edges(edges: list[DynamicGraphEdge]) -> list[DynamicGraphEdge]:
    by_key: dict[tuple[str, str, str], DynamicGraphEdge] = {}
    for edge in edges:
        key = (edge.source, edge.target, edge.edge_type)
        current = by_key.get(key)
        if current is None or edge.weight > current.weight:
            by_key[key] = edge
    return list(by_key.values())


def _extract_paths(
    nodes: list[DynamicGraphNode],
    edges: list[DynamicGraphEdge],
    structure_policy: dict[str, object] | None,
) -> list[DynamicGraphPath]:
    by_id = {node.node_id: node for node in nodes}
    adjacency: dict[str, list[DynamicGraphEdge]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source, []).append(edge)
    raw_paths: list[list[str]] = []
    for node in nodes:
        if node.family in {"day_master", ""}:
            continue
        _walk(node.node_id, adjacency, [node.node_id], raw_paths, max_depth=4)
    paths = [_path_from_ids(index + 1, ids, by_id, adjacency, structure_policy) for index, ids in enumerate(raw_paths)]
    paths = [path for path in paths if len(path.node_ids) >= 2]
    paths = _apply_path_competition(paths, structure_policy)
    return sorted(paths, key=lambda row: (-row.score, row.competition_rank, row.path_id))[:12]


def _walk(current: str, adjacency: dict[str, list[DynamicGraphEdge]], path: list[str], out: list[list[str]], *, max_depth: int) -> None:
    if current == "dynamic.day_master" or len(path) >= max_depth:
        out.append(path)
        return
    for edge in sorted(adjacency.get(current, []), key=lambda row: row.weight, reverse=True)[:6]:
        if edge.target in path:
            continue
        _walk(edge.target, adjacency, [*path, edge.target], out, max_depth=max_depth)


def _path_from_ids(
    index: int,
    ids: list[str],
    by_id: dict[str, DynamicGraphNode],
    adjacency: dict[str, list[DynamicGraphEdge]],
    structure_policy: dict[str, object] | None,
) -> DynamicGraphPath:
    node_rows = [by_id[node_id] for node_id in ids]
    edge_rows = [_find_edge(left, right, adjacency) for left, right in zip(ids, ids[1:])]
    edge_rows = [edge for edge in edge_rows if edge is not None]
    node_score = sum(node.weight for node in node_rows) / max(1, len(node_rows))
    edge_score = sum(edge.weight for edge in edge_rows) / max(1, len(edge_rows))
    blockage_penalty = 0.18 * sum(1 for edge in edge_rows if edge.role == "blockage")
    counter_penalty = 0.04 * sum(1 for edge in edge_rows if edge.role == "countered")
    conflict_weight = _conflict_family_weight(structure_policy)
    conflict_penalty = 0.07 * sum(1 for edge in edge_rows if edge.role == "conflict") / conflict_weight
    terminal_bonus = 0.1 if ids[-1] == "dynamic.day_master" else 0.02
    score = max(0.0, min(1.0, node_score * 0.42 + edge_score * 0.34 + terminal_bonus - blockage_penalty - counter_penalty - conflict_penalty))
    score, policy_reason = _weighted_score(score, structure_policy)
    conflict_families = _conflict_families(edge_rows)
    resolution_families = _resolution_families(edge_rows, ids[-1])
    resolution_weight = _path_resolution_weight(structure_policy)
    if resolution_families:
        score = max(0.0, min(1.0, score * resolution_weight))
    tongguan_zhihua_weight = _tongguan_zhihua_weight(structure_policy)
    if any(family.startswith(("tongguan", "zhihua")) for family in resolution_families):
        score = max(0.0, min(1.0, score * tongguan_zhihua_weight))
    reasons = [
        f"node_score:{round(node_score, 3)}",
        f"edge_score:{round(edge_score, 3)}",
        f"terminal_bonus:{round(terminal_bonus, 3)}",
        f"blockage_penalty:{round(blockage_penalty, 3)}",
        f"counterevidence_penalty:{round(counter_penalty, 3)}",
        f"conflict_family_penalty:{round(conflict_penalty, 3)}",
    ]
    reasons.extend([f"conflict_family:{family}" for family in conflict_families])
    reasons.extend([f"path_resolution:{family}" for family in resolution_families])
    if conflict_weight != 1.0:
        reasons.append(f"structure_policy.dynamic_graph.conflict_family:{conflict_weight}")
    if resolution_families and resolution_weight != 1.0:
        reasons.append(f"structure_policy.dynamic_graph.path_resolution:{resolution_weight}")
    if any(family.startswith(("tongguan", "zhihua")) for family in resolution_families) and tongguan_zhihua_weight != 1.0:
        reasons.append(f"structure_policy.dynamic_graph.tongguan_zhihua:{tongguan_zhihua_weight}")
    if policy_reason:
        reasons.append(policy_reason)
    return DynamicGraphPath(
        path_id=f"dynamic_path.{index}",
        node_ids=ids,
        family_chain=_compact([node.family for node in node_rows]),
        edge_types=[edge.edge_type for edge in edge_rows],
        score=round(score, 3),
        state=_path_state(edge_rows, ids[-1]),
        evidence_ids=sorted({evidence_id for node in node_rows for evidence_id in node.evidence_ids}),
        conflict_families=conflict_families,
        resolution_families=resolution_families,
        score_reasons=reasons,
    )


def _apply_path_competition(
    paths: list[DynamicGraphPath],
    structure_policy: dict[str, object] | None,
) -> list[DynamicGraphPath]:
    suppression_weight = _competition_suppression_weight(structure_policy)
    groups: dict[str, list[DynamicGraphPath]] = {}
    for path in paths:
        groups.setdefault(_competition_key(path), []).append(path)
    ranked: list[DynamicGraphPath] = []
    for rows in groups.values():
        ordered = sorted(rows, key=lambda row: (-row.score, row.path_id))
        for index, path in enumerate(ordered, start=1):
            suppression = round(max(0.0, (index - 1) * 0.035 * suppression_weight), 3)
            score = round(max(0.0, path.score - suppression), 3)
            reasons = [*path.score_reasons, f"competition_rank:{index}"]
            if suppression:
                reasons.append(f"competition_suppression:{suppression}")
            if suppression_weight != 1.0:
                reasons.append(f"structure_policy.dynamic_graph.competition_suppression:{suppression_weight}")
            ranked.append(
                path.model_copy(
                    update={
                        "competition_rank": index,
                        "suppression": suppression,
                        "score": score,
                        "score_reasons": reasons,
                    }
                )
            )
    return ranked


def _competition_key(path: DynamicGraphPath) -> str:
    if path.family_chain:
        return path.family_chain[0]
    return path.node_ids[0] if path.node_ids else "unknown"


def _competition_suppression_weight(structure_policy: dict[str, object] | None) -> float:
    weights = (structure_policy or {}).get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = weights.get("dynamic_graph.competition_suppression", 1.0)
    if not isinstance(value, int | float):
        return 1.0
    return round(max(0.25, min(float(value), 2.0)), 3)


def _conflict_family_weight(structure_policy: dict[str, object] | None) -> float:
    weights = (structure_policy or {}).get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = weights.get("dynamic_graph.conflict_family", 1.0)
    if not isinstance(value, int | float):
        return 1.0
    return round(max(0.25, min(float(value), 2.0)), 3)


def _path_resolution_weight(structure_policy: dict[str, object] | None) -> float:
    weights = (structure_policy or {}).get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = weights.get("dynamic_graph.path_resolution", 1.0)
    if not isinstance(value, int | float):
        return 1.0
    return round(max(0.25, min(float(value), 2.0)), 3)


def _tongguan_zhihua_weight(structure_policy: dict[str, object] | None) -> float:
    weights = (structure_policy or {}).get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = weights.get("dynamic_graph.tongguan_zhihua", 1.0)
    if not isinstance(value, int | float):
        return 1.0
    return round(max(0.25, min(float(value), 2.0)), 3)


def _find_edge(source: str, target: str, adjacency: dict[str, list[DynamicGraphEdge]]) -> DynamicGraphEdge | None:
    return next((edge for edge in adjacency.get(source, []) if edge.target == target), None)


def _compact(families: list[str]) -> list[str]:
    rows: list[str] = []
    for family in families:
        if not family or family == "day_master":
            continue
        if rows and rows[-1] == family:
            continue
        rows.append(family)
    return rows


def _path_state(edges: list[DynamicGraphEdge], terminal: str) -> str:
    if any(edge.role == "countered" for edge in edges):
        return "countered"
    if any(edge.role == "blockage" for edge in edges):
        return "blocked"
    if any(edge.role == "conflict" for edge in edges):
        return "conflict"
    if terminal == "dynamic.day_master":
        return "closed"
    if any(edge.role == "pressure" for edge in edges):
        return "pressure"
    return "partial"


def _rule_state(rule: FeatureEvidence) -> str:
    return next((item.removeprefix("rule_decision_state:") for item in rule.supports if item.startswith("rule_decision_state:")), "")


def _families_for_rule(rule: FeatureEvidence) -> set[str]:
    if rule.kind == "useful_god":
        return {"wealth", "resource", "output"}
    if rule.kind == "hidden_factor":
        return set(FAMILY_ELEMENT)
    if rule.kind == "branch_relation":
        return set(FAMILY_ELEMENT)
    if rule.kind == "time_context":
        return set(FAMILY_ELEMENT)
    return set()


def _branch_relation_types(evidence: list[FeatureEvidence]) -> list[str]:
    relation_types: set[str] = set()
    for row in evidence:
        if row.domain != "branch_relation":
            continue
        for support in row.supports:
            if support.startswith("branch_relation:"):
                relation_types.add(support.removeprefix("branch_relation:"))
    return sorted(relation_types)


def _branch_relation_role(relation_type: str) -> str:
    if relation_type in {"harmony", "three_harmony", "three_meeting"}:
        return "continuity"
    if relation_type in {"clash", "harm", "break", "punishment"}:
        return "conflict"
    return "pressure"


def _conflict_families(edges: list[DynamicGraphEdge]) -> list[str]:
    families: set[str] = set()
    for edge in edges:
        if edge.role == "conflict" and edge.edge_type.startswith("branch_"):
            families.add(edge.edge_type.removeprefix("branch_"))
        if edge.role == "pressure":
            families.add("control_pressure")
        if edge.role == "blockage":
            families.add("rule_blockage")
        if edge.role == "countered":
            families.add("counterevidence")
    return sorted(families)


def _resolution_families(edges: list[DynamicGraphEdge], terminal: str) -> list[str]:
    edge_types = {edge.edge_type for edge in edges}
    roles = {edge.role for edge in edges}
    node_families = [_family_from_node_id(edge.source) for edge in edges]
    if edges:
        node_families.append(_family_from_node_id(edges[-1].target))
    family_chain = _compact(node_families)
    families: set[str] = set()
    if terminal == "dynamic.day_master":
        families.add("reaches_day_master")
    if "generate" in edge_types and "control" in edge_types:
        families.add("generate_control_sequence")
    if any(edge.edge_type == "support_day_master" for edge in edges):
        families.add("resource_support_path")
    if "conflict" in roles and "continuity" in roles:
        families.add("conflict_with_continuity_review")
    if "countered" in roles:
        families.add("counterevidence_resolution")
    if {"authority", "resource"} <= set(family_chain) and terminal == "dynamic.day_master":
        families.add("tongguan_resource_mediator")
    if _contains_sequence(family_chain, ["output", "wealth"]):
        families.add("tongguan_output_wealth_bridge")
    if "control" in edge_types and "generate" in edge_types:
        families.add("zhihua_control_to_generation")
    if _contains_sequence(family_chain, ["output", "authority", "resource"]):
        families.add("zhihua_output_authority_resource")
    if _contains_sequence(family_chain, ["wealth", "authority", "resource"]):
        families.add("zhihua_wealth_authority_resource")
    return sorted(families)


def _family_from_node_id(node_id: str) -> str:
    return node_id.removeprefix("dynamic.").split(".")[-1]


def _contains_sequence(chain: list[str], sequence: list[str]) -> bool:
    if not sequence:
        return False
    cursor = 0
    for item in chain:
        if item == sequence[cursor]:
            cursor += 1
            if cursor == len(sequence):
                return True
    return False


def _weighted_score(score: float, structure_policy: dict[str, object] | None) -> tuple[float, str]:
    weights = (structure_policy or {}).get("weights")
    if not isinstance(weights, dict):
        return score, ""
    value = weights.get("dynamic_graph.v2", weights.get("*", 1.0))
    if isinstance(value, int | float):
        weighted = max(0.0, min(1.0, score * float(value)))
        if float(value) != 1.0:
            return weighted, f"structure_policy.dynamic_graph.v2:{round(float(value), 3)}"
        return weighted, ""
    return score, ""
