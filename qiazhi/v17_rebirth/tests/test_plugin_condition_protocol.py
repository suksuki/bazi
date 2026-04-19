from __future__ import annotations

from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts
from v17_rebirth.backend.services.claim_protocol import compile_claims
from v17_rebirth.backend.services.conflict_detector import detect_claim_conflicts
from v17_rebirth.backend.services.decision_compiler import compile_modifier_proposals
from v17_rebirth.backend.services.physics_layers import settle_modifier_proposals
from v17_rebirth.backend.logic.L1_atomic_ops import plugin_condition_protocol as protocol


def test_hydration_populates_liu_po_and_stem_fusion_meta() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "己酉",
            "day": "甲辰",
            "hour": "庚酉",
        },
        "luck_pillar": "丙午",
        "flow_pillar": "丁未",
        "ten_gods_absolute_intensity": {"比肩": 22.0, "正财": 19.0, "正官": 11.0},
        "total_energy_index": 80.0,
    }

    hydrate_v17_physics_tensor(pt)
    meta = pt.get("meta") or {}
    iv2 = meta.get("interaction_v2") or {}

    assert "liu_po" in iv2
    assert isinstance(iv2["liu_po"], list)
    assert "stem_fusion_v1" in meta


def test_hydration_extends_interaction_scope_with_luck_and_flow() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        },
        "luck_pillar": "戊午",
        "flow_pillar": "己未",
        "ten_gods_absolute_intensity": {"比肩": 20.0, "食神": 18.0, "正官": 12.0},
        "total_energy_index": 70.0,
    }

    hydrate_v17_physics_tensor(pt)
    meta = pt.get("meta") or {}
    iv2 = meta.get("interaction_v2") or {}

    assert iv2.get("version") == "interaction_v2.v2"
    assert "luck" in (iv2.get("pillar_scope") or [])
    assert "flow" in (iv2.get("pillar_scope") or [])
    hit = next((row for row in iv2.get("liu_chong") or [] if sorted(row.get("pillars") or []) == ["luck", "year"]), None)
    assert hit is not None
    assert hit.get("origin_type") == "luck_background"


def test_condition_plugins_emit_condition_metadata() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "己酉",
            "day": "甲辰",
            "hour": "庚酉",
        },
        "luck_pillar": "丙午",
        "flow_pillar": "丁未",
        "ten_gods_base_l0": {"比肩": 30.0, "正财": 28.0, "正官": 18.0, "七杀": 12.0},
        "ten_gods_runtime": {"比肩": 30.0, "正财": 28.0, "正官": 18.0, "七杀": 12.0},
        "energy_meta": {"month_command_god": "正财", "season_power": {"month_branch": "酉"}},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "luck"]}],
                "liu_hai": [],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "month"]}],
                "liu_he": [{"pair": ["辰", "酉"], "pillars": ["day", "month"]}],
                "san_he": [],
                "ban_he": [],
                "sanxing": [],
            },
            "stem_fusion_v1": {
                "cases": [
                    {
                        "stems": ["甲", "己"],
                        "mode": "transformed",
                        "hua_element": "earth",
                        "month_stem_supports": True,
                        "branch_hua_ratio": 0.25,
                    }
                ]
            },
            "plugin_conflicts": [{"conflict_id": "c1"}],
            "plugin_conflict_resolutions": [{"resolution_id": "r1"}],
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}

    assert by_plugin["l1.physics.op_branch_liuhe"].meta.get("condition_state") in {"supported", "contested"}
    assert by_plugin["l1.physics.op_branch_liuhe"].meta.get("origin_type") == "natal"
    assert isinstance(by_plugin["l1.physics.op_branch_liuhe"].meta.get("static_basis"), dict)
    claims = compile_claims(facts=facts, physics_tensor=pt)
    liuhe_claim = next(row for row in claims if row.get("plugin_id") == "l1.physics.op_branch_liuhe")
    assert liuhe_claim.get("origin_type") == "natal"
    assert 0.0 <= float(by_plugin["l1.physics.op_branch_liuhe"].meta.get("match_ratio", 0.0) or 0.0) <= 1.0
    assert by_plugin["l1.physics.op_stem_fusion"].meta.get("condition_trigger") == "month_support"
    assert isinstance(by_plugin["l1.physics.op_stem_fusion"].meta.get("static_basis"), dict)
    assert 0.0 <= float(by_plugin["l1.physics.op_stem_fusion"].meta.get("match_ratio", 0.0) or 0.0) <= 1.0
    assert by_plugin["classical.conflict_auditor.v1"].meta.get("conflict_count") == 1


def test_contested_relation_fact_does_not_produce_modifier_proposal() -> None:
    facts = [
        V17Fact(
            plugin_id="l1.physics.op_branch_liuhe",
            text="六合成立但受冲争夺。",
            causal_tier=4,
            priority=0.8,
            meta={
                "target_god": "正官",
                "condition_state": "contested",
                "condition_blockers": ["liu_chong"],
            },
        )
    ]
    proposals = compile_modifier_proposals(facts=facts, physics_tensor={})
    assert proposals == []


def test_pattern_candidates_enter_conflict_layer_as_exclusive_family() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.pattern.axis.v1",
            text="格局轴线候选：比肩当前为最强主轴。",
            causal_tier=3,
            priority=0.77,
            meta={
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": 0.77,
            },
        ),
        V17Fact(
            plugin_id="classical.pattern.finance_officer.v1",
            text="格局候选：财官双线并举。",
            causal_tier=3,
            priority=0.73,
            meta={
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": 0.73,
            },
        ),
    ]
    claims = compile_claims(facts=facts, physics_tensor={})
    conflicts = detect_claim_conflicts(claims)
    assert any(str(row.get("conflict_type") or "") == "pattern_family_exclusive" for row in conflicts)


def test_match_ratio_scales_modifier_proposal() -> None:
    facts = [
        V17Fact(
            plugin_id="l2.risk.risk_matrix",
            text="检测到伤官见官。",
            causal_tier=2,
            priority=0.9,
            meta={
                "target_god": "正官",
                "impact_ratio": -0.4,
                "match_ratio": 0.6,
            },
        )
    ]
    proposals = compile_modifier_proposals(facts=facts, physics_tensor={})
    assert len(proposals) == 1
    assert proposals[0]["raw_impact_ratio"] == -0.4
    assert proposals[0]["match_ratio"] == 0.6
    assert proposals[0]["impact_ratio"] == -0.24


def test_settlement_recomputes_from_base_scores() -> None:
    runtime_scores = {"正官": 40.0}
    base_scores = {"正官": 10.0}
    proposals = [
        {
            "plugin_id": "l2.risk.risk_matrix",
            "target_god": "正官",
            "impact_ratio": -0.2,
            "match_ratio": 1.0,
            "significance_weight": 1.0,
            "arbiter_type": "system",
        }
    ]
    settled, ratio_totals, applied = settle_modifier_proposals(
        runtime_scores,
        proposals,
        base_scores=base_scores,
    )
    assert ratio_totals["正官"] == -0.2
    assert settled["正官"] == 8.0
    assert applied[0]["before"] == 10.0
    assert applied[0]["delta_abs"] == -2.0


def test_diagnostic_claim_without_explicit_match_ratio_is_not_forced_to_full_score() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.climate_adjuster.v1",
            text="调候提示：当前月令主气落在 伤官。",
            causal_tier=3,
            priority=0.82,
            salience_weight=0.82,
            meta={},
        )
    ]
    claims = compile_claims(facts=facts, physics_tensor={})
    assert len(claims) == 1
    assert 0.35 <= float(claims[0]["match_ratio"]) < 1.0


def test_risk_blind_and_pattern_plugins_emit_origin_type() -> None:
    pt = {
        "four_pillars": {
            "year": "癸酉",
            "month": "甲子",
            "day": "丙寅",
            "hour": "庚子",
        },
        "luck_pillar": "丁卯",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {"伤官": 18.0, "食神": 12.0, "正官": 16.0, "偏印": 17.0, "比肩": 14.0},
        "ten_gods_runtime": {"伤官": 18.0, "食神": 12.0, "正官": 16.0, "偏印": 17.0, "比肩": 14.0},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["month", "flow"], "origin_type": "flow_trigger"}],
                "liu_hai": [{"pair": ["子", "未"], "pillars": ["hour", "luck"], "origin_type": "luck_background"}],
                "liu_po": [],
                "liu_he": [],
                "san_he": [],
                "ban_he": [{"pair": ["寅", "卯"], "pillars": ["day", "luck"], "origin_type": "luck_background"}],
                "sanxing": [],
            }
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}

    assert by_plugin["l2.risk.risk_matrix"].meta.get("origin_type") in {"natal", "flow_trigger", "luck_background", "unknown"}
    assert by_plugin["classical.blind.work_axis.v1"].meta.get("origin_type") == "flow_trigger"
    assert by_plugin["classical.pattern.break_guard.v1"].meta.get("origin_type") in {"flow_trigger", "luck_background"}


def test_pattern_dynamic_scope_reports_mixed_scope_on_luck_flow_rows() -> None:
    pt = {
        "four_pillars": {
            "year": "丁巳",
            "month": "乙丑",
            "day": "乙酉",
            "hour": "乙亥",
        },
        "ten_gods_runtime": {
            "伤官": 82.0,
            "食神": 46.0,
            "比肩": 17.0,
            "偏财": 11.0,
            "正官": 8.0,
            "正印": 6.0,
        },
        "meta": {
            "interaction_v2": {
                "liu_chong": [
                    {"pair": ["子", "午"], "pillars": ["luck", "flow"], "origin_type": "runtime_pair"},
                ],
                "sanxing": [
                    {"branches": ["巳", "酉", "丑"], "pillars": ["year", "luck"], "origin_type": "luck_background"},
                ],
            }
        },
    }
    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}
    fact = by_plugin["classical.pattern.dynamic_scope.v1"]
    assert fact.meta.get("pattern_scope") in {"mixed", "luck_background", "runtime_pair"}
    assert fact.meta.get("candidate_count", 0) >= 1
    assert isinstance(fact.meta.get("scope_weights"), dict)


def test_detect_interaction_layer_rules() -> None:
    assert protocol.detect_interaction_layer(row={"interaction_layer": "branch"}, relation_family="liu_hai") == "branch"
    assert protocol.detect_interaction_layer(row=None, relation_family="stem_fusion") == "stem"
    assert protocol.detect_interaction_layer(row=None, relation_family="liu_chong") == "branch"
    assert protocol.detect_interaction_layer(row=None, relation_family="officer_hurt", member_key="pair") == "cross_layer"
    assert protocol.detect_interaction_layer(row=None, relation_family="unknown", member_key="pair") == "branch"
    assert protocol.detect_interaction_layer(row=None, relation_family="unknown") == "unknown"


def test_infer_manifestation_state_for_cross_layer_and_branch_rows() -> None:
    rows = [
        {"pair": ["子", "午"], "origin_type": "flow_trigger", "strength": 0.97, "pillars": ["flow", "luck"]},
        {"pair": ["子", "午"], "origin_type": "flow_trigger", "pillars": ["year", "day"], "pivot_factor": 1.05},
    ]
    assert protocol.infer_manifestation_state(rows, relation_family="liu_chong", member_set=["子", "午"]) == "manifested"

    branch_rows = [{"pair": ["巳", "申"], "strength": 0.78}]
    assert protocol.infer_manifestation_state(branch_rows, relation_family="liu_chong", member_set=["子", "午"]) == "supported"

    stem_rows = [{"mode": "activated", "mode_confidence": 0.84}]
    assert protocol.infer_manifestation_state(stem_rows, relation_family="stem_fusion", member_set=None) == "supported"


def test_pattern_and_ziping_plugins_emit_cluster_projection_meta() -> None:
    pt = {
        "four_pillars": {
            "year": "丁巳",
            "month": "乙巳",
            "day": "乙丑",
            "hour": "乙酉",
        },
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {"伤官": 64.65, "食神": 47.08, "比肩": 27.5, "正官": 14.07, "偏财": 13.48, "七杀": 8.5, "正印": 7.98, "偏印": 5.46, "正财": 4.32},
        "ten_gods_runtime": {"伤官": 64.03, "食神": 46.63, "比肩": 27.75, "正官": 14.06, "偏财": 13.75, "七杀": 8.49, "正印": 8.26, "偏印": 5.65, "正财": 4.41},
        "energy_meta": {
            "month_command_god": "伤官",
            "season_power": {"month_branch": "巳"},
        },
        "meta": {
            "interaction_v2": {
                "liu_chong": [],
                "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["hour", "luck"], "origin_type": "luck_background"}],
                "liu_he": [{"pair": ["子", "丑"], "pillars": ["day", "luck"], "origin_type": "luck_background"}],
                "san_he": [{"group": ["丑", "巳", "酉"], "pillars": ["day", "hour", "month", "year"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            }
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}
    pattern_axis = by_plugin["classical.pattern.axis.v1"]
    ziping_month = by_plugin["classical.ziping.month_command.v1"]

    assert "cluster_projection" in pattern_axis.meta
    assert "projection_share" in pattern_axis.meta
    assert pattern_axis.meta.get("target_god")
    assert isinstance(pattern_axis.meta.get("cluster_projection"), dict)
    assert isinstance(pattern_axis.meta.get("static_basis"), dict)

    assert "cluster_projection" in ziping_month.meta
    assert "projection_share" in ziping_month.meta
    assert ziping_month.meta.get("target_god") == ziping_month.meta.get("month_command_god")
    assert isinstance(ziping_month.meta.get("static_basis"), dict)


def test_blind_risk_shensha_and_ten_god_pattern_emit_cluster_projection_meta() -> None:
    pt = {
        "four_pillars": {
            "year": "癸酉",
            "month": "甲子",
            "day": "丙寅",
            "hour": "庚子",
        },
        "luck_pillar": "丁卯",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {"伤官": 18.0, "食神": 12.0, "正官": 16.0, "偏印": 41.0, "比肩": 14.0, "劫财": 47.0},
        "ten_gods_runtime": {"伤官": 18.0, "食神": 12.0, "正官": 16.0, "偏印": 41.0, "比肩": 14.0, "劫财": 47.0},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["month", "flow"], "origin_type": "flow_trigger"}],
                "liu_hai": [{"pair": ["子", "未"], "pillars": ["hour", "luck"], "origin_type": "luck_background"}],
                "liu_po": [],
                "liu_he": [],
                "san_he": [],
                "ban_he": [{"pair": ["寅", "卯"], "pillars": ["day", "luck"], "origin_type": "luck_background"}],
                "sanxing": [],
            }
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}

    for plugin_id in (
        "classical.blind.work_axis.v1",
        "l2.risk.risk_matrix",
        "shensha",
        "ten_god_pattern",
    ):
        meta = by_plugin[plugin_id].meta
        assert "cluster_projection" in meta
        assert "projection_share" in meta
        assert meta.get("target_god")
    assert isinstance(by_plugin["classical.blind.work_axis.v1"].meta.get("static_basis"), dict)
    assert isinstance(by_plugin["l2.risk.risk_matrix"].meta.get("static_basis"), dict)


def test_natal_sanhe_projects_into_officer_kill_cluster_under_runtime_drag() -> None:
    pt = {
        "four_pillars": {
            "year": "丁巳",
            "month": "乙巳",
            "day": "乙丑",
            "hour": "乙酉",
        },
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_base_l0": {"伤官": 64.65, "食神": 47.08, "比肩": 27.5, "正官": 14.07, "偏财": 13.48, "七杀": 8.5, "正印": 7.98, "偏印": 5.46, "正财": 4.32},
        "ten_gods_runtime": {"伤官": 64.03, "食神": 46.63, "比肩": 27.75, "正官": 14.06, "偏财": 13.75, "七杀": 8.49, "正印": 8.26, "偏印": 5.65, "正财": 4.41},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["午", "子"], "pillars": ["flow", "luck"], "origin_type": "runtime_pair"}],
                "liu_hai": [{"pair": ["丑", "午"], "pillars": ["day", "flow"], "origin_type": "flow_trigger"}],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["hour", "luck"], "origin_type": "luck_background"}],
                "liu_he": [{"pair": ["子", "丑"], "pillars": ["day", "luck"], "origin_type": "luck_background"}],
                "san_he": [{"group": ["丑", "巳", "酉"], "pillars": ["day", "hour", "month", "year"], "origin_type": "natal"}],
                "ban_he": [],
                "sanxing": [],
            },
            "stem_fusion_v1": {
                "cases": [
                    {
                        "pillars": ["month", "luck"],
                        "stems": ["乙", "庚"],
                        "mode": "stuck",
                        "hua_element": "metal",
                        "month_stem_supports": False,
                        "branch_hua_ratio": 0.1667,
                    }
                ]
            },
        },
    }

    facts = collect_all_spec_facts(pt)
    sanhe_facts = [f for f in facts if str(f.plugin_id or "") == "l1.physics.op_branch_sanhe"]
    assert len(sanhe_facts) >= 2
    by_target = {str(f.meta.get("target_god") or ""): f for f in sanhe_facts if isinstance(f.meta, dict)}
    assert "七杀" in by_target
    assert "正官" in by_target
    assert by_target["七杀"].meta.get("condition_mode") == "natal_core_with_runtime_drag"
    assert float(by_target["正官"].meta.get("projection_share", 0.0) or 0.0) > 0.40
    assert float(by_target["七杀"].meta.get("projection_share", 0.0) or 0.0) > 0.40
    assert "impact_ratio" in by_target["七杀"].meta
    assert isinstance(by_target["七杀"].meta.get("static_basis"), dict)

    stem_fusion = next(f for f in facts if str(f.plugin_id or "") == "l1.physics.op_stem_fusion")
    assert stem_fusion.meta.get("condition_state") == "stuck"
    assert isinstance(stem_fusion.meta.get("static_basis"), dict)


def test_sanhe_and_muku_emit_protocol_layers() -> None:
    pt = {
        "four_pillars": {
            "year": "丙子",
            "month": "甲辰",
            "day": "乙丑",
            "hour": "戊辰",
        },
        "luck_pillar": "庚子",
        "flow_pillar": "己丑",
        "ten_gods_base_l0": {"伤官": 44.0, "正官": 37.0, "比肩": 33.0, "食神": 25.0},
        "ten_gods_runtime": {"伤官": 44.0, "正官": 37.0, "比肩": 33.0, "食神": 25.0},
        "meta": {
            "interaction_v2": {
                "san_he": [
                    {"group": ["丑", "巳", "酉"], "pillars": ["day", "hour", "month"], "origin_type": "natal", "stress": 1.2}
                ],
                "ban_he": [],
                "liu_chong": [],
                "liu_po": [],
                "liu_hai": [],
                "sanxing": [],
            }
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}

    sanhe = by_plugin["l1.physics.op_branch_sanhe"]
    muku = by_plugin["l1.physics.op_branch_muku"]
    assert sanhe.meta.get("interaction_layer") == "branch"
    assert sanhe.meta.get("manifestation_state") in {"manifested", "supported", "contested", "latent"}
    assert muku.meta.get("interaction_layer") == "branch"
    assert muku.meta.get("manifestation_state") in {"manifested", "supported", "contested", "latent"}
