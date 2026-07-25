from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from apps.product.canvas_projection import _chart_source, _temporal_relations
from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import (
    MingliRelationState,
    NodeRef,
    PathEligibility,
    RelationPositionContext,
    build_mingli_graph_from_material_store,
)
from core.graph.contracts import MingliGraphEdgeType, MingliGraphNodeType
from experience.canvas import (
    CanvasCompileRequest,
    CanvasLifeCaseSource,
    CanvasNode,
    CanvasTrace,
    MingliCanvasCompileInput,
    compile_canvas_spec,
    project_canvas_spec_for_role,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "v50_six02_cplus_relation_scope_v1.json"


def _graph(*, reading_id: str, pillars: tuple[str, str, str, str]):
    birth = BirthInputCanonical(
        birth_input_id=f"birth.{reading_id}",
        gender="unknown",
        calendar_type="solar",
        birth_date="2000-01-01",
        birth_time="12:00",
        timezone="Asia/Shanghai",
        year_pillar=pillars[0],
        month_pillar=pillars[1],
        day_pillar=pillars[2],
        hour_pillar=pillars[3],
        input_quality="synthetic_fixture",
        pillar_fact_source="structurally_legal_hypothetical",
    )
    store = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    return birth, build_mingli_graph_from_material_store(store)


def _node_ref(*, scope: str, level: str, component: str) -> NodeRef:
    return NodeRef(
        scene_ref="scene:six02",
        life_case_id="life-case:six02",
        chart_version_id="chart-version:six02",
        world_id="world:six02",
        scope=scope,
        slot=scope,
        level=level,
        component=component,
        temporal_snapshot_ref="" if scope == "natal" else f"temporal:{scope}:six02",
    )


def _canvas_node(*, node_ref: NodeRef, label: str, node_type: str, element: str) -> CanvasNode:
    return CanvasNode(
        node_ref=node_ref.node_ref,
        label=label,
        node_type=node_type,
        element=element,
        trace=CanvasTrace(
            source_mode="canonical" if node_ref.scope == "natal" else "derived",
            epistemic_status="fact",
            source_refs=[f"fixture:{node_ref.node_ref}"],
            disclosure="member",
        ),
    )


def test_six02_fixture_locks_the_four_state_order_and_three_synthetic_groups() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert payload["relation_state_order"] == [item.value for item in MingliRelationState]
    assert len(payload["synthetic_groups"]) == 3
    assert payload["position_context_contract"]["must_not_decide"] == [
        "strength",
        "effectiveness",
        "path_membership",
    ]


def test_six02_visible_stems_are_structural_while_hidden_stem_field_stays_potential() -> None:
    _, graph = _graph(
        reading_id="six02.atomic",
        pillars=("甲戌", "丙寅", "庚辰", "壬午"),
    )
    nodes = {item.node_id: item for item in graph.nodes}
    element_edges = [
        item
        for item in graph.edges
        if item.edge_type in {
            MingliGraphEdgeType.GENERATES,
            MingliGraphEdgeType.CONTROLS,
            MingliGraphEdgeType.SAME_ELEMENT_SUPPORT,
        }
    ]

    assert element_edges
    visible_stem_edges = [
        item
        for item in element_edges
        if nodes[item.from_node_id].node_type == MingliGraphNodeType.STEM
        and nodes[item.to_node_id].node_type == MingliGraphNodeType.STEM
    ]
    hidden_field_edges = [item for item in element_edges if item not in visible_stem_edges]

    assert visible_stem_edges
    assert hidden_field_edges
    assert all(item.relation_state == MingliRelationState.STRUCTURAL for item in visible_stem_edges)
    assert all(item.path_eligibility == PathEligibility.ELIGIBLE for item in visible_stem_edges)
    assert all(item.mechanism_ref == "visible_stem_same_layer" for item in visible_stem_edges)
    assert all(item.position_context is not None for item in visible_stem_edges)
    assert all(item.relation_state == MingliRelationState.POTENTIAL for item in hidden_field_edges)
    assert all(item.path_eligibility == PathEligibility.NOT_YET_QUALIFIED for item in hidden_field_edges)
    assert all(item.mechanism_ref == "five_element_potential_field" for item in hidden_field_edges)
    assert all(item.attributes["direct_action"] is False for item in element_edges)
    assert not any(
        {nodes[item.from_node_id].node_type, nodes[item.to_node_id].node_type}.intersection(
            {MingliGraphNodeType.BRANCH}
        )
        for item in element_edges
    )

    year_jia = next(
        item for item in graph.nodes
        if item.position == "year_stem" and item.label == "甲"
    )
    year_hidden = {
        item.node_id: item.label
        for item in graph.nodes
        if item.position == "year_hidden_stem"
    }
    jia_xu_edges = [
        item
        for item in element_edges
        if year_jia.node_id in item.participant_node_ids
        and set(item.participant_node_ids).intersection(year_hidden)
    ]
    assert {year_hidden[next(ref for ref in item.participant_node_ids if ref in year_hidden)] for item in jia_xu_edges} == {"戊", "辛", "丁"}

    position = next(
        item for item in graph.edges
        if item.edge_type == MingliGraphEdgeType.POSITION_LINK
        and item.attributes.get("slot") == "year"
    )
    assert position.relation_state == MingliRelationState.STRUCTURAL
    assert position.position_context is not None
    assert position.position_context.column_span == 0
    assert position.attributes == {
        "slot": "year",
        "mechanism": "same_pillar_bearing",
        "proximity": "same_pillar",
        "direct_action": False,
    }


def test_six02_position_context_records_distance_without_deciding_effectiveness() -> None:
    _, graph = _graph(
        reading_id="six02.position",
        pillars=("甲戌", "丙寅", "庚辰", "壬午"),
    )
    nodes = {item.node_id: item for item in graph.nodes}
    visible_relations = [
        item
        for item in graph.edges
        if item.mechanism_ref == "visible_stem_same_layer"
    ]
    adjacent = next(
        item
        for item in visible_relations
        if nodes[item.from_node_id].position == "year_stem"
        and nodes[item.to_node_id].position == "month_stem"
    )
    separated = next(
        item
        for item in visible_relations
        if nodes[item.from_node_id].position == "day_stem"
        and nodes[item.to_node_id].position == "year_stem"
    )

    assert adjacent.position_context is not None
    assert adjacent.position_context.adjacent is True
    assert adjacent.position_context.column_span == 1
    assert adjacent.relation_state == MingliRelationState.STRUCTURAL
    assert separated.position_context is not None
    assert separated.position_context.adjacent is False
    assert separated.position_context.column_span == 2
    assert len(separated.position_context.intervening_node_refs) == 1
    assert separated.position_context.direction == "right_to_left"
    assert separated.relation_state == MingliRelationState.STRUCTURAL
    assert separated.relation_state != MingliRelationState.EFFECTIVE


def test_same_slot_name_in_natal_and_year_scopes_is_not_the_same_column() -> None:
    context = RelationPositionContext(
        source_scope="natal",
        target_scope="year",
        source_slot="year",
        target_slot="year",
        source_level="stem",
        target_level="stem",
        column_span=5,
        intervening_node_refs=["month", "day", "hour", "luck"],
        ref_namespace="node_ref",
        direction="natal_to_temporal",
        scene_layer="year_state",
    )

    assert context.column_span == 5
    assert context.source_scope != context.target_scope


def test_six02_repeated_labels_keep_distinct_deterministic_potential_relations() -> None:
    _, first = _graph(
        reading_id="six02.repeated",
        pillars=("甲戌", "甲戌", "庚戌", "壬午"),
    )
    _, second = _graph(
        reading_id="six02.repeated",
        pillars=("甲戌", "甲戌", "庚戌", "壬午"),
    )
    jia_nodes = [
        item for item in first.nodes
        if item.node_type == MingliGraphNodeType.STEM and item.label == "甲"
    ]
    potential = [item for item in first.edges if item.relation_state == MingliRelationState.POTENTIAL]

    assert {item.position for item in jia_nodes} == {"year_stem", "month_stem"}
    assert len({item.node_key for item in jia_nodes}) == 2
    assert len({item.relation_key for item in potential}) == len(potential)
    assert [item.relation_key for item in potential] == [
        item.relation_key
        for item in second.edges
        if item.relation_state == MingliRelationState.POTENTIAL
    ]


def test_six02_member_projection_hides_potential_field_and_hidden_stem_detail() -> None:
    birth, graph = _graph(
        reading_id="six02.projection",
        pillars=("甲戌", "丙寅", "庚辰", "壬午"),
    )
    node_refs = {item.node_id: item.node_id for item in graph.nodes}
    relation_refs = {item.edge_id: item.relation_key for item in graph.edges}
    chart = _chart_source(
        birth=birth,
        graph=graph,
        chart_version_id="chart-version:six02",
        world_id="world:six02",
        node_refs=node_refs,
        relation_refs=relation_refs,
        relation_assertions={},
    )
    source = MingliCanvasCompileInput(
        compiler_version="six02-cplus-regression.v1",
        compiled_at=datetime(2026, 7, 21, tzinfo=timezone.utc),
        chart=chart,
        life_case=CanvasLifeCaseSource(
            life_case_id="life-case:six02",
            life_case_version="v1",
        ),
    )
    full = compile_canvas_spec(CanvasCompileRequest(source=source, stage="natal"))
    member = project_canvas_spec_for_role(full, "member")
    practitioner = project_canvas_spec_for_role(full, "practitioner")

    assert not [item for item in member.relations if item.relation_state == "potential"]
    assert not [item for item in member.relations if item.relation_state == "structural"]
    assert not [item for item in member.nodes if item.node_type == "hidden_stem"]
    assert all(not item.hidden_stems for item in member.semantic_slots)
    assert [item for item in practitioner.relations if item.relation_state == "potential"]
    assert [item for item in practitioner.nodes if item.node_type == "hidden_stem"]
    assert any(item.hidden_stems for item in practitioner.semantic_slots)


def test_six02_temporal_visible_stems_are_structural_while_named_branch_relation_activates() -> None:
    natal_stem_ref = _node_ref(scope="natal", level="stem", component="丁")
    natal_branch_ref = _node_ref(scope="natal", level="branch", component="午")
    luck_stem_ref = _node_ref(scope="luck", level="stem", component="庚")
    luck_branch_ref = _node_ref(scope="luck", level="branch", component="子")
    relations = _temporal_relations(
        layer_type="luck",
        existing_nodes=[
            (_canvas_node(node_ref=natal_stem_ref, label="丁", node_type="stem", element="fire"), natal_stem_ref),
            (_canvas_node(node_ref=natal_branch_ref, label="午", node_type="branch", element="fire"), natal_branch_ref),
        ],
        current_nodes=[
            (_canvas_node(node_ref=luck_stem_ref, label="庚", node_type="luck_stem", element="metal"), luck_stem_ref),
            (_canvas_node(node_ref=luck_branch_ref, label="子", node_type="luck_branch", element="water"), luck_branch_ref),
        ],
        scene_ref="scene:six02",
        source_refs=["fixture:six02:temporal"],
    )

    generic = [item for item in relations if item.relation_type in {"generates", "controls", "same_element_support"}]
    clash = next(item for item in relations if item.relation_type == "clashes")
    position = next(item for item in relations if item.relation_type == "position_link")
    assert generic and all(item.relation_state == "structural" for item in generic)
    assert all(item.semantic_state == "latent" for item in generic)
    assert all(item.mechanism_ref == "visible_stem_same_layer" for item in generic)
    assert all(item.position_context is not None for item in generic)
    assert all(item.position_context.scene_layer == "luck_state" for item in generic if item.position_context)
    assert clash.relation_state == "time_activated"
    assert clash.position_context is not None
    assert position.relation_state == "structural"
    assert "不自动表示直接作用" in position.trace.uncertainty[0]
