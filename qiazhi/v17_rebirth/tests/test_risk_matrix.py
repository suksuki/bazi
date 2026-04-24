from __future__ import annotations

from v17_rebirth.backend.logic.L2_structure_patterns import risk_matrix


def test_risk_matrix_uses_config_for_blade_and_officer(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 3.0,
            "OWL_FOOD_CAP": 0.3,
            "OFFICER_CRUSH_LIMIT": 0.4,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"day": "壬申"},
            "ten_gods_absolute": {"伤官": 12.0, "正官": 11.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [{"pair": ["子", "午"]}],
                }
            },
        }
    )

    assert len(facts) == 3
    blade = next(f for f in facts if f.meta.get("risk_driver") == "blade_clash")
    officer = next(f for f in facts if f.meta.get("risk_driver") == "officer_crush")
    officer_pattern = next(f for f in facts if f.meta.get("pattern_candidate") == "伤官见官")
    assert blade.meta["impact_ratio"] == 0.0
    assert blade.meta["observe_only"] is True
    assert blade.meta["work_evidence"]["relation_family"] == "risk_blade_clash"
    assert officer.meta["impact_ratio"] == 0.0
    assert officer.meta["observe_only"] is True
    assert officer.meta["work_evidence"]["effect_type"] == "harm"
    assert officer.meta["work_evidence"]["actor_gods"] == ["伤官"]
    assert officer.meta["work_evidence"]["receiver_gods"] == ["正官"]
    assert officer_pattern.meta["god_ring_bias"]["taboo_bias"]["伤官"] > 0.0


def test_risk_matrix_owl_food_cap_controls_trigger_and_magnitude(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.25,
            "OFFICER_CRUSH_LIMIT": 0.5,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "ten_gods_absolute": {"偏印": 8.0, "食神": 6.0},
            "meta": {"interaction_v2": {}},
        }
    )

    assert len(facts) == 2
    owl = next(f for f in facts if f.meta.get("risk_driver") == "owl_food")
    owl_pattern = next(f for f in facts if f.meta.get("pattern_candidate") == "枭印夺食")
    assert owl.meta["risk_driver"] == "owl_food"
    assert owl.meta["impact_ratio"] == 0.0
    assert owl.meta["observe_only"] is True
    assert owl.meta["work_evidence"]["relation_family"] == "risk_owl_food"
    assert owl.meta["work_evidence"]["actor_gods"] == ["偏印"]
    assert owl.meta["work_evidence"]["receiver_gods"] == ["食神"]
    assert owl_pattern.meta["god_ring_bias"]["use_bias"]["食神"] > 0.0
    assert owl_pattern.meta["god_ring_bias"]["taboo_bias"]["偏印"] > 0.0


def test_risk_matrix_reduces_officer_crush_when_officer_cluster_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.4,
            "OFFICER_CRUSH_LIMIT": 0.5,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "luck_pillar": "庚子",
            "flow_pillar": "丙午",
            "ten_gods_absolute": {"伤官": 64.65, "正官": 14.07, "七杀": 8.5},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [{"pair": ["子", "午"], "origin_type": "runtime_pair"}],
                    "san_he": [{"group": ["巳", "酉", "丑"], "origin_type": "natal"}],
                },
                "stem_fusion_v1": {
                    "cases": [{"stems": ["乙", "庚"], "mode": "stuck", "hua_element": "metal"}],
                },
            },
        }
    )

    officer = next(
        f for f in facts if f.meta.get("risk_driver") in {"officer_crush", "officer_hurt_contest"}
    )
    assert officer.meta["officer_support_relief"] > 0.4
    assert officer.meta["risk_driver"] == "officer_hurt_contest"
    assert officer.meta["impact_ratio"] == 0.0


def test_risk_matrix_exposes_layer_and_manifestation_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.4,
            "OFFICER_CRUSH_LIMIT": 0.5,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"day": "壬申"},
            "ten_gods_absolute": {"伤官": 20.0, "正官": 18.0, "偏印": 9.0, "食神": 8.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [
                        {
                            "pair": ["子", "午"],
                            "pillars": ["day", "luck"],
                            "origin_type": "natal",
                        }
                    ]
                }
            },
        }
    )

    blade = next(f for f in facts if f.meta.get("risk_driver") == "blade_clash")
    assert blade.meta["interaction_layer"] == "branch"
    assert blade.meta["manifestation_state"] in {"manifested", "supported", "contested", "latent"}
    assert blade.meta["origin_type"] == "natal"
    assert blade.meta["blade_branch"] == "子"


def test_risk_matrix_does_not_call_four_orthodox_clash_yangren_without_daymaster_blade(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.4,
            "OFFICER_CRUSH_LIMIT": 0.5,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"day": "乙丑"},
            "ten_gods_absolute": {"伤官": 8.0, "正官": 4.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [{"pair": ["子", "午"], "origin_type": "natal"}],
                }
            },
        }
    )

    assert [f for f in facts if f.meta.get("risk_driver") == "blade_clash"] == []


def test_risk_matrix_emits_officer_hurt_and_exhaust_pattern_candidates(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.4,
            "OFFICER_CRUSH_LIMIT": 0.5,
            "OFFICER_EXHAUST_RATIO": 2.2,
            "OFFICER_EXHAUST_SUPPORT_MAX": 0.42,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"year": "癸亥", "month": "丙午", "day": "乙丑", "hour": "甲辰"},
            "ten_gods_absolute": {"伤官": 42.0, "正官": 12.0, "七杀": 2.0},
            "meta": {"interaction_v2": {"liu_chong": [], "san_he": []}, "stem_fusion_v1": {"cases": []}},
        }
    )

    candidates = [f for f in facts if f.meta.get("claim_type") == "pattern_candidate"]
    names = {str(f.meta.get("pattern_candidate") or "") for f in candidates}
    assert "伤官见官" in names
    assert "伤官伤尽" in names

    exhaust = next(f for f in candidates if f.meta.get("pattern_candidate") == "伤官伤尽")
    assert exhaust.meta["god_ring_bias"]["use_bias"]["伤官"] > 0.0
    assert exhaust.meta["god_ring_bias"]["taboo_bias"]["正官"] > 0.0
    assert exhaust.meta["work_evidence"]["effect_type"] == "benefit"
    assert exhaust.meta["work_evidence"]["counterpart_gods"] == ["正官"]


def test_risk_matrix_does_not_emit_exhaust_when_officer_cluster_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.4,
            "OFFICER_CRUSH_LIMIT": 0.5,
            "OFFICER_EXHAUST_RATIO": 2.2,
            "OFFICER_EXHAUST_SUPPORT_MAX": 0.42,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "four_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
            "luck_pillar": "庚子",
            "flow_pillar": "丙午",
            "ten_gods_absolute": {"伤官": 64.65, "正官": 14.07, "七杀": 8.5},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [{"pair": ["子", "午"], "origin_type": "runtime_pair"}],
                    "san_he": [{"group": ["巳", "酉", "丑"], "origin_type": "natal"}],
                },
                "stem_fusion_v1": {
                    "cases": [{"stems": ["乙", "庚"], "mode": "stuck", "hua_element": "metal"}],
                },
            },
        }
    )

    pattern_names = {str(f.meta.get("pattern_candidate") or "") for f in facts}
    assert "伤官见官" in pattern_names
    assert "伤官伤尽" not in pattern_names


def test_risk_matrix_marks_owl_manifestation_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "v17_rebirth.backend.logic.configs.manager.get_plugin_config",
        lambda _plugin_id: {
            "BLADE_CLASH_IMPULSE": 2.2,
            "OWL_FOOD_CAP": 0.25,
            "OFFICER_CRUSH_LIMIT": 0.5,
        },
    )
    facts = risk_matrix.PLUGIN.collect_v17_facts(
        {
            "ten_gods_absolute": {"偏印": 10.0, "食神": 6.0},
            "meta": {"interaction_v2": {}},
        }
    )

    assert len(facts) == 2
    owl = next(f for f in facts if f.meta.get("risk_driver") == "owl_food")
    assert owl.meta["risk_driver"] == "owl_food"
    assert owl.meta["interaction_layer"] == "cross_layer"
    assert owl.meta["manifestation_state"] in {"latent", "contested", "supported", "manifested"}
