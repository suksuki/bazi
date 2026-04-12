"""终判证据行：三合局脱水。"""
from __future__ import annotations

from app.skills.final_verdict_parts.evidence import get_logical_evidence


def test_get_logical_evidence_includes_sanhe_cluster_line() -> None:
    physics = {
        "deity_energy_axes": {"比肩": {"absolute_energy": 1.0}},
        "composite_field_impact": {
            "sanhe_clusters": [
                {
                    "branches": ["丑", "巳", "酉"],
                    "energy_vault_status": "AGGREGATED",
                    "nodes": [{"pillar": "hour", "branch": "酉"}],
                }
            ]
        },
    }
    lines = get_logical_evidence(metadata={"pillars": {}}, physics_tensor=physics, selected_cards=[], consensus_history=[])
    assert lines[0] == "地支.三合.金局=巳酉丑|Status=AGGREGATED|Nodes=Hour"
    sanhe_lines = [x for x in lines if x.startswith("地支.三合.")]
    assert len(sanhe_lines) == 1


def test_get_logical_evidence_sanhe_from_interaction_v2_when_clusters_missing() -> None:
    physics = {
        "deity_energy_axes": {"比肩": {"absolute_energy": 1.0}},
        "composite_field_impact": {},
        "meta": {
            "interaction_v2": {
                "attribute_collapse": [
                    {"kind": "sanhe", "branches": ["丑", "巳", "酉"], "attribute_collapse": True},
                ]
            }
        },
    }
    lines = get_logical_evidence(metadata={"pillars": {}}, physics_tensor=physics, selected_cards=[], consensus_history=[])
    assert lines[0] == "地支.三合.金局=巳酉丑|Status=AGGREGATED|Nodes=UNKNOWN"
