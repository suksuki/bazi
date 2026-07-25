from __future__ import annotations

from typing import Any, Literal

from core.engines.bazi import derive_branch_relations, derive_element_relations
from core.engines.bazi.knowledge import BRANCH_ELEMENTS, HIDDEN_STEMS, STEM_ELEMENTS, STEM_POLARITY
from core.engines.bazi.material_engine import resolve_ten_god
from core.graph import NodeRef, RelationKey, RelationPositionContext, canonical_scene_scope_ref
from core.graph.contracts import MingliGraphEdgeType, MingliRelationState, PathEligibility
from core.graph.path_qualification import qualify_relation_for_path
from core.graph.provenance import relation_directionality
from core.life_case import LifeCase
from core.mingli_agent.contracts import ChartWorldInstance
from experience.canvas import (
    CanvasNode,
    CanvasPath,
    CanvasPathStateUpdate,
    CanvasRelation,
    CanvasSemanticSlot,
    CanvasTemporalLayer,
    CanvasTrace,
)

from product.canvas_projection_shared import (
    BRANCH_POLARITY,
    RELATION_LABELS,
    TEMPORAL_PATH_UPDATE_POLICY_VERSION,
    refs,
)


def temporal_layers(
    *,
    timing: dict[str, Any],
    world: ChartWorldInstance,
    life_case: LifeCase,
    day_stem: str,
    natal_relation_nodes: list[tuple[CanvasNode, NodeRef]],
    tracked_paths: list[CanvasPath],
) -> list[CanvasTemporalLayer]:
    source_refs = refs(
        [str(item) for item in timing.get("calculation_refs") or []],
        fallback=f"world:{world.world_id}:timing-context",
    )
    output: list[CanvasTemporalLayer] = []
    relation_nodes = list(natal_relation_nodes)
    current_paths = {item.path_ref: item for item in tracked_paths}
    luck_pillar = str(timing.get("luck_pillar") or "")
    if len(luck_pillar) >= 2:
        raw_range = timing.get("luck_year_range")
        luck_range = raw_range if isinstance(raw_range, list) else []
        suffix = "-".join(str(item) for item in luck_range) or "current"
        layer, layer_nodes = temporal_layer(
            layer_type="luck",
            pillar=luck_pillar,
            world=world,
            life_case=life_case,
            snapshot_suffix=suffix,
            day_stem=day_stem,
            source_refs=source_refs,
            relation_nodes=relation_nodes,
            tracked_paths=list(current_paths.values()),
        )
        output.append(layer)
        relation_nodes.extend(layer_nodes)
        current_paths = apply_temporal_path_updates(current_paths, layer.path_updates)
    annual_pillar = str(timing.get("annual_pillar") or "")
    if len(annual_pillar) >= 2:
        layer, layer_nodes = temporal_layer(
            layer_type="year",
            pillar=annual_pillar,
            world=world,
            life_case=life_case,
            snapshot_suffix=str(timing.get("analysis_year") or "current"),
            day_stem=day_stem,
            source_refs=source_refs,
            relation_nodes=relation_nodes,
            tracked_paths=list(current_paths.values()),
        )
        output.append(layer)
        relation_nodes.extend(layer_nodes)
        current_paths = apply_temporal_path_updates(current_paths, layer.path_updates)
    return output


def temporal_layer(
    *,
    layer_type: Literal["luck", "year"],
    pillar: str,
    world: ChartWorldInstance,
    life_case: LifeCase,
    snapshot_suffix: str,
    day_stem: str,
    source_refs: list[str],
    relation_nodes: list[tuple[CanvasNode, NodeRef]],
    tracked_paths: list[CanvasPath],
) -> tuple[CanvasTemporalLayer, list[tuple[CanvasNode, NodeRef]]]:
    stem, branch = pillar[0], pillar[1]
    layer_id = f"{layer_type}:{world.world_id}:{pillar}:{snapshot_suffix}"
    slot_ref = f"slot-{layer_type}-{world.world_id}-{pillar}"
    temporal_snapshot_ref = f"temporal:{world.world_id}:{layer_type}:{snapshot_suffix}"
    scene_ref = canonical_scene_scope_ref(
        life_case_id=life_case.life_case_id,
        chart_version_id=life_case.chart_version.version_id,
    )
    temporal_node_models = {
        "stem": NodeRef(
            scene_ref=scene_ref,
            life_case_id=life_case.life_case_id,
            chart_version_id=life_case.chart_version.version_id,
            world_id=world.world_id,
            scope=layer_type,
            slot=layer_type,
            level="stem",
            component=stem,
            temporal_snapshot_ref=temporal_snapshot_ref,
        ),
        "branch": NodeRef(
            scene_ref=scene_ref,
            life_case_id=life_case.life_case_id,
            chart_version_id=life_case.chart_version.version_id,
            world_id=world.world_id,
            scope=layer_type,
            slot=layer_type,
            level="branch",
            component=branch,
            temporal_snapshot_ref=temporal_snapshot_ref,
        ),
    }
    trace = CanvasTrace(
        source_mode="derived",
        epistemic_status="fact",
        source_refs=source_refs,
        uncertainty=["时间柱已完成历法计算；其现实作用仍需正式命理认知"],
        disclosure="member",
    )
    temporal_nodes = [
        CanvasNode(
            node_ref=temporal_node_models["stem"].node_ref,
            label=stem,
            node_type=f"{layer_type}_stem",
            semantic_slot_ref=slot_ref,
            element=STEM_ELEMENTS.get(stem, ""),
            polarity=STEM_POLARITY.get(stem, ""),
            ten_god=resolve_ten_god(day_stem=day_stem, other_stem=stem),
            trace=trace,
        ),
        CanvasNode(
            node_ref=temporal_node_models["branch"].node_ref,
            label=branch,
            node_type=f"{layer_type}_branch",
            semantic_slot_ref=slot_ref,
            element=BRANCH_ELEMENTS.get(branch, ""),
            polarity=BRANCH_POLARITY.get(branch, ""),
            trace=trace,
        ),
    ]
    current_relation_nodes = [
        (temporal_nodes[0], temporal_node_models["stem"]),
        (temporal_nodes[1], temporal_node_models["branch"]),
    ]
    relations = temporal_relations(
        layer_type=layer_type,
        existing_nodes=relation_nodes,
        current_nodes=current_relation_nodes,
        scene_ref=scene_ref,
        source_refs=source_refs,
    )
    layer = CanvasTemporalLayer(
        layer_id=layer_id,
        layer_type=layer_type,
        layer_mode="official",
        temporal_snapshot_id=temporal_snapshot_ref,
        slot=CanvasSemanticSlot(
            slot_ref=slot_ref,
            slot_type=layer_type,
            label="大运" if layer_type == "luck" else "流年",
            stem=stem,
            branch=branch,
            hidden_stems=list(HIDDEN_STEMS.get(branch, [])),
            immutable=False,
            trace=trace,
        ),
        nodes=temporal_nodes,
        relations=relations,
        path_updates=temporal_path_updates(
            tracked_paths=tracked_paths,
            relations=relations,
            temporal_node_refs={item.node_ref for item, _ in current_relation_nodes},
            layer_type=layer_type,
        ),
        source_refs=source_refs,
    )
    return layer, current_relation_nodes


def apply_temporal_path_updates(
    current_paths: dict[str, CanvasPath],
    updates: list[CanvasPathStateUpdate],
) -> dict[str, CanvasPath]:
    output = dict(current_paths)
    for update in updates:
        path = output.get(update.path_ref)
        if path is None:
            continue
        output[update.path_ref] = path.model_copy(
            update={
                "semantic_state": update.semantic_state,
                "state_trace": update.state_trace,
                "change_reason_refs": update.change_reason_refs,
            }
        )
    return output


def temporal_path_updates(
    *,
    tracked_paths: list[CanvasPath],
    relations: list[CanvasRelation],
    temporal_node_refs: set[str],
    layer_type: Literal["luck", "year"],
) -> list[CanvasPathStateUpdate]:
    updates: list[CanvasPathStateUpdate] = []
    for path in tracked_paths:
        required_refs = set(path.required_refs or path.node_refs)
        support_refs: list[str] = []
        restraint_refs: list[str] = []
        for relation in relations:
            if relation.relation_state not in {"time_activated", "effective"}:
                continue
            try:
                relation_type = MingliGraphEdgeType(relation.relation_type)
            except ValueError:
                continue
            eligibility, _ = qualify_relation_for_path(
                relation_type,
                relation_state=MingliRelationState(relation.relation_state),
            )
            if eligibility != PathEligibility.ELIGIBLE:
                continue
            if relation_type == MingliGraphEdgeType.GENERATES:
                if relation.from_node_ref in temporal_node_refs and relation.to_node_ref in required_refs:
                    support_refs.append(relation.relation_ref)
            elif relation_type == MingliGraphEdgeType.SAME_ELEMENT_SUPPORT:
                participants = set(relation.participant_node_refs) or {
                    relation.from_node_ref,
                    relation.to_node_ref,
                }
                if participants.intersection(temporal_node_refs) and participants.intersection(required_refs):
                    support_refs.append(relation.relation_ref)
            elif relation_type == MingliGraphEdgeType.CONTROLS:
                if relation.from_node_ref in temporal_node_refs and relation.to_node_ref in required_refs:
                    restraint_refs.append(relation.relation_ref)

        if not support_refs and not restraint_refs:
            continue
        if support_refs and restraint_refs:
            semantic_state = path.semantic_state
            uncertainty = ["时间层同时出现支持与制约，当前不做强弱排序，保留原路径状态。"]
            reason_code = "temporal_path.support_and_restraint_unranked"
        elif support_refs:
            semantic_state = "reinforced"
            uncertainty = ["时间层提供离散结构支持；这不表示精确能量增幅或现实事件。"]
            reason_code = "temporal_path.reinforced_by_qualified_relation"
        else:
            semantic_state = "weakened"
            uncertainty = ["时间层对路径必要节点形成制约；路径仍存在，未判定为阻断。"]
            reason_code = "temporal_path.weakened_by_qualified_relation"
        reason_refs = list(dict.fromkeys([
            TEMPORAL_PATH_UPDATE_POLICY_VERSION,
            reason_code,
            *support_refs,
            *restraint_refs,
        ]))
        updates.append(
            CanvasPathStateUpdate(
                path_ref=path.path_ref,
                semantic_state=semantic_state,
                state_trace=CanvasTrace(
                    source_mode="derived",
                    epistemic_status="derived",
                    source_refs=reason_refs,
                    uncertainty=uncertainty,
                    disclosure=path.trace.disclosure,
                ),
                change_reason_refs=reason_refs,
            )
        )
    return updates


def temporal_relations(
    *,
    layer_type: Literal["luck", "year"],
    existing_nodes: list[tuple[CanvasNode, NodeRef]],
    current_nodes: list[tuple[CanvasNode, NodeRef]],
    scene_ref: str,
    source_refs: list[str],
) -> list[CanvasRelation]:
    all_nodes = [*existing_nodes, *current_nodes]
    nodes_by_ref = {node.node_ref: node for node, _ in all_nodes}
    refs_by_ref = {model.node_ref: model for _, model in all_nodes}
    current_refs = {node.node_ref for node, _ in current_nodes}
    stems = [
        (node.node_ref, node.element)
        for node, model in all_nodes
        if model.level == "stem"
    ]
    branches = [
        (node.node_ref, node.label)
        for node, model in all_nodes
        if model.level == "branch"
    ]
    rows: list[dict[str, object]] = [
        *derive_element_relations(stems),
        *derive_branch_relations(branches),
        {
            "type": "position_link",
            "source_ref": current_nodes[0][0].node_ref,
            "target_ref": current_nodes[1][0].node_ref,
        },
    ]
    relations: dict[str, CanvasRelation] = {}
    for row in rows:
        participant_refs = relation_participant_refs(row)
        if len(participant_refs) < 2 or not current_refs.intersection(participant_refs):
            continue
        relation_type = core_relation_type(str(row.get("type", "")))
        if not relation_type or not set(participant_refs).issubset(nodes_by_ref):
            continue
        from_ref, to_ref = relation_endpoints(
            row=row,
            relation_type=relation_type,
            participant_refs=participant_refs,
            nodes_by_ref=nodes_by_ref,
        )
        relation_key = RelationKey(
            scene_ref=scene_ref,
            relation_type=relation_type,
            participant_refs=[refs_by_ref[item] for item in participant_refs],
            directionality=relation_directionality(relation_type),
            scope=layer_type,
        )
        relation_source_refs = refs(
            [*source_refs, f"rule:bazi.branch_relation:{row.get('type', '')}"],
            fallback=relation_key.relation_key,
        )
        if relation_type in {"generates", "controls", "same_element_support"}:
            relation_state = MingliRelationState.STRUCTURAL
            mechanism_ref = "visible_stem_same_layer"
            trace = CanvasTrace(
                source_mode="derived",
                epistemic_status="derived",
                source_refs=relation_source_refs,
                uncertainty=["可见天干同层关系已结构成立；时间进入不自动表示实际作用。"],
                disclosure="practitioner",
            )
        elif relation_type == "position_link":
            relation_state = MingliRelationState.STRUCTURAL
            mechanism_ref = "same_pillar_bearing"
            trace = CanvasTrace(
                source_mode="derived",
                epistemic_status="derived",
                source_refs=relation_source_refs,
                uncertainty=["同柱只表示承载与接近，不自动表示直接作用。"],
                disclosure="practitioner",
            )
        else:
            relation_state = MingliRelationState.TIME_ACTIVATED
            mechanism_ref = f"named_branch_{row.get('type', relation_type)}"
            trace = CanvasTrace(
                source_mode="derived",
                epistemic_status="derived",
                source_refs=relation_source_refs,
                uncertainty=["时间关系已激活；是否实际生效仍需正式命理认知。"],
                disclosure="member",
            )
        label = (
            " · ".join(nodes_by_ref[item].label for item in participant_refs)
            + RELATION_LABELS.get(relation_type, relation_type)
            if len(participant_refs) > 2
            else (
                f"{nodes_by_ref[from_ref].label}"
                f"{RELATION_LABELS.get(relation_type, relation_type)}"
                f"{nodes_by_ref[to_ref].label}"
            )
        )
        relations[relation_key.relation_key] = CanvasRelation(
            relation_ref=relation_key.relation_key,
            from_node_ref=from_ref,
            to_node_ref=to_ref,
            participant_node_refs=participant_refs,
            relation_type=relation_type,
            label=label,
            relation_state=relation_state.value,
            mechanism_ref=mechanism_ref,
            position_context=_temporal_position_context(
                source=refs_by_ref[from_ref],
                target=refs_by_ref[to_ref],
                all_node_refs=list(refs_by_ref.values()),
                layer_type=layer_type,
                symmetric=relation_directionality(relation_type).value == "symmetric",
            ),
            semantic_state=(
                "active"
                if relation_state in {MingliRelationState.TIME_ACTIVATED, MingliRelationState.EFFECTIVE}
                else "latent"
            ),
            trace=trace,
            state_trace=trace,
            change_reason_refs=relation_source_refs,
        )
    return [relations[key] for key in sorted(relations)]


def _temporal_position_context(
    *,
    source: NodeRef,
    target: NodeRef,
    all_node_refs: list[NodeRef],
    layer_type: Literal["luck", "year"],
    symmetric: bool,
) -> RelationPositionContext:
    source_index = _scene_column_index(source)
    target_index = _scene_column_index(target)
    span = abs(source_index - target_index)
    if symmetric:
        direction = "symmetric"
    elif source.scope in {"luck", "year"} and target.scope == "natal":
        direction = "temporal_to_natal"
    elif source.scope == "natal" and target.scope in {"luck", "year"}:
        direction = "natal_to_temporal"
    elif source.scope in {"luck", "year"} and target.scope in {"luck", "year"}:
        direction = "cross_temporal"
    elif source_index < target_index:
        direction = "left_to_right"
    elif source_index > target_index:
        direction = "right_to_left"
    else:
        direction = "same_column"
    intervening = []
    if span > 1 and source.level == target.level:
        low, high = sorted((source_index, target_index))
        intervening = [
            item.node_ref
            for item in all_node_refs
            if item.level == source.level and low < _scene_column_index(item) < high
        ]
    scopes = {source.scope, target.scope}
    scene_layer = (
        "mixed_temporal"
        if {"luck", "year"}.issubset(scopes)
        else "year_state"
        if layer_type == "year"
        else "luck_state"
    )
    return RelationPositionContext(
        source_scope=source.scope,
        target_scope=target.scope,
        source_slot=source.slot,
        target_slot=target.slot,
        source_level=source.level,
        target_level=target.level,
        adjacent=span == 1,
        column_span=span,
        intervening_node_refs=intervening,
        ref_namespace="node_ref",
        direction=direction,
        scene_layer=scene_layer,
    )


def _scene_column_index(node_ref: NodeRef) -> int:
    if node_ref.scope == "luck":
        return 4
    if node_ref.scope == "year":
        return 5
    return {"year": 0, "month": 1, "day": 2, "hour": 3}.get(node_ref.slot, 0)


def relation_participant_refs(row: dict[str, object]) -> list[str]:
    slots = row.get("slots")
    if isinstance(slots, list):
        return [str(item) for item in slots]
    source_ref = str(row.get("source_ref") or row.get("slot_a") or "")
    target_ref = str(row.get("target_ref") or row.get("slot_b") or "")
    return [item for item in (source_ref, target_ref) if item]


def core_relation_type(raw_type: str) -> str:
    return {
        "generates": "generates",
        "controls": "controls",
        "same_element_support": "same_element_support",
        "clash": "clashes",
        "harmony": "harmonizes",
        "harm": "harms",
        "break": "breaks",
        "punishment": "punishes",
        "self_punishment": "punishes",
        "half_triple_harmony": "forms_half_combination",
        "triple_harmony": "forms_triple_combination",
        "triple_punishment": "punishes",
        "position_link": "position_link",
    }.get(raw_type, "")


def relation_endpoints(
    *,
    row: dict[str, object],
    relation_type: str,
    participant_refs: list[str],
    nodes_by_ref: dict[str, CanvasNode],
) -> tuple[str, str]:
    if relation_type == "forms_triple_combination":
        bridge = str(row.get("bridge_branch") or "")
        target = next(
            (ref for ref in participant_refs if nodes_by_ref[ref].label == bridge),
            participant_refs[1],
        )
        source = next(ref for ref in participant_refs if ref != target)
        return source, target
    return participant_refs[0], participant_refs[1]
