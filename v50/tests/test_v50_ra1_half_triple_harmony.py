from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import HALF_TRIPLE_HARMONY, TRIPLE_HARMONY
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


@pytest.mark.parametrize(
    ("members", "relation_id", "element", "bridge"),
    [
        (tuple(sorted(members)), relation_id, element, bridge)
        for members, (relation_id, element, bridge) in HALF_TRIPLE_HARMONY.items()
    ],
)
def test_ra1_recognizes_only_defined_half_triple_pairs(
    members: tuple[str, str],
    relation_id: str,
    element: str,
    bridge: str,
) -> None:
    graph = _graph(
        case_id=f"ra1.half.{relation_id}",
        branches=(members[0], members[1], members[0], members[1]),
    )
    edges = [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_HALF_COMBINATION
        and edge.relation_label == relation_id
    ]

    assert len(edges) == 4
    assert all(edge.attributes["element"] == element for edge in edges)
    assert all(edge.attributes["bridge_branch"] == bridge for edge in edges)
    assert all(edge.attributes["completion_state"] == "incomplete" for edge in edges)
    assert all(edge.path_eligibility == PathEligibility.NOT_YET_QUALIFIED for edge in edges)
    assert all(edge.eligibility_reason_refs for edge in edges)


@pytest.mark.parametrize(
    "members",
    [
        tuple(sorted(set(triple) - {bridge}))
        for triple, (_, _, bridge) in TRIPLE_HARMONY.items()
    ],
)
def test_ra1_arch_pairs_do_not_masquerade_as_half_triple_harmony(
    members: tuple[str, str],
) -> None:
    graph = _graph(
        case_id=f"ra1.arch.{''.join(members)}",
        branches=(members[0], members[1], members[0], members[1]),
    )

    assert not [
        edge
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_HALF_COMBINATION
    ]


def test_ra1_half_triple_candidates_do_not_enter_legacy_path_exploration() -> None:
    graph = _graph(
        case_id="ra1.half.path-boundary",
        branches=("巳", "酉", "巳", "酉"),
    )
    half_edge_ids = {
        edge.edge_id
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.FORMS_HALF_COMBINATION
    }
    paths = explore_mingli_paths(graph)

    assert half_edge_ids
    assert not any(half_edge_ids & set(path.edge_ids) for path in paths.paths)
