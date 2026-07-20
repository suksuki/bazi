from __future__ import annotations

from typing import Any

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    BRANCH_POLARITY,
    HIDDEN_STEMS,
    STEM_ELEMENTS,
    STEM_POLARITY,
)
from core.engines.bazi.material_engine import resolve_ten_god
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphNode
from product.projection_refs import anonymous_ref


RELATION_LABELS = {
    "generates": "相生",
    "controls": "相克",
    "same_element_support": "同气",
    "stores": "藏干",
    "roots": "通根",
    "forms_half_combination": "半合",
    "forms_triple_combination": "三合",
    "clashes": "相冲",
    "harmonizes": "相合",
    "activates": "引动",
    "bridges": "通关",
    "position_link": "同柱",
}


def compile_onecanvas_structural_variant(
    *,
    axis: str,
    index: int,
    birth: BirthInputCanonical,
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
    timing_recalculation: dict[str, Any],
) -> dict[str, Any]:
    variant = compile_graph_variant(
        index=index,
        time_value=birth.birth_time,
        birth=birth,
        graph=build_structural_graph(birth=birth, reading_id=f"onecanvas-{axis}-{index:02d}"),
        baseline_pillars=baseline_pillars,
        baseline_relations=baseline_relations,
        formal_path=formal_path,
    )
    variant["variant_id"] = f"{axis}-variant-{index:02d}"
    variant["edit_axis"] = axis
    variant["cycle_index"] = index
    variant["selected_pillar"] = str(birth.year_pillar if axis == "year" else birth.day_pillar)
    variant["display_label"] = cycle_display_label(axis=axis, variant=variant)
    variant["structural_candidate_ref"] = anonymous_ref(
        f"{axis}:{index}:{'|'.join(variant['pillars'])}",
        "cycle-candidate",
    )
    variant["selection_context"] = {
        "disclosure_mode": "sexagenary_cycle_structural",
        "cycle_index": index,
        "cycle_position": index + 1,
        "selected_pillar": variant["selected_pillar"],
        "linked_slot": "month" if axis == "year" else "hour",
        "linked_pillar": str(variant["pillars"][1 if axis == "year" else 3]),
        "dependency_rule": "five_tigers" if axis == "year" else "five_rats",
        "maps_to_real_birth_datetime": False,
        "raw_birth_datetime_in_fixture": False,
    }
    variant["timing_recalculation"] = timing_recalculation
    variant.pop("time_value", None)
    variant["time_range"] = "结构实验保持原时支；不反查真实出生时刻"
    prepare_variant_for_canvas(variant)
    return variant


def build_structural_graph(*, birth: BirthInputCanonical, reading_id: str) -> MingliGraph:
    calendar = normalize_birth_input(birth)
    materials = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=calendar,
    )
    return build_mingli_graph_from_material_store(materials)


def compile_graph_variant(
    *,
    index: int,
    time_value: str,
    birth: BirthInputCanonical,
    graph: MingliGraph,
    baseline_pillars: list[str],
    baseline_relations: list[dict[str, Any]],
    formal_path: dict[str, Any],
) -> dict[str, Any]:
    pillars = [birth.year_pillar, birth.month_pillar, birth.day_pillar, birth.hour_pillar]
    nodes = visible_nodes(graph=graph, day_stem=birth.day_pillar[0])
    relations = visible_relations(graph=graph)
    relation_index = {
        (item["from_anchor"], item["to_anchor"], item["relation_type"]): item
        for item in relations
    }
    continuity = []
    for segment in formal_path["segments"]:
        replacement = relation_index.get((
            segment["from_anchor"],
            segment["to_anchor"],
            segment["relation_type"],
        ))
        continuity.append({
            "baseline": segment,
            "status": "preserved" if replacement else "missing",
            "variant_relation": replacement,
        })
    preserved_count = sum(item["status"] == "preserved" for item in continuity)
    if preserved_count == len(continuity):
        continuity_status = "preserved"
    elif preserved_count:
        continuity_status = "partial"
    else:
        continuity_status = "broken"
    baseline_keys = {relation_key(item) for item in baseline_relations}
    variant_keys = {relation_key(item) for item in relations}
    added = [item for item in relations if relation_key(item) not in baseline_keys]
    removed = [item for item in baseline_relations if relation_key(item) not in variant_keys]
    return {
        "variant_id": f"hour-variant-{index:02d}",
        "source_mode": "canonical" if pillars == baseline_pillars else "hypothetical",
        "time_value": time_value,
        "time_range": time_range(time_value),
        "pillars": pillars,
        "calendar_compatible_with_locked_ymd": pillars[:3] == baseline_pillars[:3],
        "calendar_boundary_changes": [
            {"slot": slot, "before": baseline_pillars[i], "after": pillars[i]}
            for i, slot in enumerate(("year", "month", "day"))
            if pillars[i] != baseline_pillars[i]
        ],
        "nodes": nodes,
        "relations": relations,
        "formal_path_reference": {
            "continuity_status": continuity_status,
            "preserved_segments": preserved_count,
            "total_segments": len(continuity),
            "segments": continuity,
            "authority": "deterministic_structural_comparison",
        },
        "graph_candidate": graph_candidate(graph=graph),
        "diff": {
            "changed_pillars": [
                {"slot": slot, "before": baseline_pillars[i], "after": pillars[i]}
                for i, slot in enumerate(("year", "month", "day", "hour"))
                if pillars[i] != baseline_pillars[i]
            ],
            "added_relation_count": len(added),
            "removed_relation_count": len(removed),
            "added_relations": added[:6],
            "removed_relations": removed[:6],
        },
    }


def visible_nodes(*, graph: MingliGraph, day_stem: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for node in graph.nodes:
        if node.node_type.value not in {"stem", "branch"}:
            continue
        branch = node.label if node.node_type.value == "branch" else ""
        hidden = [
            {
                "stem": stem,
                "element": STEM_ELEMENTS.get(stem, ""),
                "polarity": STEM_POLARITY.get(stem, ""),
                "ten_god": resolve_ten_god(day_stem=day_stem, other_stem=stem),
            }
            for stem in HIDDEN_STEMS.get(branch, [])
        ]
        output.append({
            "node_key": node.position,
            "label": node.label,
            "node_type": node.node_type.value,
            "position": node.position,
            "element": node.element,
            "polarity": node.yin_yang or BRANCH_POLARITY.get(branch, ""),
            "ten_god": node.ten_god,
            "hidden_stems": hidden,
            "source_refs": [
                anonymous_ref(item, "source")
                for item in [*node.material_refs, *node.evidence_refs]
            ],
        })
    return output


def visible_relations(*, graph: MingliGraph) -> list[dict[str, Any]]:
    nodes = {item.node_id: item for item in graph.nodes}
    output: list[dict[str, Any]] = []
    for edge in graph.edges:
        source = nodes[edge.from_node_id]
        target = nodes[edge.to_node_id]
        if source.node_type.value not in {"stem", "branch"} or target.node_type.value not in {"stem", "branch"}:
            continue
        output.append(project_relation(edge=edge, source=source, target=target))
    return output


def graph_candidate(*, graph: MingliGraph) -> dict[str, Any] | None:
    visible = {
        node.node_id
        for node in graph.nodes
        if node.node_type.value in {"stem", "branch"}
    }
    nodes = {item.node_id: item for item in graph.nodes}
    edges = {item.edge_id: item for item in graph.edges}
    paths = explore_mingli_paths(graph, max_edges=3, limit=80).paths
    selected = next((
        item for item in paths
        if len(item.edge_ids) >= 2
        and set(item.node_ids).issubset(visible)
        and all(edges[edge_id].edge_type.value != "position_link" for edge_id in item.edge_ids)
    ), None)
    if selected is None:
        return None
    return {
        "path_ref": anonymous_ref(selected.path_id, "path"),
        "authority": "experimental_graph_candidate",
        "epistemic_status": "candidate",
        "node_keys": [nodes[item].position for item in selected.node_ids],
        "node_labels": [nodes[item].label for item in selected.node_ids],
        "segments": [
            project_relation(
                edge=edges[edge_id],
                source=nodes[edges[edge_id].from_node_id],
                target=nodes[edges[edge_id].to_node_id],
            )
            for edge_id in selected.edge_ids
        ],
        "source_refs": [
            anonymous_ref(item, "source")
            for item in [selected.path_id, *selected.graph_refs, *selected.evidence_refs]
        ],
        "warning": "Graph 排名候选只用于结构实验，不是 LifeCase 正式主路径。",
    }


def project_relation(
    *,
    edge: MingliGraphEdge,
    source: MingliGraphNode,
    target: MingliGraphNode,
) -> dict[str, Any]:
    relation_type = edge.edge_type.value
    return {
        "relation_id": anonymous_ref(edge.edge_id, "relation"),
        "from_key": source.position,
        "to_key": target.position,
        "from_anchor": source.position,
        "to_anchor": target.position,
        "from_label": source.label,
        "to_label": target.label,
        "relation_type": relation_type,
        "label": f"{source.label}{RELATION_LABELS.get(relation_type, relation_type)}{target.label}",
        "source_refs": [
            anonymous_ref(item, "source")
            for item in [*edge.material_refs, *edge.evidence_refs]
        ],
    }


def pillar_nodes(
    *,
    pillar: str,
    slot: str,
    day_stem: str,
    source_mode: str,
    source_refs: list[str],
) -> list[dict[str, Any]]:
    if len(pillar) < 2:
        return []
    stem, branch = pillar[0], pillar[1]
    epistemic_status = "derived" if source_mode == "derived" else source_mode
    return [
        {
            "node_key": f"{slot}_stem",
            "semantic_ref": f"node:{slot}_stem",
            "label": stem,
            "node_type": "stem",
            "position": f"{slot}_stem",
            "element": STEM_ELEMENTS.get(stem, ""),
            "polarity": STEM_POLARITY.get(stem, ""),
            "ten_god": resolve_ten_god(day_stem=day_stem, other_stem=stem),
            "hidden_stems": [],
            "source_mode": source_mode,
            "epistemic_status": epistemic_status,
            "source_refs": source_refs,
        },
        {
            "node_key": f"{slot}_branch",
            "semantic_ref": f"node:{slot}_branch",
            "label": branch,
            "node_type": "branch",
            "position": f"{slot}_branch",
            "element": BRANCH_ELEMENTS.get(branch, ""),
            "polarity": BRANCH_POLARITY.get(branch, ""),
            "ten_god": "",
            "hidden_stems": [],
            "source_mode": source_mode,
            "epistemic_status": epistemic_status,
            "source_refs": source_refs,
        },
    ]


def prepare_variant_for_canvas(candidate: dict[str, Any]) -> None:
    timing = candidate["timing_recalculation"]
    day_stem = str(candidate["pillars"][2])[0]
    source_mode = str(candidate["source_mode"])
    for node in candidate["nodes"]:
        node["semantic_ref"] = f"node:{node['node_key']}"
        node["source_mode"] = source_mode
        node["epistemic_status"] = "canonical" if source_mode == "canonical" else "hypothetical"
    timing_refs = list(timing.get("calculation_refs") or [])
    candidate["nodes"].extend(pillar_nodes(
        pillar=str(timing.get("luck_pillar") or ""),
        slot="luck",
        day_stem=day_stem,
        source_mode="derived" if source_mode == "canonical" else "hypothetical",
        source_refs=timing_refs,
    ))
    candidate["nodes"].extend(pillar_nodes(
        pillar=str(timing.get("annual_pillar") or ""),
        slot="annual",
        day_stem=day_stem,
        source_mode="derived" if source_mode == "canonical" else "hypothetical",
        source_refs=timing_refs,
    ))
    for relation in candidate["relations"]:
        relation["semantic_ref"] = f"relation:{relation['relation_id']}"
    candidate_path = candidate.get("graph_candidate")
    if isinstance(candidate_path, dict):
        candidate_path["semantic_ref"] = f"path:{candidate_path['path_ref']}"
        for segment in candidate_path.get("segments") or []:
            segment["semantic_ref"] = f"relation:{segment['relation_id']}"
    reference = candidate.get("formal_path_reference")
    if isinstance(reference, dict):
        for item in reference.get("segments") or []:
            baseline = item.get("baseline")
            if isinstance(baseline, dict):
                baseline["semantic_ref"] = f"relation:{baseline['relation_ref']}"
            replacement = item.get("variant_relation")
            if isinstance(replacement, dict):
                replacement["semantic_ref"] = f"relation:{replacement['relation_id']}"


def refresh_temporal_nodes(*, variant: dict[str, Any], timing: dict[str, Any]) -> None:
    variant["nodes"] = [
        node
        for node in variant.get("nodes") or []
        if str(node.get("node_key") or "").split("_", 1)[0] not in {"luck", "annual"}
    ]
    variant["timing_recalculation"] = timing
    day_stem = str(variant["pillars"][2])[0]
    source_mode = "derived" if variant.get("source_mode") == "canonical" else "hypothetical"
    refs = list(timing.get("calculation_refs") or [])
    variant["nodes"].extend(pillar_nodes(
        pillar=str(timing.get("luck_pillar") or ""),
        slot="luck",
        day_stem=day_stem,
        source_mode=source_mode,
        source_refs=refs,
    ))
    variant["nodes"].extend(pillar_nodes(
        pillar=str(timing.get("annual_pillar") or ""),
        slot="annual",
        day_stem=day_stem,
        source_mode=source_mode,
        source_refs=refs,
    ))


def cycle_display_label(*, axis: str, variant: dict[str, Any]) -> str:
    selected = str(variant["pillars"][0 if axis == "year" else 2])
    linked = str(variant["pillars"][1 if axis == "year" else 3])
    linked_label = "月柱" if axis == "year" else "时柱"
    return f"{selected} · {linked_label}联动为 {linked}"


def relation_key(item: dict[str, Any]) -> str:
    return "|".join((
        item["from_anchor"],
        item["from_label"],
        item["relation_type"],
        item["to_anchor"],
        item["to_label"],
    ))


def time_range(time_value: str) -> str:
    hour = int(time_value[:2])
    branch = "子丑寅卯辰巳午未申酉戌亥"[hour // 2]
    start = (hour - 1) % 24
    end = (hour + 1) % 24
    return f"{branch}时 · {start:02d}:00–{end:02d}:00"
