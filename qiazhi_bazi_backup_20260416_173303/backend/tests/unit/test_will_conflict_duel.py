from __future__ import annotations

from app.services.helpers.will_conflict_duel import build_will_conflict_risk_lines


def test_will_conflict_officer_vs_blind_risk():
    lines = build_will_conflict_risk_lines(
        merged_physics_keys={"OFFICER_RESTRAINT_ALPHA"},
        merged_interaction_keys=set(),
        plugin_outputs={
            "classical.blind_school.v1": {
                "payload": {
                    "net_effect": "risk",
                    "risk_ratio": 0.5,
                    "backfire_risk": 2.0,
                    "morphing_hints": ["[DANGEROUS_TURBULENCE]"],
                }
            }
        },
        physics_tensor={"meta": {}},
    )
    assert lines
    assert "意志对垒" in lines[0]


def test_will_conflict_empty_keys_returns_empty():
    assert (
        build_will_conflict_risk_lines(
            merged_physics_keys=set(),
            merged_interaction_keys=set(),
            plugin_outputs={},
            physics_tensor={},
        )
        == []
    )
