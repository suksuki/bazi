from __future__ import annotations

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import (
    PathEligibility,
    build_mingli_graph_from_material_store,
    explore_mingli_paths,
    validate_whole_path_candidate,
)
from core.graph.contracts import MingliGraphEdgeType


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
    return build_mingli_graph_from_material_store(store)


def test_ra2_assigns_one_typed_qualification_to_every_relation() -> None:
    graph = _graph(
        reading_id="ra2.qualification.coverage",
        pillars=("丁巳", "乙巳", "乙丑", "乙酉"),
    )

    assert graph.edges
    assert all(isinstance(edge.path_eligibility, PathEligibility) for edge in graph.edges)
    assert all(edge.eligibility_reason_refs for edge in graph.edges)
    assert all("path_eligibility" not in edge.attributes for edge in graph.edges)


def test_ra2_explorer_only_consumes_explicitly_eligible_relations() -> None:
    graph = _graph(
        reading_id="ra2.qualification.explorer",
        pillars=("丁巳", "乙巳", "乙丑", "乙酉"),
    )
    edges_by_id = {edge.edge_id: edge for edge in graph.edges}
    result = explore_mingli_paths(graph)

    assert result.paths
    assert all(
        edges_by_id[edge_id].path_eligibility == PathEligibility.ELIGIBLE
        for path in result.paths
        for edge_id in path.edge_ids
    )
    forbidden = {
        MingliGraphEdgeType.POSITION_LINK,
        MingliGraphEdgeType.ROOTS,
        MingliGraphEdgeType.FORMS_HALF_COMBINATION,
        MingliGraphEdgeType.CLASHES,
        MingliGraphEdgeType.HARMONIZES,
        MingliGraphEdgeType.HARMS,
        MingliGraphEdgeType.BREAKS,
        MingliGraphEdgeType.PUNISHES,
    }
    assert not any(
        edges_by_id[edge_id].edge_type in forbidden
        for path in result.paths
        for edge_id in path.edge_ids
    )


def test_ra2_complete_triple_relation_can_form_a_qualified_path_segment() -> None:
    graph = _graph(
        reading_id="ra2.qualification.triple",
        pillars=("丁巳", "乙酉", "乙丑", "乙巳"),
    )
    triple_ids = {
        edge.edge_id
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
    }
    result = explore_mingli_paths(graph)

    assert triple_ids
    assert any(triple_ids & set(path.edge_ids) for path in result.paths)


def test_ra2_whole_path_validator_rejects_reversed_directed_relation() -> None:
    graph = _graph(
        reading_id="ra2.qualification.direction",
        pillars=("丁巳", "乙巳", "乙丑", "乙酉"),
    )
    edge = next(
        edge
        for edge in graph.edges
        if edge.edge_type in {MingliGraphEdgeType.GENERATES, MingliGraphEdgeType.CONTROLS}
    )

    validation = validate_whole_path_candidate(
        graph,
        node_ids=[edge.to_node_id, edge.from_node_id],
        edge_ids=[edge.edge_id],
    )

    assert validation.passed is False
    assert f"path.directed_edge_reversed_or_disconnected:{edge.edge_id}" in validation.reason_codes


def test_ra2_whole_path_validator_rejects_evidence_only_position_link() -> None:
    graph = _graph(
        reading_id="ra2.qualification.evidence",
        pillars=("丁巳", "乙巳", "乙丑", "乙酉"),
    )
    edge = next(
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.POSITION_LINK
    )

    validation = validate_whole_path_candidate(
        graph,
        node_ids=[edge.from_node_id, edge.to_node_id],
        edge_ids=[edge.edge_id],
    )

    assert validation.passed is False
    assert f"path.edge_not_eligible:{edge.edge_id}" in validation.reason_codes


def test_ra2_whole_path_validator_rejects_repeated_nodes() -> None:
    graph = _graph(
        reading_id="ra2.qualification.repeat",
        pillars=("丁巳", "乙巳", "乙丑", "乙酉"),
    )

    validation = validate_whole_path_candidate(
        graph,
        node_ids=[graph.nodes[0].node_id, graph.nodes[0].node_id],
        edge_ids=[graph.edges[0].edge_id],
    )

    assert validation.passed is False
    assert "path.repeated_node" in validation.reason_codes
