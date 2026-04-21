from __future__ import annotations

from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph
from v17_rebirth.backend.logic.core_engine.work_path_engine import build_work_paths


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
                "plugin_id": "l1.physics.op_stem_fusion",
                "source_label": "天干五合",
                "label": "乙庚合",
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
    fusion_path = next(path for path in result["paths"] if path["path_type"] == "stem_fusion")
    assert fusion_path["evidence"]["decision_id"] == "row_guan"
    assert fusion_path["evidence"]["source_label"] == "天干五合"
    assert fusion_path["evidence"]["decision_label"] == "乙庚合"
    assert result["confidence"] > 0.58


def test_resolve_effect_scores_preserves_contest_tension_between_officer_and_weapon() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="辛丑",
        flow_pillar="己未",
        deity_scores={"伤官": 84.0, "正官": 74.0, "食神": 32.0},
        decision_rows=[
            {
                "id": "row_officer_hurt",
                "target_god": "正官",
                "source": "l2.risk.risk_matrix",
                "plugin_id": "l2.risk.risk_matrix",
                "source_label": "伤官见官",
                "label": "伤官见官：高争衡",
                "physical_impact": {
                    "target_god": "正官",
                    "impact_ratio": 0.0,
                    "match_ratio": 0.86,
                    "work_evidence": {
                        "relation_family": "risk_officer_hurt_contest",
                        "target_god": "正官",
                        "members": ["伤官", "正官"],
                        "targets": ["正官"],
                        "counterpart_gods": ["伤官"],
                        "effect_type": "disrupt",
                        "layer": "cross_layer",
                        "origin_scope": "natal",
                        "condition_state": "contested",
                        "impact_ratio": 0.0,
                        "match_ratio": 0.86,
                        "path_strength": 0.42,
                    },
                },
            },
            {
                "id": "row_shang_gang",
                "target_god": "伤官",
                "source": "l1.physics.op_branch_muku",
                "plugin_id": "l1.physics.op_branch_muku",
                "source_label": "三合生伤官",
                "label": "三合透支",
                "physical_impact": {
                    "target_god": "伤官",
                    "impact_ratio": 0.36,
                    "match_ratio": 0.77,
                    "work_evidence": {
                        "relation_family": "sanhe",
                        "target_god": "伤官",
                        "members": ["乙", "丙", "丁"],
                        "targets": ["伤官"],
                        "counterpart_gods": ["正官"],
                        "effect_type": "benefit",
                        "layer": "branch",
                        "origin_scope": "luck",
                        "condition_state": "manifested",
                        "impact_ratio": 0.36,
                        "match_ratio": 0.77,
                        "path_strength": 0.48,
                    },
                },
            },
        ],
    )

    effect_scores = result["effect_scores"]
    assert "伤官" in effect_scores
    assert "正官" in effect_scores
    assert effect_scores["伤官"]["contest_pressure"] > 0.0
    assert effect_scores["正官"]["contest_pressure"] > 0.0
    assert effect_scores["伤官"]["resolved_utility"] >= effect_scores["伤官"]["net_utility"]
    assert effect_scores["正官"]["resolved_utility"] <= 0.0


def test_resolve_god_ring_core_detects_present_tongguan_path() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "甲寅", "month": "丁巳", "day": "戊辰", "hour": "乙卯"},
        luck_pillar="",
        flow_pillar="",
        deity_scores={"七杀": 42.0, "正官": 34.0, "正印": 20.0, "偏印": 16.0, "比肩": 28.0, "劫财": 14.0},
        decision_rows=[],
    )
    tongguan_paths = [path for path in result["paths"] if path["path_type"] == "tongguan_present"]
    assert tongguan_paths
    assert tongguan_paths[0]["evidence"]["controller_element"] == "木"
    assert tongguan_paths[0]["evidence"]["mediator_element"] == "火"
    assert tongguan_paths[0]["evidence"]["controlled_element"] == "土"
    assert any(candidate["god"] in {"正印", "偏印"} for candidate in result["use_candidates"])


def test_resolve_god_ring_core_projects_external_tongguan_candidate() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "甲寅", "month": "乙卯", "day": "戊辰", "hour": "甲寅"},
        luck_pillar="",
        flow_pillar="",
        deity_scores={"七杀": 44.0, "正官": 36.0, "比肩": 24.0, "劫财": 8.0, "正印": 0.0, "偏印": 0.0},
        decision_rows=[],
    )
    tongguan_paths = [path for path in result["paths"] if path["path_type"] == "tongguan_external"]
    assert tongguan_paths
    assert tongguan_paths[0]["target_god"] in {"正印", "偏印"}
    assert tongguan_paths[0]["evidence"]["external_candidate"] is True
    assert result["effect_scores"]["正印"]["net_utility"] > 0 or result["effect_scores"]["偏印"]["net_utility"] > 0


def test_build_work_paths_prefers_directed_near_actor_receiver_path() -> None:
    graph = build_six_pillar_graph(
        four_pillars={"year": "壬辰", "month": "丙午", "day": "甲子", "hour": "庚申"},
        luck_pillar="",
        flow_pillar="",
    )
    rows = [
        {
            "id": "close_row",
            "target_god": "七杀",
            "source": "l2.risk.risk_matrix",
            "physical_impact": {
                "target_god": "七杀",
                "impact_ratio": 0.0,
                "work_evidence": {
                    "relation_family": "risk_officer_crush",
                    "target_god": "七杀",
                    "members": ["丙", "庚"],
                    "actor_members": ["丙"],
                    "receiver_members": ["庚"],
                    "effect_type": "harm",
                    "layer": "stem",
                    "origin_scope": "natal",
                    "condition_state": "manifested",
                    "impact_ratio": 0.0,
                    "match_ratio": 0.82,
                    "path_strength": 0.36,
                },
            },
        },
        {
            "id": "far_row",
            "target_god": "七杀",
            "source": "l2.risk.risk_matrix",
            "physical_impact": {
                "target_god": "七杀",
                "impact_ratio": 0.0,
                "work_evidence": {
                    "relation_family": "risk_officer_crush",
                    "target_god": "七杀",
                    "members": ["壬", "庚"],
                    "actor_members": ["壬"],
                    "receiver_members": ["庚"],
                    "effect_type": "harm",
                    "layer": "stem",
                    "origin_scope": "natal",
                    "condition_state": "manifested",
                    "impact_ratio": 0.0,
                    "match_ratio": 0.82,
                    "path_strength": 0.36,
                },
            },
        },
    ]
    paths = build_work_paths(
        graph=graph,
        deity_scores={"七杀": 28.0, "偏印": 14.0, "食神": 16.0},
        decision_rows=rows,
    )
    close_path = next(path for path in paths if path.path_id == "close_row")
    far_path = next(path for path in paths if path.path_id == "far_row")
    assert close_path.transmission > far_path.transmission
    assert close_path.evidence["directional_factor"] > far_path.evidence["directional_factor"]


def test_resolve_god_ring_core_exposes_flux_chains_and_reverse_attribution() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "壬辰", "month": "丙午", "day": "甲子", "hour": "庚申"},
        luck_pillar="辛酉",
        flow_pillar="壬子",
        deity_scores={"伤官": 42.0, "正官": 35.0, "正印": 24.0, "偏财": 18.0},
        decision_rows=[
            {
                "id": "row_officer_contest",
                "target_god": "正官",
                "source": "l2.risk.risk_matrix",
                "physical_impact": {
                    "target_god": "正官",
                    "impact_ratio": -0.22,
                    "match_ratio": 0.83,
                    "work_evidence": {
                        "relation_family": "risk_officer_hurt_contest",
                        "target_god": "正官",
                        "members": ["伤官", "正官"],
                        "counterpart_gods": ["伤官"],
                        "effect_type": "disrupt",
                        "layer": "cross_layer",
                        "origin_scope": "natal",
                        "condition_state": "contested",
                        "impact_ratio": -0.22,
                        "match_ratio": 0.83,
                        "path_strength": 0.46,
                    },
                },
            },
            {
                "id": "row_seal_bridge",
                "target_god": "正印",
                "source": "core_engine.tongguan",
                "physical_impact": {
                    "target_god": "正印",
                    "impact_ratio": 0.18,
                    "match_ratio": 0.79,
                    "work_evidence": {
                        "relation_family": "tongguan_bridge",
                        "target_god": "正印",
                        "members": ["正官", "正印"],
                        "counterpart_gods": ["正官"],
                        "effect_type": "support",
                        "layer": "cross_layer",
                        "origin_scope": "luck",
                        "condition_state": "manifested",
                        "impact_ratio": 0.18,
                        "match_ratio": 0.79,
                        "path_strength": 0.38,
                    },
                },
            },
        ],
    )
    flux = result["flux_meta"]
    assert flux["enabled"] is True
    assert flux["edge_count"] > 0
    assert flux["chain_count"] > 0
    assert flux["top_chains"]
    assert flux["node_edge_count"] > 0
    assert flux["node_chain_count"] > 0
    assert flux["node_top_chains"]
    assert flux["interaction_count"] > 0
    assert flux["interaction_matrix"]
    assert any("_stem" in str(chain.get("source") or "") or "_branch" in str(chain.get("source") or "") for chain in flux["node_top_chains"])
    assert result["graph_meta"]["flux_chain_count"] == flux["chain_count"]
    assert result["graph_meta"]["flux_edge_count"] == flux["edge_count"]
    assert result["graph_meta"]["flux_node_chain_count"] == flux["node_chain_count"]
    assert result["graph_meta"]["flux_node_edge_count"] == flux["node_edge_count"]
    assert result["graph_meta"]["flux_interaction_count"] == flux["interaction_count"]

    effect_scores = result["effect_scores"]
    assert "正官" in effect_scores
    assert "flux_net" in effect_scores["正官"]
    assert "resolved_utility_flux" in effect_scores["正官"]
    assert isinstance(effect_scores["正官"]["flux_top_causes"], list)
