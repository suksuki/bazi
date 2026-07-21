from __future__ import annotations

import json

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.path_explorer import _candidate_order_key
from core.mingli_agent import compile_chart_world
from experience.canvas import CanvasPath, CanvasRelation, CanvasTrace
from product.canvas_projection import (
    TEMPORAL_PATH_UPDATE_POLICY_VERSION,
    _temporal_path_updates,
)
from product.theater_experiment import _snapshot_from_case_row
from test_v50_mingli_structural_experiment import _case_payload


def _birth() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth-ra3-path-evidence",
        name="RA3 path evidence",
        gender="male",
        calendar_type="solar",
        birth_date="1977-05-20",
        birth_time="18:00",
        birth_location="Guangzhou",
        timezone="Asia/Shanghai",
        input_quality="complete",
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
    )


def _graph_and_paths():
    birth = _birth()
    calendar = normalize_birth_input(birth)
    store = build_bazi_material_store(
        reading_id="reading.ra3.path-evidence",
        birth_input=birth,
        calendar=calendar,
    )
    graph = build_mingli_graph_from_material_store(store)
    return graph, explore_mingli_paths(graph)


def test_ra3_exposes_discrete_path_evidence_and_isolates_legacy_numbers() -> None:
    graph, result = _graph_and_paths()

    assert result.paths
    for path in result.paths:
        payload = path.model_dump(mode="json")
        assert path.evidence_vector.reason_refs
        assert path.evidence_vector.closure.value == "closed"
        assert "path_score" not in payload
        assert "source_strength" not in payload
        assert payload["legacy_unvalidated_metrics"]["status"].startswith(
            "legacy_unvalidated"
        )
    for edge in graph.edges:
        payload = edge.model_dump(mode="json")
        assert "strength" not in payload
        assert "legacy_unvalidated_strength" in payload


def test_ra3_candidate_order_does_not_depend_on_legacy_path_score() -> None:
    graph, result = _graph_and_paths()
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    original_ids = [path.path_id for path in result.paths]
    changed = [
        path.model_copy(
            update={
                "legacy_unvalidated_metrics": path.legacy_unvalidated_metrics.model_copy(
                    update={"path_score": round(1.0 - path.legacy_unvalidated_metrics.path_score, 3)}
                )
            }
        )
        for path in result.paths
    ]

    assert [
        path.path_id
        for path in sorted(
            changed,
            key=lambda path: _candidate_order_key(path, nodes_by_id=nodes_by_id),
        )
    ] == original_ids
    assert result.ordering_policy == "path_candidate_evidence_order_v1"


def test_ra3_llm_world_and_product_snapshot_do_not_receive_path_scores() -> None:
    world = compile_chart_world(
        reading_id="reading.ra3.world",
        birth_input=_birth(),
    )
    path_facts = [item for item in world.facts if item.category == "candidate_path"]
    assert path_facts
    for fact in path_facts:
        assert "tool_score" not in fact.payload
        assert "工具分数" not in fact.statement
        assert fact.payload["validation_status"] in {
            "qualified",
            "qualified_with_conditions",
        }

    row = _case_payload("case-ra3-product-projection")
    snapshot = _snapshot_from_case_row(
        case_id="case-ra3-product-projection",
        row=row,
    ).model_dump(mode="json")
    serialized = json.dumps(snapshot, ensure_ascii=False)
    assert '"tool_score"' not in serialized
    assert '"strength"' not in serialized
    assert all(item["evidence"]["reason_refs"] for item in snapshot["approved_paths"])
    assert all(item["eligibility_reason_refs"] for item in snapshot["edges"])


def _derived_trace(*refs: str) -> CanvasTrace:
    return CanvasTrace(
        source_mode="derived",
        epistemic_status="derived",
        source_refs=list(refs),
        uncertainty=["fixture"],
        disclosure="member",
    )


def _committed_path(*, state: str = "active") -> CanvasPath:
    trace = CanvasTrace(
        source_mode="committed",
        epistemic_status="committed",
        source_refs=["fixture:committed-path"],
        commitment_refs=["fixture:commitment"],
        disclosure="member",
    )
    return CanvasPath(
        path_ref="path:fixture",
        label="fixture path",
        node_refs=["n1", "n2"],
        relation_refs=["base:r1"],
        required_refs=["n1", "n2"],
        semantic_state=state,
        trace=trace,
        state_trace=trace,
        change_reason_refs=["fixture:commitment"],
    )


def _relation(
    relation_ref: str,
    relation_type: str,
    source: str,
    target: str,
) -> CanvasRelation:
    trace = _derived_trace(relation_ref)
    return CanvasRelation(
        relation_ref=relation_ref,
        from_node_ref=source,
        to_node_ref=target,
        participant_node_refs=[source, target],
        relation_type=relation_type,
        label=relation_type,
        trace=trace,
        state_trace=trace,
        change_reason_refs=[relation_ref],
    )


def test_ra3_temporal_path_updates_are_discrete_directional_and_unranked() -> None:
    path = _committed_path(state="weakened")
    mixed = _temporal_path_updates(
        tracked_paths=[path],
        relations=[
            _relation("relation:support", "generates", "time", "n1"),
            _relation("relation:restraint", "controls", "time", "n2"),
        ],
        temporal_node_refs={"time"},
        layer_type="year",
    )
    assert len(mixed) == 1
    assert mixed[0].semantic_state == "weakened"
    assert "不做强弱排序" in mixed[0].state_trace.uncertainty[0]
    assert TEMPORAL_PATH_UPDATE_POLICY_VERSION in mixed[0].change_reason_refs

    conflict_only = _temporal_path_updates(
        tracked_paths=[_committed_path()],
        relations=[_relation("relation:clash", "clashes", "time", "n1")],
        temporal_node_refs={"time"},
        layer_type="year",
    )
    assert conflict_only == []
