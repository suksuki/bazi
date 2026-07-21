from __future__ import annotations

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraphEdgeType


def _birth(*, case_id: str, pillars: tuple[str, str, str, str]) -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id=f"birth.{case_id}",
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


def _graph(*, case_id: str, pillars: tuple[str, str, str, str]):
    birth = _birth(case_id=case_id, pillars=pillars)
    store = build_bazi_material_store(
        reading_id=case_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    return build_mingli_graph_from_material_store(store)


def test_ra1_projects_each_existing_day_master_root_with_material_provenance() -> None:
    graph = _graph(
        case_id="ra1.root.fire",
        pillars=("壬辰", "戊申", "丙午", "丁丑"),
    )
    roots = [edge for edge in graph.edges if edge.edge_type == MingliGraphEdgeType.ROOTS]

    assert len(roots) == 1
    edge = roots[0]
    assert edge.from_node_id.endswith(":day:branch:午")
    assert edge.to_node_id.endswith(":day:stem:丙")
    assert edge.relation_label == "day_master_root"
    assert edge.material_refs == ["material:ra1.root.fire:bazi:root_strength"]
    assert edge.attributes["hidden_stems"] == "丁"
    assert edge.attributes["path_eligibility"] == "not_yet_qualified"


def test_ra1_root_projection_does_not_invent_an_unrooted_day_master_relation() -> None:
    graph = _graph(
        case_id="ra1.root.none",
        pillars=("甲子", "丙寅", "庚午", "壬子"),
    )

    assert not [edge for edge in graph.edges if edge.edge_type == MingliGraphEdgeType.ROOTS]


def test_ra1_new_root_evidence_does_not_enter_legacy_path_exploration() -> None:
    graph = _graph(
        case_id="ra1.root.path-boundary",
        pillars=("壬辰", "戊申", "丙午", "丁丑"),
    )
    root_edge_ids = {
        edge.edge_id
        for edge in graph.edges
        if edge.edge_type == MingliGraphEdgeType.ROOTS
    }
    paths = explore_mingli_paths(graph)

    assert root_edge_ids
    assert not any(root_edge_ids & set(path.edge_ids) for path in paths.paths)
