from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import (
    BRANCH_ELEMENTS,
    HIDDEN_STEMS,
    STEM_ELEMENTS,
    STEM_POLARITY,
)
from core.engines.bazi.material_engine import resolve_ten_god
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphEdge, MingliGraphNode, MingliPath
from core.life_case import LifeCase
from core.mingli_agent.contracts import MingliCognitiveRecord
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
from product.agent_case_store import AgentCaseStore


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
    "activates": "引动",
    "bridges": "通关",
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

        return {
            "schema_version": "deepbazi.read_only_six_pillar_canvas.v1",
            "status": "read_only_canvas_ready",
            "case_id": case_id,
            "role": role,
            "stage_order": ["natal", "luck", "year"],
            "default_stage": "natal",
            "source": source,
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
        source, metadata = _compile_input_from_case_row(case_id=case_id, row=row)
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
        return {
            "source": metadata["source"],
            "path_availability": metadata["path_availability"],
            "specs": specs,
            "diffs": diffs,
        }


def canvas_role(account_role: str) -> CanvasRole:
    return {
        "admin": "admin",
        "research_master": "research",
        "research": "research",
        "practitioner": "practitioner",
        "member": "member",
    }.get(str(account_role).strip().lower(), "guest")  # type: ignore[return-value]


def _compile_input_from_case_row(
    *,
    case_id: str,
    row: dict[str, Any],
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

    reading_id = str(world.get("reading_id") or case_id)
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

    chart_source = _chart_source(
        birth=birth,
        graph=graph,
        chart_version_id=life_case.chart_version.version_id,
        world_id=str(world.get("world_id") or life_case.chart_version.world_id),
    )
    committed_path = _committed_path(
        graph=graph,
        world=world,
        life_case=life_case,
        record=record,
    )
    candidate_paths = _candidate_paths(
        graph=graph,
        explored_paths=explored.paths,
        record=record,
        committed_path=committed_path,
    )
    path_available = committed_path is not None
    path_message = (
        "LifeCase 已提交主路径，并且结构化证据已唯一落到命盘关系。"
        if path_available
        else "LifeCase 已有文字判断，但尚未保存可唯一定位的结构化主路径；本页不会根据文字猜线。"
    )
    uncertainty = list(dict.fromkeys([
        *baseline.uncertainty.reasons,
        *([] if path_available else ["正式主路径缺少可视化结构引用"]),
    ]))
    life_case_source = CanvasLifeCaseSource(
        life_case_id=life_case.life_case_id,
        life_case_version=life_case.case_version,
        paths=[*([committed_path] if committed_path else []), *candidate_paths],
        uncertainty=uncertainty,
        must_not_say=[
            "不得把时间柱出现说成确定事件",
            "不得把候选路径说成已提交判断",
            "不得根据自然语言自行补画关系",
        ],
    )
    timing = world.get("timing_context") if isinstance(world.get("timing_context"), dict) else {}
    temporal_layers = _temporal_layers(
        timing=timing,
        world_id=str(world.get("world_id") or life_case.chart_version.world_id),
        day_stem=birth.day_pillar[0],
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
            "committed_path_count": 1 if path_available else 0,
            "candidate_path_count": len(candidate_paths),
        },
    }


def _chart_source(
    *,
    birth: BirthInputCanonical,
    graph: MingliGraph,
    chart_version_id: str,
    world_id: str,
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
    nodes = [_canvas_node(node) for node in graph.nodes]
    nodes_by_id = {item.node_id: item for item in graph.nodes}
    relations = [_canvas_relation(edge=edge, nodes_by_id=nodes_by_id) for edge in graph.edges]
    return CanvasChartSource(
        chart_version_id=chart_version_id,
        world_id=world_id,
        slots=slots,
        nodes=nodes,
        relations=relations,
        clusters=_graph_clusters(graph=graph),
    )


def _canvas_node(node: MingliGraphNode) -> CanvasNode:
    visible = node.node_type.value in {"stem", "branch"}
    return CanvasNode(
        node_ref=node.node_id,
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


def _canvas_relation(*, edge: MingliGraphEdge, nodes_by_id: dict[str, MingliGraphNode]) -> CanvasRelation:
    source = nodes_by_id[edge.from_node_id]
    target = nodes_by_id[edge.to_node_id]
    refs = _refs([*edge.material_refs, *edge.evidence_refs], fallback=edge.edge_id)
    label = f"{source.label}{RELATION_LABELS.get(edge.edge_type.value, edge.relation_label or edge.edge_type.value)}{target.label}"
    trace = CanvasTrace(
        source_mode="derived",
        epistemic_status="derived",
        source_refs=refs,
        disclosure="member",
    )
    return CanvasRelation(
        relation_ref=edge.edge_id,
        from_node_ref=edge.from_node_id,
        to_node_ref=edge.to_node_id,
        relation_type=edge.edge_type.value,
        label=label,
        semantic_state="active",
        trace=trace,
        state_trace=trace,
        change_reason_refs=refs,
    )


def _graph_clusters(*, graph: MingliGraph) -> list[CanvasCluster]:
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
            node_refs=[item.node_id for item in nodes],
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


def _committed_path(
    *,
    graph: MingliGraph,
    world: dict[str, Any],
    life_case: LifeCase,
    record: MingliCognitiveRecord,
) -> CanvasPath | None:
    facts = {
        str(item.get("fact_id")): item
        for item in world.get("facts") or []
        if isinstance(item, dict) and item.get("fact_id")
    }
    nodes_by_id = {item.node_id: item for item in graph.nodes}
    relation_refs: list[str] = []
    node_refs: list[str] = []
    typed_refs: list[str] = []
    for evidence_ref in record.cognition.work_path.evidence_refs:
        fact = facts.get(str(evidence_ref))
        if not fact or fact.get("category") != "graph_relation":
            continue
        payload = fact.get("payload") if isinstance(fact.get("payload"), dict) else {}
        matches = [
            edge for edge in graph.edges
            if _edge_matches_fact(edge=edge, nodes_by_id=nodes_by_id, payload=payload)
        ]
        if len(matches) != 1:
            return None
        edge = matches[0]
        typed_refs.append(str(evidence_ref))
        relation_refs.append(edge.edge_id)
        for node_ref in (edge.from_node_id, edge.to_node_id):
            if node_ref not in node_refs:
                node_refs.append(node_ref)
    if not typed_refs or len(node_refs) < 2:
        return None
    baseline = life_case.baseline_insight
    trace = CanvasTrace(
        source_mode="committed",
        epistemic_status="committed",
        source_refs=_refs([record.record_id, *typed_refs], fallback=baseline.insight_id),
        commitment_refs=[baseline.insight_id],
        uncertainty=baseline.uncertainty.reasons,
        disclosure="member",
    )
    return CanvasPath(
        path_ref=f"path-committed-{record.record_id}",
        label=_bounded(record.cognition.work_path.path_statement or baseline.claim, 240),
        node_refs=node_refs,
        relation_refs=relation_refs,
        required_refs=node_refs,
        semantic_state="active",
        trace=trace,
        state_trace=trace,
        change_reason_refs=[baseline.insight_id, *typed_refs],
    )


def _candidate_paths(
    *,
    graph: MingliGraph,
    explored_paths: list[MingliPath],
    record: MingliCognitiveRecord,
    committed_path: CanvasPath | None,
) -> list[CanvasPath]:
    by_id = {item.path_id: item for item in explored_paths}
    output: list[CanvasPath] = []
    refs = list(dict.fromkeys(record.cognition.work_path.competing_path_refs))
    for ref in refs:
        path = by_id.get(ref)
        if path is None:
            continue
        relation_refs = list(path.edge_ids)
        if committed_path and relation_refs == committed_path.relation_refs:
            continue
        nodes_by_id = {item.node_id: item for item in graph.nodes}
        label = "竞争路径：" + " → ".join(nodes_by_id[item].label for item in path.node_ids)
        trace = CanvasTrace(
            source_mode="derived",
            epistemic_status="candidate",
            source_refs=_refs([ref, *path.graph_refs, *path.evidence_refs], fallback=path.path_id),
            uncertainty=["这条路径尚未进入 LifeCase 正式主判断"],
            disclosure="practitioner",
        )
        output.append(CanvasPath(
            path_ref=path.path_id,
            label=_bounded(label, 240),
            node_refs=path.node_ids,
            relation_refs=path.edge_ids,
            semantic_state="latent",
            trace=trace,
            state_trace=trace,
            change_reason_refs=[ref],
        ))
    return output


def _edge_matches_fact(
    *,
    edge: MingliGraphEdge,
    nodes_by_id: dict[str, MingliGraphNode],
    payload: dict[str, Any],
) -> bool:
    source = nodes_by_id.get(edge.from_node_id)
    target = nodes_by_id.get(edge.to_node_id)
    return bool(
        source
        and target
        and edge.edge_type.value == str(payload.get("relation") or "")
        and source.position == str(payload.get("from_position") or "")
        and target.position == str(payload.get("to_position") or "")
        and source.label == str(payload.get("from") or "")
        and target.label == str(payload.get("to") or "")
    )


def _temporal_layers(
    *,
    timing: dict[str, Any],
    world_id: str,
    day_stem: str,
) -> list[CanvasTemporalLayer]:
    refs = _refs(
        [str(item) for item in timing.get("calculation_refs") or []],
        fallback=f"world:{world_id}:timing-context",
    )
    output: list[CanvasTemporalLayer] = []
    luck_pillar = str(timing.get("luck_pillar") or "")
    if len(luck_pillar) >= 2:
        luck_range = timing.get("luck_year_range") if isinstance(timing.get("luck_year_range"), list) else []
        suffix = "-".join(str(item) for item in luck_range) or "current"
        output.append(_temporal_layer(
            layer_type="luck",
            pillar=luck_pillar,
            world_id=world_id,
            snapshot_suffix=suffix,
            day_stem=day_stem,
            source_refs=refs,
        ))
    annual_pillar = str(timing.get("annual_pillar") or "")
    if len(annual_pillar) >= 2:
        output.append(_temporal_layer(
            layer_type="year",
            pillar=annual_pillar,
            world_id=world_id,
            snapshot_suffix=str(timing.get("analysis_year") or "current"),
            day_stem=day_stem,
            source_refs=refs,
        ))
    return output


def _temporal_layer(
    *,
    layer_type: Literal["luck", "year"],
    pillar: str,
    world_id: str,
    snapshot_suffix: str,
    day_stem: str,
    source_refs: list[str],
) -> CanvasTemporalLayer:
    stem, branch = pillar[0], pillar[1]
    layer_id = f"{layer_type}:{world_id}:{pillar}:{snapshot_suffix}"
    slot_ref = f"slot-{layer_type}-{world_id}-{pillar}"
    trace = CanvasTrace(
        source_mode="derived",
        epistemic_status="fact",
        source_refs=source_refs,
        uncertainty=["时间柱已完成历法计算；其现实作用仍需正式命理认知"],
        disclosure="member",
    )
    return CanvasTemporalLayer(
        layer_id=layer_id,
        layer_type=layer_type,
        layer_mode="official",
        temporal_snapshot_id=f"temporal:{world_id}:{layer_type}:{snapshot_suffix}",
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
        nodes=[
            CanvasNode(
                node_ref=f"node:{world_id}:{layer_type}:stem:{stem}",
                label=stem,
                node_type=f"{layer_type}_stem",
                semantic_slot_ref=slot_ref,
                element=STEM_ELEMENTS.get(stem, ""),
                polarity=STEM_POLARITY.get(stem, ""),
                ten_god=resolve_ten_god(day_stem=day_stem, other_stem=stem),
                trace=trace,
            ),
            CanvasNode(
                node_ref=f"node:{world_id}:{layer_type}:branch:{branch}",
                label=branch,
                node_type=f"{layer_type}_branch",
                semantic_slot_ref=slot_ref,
                element=BRANCH_ELEMENTS.get(branch, ""),
                polarity=BRANCH_POLARITY.get(branch, ""),
                trace=trace,
            ),
        ],
        source_refs=source_refs,
    )


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
