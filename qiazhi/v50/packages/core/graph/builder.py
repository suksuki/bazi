from __future__ import annotations

from itertools import combinations
from typing import Any

from core.contracts.material import MaterialType, MingliMaterial, UnifiedMingliMaterialStore
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, CONTROLS, GENERATES, HIDDEN_STEMS, STEM_ELEMENTS, STEM_POLARITY
from core.engines.bazi.material_engine import resolve_ten_god
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphEdgeType, MingliGraphNode, MingliGraphNodeType


POSITION_ORDER = ("year", "month", "day", "hour")

TRIPLE_COMBINATIONS: dict[frozenset[str], tuple[str, str, str]] = {
    frozenset(("巳", "酉", "丑")): ("si_you_chou_metal", "metal", "酉"),
}


def build_mingli_graph_from_material_store(store: UnifiedMingliMaterialStore) -> MingliGraph:
    pillars = _extract_pillars(store)
    if not pillars:
        return MingliGraph(
            graph_id=f"graph:{store.reading_id}:bazi",
            reading_id=store.reading_id,
            nodes=[],
            edges=[],
            source_store_id=store.store_id,
        )

    day_stem = pillars["day"][0]
    nodes: list[MingliGraphNode] = []
    edges: list[MingliGraphEdge] = []
    chart_material_ref = _chart_material_ref(store)

    for position in POSITION_ORDER:
        pillar = pillars[position]
        stem = pillar[0]
        branch = pillar[1]
        stem_node_id = _node_id(store.reading_id, position, "stem", stem)
        branch_node_id = _node_id(store.reading_id, position, "branch", branch)
        nodes.append(
            MingliGraphNode(
                node_id=stem_node_id,
                reading_id=store.reading_id,
                label=stem,
                node_type=MingliGraphNodeType.STEM,
                position=f"{position}_stem",
                element=STEM_ELEMENTS.get(stem, ""),
                yin_yang=STEM_POLARITY.get(stem, ""),
                ten_god="day_master" if position == "day" else resolve_ten_god(day_stem=day_stem, other_stem=stem),
                attributes={"pillar": pillar, "slot": position, "visible": True},
                material_refs=[chart_material_ref],
                evidence_refs=[chart_material_ref],
            )
        )
        nodes.append(
            MingliGraphNode(
                node_id=branch_node_id,
                reading_id=store.reading_id,
                label=branch,
                node_type=MingliGraphNodeType.BRANCH,
                position=f"{position}_branch",
                element=BRANCH_ELEMENTS.get(branch, ""),
                attributes={"pillar": pillar, "slot": position, "hidden_stems": HIDDEN_STEMS.get(branch, [])},
                material_refs=[chart_material_ref],
                evidence_refs=[chart_material_ref],
            )
        )
        edges.append(
            _edge(
                store=store,
                edge_id=f"edge:{store.reading_id}:position:{position}",
                from_node_id=stem_node_id,
                to_node_id=branch_node_id,
                edge_type=MingliGraphEdgeType.POSITION_LINK,
                strength=0.72,
                relation_label="same_pillar_position",
                material_refs=[chart_material_ref],
                attributes={"slot": position},
            )
        )
        for hidden_stem in HIDDEN_STEMS.get(branch, []):
            hidden_id = _node_id(store.reading_id, position, "hidden", hidden_stem)
            nodes.append(
                MingliGraphNode(
                    node_id=hidden_id,
                    reading_id=store.reading_id,
                    label=hidden_stem,
                    node_type=MingliGraphNodeType.HIDDEN_STEM,
                    position=f"{position}_hidden_stem",
                    element=STEM_ELEMENTS.get(hidden_stem, ""),
                    yin_yang=STEM_POLARITY.get(hidden_stem, ""),
                    ten_god=resolve_ten_god(day_stem=day_stem, other_stem=hidden_stem),
                    attributes={"stored_in": branch_node_id, "slot": position, "visible": False},
                    material_refs=[chart_material_ref],
                    evidence_refs=[chart_material_ref],
                )
            )
            edges.append(
                _edge(
                    store=store,
                    edge_id=f"edge:{store.reading_id}:stores:{position}:{branch}:{hidden_stem}",
                    from_node_id=branch_node_id,
                    to_node_id=hidden_id,
                    edge_type=MingliGraphEdgeType.STORES,
                    strength=0.64,
                    relation_label="branch_stores_hidden_stem",
                    material_refs=[chart_material_ref],
                    attributes={"branch": branch, "hidden_stem": hidden_stem},
                )
            )

    nodes = _mark_structural_attributes(nodes, pillars=pillars)
    edges.extend(_element_edges(store=store, nodes=nodes, chart_material_ref=chart_material_ref))
    edges.extend(_combination_edges(store=store, nodes=nodes, pillars=pillars, chart_material_ref=chart_material_ref))

    return MingliGraph(
        graph_id=f"graph:{store.reading_id}:bazi",
        reading_id=store.reading_id,
        nodes=nodes,
        edges=edges,
        source_store_id=store.store_id,
    )


def _extract_pillars(store: UnifiedMingliMaterialStore) -> dict[str, str]:
    for material in store.materials:
        if material.material_type != MaterialType.BAZI_CHART_FACT:
            continue
        pillars = material.raw_value.get("pillars")
        if isinstance(pillars, dict) and all(str(pillars.get(position, "")).strip() for position in POSITION_ORDER):
            return {position: str(pillars[position]) for position in POSITION_ORDER}
    return {}


def _chart_material_ref(store: UnifiedMingliMaterialStore) -> str:
    for material in store.materials:
        if material.material_type == MaterialType.BAZI_CHART_FACT and "pillars" in material.raw_value:
            return material.material_id
    return store.store_id


def _node_id(reading_id: str, position: str, node_kind: str, label: str) -> str:
    return f"node:{reading_id}:bazi:{position}:{node_kind}:{label}"


def _edge(
    *,
    store: UnifiedMingliMaterialStore,
    edge_id: str,
    from_node_id: str,
    to_node_id: str,
    edge_type: MingliGraphEdgeType,
    strength: float,
    relation_label: str,
    material_refs: list[str],
    attributes: dict[str, object] | None = None,
) -> MingliGraphEdge:
    return MingliGraphEdge(
        edge_id=edge_id,
        reading_id=store.reading_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        edge_type=edge_type,
        strength=strength,
        relation_label=relation_label,
        attributes=attributes or {},
        material_refs=material_refs,
        evidence_refs=material_refs,
    )


def _mark_structural_attributes(nodes: list[MingliGraphNode], *, pillars: dict[str, str]) -> list[MingliGraphNode]:
    branch_slots = {position: pillar[1] for position, pillar in pillars.items()}
    present_branches = set(branch_slots.values())
    marked: list[MingliGraphNode] = []
    for node in nodes:
        attrs: dict[str, Any] = dict(node.attributes)
        if node.node_type == MingliGraphNodeType.BRANCH:
            for combination, (combo_id, combo_element, bridge_label) in TRIPLE_COMBINATIONS.items():
                if combination.issubset(present_branches):
                    if node.label in combination:
                        attrs["triple_combination"] = combo_id
                        attrs["triple_combination_element"] = combo_element
                    if node.label == bridge_label:
                        attrs["triple_combination_bridge"] = True
        if node.node_type == MingliGraphNodeType.STEM and node.ten_god in {"shi_shen", "shang_guan"}:
            attrs["output_converter"] = True
        marked.append(node.model_copy(update={"attributes": attrs}))
    return marked


def _element_edges(*, store: UnifiedMingliMaterialStore, nodes: list[MingliGraphNode], chart_material_ref: str) -> list[MingliGraphEdge]:
    edges: list[MingliGraphEdge] = []
    visible_nodes = [node for node in nodes if node.node_type in {MingliGraphNodeType.STEM, MingliGraphNodeType.BRANCH}]
    for source, target in combinations(visible_nodes, 2):
        source_element = source.element
        target_element = target.element
        if not source_element or not target_element:
            continue
        if GENERATES.get(source_element) == target_element:
            edges.append(_element_edge(store, source, target, MingliGraphEdgeType.GENERATES, 0.7, chart_material_ref))
        elif GENERATES.get(target_element) == source_element:
            edges.append(_element_edge(store, target, source, MingliGraphEdgeType.GENERATES, 0.7, chart_material_ref))
        if CONTROLS.get(source_element) == target_element:
            edges.append(_element_edge(store, source, target, MingliGraphEdgeType.CONTROLS, 0.68, chart_material_ref))
        elif CONTROLS.get(target_element) == source_element:
            edges.append(_element_edge(store, target, source, MingliGraphEdgeType.CONTROLS, 0.68, chart_material_ref))
        if source_element == target_element and source.node_id != target.node_id:
            edges.append(_element_edge(store, source, target, MingliGraphEdgeType.SAME_ELEMENT_SUPPORT, 0.58, chart_material_ref))
    return edges


def _element_edge(
    store: UnifiedMingliMaterialStore,
    source: MingliGraphNode,
    target: MingliGraphNode,
    edge_type: MingliGraphEdgeType,
    strength: float,
    chart_material_ref: str,
) -> MingliGraphEdge:
    return _edge(
        store=store,
        edge_id=f"edge:{store.reading_id}:{edge_type.value}:{source.node_id.split(':')[-3]}:{source.label}:{target.node_id.split(':')[-3]}:{target.label}",
        from_node_id=source.node_id,
        to_node_id=target.node_id,
        edge_type=edge_type,
        strength=strength,
        relation_label=edge_type.value,
        material_refs=[chart_material_ref],
        attributes={"from_element": source.element, "to_element": target.element},
    )


def _combination_edges(
    *,
    store: UnifiedMingliMaterialStore,
    nodes: list[MingliGraphNode],
    pillars: dict[str, str],
    chart_material_ref: str,
) -> list[MingliGraphEdge]:
    edges: list[MingliGraphEdge] = []
    branch_nodes = {node.position: node for node in nodes if node.node_type == MingliGraphNodeType.BRANCH}
    present_branches = {pillar[1] for pillar in pillars.values()}
    for combination, (combo_id, combo_element, bridge_label) in TRIPLE_COMBINATIONS.items():
        if not combination.issubset(present_branches):
            continue
        bridge_nodes = [node for node in branch_nodes.values() if node.label == bridge_label]
        if not bridge_nodes:
            continue
        bridge_node = bridge_nodes[0]
        for node in branch_nodes.values():
            if node.label not in combination or node.node_id == bridge_node.node_id:
                continue
            edges.append(
                _edge(
                    store=store,
                    edge_id=f"edge:{store.reading_id}:triple:{combo_id}:{node.position}:{bridge_node.position}",
                    from_node_id=node.node_id,
                    to_node_id=bridge_node.node_id,
                    edge_type=MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION,
                    strength=0.92,
                    relation_label=combo_id,
                    material_refs=[chart_material_ref],
                    attributes={"combination": combo_id, "element": combo_element, "bridge_node_id": bridge_node.node_id},
                )
            )
    return edges
