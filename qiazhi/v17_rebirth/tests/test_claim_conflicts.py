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


def test_detect_claim_conflicts_routes_same_plugin_officer_hurt_family_to_llm() -> None:
    claims = [
        {
            "claim_id": "hurt_manifest",
            "plugin_id": "l2.risk.risk_matrix",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:officer_hurt_manifest",
            "exclusivity_key": "pattern:officer_hurt_profile",
            "target_god": "伤官",
            "intent_vector": {"伤官": -0.22},
            "logic_level": "L2",
            "priority": 0.86,
            "confidence": 0.64,
        },
        {
            "claim_id": "hurt_exhaust",
            "plugin_id": "l2.risk.risk_matrix",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:officer_hurt_exhaust",
            "exclusivity_key": "pattern:officer_hurt_profile",
            "target_god": "伤官",
            "intent_vector": {"伤官": 0.26},
            "logic_level": "L2",
            "priority": 0.87,
            "confidence": 0.7,
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    family_conflict = next(c for c in conflicts if c["conflict_type"] == "pattern_family_exclusive")
    assert family_conflict["recommended_arbiter"] == "llm"
    assert family_conflict["severity"] == "P2"


def test_detect_claim_conflicts_routes_food_output_profile_to_llm() -> None:
    claims = [
        {
            "claim_id": "owl_food",
            "plugin_id": "l2.risk.risk_matrix",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:owl_food",
            "exclusivity_key": "pattern:food_output_profile",
            "target_god": "食神",
            "intent_vector": {"食神": 0.18},
            "logic_level": "L2",
            "priority": 0.84,
            "confidence": 0.62,
        },
        {
            "claim_id": "zhisha",
            "plugin_id": "classical.pattern.shishen_zhisha.v1",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:shishen_zhisha",
            "exclusivity_key": "pattern:food_output_profile",
            "target_god": "七杀",
            "intent_vector": {"食神": 0.24},
            "logic_level": "L3",
            "priority": 0.75,
            "confidence": 0.67,
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    family_conflict = next(c for c in conflicts if c["conflict_type"] == "pattern_family_exclusive")
    assert family_conflict["recommended_arbiter"] == "llm"
    assert family_conflict["severity"] == "P2"


def test_detect_claim_conflicts_routes_wealth_output_profile_to_llm() -> None:
    claims = [
        {
            "claim_id": "food_wealth",
            "plugin_id": "classical.pattern.shishen_shengcai.v1",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:shishen_shengcai",
            "exclusivity_key": "pattern:wealth_output_profile",
            "target_god": "食神",
            "intent_vector": {"食神": 0.22},
            "logic_level": "L3",
            "priority": 0.75,
            "confidence": 0.66,
        },
        {
            "claim_id": "hurt_wealth",
            "plugin_id": "classical.pattern.shangguan_shengcai.v1",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:shangguan_shengcai",
            "exclusivity_key": "pattern:wealth_output_profile",
            "target_god": "伤官",
            "intent_vector": {"伤官": 0.23},
            "logic_level": "L3",
            "priority": 0.74,
            "confidence": 0.65,
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    family_conflict = next(c for c in conflicts if c["conflict_type"] == "pattern_family_exclusive")
    assert family_conflict["recommended_arbiter"] == "llm"
    assert family_conflict["severity"] == "P2"


def test_detect_claim_conflicts_routes_seal_support_profile_to_llm() -> None:
    claims = [
        {
            "claim_id": "guanyin",
            "plugin_id": "classical.pattern.guanyin.v1",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:guanyin",
            "exclusivity_key": "pattern:seal_support_profile",
            "target_god": "正官",
            "intent_vector": {"正官": 0.2, "正印": 0.16},
            "logic_level": "L3",
            "priority": 0.748,
            "confidence": 0.748,
        },
        {
            "claim_id": "caipoyin",
            "plugin_id": "classical.pattern.caipoyin.v1",
            "claim_type": "pattern_candidate",
            "entity_scope": "pattern",
            "source_event": "pattern:caipoyin",
            "exclusivity_key": "pattern:seal_support_profile",
            "target_god": "正印",
            "intent_vector": {"正印": 0.18, "正财": -0.22},
            "logic_level": "L3",
            "priority": 0.744,
            "confidence": 0.744,
        },
    ]
    conflicts = detect_claim_conflicts(claims)
    family_conflict = next(c for c in conflicts if c["conflict_type"] == "pattern_family_exclusive")
    assert family_conflict["recommended_arbiter"] == "llm"
    assert family_conflict["severity"] == "P2"
