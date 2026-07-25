from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import (
    PAIR_PUNISHMENT,
    SELF_PUNISHMENT,
    SIX_BREAK,
    SIX_HARM,
    TRIPLE_PUNISHMENT,
)
from core.engines.bazi.pillar_cycle import BRANCHES, JIAZI
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraphEdgeType, PathEligibility


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


@pytest.mark.parametrize("pair", sorted(SIX_HARM, key=lambda item: sorted(item)))
def test_ra1_projects_all_six_harms_as_non_path_relations(pair: frozenset[str]) -> None:
    left, right = sorted(pair)
    graph = _graph(case_id=f"ra1.harm.{left}{right}", branches=(left, right, left, right))
    edges = [edge for edge in graph.edges if edge.edge_type == MingliGraphEdgeType.HARMS]

    assert len(edges) == 4
    assert all(edge.relation_label == "six_harm" for edge in edges)
    assert all(edge.path_eligibility == PathEligibility.NOT_YET_QUALIFIED for edge in edges)
    assert all(edge.eligibility_reason_refs for edge in edges)
    assert all(edge.material_refs for edge in edges)


@pytest.mark.parametrize("pair", sorted(SIX_BREAK, key=lambda item: sorted(item)))
def test_ra1_projects_all_six_breaks_as_non_path_relations(pair: frozenset[str]) -> None:
    left, right = sorted(pair)
    graph = _graph(case_id=f"ra1.break.{left}{right}", branches=(left, right, left, right))
    edges = [edge for edge in graph.edges if edge.edge_type == MingliGraphEdgeType.BREAKS]

    assert len(edges) == 4
    assert all(edge.relation_label == "six_break" for edge in edges)
    assert all(edge.path_eligibility == PathEligibility.NOT_YET_QUALIFIED for edge in edges)
    assert all(edge.eligibility_reason_refs for edge in edges)


def test_ra1_preserves_multiple_relation_types_on_the_same_branch_pair() -> None:
    graph = _graph(case_id="ra1.multi.si-shen", branches=("巳", "申", "巳", "申"))
    relation_types = {
        edge.edge_type
        for edge in graph.edges
        if set(edge.attributes.get("branches", [])) == {"巳", "申"}
    }

    assert MingliGraphEdgeType.HARMONIZES in relation_types
    assert MingliGraphEdgeType.BREAKS in relation_types


def test_ra1_projects_zi_mao_pair_punishment_under_conservative_profile() -> None:
    pair, relation_id = next(iter(PAIR_PUNISHMENT.items()))
    left, right = sorted(pair)
    graph = _graph(case_id="ra1.punishment.zi-mao", branches=(left, right, left, right))
    edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.PUNISHES
        and edge.relation_label == relation_id
    ]

    assert len(edges) == 4
    assert all(edge.attributes["school_profile"] == "conservative_complete_set_v1" for edge in edges)


@pytest.mark.parametrize(("branch", "relation_id"), sorted(SELF_PUNISHMENT.items()))
def test_ra1_self_punishment_requires_two_distinct_nodes_with_same_branch(
    branch: str,
    relation_id: str,
) -> None:
    graph = _graph(case_id=f"ra1.self.{branch}", branches=(branch, branch, "子", "子"))
    edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.PUNISHES
        and edge.relation_label == relation_id
    ]

    assert len(edges) == 1
    assert len(edges[0].participant_node_ids) == 2
    assert edges[0].attributes["punishment_kind"] == "self_punishment"


@pytest.mark.parametrize(
    ("members", "relation_id", "required_order"),
    [
        (tuple(sorted(members)), relation_id, required_order)
        for members, (relation_id, required_order) in TRIPLE_PUNISHMENT.items()
    ],
)
def test_ra1_triple_punishment_requires_the_complete_three_member_set(
    members: tuple[str, str, str],
    relation_id: str,
    required_order: tuple[str, str, str],
) -> None:
    graph = _graph(
        case_id=f"ra1.triple-punishment.{relation_id}",
        branches=(*required_order, required_order[0]),
    )
    edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.PUNISHES
        and edge.relation_label == relation_id
    ]

    assert len(edges) == 2
    assert all(len(edge.participant_node_ids) == 3 for edge in edges)
    assert all(
        {node_id.split(":")[-1] for node_id in edge.participant_node_ids} == set(members)
        for edge in edges
    )
    assert all(edge.attributes["punishment_kind"] == "triple_complete" for edge in edges)


@pytest.mark.parametrize(
    ("required_order", "relation_id"),
    [
        (required_order, relation_id)
        for _, (relation_id, required_order) in TRIPLE_PUNISHMENT.items()
    ],
)
def test_ra1_partial_triple_punishment_is_not_silently_promoted(
    required_order: tuple[str, str, str],
    relation_id: str,
) -> None:
    graph = _graph(
        case_id=f"ra1.partial-punishment.{relation_id}",
        branches=(required_order[0], required_order[1], required_order[0], required_order[1]),
    )

    assert not [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.PUNISHES
        and edge.relation_label == relation_id
    ]


def test_ra1_conflict_relations_do_not_enter_legacy_path_exploration() -> None:
    graph = _graph(case_id="ra1.conflict.path-boundary", branches=("巳", "申", "寅", "亥"))
    conflict_edge_ids = {
        edge.edge_id
        for edge in graph.edges
        if edge.edge_type in {
            MingliGraphEdgeType.HARMS,
            MingliGraphEdgeType.BREAKS,
            MingliGraphEdgeType.PUNISHES,
        }
    }
    paths = explore_mingli_paths(graph)

    assert conflict_edge_ids
    assert not any(conflict_edge_ids & set(path.edge_ids) for path in paths.paths)
