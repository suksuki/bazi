from __future__ import annotations

from v17_rebirth.backend.services.conflict_resolution_service import apply_conflict_resolution


def test_apply_conflict_resolution_marks_system_resolution_as_applied() -> None:
    meta = {
        "plugin_conflicts": [
            {"conflict_id": "cx_1", "conflict_type": "same_event_duplicate"},
        ],
        "plugin_conflict_resolutions": [
            {"conflict_id": "cx_1", "status": "suggested", "applied_to_settlement": False},
        ],
    }

    out = apply_conflict_resolution(meta=meta, conflict_id="cx_1", arbiter="system")
    assert out["plugin_conflicts"][0]["resolution_status"] == "approved"
    assert out["plugin_conflicts"][0]["resolved_by"] == "system"
    assert out["plugin_conflict_resolutions"][0]["status"] == "approved"
    assert out["plugin_conflict_resolutions"][0]["applied_to_settlement"] is True


def test_apply_conflict_resolution_can_queue_user_resolution_without_existing_suggestion() -> None:
    meta = {
        "plugin_conflicts": [
            {"conflict_id": "cx_2", "conflict_type": "cross_layer_override"},
        ],
        "plugin_conflict_resolutions": [],
    }

    out = apply_conflict_resolution(meta=meta, conflict_id="cx_2", arbiter="user")
    assert out["plugin_conflicts"][0]["resolution_status"] == "queued_user"
    assert out["plugin_conflicts"][0]["resolved_by"] == "user"
    assert out["plugin_conflict_resolutions"][0]["conflict_id"] == "cx_2"
    assert out["plugin_conflict_resolutions"][0]["applied_to_settlement"] is False
