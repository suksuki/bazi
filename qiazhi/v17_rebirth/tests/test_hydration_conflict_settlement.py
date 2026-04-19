from __future__ import annotations

from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _extract_claims_resolution_plan


def test_extract_claims_resolution_plan_ignores_user_p1_like_resolution_from_settlement() -> None:
    claim_rows = [
        {
            "claim_id": "plugin_a_claim_1",
            "claim_type": "enhance",
            "plugin_id": "l2.block_a",
            "target_god": "食神",
            "intent_vector": {"食神": 0.2},
        }
    ]
    current_proposals = [
        {
            "id": "plugin_a_claim_1_prop",
            "claim_id": "plugin_a_claim_1",
            "plugin_id": "l2.block_a",
            "title": "测试",
            "target_god": "食神",
            "impact_ratio": 0.2,
            "significance_weight": 1.0,
            "arbiter_type": "system",
        }
    ]
    conflict_resolutions = [
        {
            "conflict_id": "c1",
            "claims": ["plugin_a_claim_1"],
            "winner_claim_ids": ["plugin_a_claim_1"],
            "dropped_claim_ids": [],
            "resolved_by": "user",
            "status": "approved",
            "applied_to_settlement": False,
        }
    ]

    proposals, settlement_meta = _extract_claims_resolution_plan(
        claim_rows=claim_rows,
        conflict_resolutions=conflict_resolutions,
        current_proposals=current_proposals,
    )

    assert len(proposals) == 1
    assert proposals[0]["claim_id"] == "plugin_a_claim_1"
    trace = settlement_meta.get("resolved_conflict_settlement", {})
    assert trace.get("applied_resolution_count") == 0
    assert trace.get("dropped_claim_count") == 0
    assert trace.get("winner_claim_count") == 0


def test_extract_claims_resolution_plan_applies_system_resolution_winners_and_drops() -> None:
    claim_rows = [
        {
            "claim_id": "c1",
            "claim_type": "enhance",
            "plugin_id": "l2.block_a",
            "target_god": "食神",
            "intent_vector": {"食神": 0.12},
            "claim_text": "提升食神",
        },
        {
            "claim_id": "c2",
            "claim_type": "weaken",
            "plugin_id": "l2.block_b",
            "target_god": "食神",
            "intent_vector": {"食神": -0.08},
            "claim_text": "抑制食神",
        },
    ]
    current_proposals = [
        {
            "id": "prop_c1",
            "claim_id": "c1",
            "plugin_id": "l2.block_a",
            "title": "提升食神",
            "target_god": "食神",
            "impact_ratio": 0.12,
            "significance_weight": 1.0,
            "arbiter_type": "system",
        },
        {
            "id": "prop_c2",
            "claim_id": "c2",
            "plugin_id": "l2.block_b",
            "title": "抑制食神",
            "target_god": "食神",
            "impact_ratio": -0.08,
            "significance_weight": 1.0,
            "arbiter_type": "system",
        },
    ]
    conflict_resolutions = [
        {
            "conflict_id": "c1",
            "claims": ["c1", "c2"],
            "winner_claim_ids": ["c2"],
            "dropped_claim_ids": ["c1"],
            "resolved_by": "system",
            "status": "approved",
            "applied_to_settlement": True,
        }
    ]

    proposals, settlement_meta = _extract_claims_resolution_plan(
        claim_rows=claim_rows,
        conflict_resolutions=conflict_resolutions,
        current_proposals=current_proposals,
    )

    claim_ids = {p.get("claim_id") for p in proposals}
    assert claim_ids == {"c2"}
    trace = settlement_meta.get("resolved_conflict_settlement", {})
    assert trace.get("applied_resolution_count") == 1
    assert trace.get("dropped_claim_count") == 1
    assert trace.get("winner_claim_count") == 1
    assert trace.get("synthetic_proposal_count") == 0


def test_extract_claims_resolution_plan_synthesizes_winner_without_base_proposal() -> None:
    claim_rows = [
        {
            "claim_id": "winner_only",
            "claim_type": "enhance",
            "plugin_id": "l2.block_a",
            "target_god": "七杀",
            "intent_vector": {"七杀": 0.2},
            "claim_text": "测试合成",
        },
    ]
    current_proposals = []
    conflict_resolutions = [
        {
            "conflict_id": "c1",
            "claims": ["winner_only"],
            "winner_claim_ids": ["winner_only"],
            "resolved_by": "system",
            "status": "approved",
            "applied_to_settlement": True,
        }
    ]

    proposals, settlement_meta = _extract_claims_resolution_plan(
        claim_rows=claim_rows,
        conflict_resolutions=conflict_resolutions,
        current_proposals=current_proposals,
    )

    assert len(proposals) == 1
    assert proposals[0]["claim_id"] == "winner_only"
    assert proposals[0]["arbiter_type"] == "system"
    assert proposals[0]["impact_ratio"] == 0.2
    assert proposals[0]["target_god"] == "七杀"
    assert settlement_meta.get("resolved_conflict_settlement", {}).get("synthetic_proposal_count") == 1
