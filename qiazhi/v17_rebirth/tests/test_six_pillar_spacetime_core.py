from __future__ import annotations

from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph


def test_build_six_pillar_graph_has_nodes_and_edges() -> None:
    graph = build_six_pillar_graph(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
    )
    assert len(graph.nodes) == 12
    assert len(graph.edges) > 12
    assert graph.position_weights["month"] == 1.0
    assert graph.distance_weights[1] == 0.78


def test_resolve_god_ring_core_prefers_positive_work_path() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        deity_scores={"伤官": 74.0, "食神": 53.0, "正官": 15.0, "七杀": 9.0},
        decision_rows=[
            {
                "id": "row_guan",
                "target_god": "正官",
                "source": "l1.physics.op_stem_fusion",
                "physical_impact": {
                    "target_god": "正官",
                    "impact_ratio": 0.32,
                    "match_ratio": 0.84,
                    "work_evidence": {
                        "relation_family": "stem_fusion",
                        "target_god": "正官",
                        "targets": ["正官"],
                        "members": ["庚", "乙"],
                        "effect_type": "transform",
                        "layer": "stem",
                        "origin_scope": "luck",
                        "condition_state": "formed",
                        "impact_ratio": 0.32,
                        "match_ratio": 0.84,
                        "path_strength": 0.41,
                    },
                },
            },
            {
                "id": "row_shang",
                "target_god": "伤官",
                "source": "l1.physics.op_branch_liuchong",
                "physical_impact": {
                    "target_god": "伤官",
                    "impact_ratio": -0.28,
                    "match_ratio": 0.77,
                    "work_evidence": {
                        "relation_family": "liu_chong",
                        "target_god": "伤官",
                        "targets": ["伤官"],
                        "members": ["巳", "午"],
                        "effect_type": "harm",
                        "layer": "branch",
                        "origin_scope": "flow",
                        "condition_state": "supported",
                        "impact_ratio": -0.28,
                        "match_ratio": 0.77,
                        "path_strength": 0.33,
                    },
                },
            },
        ],
    )
    assert result["use_candidates"]
    assert result["use_candidates"][0]["god"] == "正官"
    assert result["taboo_candidates"]
    assert result["taboo_candidates"][0]["god"] == "伤官"
    assert result["path_count"] >= 6
    assert any(path["path_type"] == "stem_fusion" for path in result["paths"])
    assert result["confidence"] > 0.58
