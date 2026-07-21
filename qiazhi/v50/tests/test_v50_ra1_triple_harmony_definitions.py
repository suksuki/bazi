from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import TRIPLE_HARMONY
from core.engines.bazi.pillar_cycle import BRANCHES, JIAZI
from core.graph import build_mingli_graph_from_material_store
from core.graph.contracts import MingliGraphEdgeType


PILLAR_BY_BRANCH = {
    branch: next(pillar for pillar in JIAZI if pillar[1] == branch)
    for branch in BRANCHES
}


def _graph(*, case_id: str, branches: tuple[str, str, str, str]):
    birth = BirthInputCanonical(
        birth_input_id=f"birth.{case_id}",
        gender="unknown",
        calendar_type="solar",
        birth_date="2000-01-01",
        birth_time="12:00",
        timezone="Asia/Shanghai",
        year_pillar=PILLAR_BY_BRANCH[branches[0]],
        month_pillar=PILLAR_BY_BRANCH[branches[1]],
        day_pillar=PILLAR_BY_BRANCH[branches[2]],
        hour_pillar=PILLAR_BY_BRANCH[branches[3]],
        input_quality="synthetic_fixture",
        pillar_fact_source="structurally_legal_hypothetical",
    )
    store = build_bazi_material_store(
        reading_id=case_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    return build_mingli_graph_from_material_store(store)


@pytest.mark.parametrize(
    ("members", "relation_id", "element", "bridge"),
    [
        (tuple(sorted(members)), relation_id, element, bridge)
        for members, (relation_id, element, bridge) in TRIPLE_HARMONY.items()
    ],
)
def test_ra1_all_four_triple_harmony_definitions_are_recognized(
    members: tuple[str, str, str],
    relation_id: str,
    element: str,
    bridge: str,
) -> None:
    graph = _graph(
        case_id=f"ra1.triple.{relation_id}",
        branches=(*members, members[0]),
    )
    edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
        and edge.relation_label == relation_id
    ]
    bridge_nodes = [
        node
        for node in graph.nodes
        if node.label == bridge and node.attributes.get("triple_combination_bridge")
    ]

    assert edges
    assert bridge_nodes
    assert all(len(edge.participant_node_ids) == 3 for edge in edges)
    assert all(
        {node_id.split(":")[-1] for node_id in edge.participant_node_ids} == set(members)
        for edge in edges
    )
    assert all(edge.attributes["element"] == element for edge in edges)
    assert all(edge.material_refs for edge in edges)


@pytest.mark.parametrize(
    ("members", "relation_id"),
    [
        (tuple(sorted(members)), relation_id)
        for members, (relation_id, _, _) in TRIPLE_HARMONY.items()
    ],
)
def test_ra1_triple_harmony_requires_every_member(
    members: tuple[str, str, str],
    relation_id: str,
) -> None:
    graph = _graph(
        case_id=f"ra1.triple.missing.{relation_id}",
        branches=(members[0], members[1], members[0], members[1]),
    )

    assert not [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_TRIPLE_COMBINATION
        and edge.relation_label == relation_id
    ]
