from __future__ import annotations

from typing import Any

from core.contracts.material import MaterialType, MingliMaterial, UnifiedMingliMaterialStore
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, HIDDEN_STEMS, STEM_ELEMENTS, STEM_POLARITY, TRIPLE_HARMONY
from core.engines.bazi.material_engine import derive_element_relations, resolve_ten_god
from core.graph.contracts import (
    MingliGraph,
    MingliGraphEdge,
    MingliGraphEdgeType,
    MingliGraphNode,
    MingliGraphNodeType,
    MingliRelationState,
)
from core.graph.path_qualification import qualify_relation_for_path


POSITION_ORDER = ("year", "month", "day", "hour")

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
                legacy_unvalidated_strength=0.72,
                relation_label="same_pillar_position",
                material_refs=[chart_material_ref],
                attributes={
                    "slot": position,
                    "mechanism": "same_pillar_bearing",
                    "proximity": "same_pillar",
                    "direct_action": False,
                },
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
                    legacy_unvalidated_strength=0.64,
                    relation_label="branch_stores_hidden_stem",
                    material_refs=[chart_material_ref],
                    attributes={"branch": branch, "hidden_stem": hidden_stem},
                )
            )

    nodes = _mark_structural_attributes(nodes, pillars=pillars)
    edges.extend(_element_edges(store=store, nodes=nodes, chart_material_ref=chart_material_ref))
    edges.extend(_material_relation_edges(store=store, nodes=nodes))
    edges.extend(_material_root_edges(store=store, nodes=nodes))

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
    legacy_unvalidated_strength: float,
    relation_label: str,
    material_refs: list[str],
    relation_state: MingliRelationState = MingliRelationState.STRUCTURAL,
    evidence_refs: list[str] | None = None,
    participant_node_ids: list[str] | None = None,
    attributes: dict[str, object] | None = None,
) -> MingliGraphEdge:
    path_eligibility, eligibility_reason_refs = qualify_relation_for_path(
        edge_type,
        relation_state=relation_state,
    )
    return MingliGraphEdge(
        edge_id=edge_id,
        reading_id=store.reading_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        edge_type=edge_type,
        participant_node_ids=participant_node_ids or [],
        legacy_unvalidated_strength=legacy_unvalidated_strength,
        relation_label=relation_label,
        relation_state=relation_state,
        path_eligibility=path_eligibility,
        eligibility_reason_refs=eligibility_reason_refs,
        attributes=attributes or {},
        material_refs=material_refs,
        evidence_refs=evidence_refs or material_refs,
    )


def _mark_structural_attributes(nodes: list[MingliGraphNode], *, pillars: dict[str, str]) -> list[MingliGraphNode]:
    branch_slots = {position: pillar[1] for position, pillar in pillars.items()}
    present_branches = set(branch_slots.values())
    marked: list[MingliGraphNode] = []
    for node in nodes:
        attrs: dict[str, Any] = dict(node.attributes)
        if node.node_type == MingliGraphNodeType.BRANCH:
            for combination, (combo_id, combo_element, bridge_label) in TRIPLE_HARMONY.items():
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
    atomic_nodes = [
        node
        for node in nodes
        if node.node_type in {MingliGraphNodeType.STEM, MingliGraphNodeType.HIDDEN_STEM}
    ]
    nodes_by_id = {node.node_id: node for node in atomic_nodes}
    strengths = {
        MingliGraphEdgeType.GENERATES: 0.70,
        MingliGraphEdgeType.CONTROLS: 0.68,
        MingliGraphEdgeType.SAME_ELEMENT_SUPPORT: 0.58,
    }
    output: list[MingliGraphEdge] = []
    for relation in derive_element_relations([
        (node.node_id, node.element) for node in atomic_nodes
    ]):
        edge_type = MingliGraphEdgeType(relation["type"])
        output.append(_element_edge(
            store,
            nodes_by_id[relation["source_ref"]],
            nodes_by_id[relation["target_ref"]],
            edge_type,
            strengths[edge_type],
            chart_material_ref,
        ))
    return output


def _element_edge(
    store: UnifiedMingliMaterialStore,
    source: MingliGraphNode,
    target: MingliGraphNode,
    edge_type: MingliGraphEdgeType,
    legacy_unvalidated_strength: float,
    chart_material_ref: str,
) -> MingliGraphEdge:
    return _edge(
        store=store,
        edge_id=f"edge:{store.reading_id}:{edge_type.value}:{source.node_id.split(':')[-3]}:{source.label}:{target.node_id.split(':')[-3]}:{target.label}",
        from_node_id=source.node_id,
        to_node_id=target.node_id,
        edge_type=edge_type,
        legacy_unvalidated_strength=legacy_unvalidated_strength,
        relation_label=edge_type.value,
        material_refs=[chart_material_ref],
        relation_state=MingliRelationState.POTENTIAL,
        attributes={
            "from_element": source.element,
            "to_element": target.element,
            "from_level": source.node_type.value,
            "to_level": target.node_type.value,
            "relation_field": "five_element_potential",
            "projection_scope": "practitioner_or_lab",
            "mechanism_required": True,
            "direct_action": False,
            "same_pillar": source.attributes.get("slot") == target.attributes.get("slot"),
        },
    )


def _material_relation_edges(
    *,
    store: UnifiedMingliMaterialStore,
    nodes: list[MingliGraphNode],
) -> list[MingliGraphEdge]:
    """Project deterministic branch-relation materials into candidate graph edges."""

    branch_nodes = {
        str(node.attributes.get("slot", "")): node
        for node in nodes
        if node.node_type == MingliGraphNodeType.BRANCH
    }
    pair_relation_types = {
        "clash": MingliGraphEdgeType.CLASHES,
        "harmony": MingliGraphEdgeType.HARMONIZES,
        "harm": MingliGraphEdgeType.HARMS,
        "break": MingliGraphEdgeType.BREAKS,
        "punishment": MingliGraphEdgeType.PUNISHES,
        "self_punishment": MingliGraphEdgeType.PUNISHES,
        "half_triple_harmony": MingliGraphEdgeType.FORMS_HALF_COMBINATION,
    }
    relation_labels = {
        "clash": "six_clash",
        "harmony": "six_harmony",
        "harm": "six_harm",
        "break": "six_break",
    }
    edges: list[MingliGraphEdge] = []
    for material in store.materials:
        if material.material_type != MaterialType.BAZI_COMBINATION:
            continue
        relations = material.raw_value.get("relations")
        if not isinstance(relations, list):
            continue
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            relation_name = str(relation.get("type", ""))
            if relation_name in {"triple_harmony", "triple_punishment"}:
                slots = relation.get("slots")
                branches = relation.get("branches")
                if not isinstance(slots, list) or not isinstance(branches, list):
                    continue
                if len(slots) != 3 or len(branches) != 3:
                    continue
                participant_nodes = [branch_nodes.get(str(slot)) for slot in slots]
                if any(node is None for node in participant_nodes):
                    continue
                participants = sorted(
                    (node for node in participant_nodes if node is not None),
                    key=lambda node: POSITION_ORDER.index(str(node.attributes["slot"])),
                )
                if [node.label for node in participant_nodes if node is not None] != [str(branch) for branch in branches]:
                    continue
                source_refs = list(dict.fromkeys([material.material_id, *material.evidence_refs]))
                relation_id = str(relation.get("relation_id", relation_name))
                member_key = ":".join(
                    f"{node.attributes['slot']}:{node.label}"
                    for node in participants
                )
                is_harmony = relation_name == "triple_harmony"
                edge_type = (
                    MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
                    if is_harmony
                    else MingliGraphEdgeType.PUNISHES
                )
                bridge_branch = str(relation.get("bridge_branch", ""))
                bridge_node = next(
                    (node for node in participants if node.label == bridge_branch),
                    participants[1],
                )
                source_node = next(
                    (node for node in participants if node.node_id != bridge_node.node_id),
                    participants[0],
                )
                edges.append(
                    _edge(
                        store=store,
                        edge_id=(
                            f"edge:{store.reading_id}:"
                            f"{'triple' if is_harmony else 'punishes'}:{relation_id}:{member_key}"
                        ),
                        from_node_id=source_node.node_id,
                        to_node_id=bridge_node.node_id,
                        edge_type=edge_type,
                        participant_node_ids=[node.node_id for node in participants],
                        legacy_unvalidated_strength=0.92 if is_harmony else material.confidence,
                        relation_label=relation_id,
                        material_refs=[material.material_id],
                        evidence_refs=source_refs,
                        attributes={
                            "source_material_type": material.material_type.value,
                            "relation_family": "branch_hyperrelation",
                            **({
                                "combination": relation_id,
                                "element": str(relation.get("element", "")),
                                "bridge_node_id": bridge_node.node_id,
                                "required_branches": sorted(str(item) for item in branches),
                            } if is_harmony else {
                                "school_profile": "conservative_complete_set_v1",
                                "punishment_kind": "triple_complete",
                            }),
                        },
                    )
                )
                continue
            edge_type = pair_relation_types.get(relation_name)
            slot_a = str(relation.get("slot_a", ""))
            slot_b = str(relation.get("slot_b", ""))
            node_a = branch_nodes.get(slot_a)
            node_b = branch_nodes.get(slot_b)
            if edge_type is None or node_a is None or node_b is None:
                continue
            if node_a.label != relation.get("branch_a") or node_b.label != relation.get("branch_b"):
                continue
            first, second = sorted(
                (node_a, node_b),
                key=lambda node: (POSITION_ORDER.index(str(node.attributes["slot"])), node.node_id),
            )
            source_refs = list(dict.fromkeys([material.material_id, *material.evidence_refs]))
            edges.append(
                _edge(
                    store=store,
                    edge_id=(
                        f"edge:{store.reading_id}:branch_relation:{edge_type.value}:"
                        f"{first.attributes['slot']}:{first.label}:"
                        f"{second.attributes['slot']}:{second.label}"
                    ),
                    from_node_id=first.node_id,
                    to_node_id=second.node_id,
                    edge_type=edge_type,
                    legacy_unvalidated_strength=(
                        0.66
                        if relation_name == "half_triple_harmony"
                        else material.confidence
                    ),
                    relation_label=str(
                        relation.get("relation_id")
                        or relation_labels.get(relation_name)
                        or relation_name
                    ),
                    material_refs=[material.material_id],
                    evidence_refs=source_refs,
                    attributes={
                        "source_material_type": material.material_type.value,
                        "relation_family": (
                            "branch_pair_candidate"
                            if relation_name == "half_triple_harmony"
                            else "branch_pair"
                        ),
                        "school_profile": (
                            "conservative_complete_set_v1"
                            if relation_name in {"punishment", "self_punishment"}
                            else "shared_structural_v1"
                        ),
                        "punishment_kind": (
                            relation_name if relation_name in {"punishment", "self_punishment"} else ""
                        ),
                        "slots": [first.attributes["slot"], second.attributes["slot"]],
                        "branches": [first.label, second.label],
                        **({
                            "element": str(relation.get("element", "")),
                            "bridge_branch": str(relation.get("bridge_branch", "")),
                            "completion_state": "incomplete",
                            "required_full_relation": next(
                                combo_id
                                for _, (combo_id, combo_element, combo_bridge) in TRIPLE_HARMONY.items()
                                if combo_element == relation.get("element")
                                and combo_bridge == relation.get("bridge_branch")
                            ),
                        } if relation_name == "half_triple_harmony" else {}),
                    },
                )
            )
    return edges


def _material_root_edges(
    *,
    store: UnifiedMingliMaterialStore,
    nodes: list[MingliGraphNode],
) -> list[MingliGraphEdge]:
    day_stem_node = next(
        (
            node
            for node in nodes
            if node.node_type == MingliGraphNodeType.STEM
            and node.position == "day_stem"
        ),
        None,
    )
    branch_nodes = {
        str(node.attributes.get("slot", "")): node
        for node in nodes
        if node.node_type == MingliGraphNodeType.BRANCH
    }
    if day_stem_node is None:
        return []

    edges: list[MingliGraphEdge] = []
    for material in store.materials:
        if material.material_type != MaterialType.BAZI_ROOT_STRENGTH:
            continue
        root_sources = material.raw_value.get("root_sources")
        if not isinstance(root_sources, list):
            continue
        for root_source in root_sources:
            if not isinstance(root_source, dict):
                continue
            slot = str(root_source.get("slot", ""))
            branch = str(root_source.get("branch", ""))
            branch_node = branch_nodes.get(slot)
            if branch_node is None or branch_node.label != branch:
                continue
            source_refs = list(dict.fromkeys([material.material_id, *material.evidence_refs]))
            edges.append(
                _edge(
                    store=store,
                    edge_id=(
                        f"edge:{store.reading_id}:roots:{slot}:{branch}:"
                        f"day:{day_stem_node.label}"
                    ),
                    from_node_id=branch_node.node_id,
                    to_node_id=day_stem_node.node_id,
                    edge_type=MingliGraphEdgeType.ROOTS,
                    legacy_unvalidated_strength=material.confidence,
                    relation_label="day_master_root",
                    material_refs=[material.material_id],
                    evidence_refs=source_refs,
                    attributes={
                        "source_material_type": material.material_type.value,
                        "relation_family": "root_support",
                        "slot": slot,
                        "branch": branch,
                        "hidden_stems": str(root_source.get("hidden_stems", "")),
                        "rooted_stem": day_stem_node.label,
                    },
                )
            )
    return edges
