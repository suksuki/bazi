from __future__ import annotations

from v17_rebirth.backend.services.authority_judgement_protocol import (
    authority_target_signal_map,
    build_judgement_bias_protocol,
    build_stage_bias_protocol,
)


def test_build_judgement_bias_protocol_normalizes_bias_and_evidence() -> None:
    protocol = build_judgement_bias_protocol(
        [
            {
                "id": "d1",
                "plugin_id": "l2.risk.risk_matrix",
                "label": "伤官见官",
                "target_god": "正官",
                "arbiter_type": "user",
                "physical_impact": {
                    "god_ring_bias": {
                        "reason": "伤官与正官在当前盘面形成强对抗。",
                        "use_bias": {"正官": 0.18},
                        "taboo_bias": {"伤官": 0.24},
                    },
                    "work_evidence": {
                        "relation_family": "officer_hurt",
                        "target_god": "正官",
                        "targets": ["正官"],
                        "actor_gods": ["伤官"],
                        "receiver_gods": ["正官"],
                        "members": ["巳", "酉", "丑"],
                        "effect_type": "contest",
                    },
                },
            }
        ]
    )

    assert protocol["contract"] == "v17.authority.judgement_bias.v1"
    assert protocol["use_bias"]["正官"] == 0.18
    assert protocol["taboo_bias"]["伤官"] == 0.24
    assert protocol["summary"]["entry_count"] == 1
    entry = protocol["entries"][0]
    assert entry["source_label"]
    assert entry["evidence_contract"] == "v17.work_evidence.v1"
    assert "伤官->正官" in entry["evidence_summary"]


def test_stage_bias_protocol_and_target_signal_map_export_target_metrics() -> None:
    stage_protocol = build_stage_bias_protocol(
        {
            "正官": {
                "lu": 0.0,
                "blade": 0.0,
                "general": 0.0,
                "stage": 0.0,
                "use_boost": 0.22,
                "taboo_boost": 0.04,
                "stability_boost": 0.11,
                "volatility_boost": 0.02,
            }
        }
    )
    judgement_protocol = {
        "summary": {
            "by_target": {
                "正官": {"use_bias": 0.18, "taboo_bias": 0.07, "entry_count": 2},
            }
        }
    }

    signal_map = authority_target_signal_map(
        judgement_protocol=judgement_protocol,
        stage_protocol=stage_protocol,
    )

    assert stage_protocol["contract"] == "v17.authority.stage_bias.v1"
    assert signal_map["正官"]["judgement_use_bias"] == 0.18
    assert signal_map["正官"]["judgement_entry_count"] == 2.0
    assert signal_map["正官"]["stage_use_boost"] == 0.22
