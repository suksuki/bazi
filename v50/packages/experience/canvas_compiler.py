from __future__ import annotations

from datetime import datetime
from typing import Any

from experience.canvas_contracts import (
    CanvasChangeType,
    CanvasCluster,
    CanvasCompileError,
    CanvasCompileRequest,
    CanvasContextPack,
    CanvasDiffSpec,
    CanvasEpistemicDelta,
    CanvasEpistemology,
    CanvasIdentity,
    CanvasInteractionPolicy,
    CanvasNode,
    CanvasObjectDelta,
    CanvasPath,
    CanvasPresentation,
    CanvasRelation,
    CanvasRole,
    CanvasSemanticSlot,
    CanvasStage,
    CanvasTemporalLayer,
    CanvasTrace,
    CanvasVisualAnchor,
    MingliCanvasSpec,
    TemporalSandboxState,
)
from experience.compiler import canonical_hash


def compile_canvas_spec(request: CanvasCompileRequest) -> MingliCanvasSpec:
    source = request.source
    layers = {item.layer_id: item for item in source.temporal_layers}
    sandbox_active = request.sandbox is not None and request.sandbox.status in {"active", "modified"}
    luck_id = request.sandbox.selected_luck_layer_id if sandbox_active else request.luck_layer_id
    year_id = request.sandbox.selected_year_layer_id if sandbox_active else request.year_layer_id
    selected = _selected_layers(stage=request.stage, luck_id=luck_id, year_id=year_id, layers=layers)

    slots = list(source.chart.slots)
    nodes = {item.node_ref: item for item in source.chart.nodes}
    relations = {item.relation_ref: item for item in source.chart.relations}
    clusters = {item.cluster_ref: item for item in source.chart.clusters}
    paths = {item.path_ref: item for item in source.life_case.paths}

    for layer in selected:
        slots.append(layer.slot)
        nodes.update({item.node_ref: item for item in layer.nodes})
        relations.update({item.relation_ref: item for item in layer.relations})
        clusters.update({item.cluster_ref: item for item in layer.clusters})
        paths.update({item.path_ref: item for item in layer.paths})
        for removal in layer.removals:
            target = {"node": nodes, "relation": relations, "cluster": clusters, "path": paths}[removal.object_type]
            target.pop(removal.target_ref, None)
        for update in layer.path_updates:
            current = paths.get(update.path_ref)
            if current is None:
                raise CanvasCompileError(f"canvas_path_update_missing_path:{update.path_ref}")
            paths[update.path_ref] = current.model_copy(update={
                "semantic_state": update.semantic_state,
                "state_trace": update.state_trace,
                "change_reason_refs": update.change_reason_refs,
            })

    sandbox_id = request.sandbox.sandbox_session_id if sandbox_active else ""
    temporal_snapshot_id = selected[-1].temporal_snapshot_id if selected else ""
    return _issue_canvas_spec(
        chart_version_id=source.chart.chart_version_id,
        life_case_id=source.life_case.life_case_id,
        compiler_version=source.compiler_version,
        compiled_at=source.compiled_at,
        base_uncertainty=source.life_case.uncertainty,
        must_not_say=source.life_case.must_not_say,
        stage=request.stage,
        temporal_snapshot_id=temporal_snapshot_id,
        sandbox_session_id=sandbox_id,
        audience_role=None,
        slots=slots,
        nodes=list(nodes.values()),
        relations=list(relations.values()),
        clusters=list(clusters.values()),
        paths=list(paths.values()),
    )


def compile_canvas_diff(
    from_spec: MingliCanvasSpec,
    to_spec: MingliCanvasSpec,
    *,
    source_action_ref: str,
) -> CanvasDiffSpec:
    from_nodes = {item.node_ref: item for item in from_spec.nodes}
    to_nodes = {item.node_ref: item for item in to_spec.nodes}
    from_relations = {item.relation_ref: item for item in from_spec.relations}
    to_relations = {item.relation_ref: item for item in to_spec.relations}
    from_clusters = {item.cluster_ref: item for item in from_spec.clusters}
    to_clusters = {item.cluster_ref: item for item in to_spec.clusters}
    from_paths = {item.path_ref: item for item in from_spec.paths}
    to_paths = {item.path_ref: item for item in to_spec.paths}

    added_nodes = _added_deltas("node", from_nodes, to_nodes)
    removed_nodes = _removed_deltas("node", from_nodes, to_nodes)
    added_relations = _added_deltas("relation", from_relations, to_relations)
    removed_relations = _removed_deltas("relation", from_relations, to_relations)
    changed_relations = _state_deltas("relation", from_relations, to_relations)
    added_clusters = _added_deltas("cluster", from_clusters, to_clusters)
    removed_clusters = _removed_deltas("cluster", from_clusters, to_clusters)
    path_deltas = _path_deltas(from_paths, to_paths)
    epistemic = _epistemic_deltas(
        ("node", from_nodes, to_nodes),
        ("relation", from_relations, to_relations),
        ("cluster", from_clusters, to_clusters),
        ("path", from_paths, to_paths),
    )

    grouped = {kind: [item for item in path_deltas if item.change_type == kind] for kind in (
        "introduced", "removed", "activated", "blocked", "reopened", "reinforced", "weakened", "unchanged"
    )}
    explanation_refs = sorted({
        ref
        for collection in [
            added_nodes, removed_nodes, added_relations, removed_relations, changed_relations,
            added_clusters, removed_clusters, path_deltas,
        ]
        for item in collection
        for ref in item.reason_refs
    })
    payload = {
        "from_spec_id": from_spec.identity.canvas_spec_id,
        "to_spec_id": to_spec.identity.canvas_spec_id,
        "source_action_ref": source_action_ref,
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "added_relations": added_relations,
        "removed_relations": removed_relations,
        "changed_relations": changed_relations,
        "added_clusters": added_clusters,
        "removed_clusters": removed_clusters,
        "introduced_paths": grouped["introduced"],
        "removed_paths": grouped["removed"],
        "activated_paths": grouped["activated"],
        "blocked_paths": grouped["blocked"],
        "reopened_paths": grouped["reopened"],
        "reinforced_paths": grouped["reinforced"],
        "weakened_paths": grouped["weakened"],
        "unchanged_paths": grouped["unchanged"],
        "changed_epistemic_status": epistemic,
        "explanation_refs": explanation_refs,
        "uncertainty": sorted(set(to_spec.epistemology.uncertainty)),
    }
    digest = canonical_hash(payload)
    return CanvasDiffSpec(
        diff_id=f"canvas-diff-{digest[:24]}",
        content_hash=digest,
        **payload,
    )


def project_canvas_spec_for_role(spec: MingliCanvasSpec, role: CanvasRole) -> MingliCanvasSpec:
    slots = [item for item in spec.semantic_slots if _trace_visible(item.trace, role)]
    if role in {"guest", "member"}:
        slots = [item.model_copy(update={"hidden_stems": []}) for item in slots]
    nodes = [item for item in spec.nodes if _trace_visible(item.trace, role)]
    node_refs = {item.node_ref for item in nodes}
    relations = [
        item for item in spec.relations
        if item.from_node_ref in node_refs
        and item.to_node_ref in node_refs
        and _trace_visible(item.trace, role)
        and _trace_visible(item.state_trace, role)
    ]
    relation_refs = {item.relation_ref for item in relations}
    clusters = [
        item for item in spec.clusters
        if set(item.node_refs).issubset(node_refs)
        and set(item.relation_refs).issubset(relation_refs)
        and _trace_visible(item.trace, role)
    ]
    paths = [
        item for item in spec.paths
        if set(item.node_refs).issubset(node_refs)
        and set(item.relation_refs).issubset(relation_refs)
        and _trace_visible(item.trace, role)
        and _trace_visible(item.state_trace, role)
    ]
    visible_refs = {
        *(item.slot_ref for item in slots),
        *node_refs,
        *relation_refs,
        *(item.cluster_ref for item in clusters),
        *(item.path_ref for item in paths),
    }
    presentation = spec.presentation.model_copy(update={
        "visual_anchors": [item for item in spec.presentation.visual_anchors if item.object_ref in visible_refs],
        "emphasis": [item for item in spec.presentation.emphasis if item in visible_refs],
        "narration_targets": [item for item in spec.presentation.narration_targets if item in visible_refs],
    })
    return _issue_canvas_spec(
        chart_version_id=spec.identity.chart_version_id,
        life_case_id=spec.identity.life_case_id,
        compiler_version=spec.identity.compiler_version,
        compiled_at=spec.identity.compiled_at,
        base_uncertainty=spec.epistemology.uncertainty,
        must_not_say=spec.epistemology.must_not_say,
        stage=spec.stage,
        temporal_snapshot_id=spec.identity.temporal_snapshot_id,
        sandbox_session_id=spec.identity.sandbox_session_id,
        audience_role=role,
        slots=slots,
        nodes=nodes,
        relations=relations,
        clusters=clusters,
        paths=paths,
        presentation=presentation,
    )


def compile_canvas_context(
    *,
    spec: MingliCanvasSpec,
    diff: CanvasDiffSpec | None,
    role: CanvasRole,
    selected_object_refs: list[str],
    visible_layers: list[str],
    sandbox: TemporalSandboxState | None = None,
) -> CanvasContextPack:
    projected = project_canvas_spec_for_role(spec, role)
    disclosed = sorted({
        *(item.slot_ref for item in projected.semantic_slots),
        *(item.node_ref for item in projected.nodes),
        *(item.relation_ref for item in projected.relations),
        *(item.cluster_ref for item in projected.clusters),
        *(item.path_ref for item in projected.paths),
    })
    disclosed_set = set(disclosed)
    selected = sorted(set(selected_object_refs).intersection(disclosed_set))
    committed = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "committed")
    candidate = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "candidate")
    blocked = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "blocked")
    mutations = []
    if sandbox and sandbox.status == "modified":
        mutations = [item for item in sandbox.mutations if item.source_mode == "hypothetical"]
    diff_reasons: list[str] = []
    if diff:
        delta_collections = [
            diff.added_nodes,
            diff.removed_nodes,
            diff.added_relations,
            diff.removed_relations,
            diff.changed_relations,
            diff.added_clusters,
            diff.removed_clusters,
            diff.introduced_paths,
            diff.removed_paths,
            diff.activated_paths,
            diff.blocked_paths,
            diff.reopened_paths,
            diff.reinforced_paths,
            diff.weakened_paths,
            diff.unchanged_paths,
        ]
        diff_reasons = sorted({
            ref
            for collection in delta_collections
            for item in collection
            if item.target_ref in disclosed_set
            for ref in item.reason_refs
        })
    payload = {
        "canvas_spec_id": projected.identity.canvas_spec_id,
        "diff_spec_id": diff.diff_id if diff else "",
        "role": role,
        "current_stage": projected.stage,
        "selected_object_refs": selected,
        "visible_layers": sorted(set(visible_layers).intersection(projected.presentation.layers)),
        "committed_path_refs": committed,
        "candidate_path_refs": candidate,
        "blocked_path_refs": blocked,
        "hypothetical_mutations": mutations,
        "diff_reason_refs": diff_reasons,
        "uncertainty": projected.epistemology.uncertainty,
        "must_not_say": projected.epistemology.must_not_say,
        "disclosed_object_refs": disclosed,
    }
    digest = canonical_hash(payload)
    return CanvasContextPack(
        context_pack_id=f"canvas-context-{digest[:24]}",
        content_hash=digest,
        **payload,
    )


def _selected_layers(
    *,
    stage: CanvasStage,
    luck_id: str,
    year_id: str,
    layers: dict[str, CanvasTemporalLayer],
) -> list[CanvasTemporalLayer]:
    if stage == "natal":
        if luck_id or year_id:
            raise CanvasCompileError("natal_stage_cannot_select_temporal_layer")
        return []
    if not luck_id or luck_id not in layers or layers[luck_id].layer_type != "luck":
        raise CanvasCompileError("luck_stage_requires_valid_luck_layer")
    selected = [layers[luck_id]]
    if stage == "luck":
        if year_id:
            raise CanvasCompileError("luck_stage_cannot_select_year_layer")
        return selected
    if not year_id or year_id not in layers or layers[year_id].layer_type != "year":
        raise CanvasCompileError("year_stage_requires_valid_year_layer")
    return [*selected, layers[year_id]]


def _issue_canvas_spec(
    *,
    chart_version_id: str,
    life_case_id: str,
    compiler_version: str,
    compiled_at: datetime,
    base_uncertainty: list[str],
    must_not_say: list[str],
    stage: CanvasStage,
    temporal_snapshot_id: str,
    sandbox_session_id: str,
    audience_role: CanvasRole | None,
    slots: list[CanvasSemanticSlot],
    nodes: list[CanvasNode],
    relations: list[CanvasRelation],
    clusters: list[CanvasCluster],
    paths: list[CanvasPath],
    presentation: CanvasPresentation | None = None,
) -> MingliCanvasSpec:
    slots = sorted(slots, key=lambda item: _slot_order(item.slot_type))
    nodes = sorted(nodes, key=lambda item: item.node_ref)
    relations = sorted(relations, key=lambda item: item.relation_ref)
    clusters = sorted(clusters, key=lambda item: item.cluster_ref)
    paths = sorted(paths, key=lambda item: item.path_ref)
    traces = [
        *(item.trace for item in slots),
        *(item.trace for item in nodes),
        *(item.trace for item in relations),
        *(item.state_trace for item in relations),
        *(item.trace for item in clusters),
        *(item.trace for item in paths),
        *(item.state_trace for item in paths),
    ]
    epistemology = CanvasEpistemology(
        epistemic_statuses=sorted(set(item.epistemic_status for item in traces)),
        source_refs=sorted({ref for item in traces for ref in item.source_refs}),
        commitment_refs=sorted({ref for item in traces for ref in item.commitment_refs}),
        uncertainty=sorted({*base_uncertainty, *(reason for item in traces for reason in item.uncertainty)}),
        rejection_or_block_reasons=sorted({reason for item in traces for reason in item.rejection_or_block_reasons}),
        must_not_say=must_not_say,
    )
    interaction = CanvasInteractionPolicy(
        allowed_interactions=["select_object", "toggle_layer", "set_luck", "set_year", "replace_year", "restore"],
        immutable_slots=[item.slot_ref for item in slots if item.immutable],
        sandbox_mutations=["temporal.luck", "temporal.year"],
    )
    if presentation is None:
        object_refs = [
            *(item.slot_ref for item in slots),
            *(item.node_ref for item in nodes),
            *(item.relation_ref for item in relations),
            *(item.cluster_ref for item in clusters),
            *(item.path_ref for item in paths),
        ]
        presentation_trace = CanvasTrace(
            source_mode="presentation",
            epistemic_status="presentation_only",
            source_refs=["presentation:canvas-default-v1"],
            disclosure="public",
        )
        presentation = CanvasPresentation(
            visual_anchors=[
                CanvasVisualAnchor(
                    anchor_ref=f"anchor-{ref}",
                    object_ref=ref,
                    group=_anchor_group(ref),
                    trace=presentation_trace,
                )
                for ref in object_refs
            ],
            layers=[
                "generation_control",
                "combination",
                "conflict",
                "overview",
                "five_element",
                "combination_conflict",
                "roots_reveal",
                "timing",
                "work_path",
            ],
            emphasis=[item.path_ref for item in paths if item.trace.epistemic_status == "committed"],
            narration_targets=[item.path_ref for item in paths if item.trace.epistemic_status in {"committed", "candidate"}],
        )
    identity_seed = {
        "chart_version_id": chart_version_id,
        "temporal_snapshot_id": temporal_snapshot_id,
        "life_case_id": life_case_id,
        "sandbox_session_id": sandbox_session_id,
        "compiler_version": compiler_version,
        "compiled_at": compiled_at,
        "audience_role": audience_role,
    }
    body = {
        "stage": stage,
        "semantic_slots": slots,
        "nodes": nodes,
        "relations": relations,
        "clusters": clusters,
        "paths": paths,
        "epistemology": epistemology,
        "interaction": interaction,
        "presentation": presentation,
    }
    digest = canonical_hash({"identity": identity_seed, **body})
    identity = CanvasIdentity(
        canvas_spec_id=f"canvas-spec-{digest[:24]}",
        content_hash=digest,
        **identity_seed,
    )
    return MingliCanvasSpec(identity=identity, **body)


def _added_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    return [
        _object_delta(object_type, after[ref], "introduced", before_state="", after_state=_object_state(after[ref]))
        for ref in sorted(set(after) - set(before))
    ]


def _removed_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    return [
        _object_delta(object_type, before[ref], "removed", before_state=_object_state(before[ref]), after_state="")
        for ref in sorted(set(before) - set(after))
    ]


def _state_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    result: list[CanvasObjectDelta] = []
    for ref in sorted(set(before).intersection(after)):
        old = _object_state(before[ref])
        new = _object_state(after[ref])
        if old != new:
            result.append(_object_delta(object_type, after[ref], _semantic_change(old, new), old, new))
    return result


def _path_deltas(before: dict[str, CanvasPath], after: dict[str, CanvasPath]) -> list[CanvasObjectDelta]:
    result = _added_deltas("path", before, after)
    result.extend(_removed_deltas("path", before, after))
    for ref in sorted(set(before).intersection(after)):
        old = before[ref].semantic_state
        new = after[ref].semantic_state
        result.append(_object_delta("path", after[ref], _semantic_change(old, new), old, new))
    return sorted(result, key=lambda item: (item.target_ref, item.change_type))


def _epistemic_deltas(*collections: tuple[str, dict[str, Any], dict[str, Any]]) -> list[CanvasEpistemicDelta]:
    result: list[CanvasEpistemicDelta] = []
    for object_type, before, after in collections:
        for ref in sorted(set(before).intersection(after)):
            pairs = [("object", before[ref].trace, after[ref].trace)]
            if hasattr(before[ref], "state_trace"):
                pairs.append(("state", before[ref].state_trace, after[ref].state_trace))
            for scope, old, new in pairs:
                if old.epistemic_status == new.epistemic_status:
                    continue
                result.append(CanvasEpistemicDelta(
                    object_type=object_type,
                    target_ref=ref,
                    status_scope=scope,
                    before_status=old.epistemic_status,
                    after_status=new.epistemic_status,
                    reason_refs=_reasons(after[ref]),
                    source_refs=sorted(set(old.source_refs + new.source_refs)),
                ))
    return result


def _object_delta(
    object_type: str,
    item: Any,
    change_type: CanvasChangeType,
    before_state: str,
    after_state: str,
) -> CanvasObjectDelta:
    return CanvasObjectDelta(
        object_type=object_type,
        target_ref=_object_ref(item),
        change_type=change_type,
        before_state=before_state,
        after_state=after_state,
        reason_refs=_reasons(item),
        source_refs=_sources(item),
    )


def _semantic_change(before: str, after: str) -> CanvasChangeType:
    if before == after:
        return "unchanged"
    if before == "blocked" and after != "blocked":
        return "reopened"
    if after == "blocked":
        return "blocked"
    if after == "reinforced":
        return "reinforced"
    if after == "weakened" or (before == "active" and after == "latent"):
        return "weakened"
    if before == "latent" and after == "active":
        return "activated"
    return "activated"


def _object_ref(item: Any) -> str:
    for field in ("node_ref", "relation_ref", "cluster_ref", "path_ref"):
        value = getattr(item, field, "")
        if value:
            return value
    raise CanvasCompileError("canvas_object_missing_ref")


def _object_state(item: Any) -> str:
    return str(getattr(item, "semantic_state", item.trace.epistemic_status))


def _sources(item: Any) -> list[str]:
    refs = list(item.trace.source_refs)
    if hasattr(item, "state_trace"):
        refs.extend(item.state_trace.source_refs)
    return sorted(set(refs))


def _reasons(item: Any) -> list[str]:
    reasons = list(getattr(item, "change_reason_refs", []))
    reasons.extend(item.trace.rejection_or_block_reasons)
    if hasattr(item, "state_trace"):
        reasons.extend(item.state_trace.rejection_or_block_reasons)
    return sorted(set(reasons or _sources(item)))


def _trace_visible(trace: CanvasTrace, role: CanvasRole) -> bool:
    if role == "admin":
        return True
    rank = {"public": 0, "member": 1, "practitioner": 2, "research": 3}
    role_rank = {"guest": 0, "member": 1, "practitioner": 2, "research": 3}[role]
    return role_rank >= rank[trace.disclosure]


def _slot_order(slot_type: str) -> int:
    return {"natal_year": 0, "natal_month": 1, "natal_day": 2, "natal_hour": 3, "luck": 4, "year": 5}[slot_type]


def _anchor_group(ref: str) -> str:
    return ref.split("-", 1)[0]


