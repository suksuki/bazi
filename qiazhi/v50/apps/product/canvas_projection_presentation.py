from __future__ import annotations

from typing import Any

from experience.canvas import CanvasDiffSpec, MingliCanvasSpec

from product.canvas_projection_shared import CHANGE_GROUPS, LAYER_DEFINITIONS


def layer_catalog(spec: MingliCanvasSpec) -> list[dict[str, Any]]:
    relations = {item.relation_ref: item for item in spec.relations}
    nodes = {item.node_ref: item for item in spec.nodes}
    disclosed_paths = list(spec.paths)
    formal_paths = [
        item for item in disclosed_paths
        if item.trace.epistemic_status == "committed"
    ]
    formal_path_refs = {item.path_ref for item in formal_paths}
    formal_path_relation_refs = {
        ref
        for path in formal_paths
        for ref in path.relation_refs
        if ref in relations
    }
    audit_path_relation_refs = {
        ref
        for path in disclosed_paths
        for ref in path.relation_refs
        if ref in relations
    }
    formal_path_node_refs = {
        ref for path in formal_paths for ref in path.node_refs
    }
    formal_relation_refs = {
        item.relation_ref
        for item in spec.relations
        if item.relation_state != "potential"
        and item.trace.epistemic_status != "candidate"
    }
    committed_related = [
        item
        for item in spec.relations
        if item.relation_ref in formal_relation_refs
        and item.trace.epistemic_status == "committed"
        and formal_path_node_refs.intersection(item.participant_node_refs)
        and item.relation_ref not in formal_path_relation_refs
    ]
    overview_extras = _overview_relation_refs(
        committed_related,
        nodes=nodes,
    )

    output: list[dict[str, Any]] = []
    for layer_id, label, description, relation_types in LAYER_DEFINITIONS:
        if layer_id == "overview":
            audit_refs = sorted(audit_path_relation_refs | set(overview_extras))
            formal_refs = sorted(formal_path_relation_refs | set(overview_extras))
            audit_paths = [item.path_ref for item in disclosed_paths]
            layer_formal_paths = sorted(formal_path_refs)
        elif layer_id == "work_path":
            audit_refs = sorted(audit_path_relation_refs)
            formal_refs = sorted(formal_path_relation_refs)
            audit_paths = [item.path_ref for item in disclosed_paths]
            layer_formal_paths = sorted(formal_path_refs)
        elif layer_id == "timing":
            audit_refs = sorted(
                item.relation_ref
                for item in spec.relations
                if _is_temporal_relation(item.participant_node_refs, nodes=nodes)
            )
            formal_refs = sorted(set(audit_refs).intersection(formal_relation_refs))
            audit_paths = []
            layer_formal_paths = []
        else:
            audit_refs = sorted(
                item.relation_ref
                for item in spec.relations
                if item.relation_type in relation_types
            )
            relevant_formal = {
                item.relation_ref
                for item in spec.relations
                if item.relation_type in relation_types
                and item.relation_ref in formal_relation_refs
                and (
                    item.relation_ref in formal_path_relation_refs
                    or bool(formal_path_node_refs.intersection(item.participant_node_refs))
                )
            }
            formal_refs = sorted(relevant_formal)
            audit_paths = []
            layer_formal_paths = []
        output.append({
            "layer_id": layer_id,
            "label": label,
            "description": description,
            "relation_refs": audit_refs,
            "formal_relation_refs": formal_refs,
            "path_refs": sorted(audit_paths),
            "formal_path_refs": layer_formal_paths,
            "available": bool(audit_refs or audit_paths),
            "count": len(audit_refs),
            "formal_count": len(formal_refs),
        })
    return output


def scene_slot_catalog(
    *,
    spec: MingliCanvasSpec,
    canonical_spec: MingliCanvasSpec,
) -> list[dict[str, Any]]:
    slot_order = (
        ("natal_year", "年柱"),
        ("natal_month", "月柱"),
        ("natal_day", "日柱"),
        ("natal_hour", "时柱"),
        ("luck", "大运"),
        ("year", "流年"),
    )
    current_slots = {item.slot_type: item for item in spec.semantic_slots}
    canonical_slots = {item.slot_type: item for item in canonical_spec.semantic_slots}
    nodes_by_slot: dict[str, list[Any]] = {}
    for node in spec.nodes:
        nodes_by_slot.setdefault(node.semantic_slot_ref, []).append(node)
    output: list[dict[str, Any]] = []
    for index, (slot_type, fallback_label) in enumerate(slot_order):
        current = current_slots.get(slot_type)
        canonical = canonical_slots.get(slot_type)
        slot = current or canonical
        slot_nodes = nodes_by_slot.get(current.slot_ref, []) if current else []
        stem_node = next(
            (
                item for item in slot_nodes
                if "stem" in item.node_type and "hidden" not in item.node_type
            ),
            None,
        )
        branch_node = next(
            (item for item in slot_nodes if "branch" in item.node_type),
            None,
        )
        output.append({
            "position_index": index,
            "slot_type": slot_type,
            "label": slot.label if slot else fallback_label,
            "state": "active" if current else "inactive" if canonical else "not_loaded",
            "slot_ref": slot.slot_ref if slot else f"slot-placeholder-{slot_type}",
            "stem_node_ref": stem_node.node_ref if stem_node else "",
            "branch_node_ref": branch_node.node_ref if branch_node else "",
            "stem": slot.stem if slot else "",
            "branch": slot.branch if slot else "",
            "hidden_stems": list(slot.hidden_stems) if slot else [],
            "immutable": bool(slot.immutable) if slot else slot_type.startswith("natal_"),
        })
    return output


def _overview_relation_refs(relations: list[Any], *, nodes: dict[str, Any]) -> list[str]:
    support_types = {
        "generates",
        "same_element_support",
        "roots",
        "stores",
        "harmonizes",
        "forms_half_combination",
        "forms_triple_combination",
    }
    restraint_types = {"controls", "clashes", "punishes", "harms", "breaks"}
    selected: list[str] = []
    for relation_types in (support_types, restraint_types):
        match = next(
            (
                item for item in sorted(relations, key=lambda row: row.relation_ref)
                if item.relation_type in relation_types
            ),
            None,
        )
        if match is not None:
            selected.append(match.relation_ref)
    timing = next(
        (
            item for item in sorted(relations, key=lambda row: row.relation_ref)
            if _is_temporal_relation(item.participant_node_refs, nodes=nodes)
        ),
        None,
    )
    if timing is not None and timing.relation_ref not in selected:
        selected.append(timing.relation_ref)
    return selected[:3]


def _is_temporal_relation(
    participant_node_refs: list[str],
    *,
    nodes: dict[str, Any],
) -> bool:
    return any(
        (node := nodes.get(ref)) is not None
        and node.semantic_slot_ref
        and (node.node_type.startswith("luck_") or node.node_type.startswith("year_"))
        for ref in participant_node_refs
    )


def change_groups(
    *,
    diff: CanvasDiffSpec | None,
    before_spec: MingliCanvasSpec,
    after_spec: MingliCanvasSpec,
) -> list[dict[str, Any]]:
    if diff is None:
        return [
            {"change_type": kind, "label": label, "items": [], "count": 0}
            for kind, label in CHANGE_GROUPS
        ]
    before = object_labels(before_spec)
    after = object_labels(after_spec)
    collections = {
        "introduced": [*diff.added_nodes, *diff.added_relations, *diff.added_clusters, *diff.introduced_paths],
        "removed": [*diff.removed_nodes, *diff.removed_relations, *diff.removed_clusters, *diff.removed_paths],
        "activated": [*diff.changed_relations, *diff.activated_paths],
        "reinforced": list(diff.reinforced_paths),
        "weakened": list(diff.weakened_paths),
        "blocked": list(diff.blocked_paths),
        "reopened": list(diff.reopened_paths),
        "unchanged": list(diff.unchanged_paths),
    }
    output: list[dict[str, Any]] = []
    for kind, label in CHANGE_GROUPS:
        rows = collections[kind]
        items = [
            {
                "target_ref": item.target_ref,
                "object_type": item.object_type,
                "label": after.get(item.target_ref) or before.get(item.target_ref) or item.target_ref,
                "before_state": item.before_state,
                "after_state": item.after_state,
                "reason_refs": item.reason_refs,
            }
            for item in rows
            if item.change_type == kind
        ]
        output.append({"change_type": kind, "label": label, "items": items, "count": len(items)})
    return output


def object_labels(spec: MingliCanvasSpec) -> dict[str, str]:
    return {
        **{item.slot_ref: f"{item.label} {item.stem}{item.branch}" for item in spec.semantic_slots},
        **{item.node_ref: item.label for item in spec.nodes},
        **{item.relation_ref: item.label for item in spec.relations},
        **{item.cluster_ref: item.label for item in spec.clusters},
        **{item.path_ref: item.label for item in spec.paths},
    }


def object_refs(spec: MingliCanvasSpec) -> set[str]:
    return {
        *(item.slot_ref for item in spec.semantic_slots),
        *(item.node_ref for item in spec.nodes),
        *(item.relation_ref for item in spec.relations),
        *(item.cluster_ref for item in spec.clusters),
        *(item.path_ref for item in spec.paths),
    }


def previous_stage(stage: str) -> str:
    return {"natal": "natal", "luck": "natal", "year": "luck"}[stage]


def stage_title(stage: str, source: dict[str, Any]) -> str:
    return {
        "natal": "只看原局",
        "luck": f"加入 {source['luck_pillar']} 大运",
        "year": f"再加入 {source['analysis_year']} · {source['annual_pillar']} 流年",
    }[stage]


def stage_summary(stage: str, source: dict[str, Any]) -> str:
    if stage == "natal":
        return "四柱与正式基线结构，不叠加时间变量。"
    if stage == "luck":
        return "大运位置已加入；没有正式路径更新时，系统不会猜测增强或受阻。"
    return "流年位置已加入；只展示已有合同变化，不预测具体事件。"
