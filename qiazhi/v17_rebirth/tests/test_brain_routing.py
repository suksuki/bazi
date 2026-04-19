from __future__ import annotations

from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot


def test_build_knowledge_snapshot_summarizes_claims_conflicts_and_resolutions() -> None:
    snapshot = build_knowledge_snapshot(
        claims=[
            {"claim_type": "weaken", "target_god": "食神"},
            {"claim_type": "weaken", "target_god": "食神"},
            {"claim_type": "enhance", "target_god": "正财"},
        ],
        conflicts=[
            {"conflict_type": "same_event_duplicate", "recommended_arbiter": "system"},
            {"conflict_type": "same_target_opposite_sign", "recommended_arbiter": "llm"},
        ],
        conflict_resolutions=[
            {"resolved_by": "system"},
        ],
    )

    assert snapshot["claim_history"]["total_claims"] == 3
    assert snapshot["claim_history"]["by_type"]["weaken"] == 2
    assert snapshot["conflict_history"]["by_type"]["same_event_duplicate"] == 1
    assert snapshot["resolution_preview"]["resolved_by"]["system"] == 1


def test_route_conflicts_prefers_severity_policy_with_session_knowledge() -> None:
    conflicts = [
        {"conflict_id": "c1", "severity": "P3", "recommended_arbiter": "system"},
        {"conflict_id": "c2", "severity": "P2", "recommended_arbiter": "llm"},
        {"conflict_id": "c3", "severity": "P1", "recommended_arbiter": "llm"},
    ]
    knowledge_snapshot = {
        "conflict_history": {
            "recommended_arbiters": {
                "system": 4,
                "llm": 2,
                "user": 1,
            }
        }
    }

    routed = route_conflicts(conflicts=conflicts, knowledge_snapshot=knowledge_snapshot)
    assert routed[0]["recommended_arbiter"] == "system"
    assert routed[1]["recommended_arbiter"] == "llm"
    assert routed[2]["recommended_arbiter"] == "user"
    assert routed[0]["routing_policy"] == "severity_plus_session_preference"
