from __future__ import annotations

from typing import Any

from core.contracts import BirthInputCanonical
from core.engines.bazi.knowledge import HIDDEN_STEMS
from core.graph import NodeRef
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphNode, MingliPath, MingliRelationState
from core.life_case import LifeCase, path_key_for_graph_path
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord
from experience.canvas import (
    CanvasChartSource,
    CanvasCluster,
    CanvasNode,
    CanvasPath,
    CanvasRelation,
    CanvasSemanticSlot,
    CanvasTrace,
)

from product.canvas_projection_shared import (
    POSITION_LABELS,
    POSITION_SLOT_TYPES,
    RELATION_LABELS,
    bounded,
    refs,
    slot_ref_for_position,
)


def chart_source(
    *,
    birth: BirthInputCanonical,
    graph: MingliGraph,
    chart_version_id: str,
    world_id: str,
    node_refs: dict[str, str],
    relation_refs: dict[str, str],
    relation_assertions: dict[str, dict[str, Any]],
) -> CanvasChartSource:
    pillar_values = {
        "year": birth.year_pillar,
        "month": birth.month_pillar,
        "day": birth.day_pillar,
        "hour": birth.hour_pillar,
    }
    slots = [
        CanvasSemanticSlot(
            slot_ref=f"slot-natal-{position}",
            slot_type=POSITION_SLOT_TYPES[position],
            label=POSITION_LABELS[position],
            stem=value[0],
            branch=value[1],
            hidden_stems=list(HIDDEN_STEMS.get(value[1], [])),
            immutable=True,
            trace=CanvasTrace(
                source_mode="canonical",
                epistemic_status="fact",
                source_refs=[f"chart:{chart_version_id}:{position}-pillar"],
                disclosure="public",
            ),
        )
        for position, value in pillar_values.items()
    ]
    nodes = [
        canvas_node(node, node_ref=node_refs[node.node_id])
        for node in graph.nodes
    ]
    nodes_by_id = {item.node_id: item for item in graph.nodes}
    relations = [
        canvas_relation(
            edge=edge,
            nodes_by_id=nodes_by_id,
            node_refs=node_refs,
            relation_ref=relation_refs[edge.edge_id],
            assertion=relation_assertions.get(relation_refs[edge.edge_id]),
        )
        for edge in graph.edges
    ]
    return CanvasChartSource(
        chart_version_id=chart_version_id,
        world_id=world_id,
        slots=slots,
        nodes=nodes,
        relations=relations,
        clusters=graph_clusters(graph=graph, node_refs=node_refs),
    )


def canvas_node(node: MingliGraphNode, *, node_ref: str) -> CanvasNode:
    visible = node.node_type.value in {"stem", "branch"}
    return CanvasNode(
        node_ref=node_ref,
        label=node.label,
        node_type=node.node_type.value,
        semantic_slot_ref=slot_ref_for_position(node.position),
        element=node.element,
        polarity=node.yin_yang,
        ten_god=node.ten_god,
        trace=CanvasTrace(
            source_mode="canonical" if visible else "derived",
            epistemic_status="fact" if visible else "derived",
            source_refs=refs([*node.material_refs, *node.evidence_refs], fallback=node.node_id),
            disclosure="public" if visible else "practitioner",
        ),
    )


def canvas_relation(
    *,
    edge: MingliGraphEdge,
    nodes_by_id: dict[str, MingliGraphNode],
    node_refs: dict[str, str],
    relation_ref: str,
    assertion: dict[str, Any] | None,
) -> CanvasRelation:
    source = nodes_by_id[edge.from_node_id]
    target = nodes_by_id[edge.to_node_id]
    source_refs = refs([*edge.material_refs, *edge.evidence_refs], fallback=edge.edge_id)
    label = (
        f"{source.label}"
        f"{RELATION_LABELS.get(edge.edge_type.value, edge.relation_label or edge.edge_type.value)}"
        f"{target.label}"
    )
    assertion_ref = str(assertion.get("assertion_ref")) if assertion else ""
    relation_state = MingliRelationState.EFFECTIVE if assertion_ref else edge.relation_state
    if assertion_ref:
        trace = CanvasTrace(
            source_mode="committed",
            epistemic_status="committed",
            source_refs=refs(
                [assertion_ref, *(assertion.get("source_refs") or []), *source_refs],
                fallback=relation_ref,
            ),
            commitment_refs=[assertion_ref],
            disclosure="member",
        )
    elif relation_state == MingliRelationState.POTENTIAL:
        trace = CanvasTrace(
            source_mode="derived",
            epistemic_status="candidate",
            source_refs=source_refs,
            uncertainty=["五行生克只表示潜在关系；需经具名机制后才能进入正式作用图。"],
            disclosure="practitioner",
        )
    else:
        trace = CanvasTrace(
            source_mode="derived",
            epistemic_status="derived",
            source_refs=source_refs,
            disclosure="member",
        )
    return CanvasRelation(
        relation_ref=relation_ref,
        from_node_ref=node_refs[edge.from_node_id],
        to_node_ref=node_refs[edge.to_node_id],
        participant_node_refs=[node_refs[item] for item in edge.participant_node_ids],
        relation_type=edge.edge_type.value,
        label=label,
        relation_state=relation_state.value,
        semantic_state="latent" if relation_state == MingliRelationState.POTENTIAL else "active",
        trace=trace,
        state_trace=trace,
        change_reason_refs=source_refs,
    )


def graph_clusters(*, graph: MingliGraph, node_refs: dict[str, str]) -> list[CanvasCluster]:
    groups: dict[str, list[MingliGraphNode]] = {}
    for node in graph.nodes:
        cluster_id = str(node.attributes.get("triple_combination") or "")
        if cluster_id:
            groups.setdefault(cluster_id, []).append(node)
    output: list[CanvasCluster] = []
    for cluster_id, nodes in sorted(groups.items()):
        source_refs = refs(
            [ref for node in nodes for ref in [*node.material_refs, *node.evidence_refs]],
            fallback=f"graph:cluster:{cluster_id}",
        )
        output.append(CanvasCluster(
            cluster_ref=f"cluster:{graph.reading_id}:{cluster_id}",
            label="结构组合候选",
            node_refs=[node_refs[item.node_id] for item in nodes],
            relation_refs=[],
            trace=CanvasTrace(
                source_mode="derived",
                epistemic_status="candidate",
                source_refs=source_refs,
                uncertainty=["结构组合候选不自动等于成局或吉凶"],
                disclosure="practitioner",
            ),
        ))
    return output


def committed_paths(
    *,
    canonical_projection_payload: dict[str, Any],
    life_case: LifeCase,
    available_node_refs: set[str],
    available_relation_refs: set[str],
) -> list[CanvasPath]:
    baseline = life_case.baseline_insight
    output: list[CanvasPath] = []
    for item in active_projection_assertions(
        canonical_projection_payload.get("path_assertions")
    ):
        node_refs = [str(ref) for ref in item.get("node_refs") or []]
        relation_refs = [str(ref) for ref in item.get("relation_refs") or []]
        assertion_ref = str(item.get("assertion_ref") or "")
        path_ref = str(item.get("path_ref") or "")
        if (
            not assertion_ref
            or not path_ref
            or len(node_refs) < 2
            or not relation_refs
            or not set(node_refs).issubset(available_node_refs)
            or not set(relation_refs).issubset(available_relation_refs)
        ):
            continue
        trace = CanvasTrace(
            source_mode="committed",
            epistemic_status="committed",
            source_refs=refs(
                [assertion_ref, *(item.get("source_refs") or [])],
                fallback=baseline.insight_id,
            ),
            commitment_refs=[assertion_ref, baseline.insight_id],
            uncertainty=baseline.uncertainty.reasons,
            disclosure="member",
        )
        output.append(CanvasPath(
            path_ref=path_ref,
            label=bounded(str(item.get("statement") or baseline.claim), 240),
            node_refs=node_refs,
            relation_refs=relation_refs,
            required_refs=node_refs,
            semantic_state="active",
            trace=trace,
            state_trace=trace,
            change_reason_refs=[assertion_ref, baseline.insight_id],
        ))
    return output


def candidate_paths(
    *,
    explored_paths: list[MingliPath],
    record: MingliCognitiveRecord,
    committed_paths: list[CanvasPath],
    nodes_by_id: dict[str, MingliGraphNode],
    edges_by_id: dict[str, MingliGraphEdge],
    node_refs: dict[str, str],
    relation_refs: dict[str, str],
    node_ref_models: dict[str, NodeRef],
    relation_key_models: dict[str, Any],
    world: ChartWorldInstance,
    life_case: LifeCase,
) -> list[CanvasPath]:
    by_id = {
        ref: item
        for item in explored_paths
        for ref in (item.path_id, item.path_key)
    }
    output: list[CanvasPath] = []
    candidate_refs = list(dict.fromkeys(record.cognition.work_path.competing_path_refs))
    committed_relation_chains = {
        tuple(item.relation_refs) for item in committed_paths
    }
    for candidate_ref in candidate_refs:
        path = by_id.get(candidate_ref)
        if path is None:
            continue
        stable_path = path_key_for_graph_path(
            path=path,
            nodes_by_id=nodes_by_id,
            edges_by_id=edges_by_id,
            world=world,
            life_case=life_case,
            node_refs_by_id=node_ref_models,
            relation_keys_by_id=relation_key_models,
        )
        stable_relation_refs = [relation_refs[item] for item in path.edge_ids]
        if tuple(stable_relation_refs) in committed_relation_chains:
            continue
        label = "竞争路径：" + " → ".join(nodes_by_id[item].label for item in path.node_ids)
        trace = CanvasTrace(
            source_mode="derived",
            epistemic_status="candidate",
            source_refs=refs(
                [candidate_ref, path.path_key, *path.graph_refs, *path.evidence_refs],
                fallback=stable_path.path_key,
            ),
            uncertainty=["这条路径尚未进入 LifeCase 正式主判断"],
            disclosure="practitioner",
        )
        output.append(CanvasPath(
            path_ref=stable_path.path_key,
            label=bounded(label, 240),
            node_refs=[node_refs[item] for item in path.node_ids],
            relation_refs=stable_relation_refs,
            semantic_state="latent",
            trace=trace,
            state_trace=trace,
            change_reason_refs=[candidate_ref],
        ))
    return output


def active_projection_assertions(value: Any) -> list[dict[str, Any]]:
    rows = [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
    superseded = {str(item.get("supersedes")) for item in rows if item.get("supersedes")}
    return [
        item for item in rows
        if item.get("status") == "committed"
        and str(item.get("assertion_ref") or "") not in superseded
    ]
