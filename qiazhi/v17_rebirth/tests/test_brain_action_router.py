from __future__ import annotations

from v17_rebirth.backend.services.brain_action_router import apply_brain_action_queue


def test_apply_brain_action_queue_routes_actions_into_arbitration_buckets() -> None:
    arbitration = {
        "manual_decisions": [],
        "auto_resolutions": [],
        "llm_arbitration_context": [],
        "pending_decisions": [],
    }
    meta = {
        "brain_action_queue": [
            {
                "action_id": "a1",
                "conflict_id": "cx_system",
                "action_type": "system_merge_suggestion",
                "queue": "system",
                "confidence": 0.8,
            },
            {
                "action_id": "a2",
                "conflict_id": "cx_user",
                "action_type": "manual_escalation",
                "queue": "user",
                "confidence": 0.7,
            },
            {
                "action_id": "a3",
                "conflict_id": "cx_llm",
                "action_type": "llm_context_hold",
                "queue": "llm",
                "confidence": 0.6,
            },
        ]
    }

    out = apply_brain_action_queue(arbitration=arbitration, meta=meta)
    assert len(out["auto_resolutions"]) == 1
    assert out["auto_resolutions"][0]["conflict_id"] == "cx_system"
    assert len(out["manual_decisions"]) == 1
    assert out["manual_decisions"][0]["conflict_id"] == "cx_user"
    assert len(out["pending_decisions"]) == 1
    assert out["pending_decisions"][0]["conflict_id"] == "cx_user"
    assert len(out["llm_arbitration_context"]) == 1
    assert out["llm_arbitration_context"][0]["conflict_id"] == "cx_llm"


def test_apply_brain_action_queue_avoids_duplicate_conflict_rows() -> None:
    arbitration = {
        "manual_decisions": [{"conflict_id": "cx_user"}],
        "auto_resolutions": [],
        "llm_arbitration_context": [],
        "pending_decisions": [],
    }
    meta = {
        "brain_action_queue": [
            {
                "action_id": "a2",
                "conflict_id": "cx_user",
                "action_type": "manual_escalation",
                "queue": "user",
                "confidence": 0.7,
            }
        ]
    }

    out = apply_brain_action_queue(arbitration=arbitration, meta=meta)
    assert len(out["manual_decisions"]) == 1
