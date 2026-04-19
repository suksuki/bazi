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
            "ten_gods_absolute": {"伤官": 12.0, "正官": 11.0},
            "meta": {
                "interaction_v2": {
                    "liu_chong": [{"pair": ["子", "午"]}],
                }
            },
        }
    )

    assert len(facts) == 2
    blade = next(f for f in facts if f.meta.get("risk_driver") == "blade_clash")
    officer = next(f for f in facts if f.meta.get("risk_driver") == "officer_crush")
    assert blade.meta["impact_ratio"] == 0.3
    assert officer.meta["impact_ratio"] == -0.4


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

    assert len(facts) == 1
    owl = facts[0]
    assert owl.meta["risk_driver"] == "owl_food"
    assert owl.meta["impact_ratio"] == -0.25
