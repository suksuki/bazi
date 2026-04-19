from __future__ import annotations

from v17_rebirth.backend.services.arbiter_router import route_conflicts
from v17_rebirth.backend.services.conflict_scoring import build_conflict_scores


def _claims() -> list[dict]:
    return [
        {
            "claim_id": "c1",
            "plugin_id": "plugin.a",
            "logic_level": "L1",
            "priority": 0.7,
            "confidence": 0.8,
            "intent_vector": {"食神": 0.12},
        },
        {
            "claim_id": "c2",
            "plugin_id": "plugin.b",
            "logic_level": "L2",
            "priority": 0.6,
            "confidence": 0.7,
            "intent_vector": {"食神": -0.12},
        },
        {
            "claim_id": "c3",
            "plugin_id": "plugin.c",
            "logic_level": "L3",
            "priority": 0.4,
            "confidence": 0.5,
            "intent_vector": {"食神": 0.05},
        },
    ]


def test_build_conflict_scores_embeds_confidence_and_band() -> None:
    conflicts = [
        {
            "conflict_id": "cx_1",
            "severity": "P2",
            "conflict_type": "same_target_opposite_sign",
            "claims": ["c1", "c2"],
            "why_conflict": "test",
        },
        {
            "conflict_id": "cx_2",
            "severity": "P3",
            "conflict_type": "same_event_duplicate",
            "claims": ["c3"],
            "why_conflict": "test",
        },
    ]
    scored = build_conflict_scores(conflicts=conflicts, claim_rows=_claims())
    assert all("conflict_score" in row for row in scored)
    assert all("conflict_score_breakdown" in row for row in scored)
    assert all("confidence_band" in row for row in scored)
    assert 0.0 <= float(scored[0]["conflict_score"]) <= 1.0
    assert isinstance(scored[0]["confidence_band"], str)


def test_route_conflicts_uses_conflict_score_for_escalation_to_user() -> None:
    conflicts = [
        {
            "conflict_id": "cx_1",
            "severity": "P1",
            "conflict_type": "cross_layer_override",
            "conflict_score": 0.96,
            "claims": ["c1", "c2"],
            "recommended_arbiter": "system",
        },
    ]
    out = route_conflicts(
        conflicts=conflicts,
        knowledge_snapshot={"conflict_history": {"recommended_arbiters": {"system": 1, "llm": 0, "user": 0}}},
    )
    assert out[0]["recommended_arbiter"] == "user"
