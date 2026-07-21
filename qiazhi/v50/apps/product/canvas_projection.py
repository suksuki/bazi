from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import (
    build_bazi_material_store,
    derive_branch_relations,
    derive_element_relations,
)
from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    HIDDEN_STEMS,
    STEM_ELEMENTS,
    STEM_POLARITY,
)
from core.engines.bazi.material_engine import resolve_ten_god
from core.graph import NodeRef, RelationKey, build_mingli_graph_from_material_store, canonical_scene_scope_ref, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphNode, MingliPath
from core.graph.provenance import relation_directionality
from core.life_case import (
    LifeCase,
    node_ref_for_graph_node,
    path_key_for_graph_path,
    relation_key_for_graph_edge,
)
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord
from experience.canvas import (
    CanvasChartSource,
    CanvasCluster,
    CanvasCompileRequest,
    CanvasContextPack,
    CanvasDiffSpec,
    CanvasLifeCaseSource,
    CanvasNode,
    CanvasPath,
    CanvasRelation,
    CanvasSemanticSlot,
    CanvasTemporalLayer,
    CanvasTrace,
    MingliCanvasCompileInput,
    MingliCanvasSpec,
    compile_canvas_context,
    compile_canvas_diff,
    compile_canvas_spec,
    project_canvas_spec_for_role,
)
from experience.compiler import canonical_hash
from experience.product_projection import ReadOnlySixPillarCanvas
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable


CanvasRole = Literal["guest", "member", "practitioner", "research", "admin"]

POSITION_LABELS = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}
POSITION_SLOT_TYPES = {
    "year": "natal_year",
    "month": "natal_month",
    "day": "natal_day",
    "hour": "natal_hour",
}
BRANCH_POLARITY = {
    "子": "yang", "丑": "yin", "寅": "yang", "卯": "yin",
    "辰": "yang", "巳": "yin", "午": "yang", "未": "yin",
    "申": "yang", "酉": "yin", "戌": "yang", "亥": "yin",
}
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
    "harms": "相害",
    "breaks": "相破",
    "punishes": "相刑",
    "position_link": "同柱",
}
LAYER_DEFINITIONS = (
    (
        "generation_control",
        "生克",
        "只看生、克与同气支持。",
        {"generates", "controls", "same_element_support", "roots"},
    ),
    (
        "combination",
        "合",
        "只看已经由结构工具给出的合与组合关系。",
        {"harmonizes", "forms_half_combination", "forms_triple_combination"},
    ),
    (
        "conflict",
        "冲刑害破",
        "只看当前正式结构中已经存在的冲突关系。",
        {"clashes", "punishes", "harms", "breaks"},
    ),
)
CHANGE_GROUPS = (
    ("introduced", "新增"),
    ("removed", "消失"),
    ("activated", "激活"),
    ("reinforced", "增强支持"),
    ("weakened", "受到制约"),
    ("blocked", "路径受阻"),
    ("reopened", "重新打开"),
    ("unchanged", "保持不变"),
)


class ReadOnlyCanvasUnavailable(ValueError):
    pass


class ReadOnlySixPillarCanvasService:
    """Project formal case state into C0 Canvas contracts without writes or LLM use."""

    def __init__(self, *, case_store: AgentCaseStore) -> None:
        self.case_store = case_store
        self.scene_owner = CanonicalSceneOwner(case_store=case_store)
        self._compiled_cache: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    def issue(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> dict[str, Any]:
        role = canvas_role(account_role)
        compiled = self._compile(case_id=case_id, participant_id=participant_id, role=role)
        source = compiled["source"]
        specs: dict[str, MingliCanvasSpec] = compiled["specs"]
        diffs: dict[str, CanvasDiffSpec | None] = compiled["diffs"]

        stages: dict[str, Any] = {}
        for stage in ("natal", "luck", "year"):
            spec = specs[stage]
            diff = diffs[stage]
            layers = _layer_catalog(spec)
            default_layer = "work_path" if any(item["layer_id"] == "work_path" and item["available"] for item in layers) else "generation_control"
            default_selected = spec.semantic_slots[0].slot_ref
            context = compile_canvas_context(
                spec=spec,
                diff=diff,
                role=role,
                selected_object_refs=[default_selected],
                visible_layers=[default_layer],
            )
            stages[stage] = {
                "stage": stage,
                "title": _stage_title(stage, source),
                "summary": _stage_summary(stage, source),
                "spec": spec.model_dump(mode="json"),
                "diff": diff.model_dump(mode="json") if diff else None,
                "context": context.model_dump(mode="json"),
                "layers": layers,
                "default_layer_id": default_layer,
                "change_groups": _change_groups(diff=diff, before_spec=specs[_previous_stage(stage)], after_spec=spec),
            }

        payload = {
            "schema_version": "deepbazi.read_only_six_pillar_canvas.v1",
            "status": "read_only_canvas_ready",
            "case_id": case_id,
            "role": role,
            "stage_order": ["natal", "luck", "year"],
            "default_stage": "natal",
            "source": source,
            "canonical_scene": compiled["canonical_scene"],
            "projection_envelope": compiled["projection_envelope"],
            "path_availability": compiled["path_availability"],
            "stages": stages,
            "renderer_policy": {
                "read_only": True,
                "allowed_interactions": ["set_stage", "toggle_layer", "select_object", "inspect_context"],
                "forbidden_interactions": [
                    "mutate_natal_pillar",
                    "replace_temporal_pillar",
                    "write_life_case",
                    "promote_candidate",
                    "infer_relation",
                    "infer_diff",
                ],
            },
            "boundaries": [
                "原局四柱不可修改",
                "大运与流年只来自正式历法计算",
                "页面不补算关系、路径或阶段结论",
                "当前查看不会写入 LifeCase",
            ],
            "llm_used": False,
            "formal_state_writes": False,
            "sandbox_mutations": False,
        }
        return ReadOnlySixPillarCanvas.model_validate(payload).model_dump(mode="json")

    def issue_context(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        stage: str,
        selected_object_ref: str,
        visible_layer: str,
    ) -> CanvasContextPack:
        if stage not in {"natal", "luck", "year"}:
            raise ReadOnlyCanvasUnavailable("canvas_stage_invalid")
        role = canvas_role(account_role)
        compiled = self._compile(case_id=case_id, participant_id=participant_id, role=role)
        spec: MingliCanvasSpec = compiled["specs"][stage]
        diff: CanvasDiffSpec | None = compiled["diffs"][stage]
        disclosed = _object_refs(spec)
        if selected_object_ref not in disclosed:
            raise ReadOnlyCanvasUnavailable("canvas_object_not_disclosed")
        approved_layers = {item["layer_id"] for item in _layer_catalog(spec)}
        if visible_layer not in approved_layers:
            raise ReadOnlyCanvasUnavailable("canvas_layer_invalid")
        return compile_canvas_context(
            spec=spec,
            diff=diff,
            role=role,
            selected_object_refs=[selected_object_ref],
            visible_layers=[visible_layer],
        )

    def _compile(
        self,
        *,
        case_id: str,
        participant_id: str,
        role: CanvasRole,
    ) -> dict[str, Any]:
        row = self.case_store.get(case_id=case_id, user_id=participant_id)
        if row is None:
            raise ReadOnlyCanvasUnavailable("experience_case_not_found")
        try:
            canonical_projection = self.scene_owner.issue_projection(
                case_id=case_id,
                participant_id=participant_id,
                account_role=role,
                projection_kind="onecanvas",
            )
        except CanonicalSceneUnavailable as exc:
            raise ReadOnlyCanvasUnavailable(str(exc)) from exc
        cache_key = (
            case_id,
            participant_id,
            role,
            canonical_projection.projection_hash,
            _candidate_selection_revision_token(row),
        )
        cached = self._compiled_cache.get(cache_key)
        if cached is not None:
            return cached
        source, metadata = _compile_input_from_case_row(
            case_id=case_id,
            row=row,
            canonical_projection_payload=canonical_projection.payload,
        )
        identity = canonical_projection.scene_identity
        if (
            metadata["source"]["chart_version_id"] != identity.chart_version_id
            or metadata["source"]["life_case_id"] != identity.life_case_id
            or metadata["source"]["life_case_version"] != identity.life_case_version
        ):
            raise ReadOnlyCanvasUnavailable("canvas_canonical_scene_identity_mismatch")
        layer_ids = {item.layer_type: item.layer_id for item in source.temporal_layers}
        if "luck" not in layer_ids or "year" not in layer_ids:
            raise ReadOnlyCanvasUnavailable("canvas_official_timing_required")

        raw_specs = {
            "natal": compile_canvas_spec(CanvasCompileRequest(source=source, stage="natal")),
            "luck": compile_canvas_spec(CanvasCompileRequest(
                source=source,
                stage="luck",
                luck_layer_id=layer_ids["luck"],
            )),
            "year": compile_canvas_spec(CanvasCompileRequest(
                source=source,
                stage="year",
                luck_layer_id=layer_ids["luck"],
                year_layer_id=layer_ids["year"],
            )),
        }
        specs = {
            stage: project_canvas_spec_for_role(spec, role)
            for stage, spec in raw_specs.items()
        }
        diffs: dict[str, CanvasDiffSpec | None] = {
            "natal": None,
            "luck": compile_canvas_diff(specs["natal"], specs["luck"], source_action_ref="official:add-luck"),
            "year": compile_canvas_diff(specs["luck"], specs["year"], source_action_ref="official:add-year"),
        }
        compiled = {
            "source": metadata["source"],
            "path_availability": metadata["path_availability"],
            "specs": specs,
            "diffs": diffs,
            "canonical_scene": identity.model_dump(mode="json"),
            "projection_envelope": canonical_projection.model_dump(mode="json"),
        }
        for key in list(self._compiled_cache):
            if key[:3] == cache_key[:3] and key != cache_key:
                self._compiled_cache.pop(key, None)
        if len(self._compiled_cache) >= 128:
            self._compiled_cache.clear()
        self._compiled_cache[cache_key] = compiled
        return compiled


def canvas_role(account_role: str) -> CanvasRole:
    return {
        "admin": "admin",
        "research_master": "research",
        "research": "research",
        "practitioner": "practitioner",
        "member": "member",
    }.get(str(account_role).strip().lower(), "guest")  # type: ignore[return-value]


def _candidate_selection_revision_token(row: dict[str, Any]) -> str:
    record = row.get("record") if isinstance(row.get("record"), dict) else {}
    cognition = record.get("cognition") if isinstance(record.get("cognition"), dict) else {}
    work_path = (
        cognition.get("work_path")
        if isinstance(cognition.get("work_path"), dict)
        else {}
    )
    return canonical_hash({
        "record_id": record.get("record_id"),
        "candidate_path_refs": work_path.get("candidate_path_refs"),
        "competing_path_refs": work_path.get("competing_path_refs"),
        "evidence_refs": work_path.get("evidence_refs"),
    })


def _compile_input_from_case_row(
    *,
    case_id: str,
    row: dict[str, Any],
    canonical_projection_payload: dict[str, Any],
) -> tuple[MingliCanvasCompileInput, dict[str, Any]]:
    birth_payload = row.get("birth_input")
    world = row.get("world")
    life_case_payload = row.get("life_case")
    record_payload = row.get("record")
    if not isinstance(birth_payload, dict) or not isinstance(world, dict):
        raise ReadOnlyCanvasUnavailable("canvas_chart_world_required")
    if not isinstance(life_case_payload, dict) or not isinstance(record_payload, dict):
        raise ReadOnlyCanvasUnavailable("formal_life_case_not_available")

    birth = BirthInputCanonical.model_validate(birth_payload)
    world_model = ChartWorldInstance.model_validate(world)
    life_case = LifeCase.model_validate(life_case_payload)
    record = MingliCognitiveRecord.model_validate(record_payload)
    baseline = life_case.baseline_insight
    if (
        life_case.status != "active"
        or not life_case.chart_version.active
        or baseline.status != "committed"
        or baseline.epistemic_state not in {"reliable", "competing"}
        or record.reliability_disposition not in {"reliable", "competing"}
        or record.review.disposition not in {"reliable", "competing"}
    ):
        raise ReadOnlyCanvasUnavailable("formal_life_case_not_available")
    source_record_id = baseline.provenance.source_record_id or baseline.baseline_record_id
    if source_record_id and source_record_id != record.record_id:
        raise ReadOnlyCanvasUnavailable("canvas_baseline_record_mismatch")

    reading_id = world_model.reading_id or case_id
    calendar = normalize_birth_input(birth)
    material_store = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=calendar,
    )
    graph = build_mingli_graph_from_material_store(material_store)
    explored = explore_mingli_paths(graph)
    if not graph.nodes:
        raise ReadOnlyCanvasUnavailable("canvas_graph_unavailable")

    nodes_by_id = {item.node_id: item for item in graph.nodes}
    edges_by_id = {item.edge_id: item for item in graph.edges}
    node_ref_models = {
        node_id: node_ref_for_graph_node(
            node=node,
            world=world_model,
            life_case=life_case,
        )
        for node_id, node in nodes_by_id.items()
    }
    node_refs = {node_id: item.node_ref for node_id, item in node_ref_models.items()}
    relation_key_models = {
        edge_id: relation_key_for_graph_edge(
            edge=edge,
            nodes_by_id=nodes_by_id,
            world=world_model,
            life_case=life_case,
            node_refs_by_id=node_ref_models,
        )
        for edge_id, edge in edges_by_id.items()
    }
    relation_refs = {
        edge_id: item.relation_key
        for edge_id, item in relation_key_models.items()
    }
    relation_assertions = {
        str(item.get("relation_ref")): item
        for item in _active_projection_assertions(
            canonical_projection_payload.get("relation_assertions")
        )
        if item.get("relation_ref")
    }
    chart_source = _chart_source(
        birth=birth,
        graph=graph,
        chart_version_id=life_case.chart_version.version_id,
        world_id=world_model.world_id,
        node_refs=node_refs,
        relation_refs=relation_refs,
        relation_assertions=relation_assertions,
    )
    committed_paths = _committed_paths(
        canonical_projection_payload=canonical_projection_payload,
        life_case=life_case,
        available_node_refs=set(node_refs.values()),
        available_relation_refs=set(relation_refs.values()),
    )
    candidate_paths = _candidate_paths(
        explored_paths=explored.paths,
        record=record,
        committed_paths=committed_paths,
        nodes_by_id=nodes_by_id,
        edges_by_id=edges_by_id,
        node_refs=node_refs,
        relation_refs=relation_refs,
        node_ref_models=node_ref_models,
        relation_key_models=relation_key_models,
        world=world_model,
        life_case=life_case,
    )
    path_available = bool(committed_paths)
    projected_paths = canonical_projection_payload.get("path_assertions")
    projected_paths = projected_paths if isinstance(projected_paths, list) else []
    unresolved_count = sum(
        1 for item in projected_paths
        if isinstance(item, dict) and item.get("status") == "legacy_unresolved"
    )
    path_message = (
        "LifeCase 已提交主路径，并以稳定身份绑定到命盘关系。"
        if path_available
        else "LifeCase 的历史路径未能精确落到当前结构；原断言仍保留，本页不会根据文字猜线。"
    )
    uncertainty = list(dict.fromkeys([
        *baseline.uncertainty.reasons,
        *([] if path_available else ["正式主路径缺少可视化结构引用"]),
    ]))
    life_case_source = CanvasLifeCaseSource(
        life_case_id=life_case.life_case_id,
        life_case_version=life_case.case_version,
        paths=[*committed_paths, *candidate_paths],
        uncertainty=uncertainty,
        must_not_say=[
            "不得把时间柱出现说成确定事件",
            "不得把候选路径说成已提交判断",
            "不得根据自然语言自行补画关系",
        ],
    )
    timing = world.get("timing_context") if isinstance(world.get("timing_context"), dict) else {}
    canvas_nodes_by_ref = {item.node_ref: item for item in chart_source.nodes}
    natal_relation_nodes = [
        (canvas_nodes_by_ref[node_ref.node_ref], node_ref)
        for node_id, node_ref in node_ref_models.items()
        if node_ref.node_ref in canvas_nodes_by_ref
        and nodes_by_id[node_id].node_type.value in {"stem", "branch"}
    ]
    temporal_layers = _temporal_layers(
        timing=timing,
        world=world_model,
        life_case=life_case,
        day_stem=birth.day_pillar[0],
        natal_relation_nodes=natal_relation_nodes,
    )
    compiled_at = _parse_datetime(life_case.updated_at)
    source = MingliCanvasCompileInput(
        compiler_version="mingli-canvas-compiler.c1-real.v1",
        compiled_at=compiled_at,
        chart=chart_source,
        life_case=life_case_source,
        temporal_layers=temporal_layers,
    )
    luck_range = timing.get("luck_year_range") if isinstance(timing.get("luck_year_range"), list) else []
    return source, {
        "source": {
            "chart_version_id": life_case.chart_version.version_id,
            "life_case_id": life_case.life_case_id,
            "life_case_version": life_case.case_version,
            "cognitive_record_id": record.record_id,
            "luck_pillar": str(timing.get("luck_pillar") or ""),
            "luck_year_range": luck_range,
            "annual_pillar": str(timing.get("annual_pillar") or ""),
            "analysis_year": timing.get("analysis_year"),
            "timing_validation_status": str(timing.get("validation_status") or "unavailable"),
            "timing_publicly_supported": bool(timing.get("publicly_supported")),
        },
        "path_availability": {
            "status": "available" if path_available else "unavailable",
            "message": path_message,
            "committed_path_count": len(committed_paths),
            "candidate_path_count": len(candidate_paths),
            "legacy_unresolved_count": unresolved_count,
        },
    }


def _chart_source(
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
        _canvas_node(node, node_ref=node_refs[node.node_id])
        for node in graph.nodes
    ]
    nodes_by_id = {item.node_id: item for item in graph.nodes}
    relations = [
        _canvas_relation(
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
        clusters=_graph_clusters(graph=graph, node_refs=node_refs),
    )


def _canvas_node(node: MingliGraphNode, *, node_ref: str) -> CanvasNode:
    visible = node.node_type.value in {"stem", "branch"}
    return CanvasNode(
        node_ref=node_ref,
        label=node.label,
        node_type=node.node_type.value,
        semantic_slot_ref=_slot_ref_for_position(node.position),
        element=node.element,
        polarity=node.yin_yang,
        ten_god=node.ten_god,
        trace=CanvasTrace(
            source_mode="canonical" if visible else "derived",
            epistemic_status="fact" if visible else "derived",
            source_refs=_refs([*node.material_refs, *node.evidence_refs], fallback=node.node_id),
            disclosure="public" if visible else "member",
        ),
    )


def _canvas_relation(
    *,
    edge: MingliGraphEdge,
    nodes_by_id: dict[str, MingliGraphNode],
    node_refs: dict[str, str],
    relation_ref: str,
    assertion: dict[str, Any] | None,
) -> CanvasRelation:
    source = nodes_by_id[edge.from_node_id]
    target = nodes_by_id[edge.to_node_id]
    refs = _refs([*edge.material_refs, *edge.evidence_refs], fallback=edge.edge_id)
    label = f"{source.label}{RELATION_LABELS.get(edge.edge_type.value, edge.relation_label or edge.edge_type.value)}{target.label}"
    assertion_ref = str(assertion.get("assertion_ref")) if assertion else ""
    trace = (
        CanvasTrace(
            source_mode="committed",
            epistemic_status="committed",
            source_refs=_refs(
                [assertion_ref, *(assertion.get("source_refs") or []), *refs],
                fallback=relation_ref,
            ),
            commitment_refs=[assertion_ref],
            disclosure="member",
        )
        if assertion_ref
        else CanvasTrace(
            source_mode="derived",
            epistemic_status="derived",
            source_refs=refs,
            disclosure="member",
        )
    )
    return CanvasRelation(
        relation_ref=relation_ref,
        from_node_ref=node_refs[edge.from_node_id],
        to_node_ref=node_refs[edge.to_node_id],
        participant_node_refs=[node_refs[item] for item in edge.participant_node_ids],
        relation_type=edge.edge_type.value,
        label=label,
        semantic_state="active",
        trace=trace,
        state_trace=trace,
        change_reason_refs=refs,
    )


def _graph_clusters(*, graph: MingliGraph, node_refs: dict[str, str]) -> list[CanvasCluster]:
    groups: dict[str, list[MingliGraphNode]] = {}
    for node in graph.nodes:
        cluster_id = str(node.attributes.get("triple_combination") or "")
        if cluster_id:
            groups.setdefault(cluster_id, []).append(node)
    output: list[CanvasCluster] = []
    for cluster_id, nodes in sorted(groups.items()):
        refs = _refs(
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
                source_refs=refs,
                uncertainty=["结构组合候选不自动等于成局或吉凶"],
                disclosure="practitioner",
            ),
        ))
    return output


def _committed_paths(
    *,
    canonical_projection_payload: dict[str, Any],
    life_case: LifeCase,
    available_node_refs: set[str],
    available_relation_refs: set[str],
) -> list[CanvasPath]:
    baseline = life_case.baseline_insight
    output: list[CanvasPath] = []
    for item in _active_projection_assertions(
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
            source_refs=_refs(
                [assertion_ref, *(item.get("source_refs") or [])],
                fallback=baseline.insight_id,
            ),
            commitment_refs=[assertion_ref, baseline.insight_id],
            uncertainty=baseline.uncertainty.reasons,
            disclosure="member",
        )
        output.append(CanvasPath(
            path_ref=path_ref,
            label=_bounded(str(item.get("statement") or baseline.claim), 240),
            node_refs=node_refs,
            relation_refs=relation_refs,
            required_refs=node_refs,
            semantic_state="active",
            trace=trace,
            state_trace=trace,
            change_reason_refs=[assertion_ref, baseline.insight_id],
        ))
    return output


def _candidate_paths(
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
    refs = list(dict.fromkeys(record.cognition.work_path.competing_path_refs))
    committed_relation_chains = {
        tuple(item.relation_refs) for item in committed_paths
    }
    for ref in refs:
        path = by_id.get(ref)
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
            source_refs=_refs(
                [ref, path.path_key, *path.graph_refs, *path.evidence_refs],
                fallback=stable_path.path_key,
            ),
            uncertainty=["这条路径尚未进入 LifeCase 正式主判断"],
            disclosure="practitioner",
        )
        output.append(CanvasPath(
            path_ref=stable_path.path_key,
            label=_bounded(label, 240),
            node_refs=[node_refs[item] for item in path.node_ids],
            relation_refs=stable_relation_refs,
            semantic_state="latent",
            trace=trace,
            state_trace=trace,
            change_reason_refs=[ref],
        ))
    return output


def _active_projection_assertions(value: Any) -> list[dict[str, Any]]:
    rows = [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
    superseded = {str(item.get("supersedes")) for item in rows if item.get("supersedes")}
    return [
        item for item in rows
        if item.get("status") == "committed"
        and str(item.get("assertion_ref") or "") not in superseded
    ]


def _temporal_layers(
    *,
    timing: dict[str, Any],
    world: ChartWorldInstance,
    life_case: LifeCase,
    day_stem: str,
    natal_relation_nodes: list[tuple[CanvasNode, NodeRef]],
) -> list[CanvasTemporalLayer]:
    refs = _refs(
        [str(item) for item in timing.get("calculation_refs") or []],
        fallback=f"world:{world.world_id}:timing-context",
    )
    output: list[CanvasTemporalLayer] = []
    relation_nodes = list(natal_relation_nodes)
    luck_pillar = str(timing.get("luck_pillar") or "")
    if len(luck_pillar) >= 2:
        luck_range = timing.get("luck_year_range") if isinstance(timing.get("luck_year_range"), list) else []
        suffix = "-".join(str(item) for item in luck_range) or "current"
        layer, layer_nodes = _temporal_layer(
            layer_type="luck",
            pillar=luck_pillar,
            world=world,
            life_case=life_case,
            snapshot_suffix=suffix,
            day_stem=day_stem,
            source_refs=refs,
            relation_nodes=relation_nodes,
        )
        output.append(layer)
        relation_nodes.extend(layer_nodes)
    annual_pillar = str(timing.get("annual_pillar") or "")
    if len(annual_pillar) >= 2:
        layer, layer_nodes = _temporal_layer(
            layer_type="year",
            pillar=annual_pillar,
            world=world,
            life_case=life_case,
            snapshot_suffix=str(timing.get("analysis_year") or "current"),
            day_stem=day_stem,
            source_refs=refs,
            relation_nodes=relation_nodes,
        )
        output.append(layer)
        relation_nodes.extend(layer_nodes)
    return output


def _temporal_layer(
    *,
    layer_type: Literal["luck", "year"],
    pillar: str,
    world: ChartWorldInstance,
    life_case: LifeCase,
    snapshot_suffix: str,
    day_stem: str,
    source_refs: list[str],
    relation_nodes: list[tuple[CanvasNode, NodeRef]],
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
        relations=_temporal_relations(
            layer_type=layer_type,
            existing_nodes=relation_nodes,
            current_nodes=current_relation_nodes,
            scene_ref=scene_ref,
            source_refs=source_refs,
        ),
        source_refs=source_refs,
    )
    return layer, current_relation_nodes


def _temporal_relations(
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
    ]
    relations: dict[str, CanvasRelation] = {}
    for row in rows:
        participant_refs = _relation_participant_refs(row)
        if len(participant_refs) < 2 or not current_refs.intersection(participant_refs):
            continue
        relation_type = _core_relation_type(str(row.get("type", "")))
        if not relation_type or not set(participant_refs).issubset(nodes_by_ref):
            continue
        from_ref, to_ref = _relation_endpoints(
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
        refs = _refs(
            [*source_refs, f"rule:bazi.branch_relation:{row.get('type', '')}"],
            fallback=relation_key.relation_key,
        )
        trace = CanvasTrace(
            source_mode="derived",
            epistemic_status="derived",
            source_refs=refs,
            uncertainty=["结构关系存在不等于做功路径已经成立"],
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
            semantic_state="active",
            trace=trace,
            state_trace=trace,
            change_reason_refs=refs,
        )
    return [relations[key] for key in sorted(relations)]


def _relation_participant_refs(row: dict[str, object]) -> list[str]:
    slots = row.get("slots")
    if isinstance(slots, list):
        return [str(item) for item in slots]
    source_ref = str(row.get("source_ref") or row.get("slot_a") or "")
    target_ref = str(row.get("target_ref") or row.get("slot_b") or "")
    return [item for item in (source_ref, target_ref) if item]


def _core_relation_type(raw_type: str) -> str:
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
    }.get(raw_type, "")


def _relation_endpoints(
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


def _layer_catalog(spec: MingliCanvasSpec) -> list[dict[str, Any]]:
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


def _change_groups(
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
    before = _object_labels(before_spec)
    after = _object_labels(after_spec)
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


def _object_labels(spec: MingliCanvasSpec) -> dict[str, str]:
    return {
        **{item.slot_ref: f"{item.label} {item.stem}{item.branch}" for item in spec.semantic_slots},
        **{item.node_ref: item.label for item in spec.nodes},
        **{item.relation_ref: item.label for item in spec.relations},
        **{item.cluster_ref: item.label for item in spec.clusters},
        **{item.path_ref: item.label for item in spec.paths},
    }


def _object_refs(spec: MingliCanvasSpec) -> set[str]:
    return {
        *(item.slot_ref for item in spec.semantic_slots),
        *(item.node_ref for item in spec.nodes),
        *(item.relation_ref for item in spec.relations),
        *(item.cluster_ref for item in spec.clusters),
        *(item.path_ref for item in spec.paths),
    }


def _previous_stage(stage: str) -> str:
    return {"natal": "natal", "luck": "natal", "year": "luck"}[stage]


def _stage_title(stage: str, source: dict[str, Any]) -> str:
    return {
        "natal": "只看原局",
        "luck": f"加入 {source['luck_pillar']} 大运",
        "year": f"再加入 {source['analysis_year']} · {source['annual_pillar']} 流年",
    }[stage]


def _stage_summary(stage: str, source: dict[str, Any]) -> str:
    if stage == "natal":
        return "四柱与正式基线结构，不叠加时间变量。"
    if stage == "luck":
        return "大运位置已加入；没有正式路径更新时，系统不会猜测增强或受阻。"
    return "流年位置已加入；只展示已有合同变化，不预测具体事件。"


def _slot_ref_for_position(position: str) -> str:
    for prefix in POSITION_LABELS:
        if position.startswith(f"{prefix}_"):
            return f"slot-natal-{prefix}"
    return ""


def _refs(values: list[str], *, fallback: str) -> list[str]:
    refs = [str(item).strip() for item in values if str(item).strip()]
    return list(dict.fromkeys(refs or [fallback]))


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


def _bounded(value: str, limit: int) -> str:
    clean = " ".join(str(value).split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1]}…"
