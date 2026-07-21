from __future__ import annotations

import pytest

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.engines.bazi.knowledge import SIX_CLASH, SIX_HARMONY
from core.engines.bazi.pillar_cycle import BRANCHES, JIAZI
from core.graph import build_mingli_graph_from_material_store
from core.graph.contracts import MingliGraphEdgeType
from core.graph.provenance import RelationDirectionality


PILLAR_BY_BRANCH = {
    branch: next(pillar for pillar in JIAZI if pillar[1] == branch)
    for branch in BRANCHES
}


def _birth(*, reading_id: str, branches: tuple[str, str, str, str]) -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id=f"birth.{reading_id}",
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


def _neutral_fillers(pair: frozenset[str]) -> tuple[str, str]:
    for first in BRANCHES:
        for second in BRANCHES:
            branches = [*pair, first, second]
            if len(set(branches)) != 4:
                continue
            observed_pairs = {
                frozenset((left, right))
                for index, left in enumerate(branches)
                for right in branches[index + 1 :]
            }
            if not any(
                item in SIX_CLASH or item in SIX_HARMONY
                for item in observed_pairs
                if item != pair
            ):
                return first, second
    raise AssertionError(f"no neutral fillers for {sorted(pair)}")


def _relation_edges(*, pair: frozenset[str], reading_id: str):
    left, right = sorted(pair)
    filler_a, filler_b = _neutral_fillers(pair)
    birth = _birth(
        reading_id=reading_id,
        branches=(left, right, filler_a, filler_b),
    )
    store = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    graph = build_mingli_graph_from_material_store(store)
    return store, [
        edge
        for edge in graph.edges
        if edge.edge_type in {MingliGraphEdgeType.CLASHES, MingliGraphEdgeType.HARMONIZES}
    ]


@pytest.mark.parametrize("pair", sorted(SIX_CLASH, key=lambda item: sorted(item)))
def test_ra1_projects_all_six_clashes_from_material_authority(pair: frozenset[str]) -> None:
    store, edges = _relation_edges(pair=pair, reading_id=f"ra1.clash.{''.join(sorted(pair))}")

    assert len(edges) == 1
    edge = edges[0]
    assert edge.edge_type == MingliGraphEdgeType.CLASHES
    assert edge.directionality == RelationDirectionality.SYMMETRIC
    assert edge.relation_label == "six_clash"
    assert edge.material_refs == [f"material:{store.reading_id}:bazi:branch_relations"]
    assert set(edge.attributes["branches"]) == pair
    assert edge.attributes["path_eligibility"] == "not_yet_qualified"
    assert edge.boundary == "graph_edge_is_computational_relation_not_judgment"


@pytest.mark.parametrize("pair", sorted(SIX_HARMONY, key=lambda item: sorted(item)))
def test_ra1_projects_all_six_harmonies_from_material_authority(pair: frozenset[str]) -> None:
    store, edges = _relation_edges(pair=pair, reading_id=f"ra1.harmony.{''.join(sorted(pair))}")

    assert len(edges) == 1
    edge = edges[0]
    assert edge.edge_type == MingliGraphEdgeType.HARMONIZES
    assert edge.directionality == RelationDirectionality.SYMMETRIC
    assert edge.relation_label == "six_harmony"
    assert edge.material_refs == [f"material:{store.reading_id}:bazi:branch_relations"]
    assert set(edge.attributes["branches"]) == pair


def test_ra1_branch_relation_projection_preserves_stable_symmetric_identity() -> None:
    pair = frozenset(("子", "午"))
    _, first_edges = _relation_edges(pair=pair, reading_id="ra1.identity")
    _, second_edges = _relation_edges(pair=pair, reading_id="ra1.identity")

    assert first_edges[0].relation_key == second_edges[0].relation_key
    assert first_edges[0].evidence_refs == second_edges[0].evidence_refs


def test_ra1_does_not_create_branch_relation_without_material_evidence() -> None:
    birth = _birth(reading_id="ra1.negative", branches=("子", "子", "子", "子"))
    store = build_bazi_material_store(
        reading_id="ra1.negative",
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    graph = build_mingli_graph_from_material_store(store)

    assert not [
        edge
        for edge in graph.edges
        if edge.edge_type in {MingliGraphEdgeType.CLASHES, MingliGraphEdgeType.HARMONIZES}
    ]
