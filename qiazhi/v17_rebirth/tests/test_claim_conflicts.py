from __future__ import annotations

from v17_rebirth.backend.plugins.spec import ArbiterType, V17Fact
from v17_rebirth.backend.services.claim_protocol import CLAIM_JSON_SCHEMA, compile_claims
from v17_rebirth.backend.services.conflict_detector import detect_claim_conflicts, recommend_conflict_resolutions


def test_compile_claims_exposes_minimum_protocol_fields() -> None:
    claims = compile_claims(
        facts=[
            V17Fact(
                plugin_id="l1.physics.op_branch_liuhe",
                text="检测到地支六合：正财 能级提升 15%。",
                causal_tier=4,
                suggested_arbiter=ArbiterType.SYSTEM,
                meta={"impact_ratio": 0.15, "target_god": "正财", "source_event": "liuhe(午未)"},
            )
        ],
        physics_tensor={"ten_gods_base_l0": {"正财": 10.0}},
    )
    assert CLAIM_JSON_SCHEMA["title"] == "V17Claim"
    assert len(claims) == 1
    assert claims[0]["plugin_id"] == "l1.physics.op_branch_liuhe"
    assert claims[0]["target_god"] == "正财"
    assert claims[0]["logic_level"] == "L1"
    assert claims[0]["intent_vector"]["正财"] == 0.15


def test_detect_claim_conflicts_flags_same_event_duplicate() -> None:
    claims = [
        {
            "claim_id": "a",
            "plugin_id": "l1.physics.op_branch_liupo",
            "source_event": "liupo(子卯)",
            "target_god": "食神",
            "intent_vector": {"食神": -0.08},
            "logic_level": "L1",
        },
        {
            "claim_id": "b",
            "plugin_id": "l1.physics.op_branch_liuhai",
            "source_event": "liupo(子卯)",
            "target_god": "食神",
            "intent_vector": {"食神": -0.12},
            "logic_level": "L1",
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    assert any(c["conflict_type"] == "same_event_duplicate" for c in conflicts)
    resolutions = recommend_conflict_resolutions(claims, conflicts)
    assert len(resolutions) == 1
    assert resolutions[0]["resolved_by"] == "system"
    assert resolutions[0]["winner_claim_id"] in {"a", "b"}
    assert resolutions[0]["applied_to_settlement"] is False


def test_detect_claim_conflicts_flags_same_target_opposite_sign_and_cross_layer() -> None:
    claims = [
        {
            "claim_id": "l1_gain",
            "plugin_id": "l1.physics.op_branch_liuhe",
            "source_event": "liuhe(午未)",
            "target_god": "正财",
            "intent_vector": {"正财": 0.15},
            "logic_level": "L1",
        },
        {
            "claim_id": "l2_risk",
            "plugin_id": "l2.risk.risk_matrix",
            "source_event": "risk(owl_food)",
            "target_god": "正财",
            "intent_vector": {"正财": -0.15},
            "logic_level": "L2",
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    assert any(c["conflict_type"] == "same_target_opposite_sign" for c in conflicts)
    assert any(c["conflict_type"] == "cross_layer_override" for c in conflicts)
