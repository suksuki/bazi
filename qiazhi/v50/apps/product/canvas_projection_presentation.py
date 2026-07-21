from __future__ import annotations

from typing import Any

from experience.canvas import CanvasDiffSpec, MingliCanvasSpec

from product.canvas_projection_shared import CHANGE_GROUPS, LAYER_DEFINITIONS


def layer_catalog(spec: MingliCanvasSpec) -> list[dict[str, Any]]:
    relations = {item.relation_ref: item for item in spec.relations}
    output = [
        {
            "layer_id": layer_id,
            "label": label,
            "description": description,
            "relation_refs": sorted(
                item.relation_ref
                for item in relations.values()
                if item.relation_type in relation_types
            ),
        }
        for layer_id, label, description, relation_types in LAYER_DEFINITIONS
    ]
    work_refs = sorted({ref for path in spec.paths for ref in path.relation_refs if ref in relations})
    output.append({
        "layer_id": "work_path",
        "label": "做功",
        "description": "只显示已经进入当前角色披露范围的路径关系。",
        "relation_refs": work_refs,
    })
    for item in output:
        item["available"] = bool(item["relation_refs"])
        item["count"] = len(item["relation_refs"])
    return output


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
