from __future__ import annotations

from typing import Any

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.life_case import LifeCase, node_ref_for_graph_node, relation_key_for_graph_edge
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord
from experience.canvas import CanvasLifeCaseSource, MingliCanvasCompileInput

from product.canvas_projection_graph import (
    active_projection_assertions,
    candidate_paths,
    chart_source,
    committed_paths,
)
from product.canvas_projection_shared import ReadOnlyCanvasUnavailable, parse_datetime
from product.canvas_projection_temporal import temporal_layers


def compile_input_from_case_row(
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
        for item in active_projection_assertions(
            canonical_projection_payload.get("relation_assertions")
        )
        if item.get("relation_ref")
    }
    chart = chart_source(
        birth=birth,
        graph=graph,
        chart_version_id=life_case.chart_version.version_id,
        world_id=world_model.world_id,
        node_refs=node_refs,
        relation_refs=relation_refs,
        relation_assertions=relation_assertions,
    )
    formal_paths = committed_paths(
        canonical_projection_payload=canonical_projection_payload,
        life_case=life_case,
        available_node_refs=set(node_refs.values()),
        available_relation_refs=set(relation_refs.values()),
    )
    research_paths = candidate_paths(
        explored_paths=explored.paths,
        record=record,
        committed_paths=formal_paths,
        nodes_by_id=nodes_by_id,
        edges_by_id=edges_by_id,
        node_refs=node_refs,
        relation_refs=relation_refs,
        node_ref_models=node_ref_models,
        relation_key_models=relation_key_models,
        world=world_model,
        life_case=life_case,
    )
    path_available = bool(formal_paths)
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
        paths=[*formal_paths, *research_paths],
        uncertainty=uncertainty,
        must_not_say=[
            "不得把时间柱出现说成确定事件",
            "不得把候选路径说成已提交判断",
            "不得根据自然语言自行补画关系",
        ],
    )
    timing = world.get("timing_context") if isinstance(world.get("timing_context"), dict) else {}
    canvas_nodes_by_ref = {item.node_ref: item for item in chart.nodes}
    natal_relation_nodes = [
        (canvas_nodes_by_ref[node_ref.node_ref], node_ref)
        for node_id, node_ref in node_ref_models.items()
        if node_ref.node_ref in canvas_nodes_by_ref
        and nodes_by_id[node_id].node_type.value in {"stem", "branch"}
    ]
    time_layers = temporal_layers(
        timing=timing,
        world=world_model,
        life_case=life_case,
        day_stem=birth.day_pillar[0],
        natal_relation_nodes=natal_relation_nodes,
        tracked_paths=formal_paths,
    )
    source = MingliCanvasCompileInput(
        compiler_version="mingli-canvas-compiler.c1-real.v1",
        compiled_at=parse_datetime(life_case.updated_at),
        chart=chart,
        life_case=life_case_source,
        temporal_layers=time_layers,
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
            "committed_path_count": len(formal_paths),
            "candidate_path_count": len(research_paths),
            "legacy_unresolved_count": unresolved_count,
        },
    }
