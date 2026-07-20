from __future__ import annotations

from datetime import datetime, timezone

from experience.voice_validation import (
    VoiceComprehensionAnalystReview,
)
from product.voice_validation_api import summarize_voice_validation
from product.voice_validation_store import MemoryVoiceValidationStore
from tests.test_v50_abu_narrated_workspace import _narrated_case


def test_voice_study_is_balanced_private_and_does_not_store_birth_data(tmp_path) -> None:
    _, client, _, _, _, case_id = _narrated_case(tmp_path)

    started = client.post(
        "/api/v50/narration/validation/sessions",
        json={"case_id": case_id},
    )

    assert started.status_code == 200, started.text
    session = started.json()["session"]
    assert session["arm"] in {"text_only", "text_and_abu_voice"}
    assert session["privacy_scope"] == "participant_private_research"
    assert session["raw_birth_data_stored"] is False
    assert "birth" not in session
    assert len(session["assignment_hash"]) == 64


def test_voice_study_records_idempotent_structured_events_and_locks_submission(tmp_path) -> None:
    _, client, _, _, _, case_id = _narrated_case(tmp_path)
    session = client.post(
        "/api/v50/narration/validation/sessions", json={"case_id": case_id}
    ).json()["session"]
    event = {
        "client_event_id": "evt-1",
        "event_type": "playback_paused",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_since_session_ms": 1200,
        "segment_id": "baseline-thesis",
        "playback_position_ms": 860,
        "request_wait_ms": None,
        "cache_hit": True,
    }
    first = client.post(
        f"/api/v50/narration/validation/sessions/{session['session_id']}/events",
        json={"event": event},
    )
    duplicate = client.post(
        f"/api/v50/narration/validation/sessions/{session['session_id']}/events",
        json={"event": event},
    )
    submission = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "consent_confirmed": True,
        "whole_chart_summary": "整盘重心在输出能否获得现实承接。",
        "work_path_summary": "从内部能力出发，经表达转成现实结果。",
        "key_condition_summary": "需要持续反馈与承接环境。",
        "uncertainty_summary": "当前尚未确认现实输出是否稳定。",
        "natural_followup_question": "怎样确认承接条件已经出现？",
        "fatigue_score": 2,
        "professional_trust_delta": 1,
        "abu_long_term_listening_score": 4,
    }
    submitted = client.post(
        f"/api/v50/narration/validation/sessions/{session['session_id']}/comprehension",
        json={"submission": submission},
    )
    conflicting = client.post(
        f"/api/v50/narration/validation/sessions/{session['session_id']}/comprehension",
        json={"submission": {**submission, "fatigue_score": 5}},
    )

    assert first.status_code == duplicate.status_code == 200
    assert first.json()["event_count"] == duplicate.json()["event_count"] == 1
    assert submitted.status_code == 200
    assert conflicting.status_code == 409


def test_voice_study_arm_override_and_summary_are_not_available_to_members(tmp_path) -> None:
    _, client, _, _, _, case_id = _narrated_case(tmp_path)

    override = client.post(
        "/api/v50/narration/validation/sessions",
        json={"case_id": case_id, "requested_arm": "text_only"},
    )
    summary = client.get("/api/v50/narration/validation/summary")

    assert override.status_code == 403
    assert summary.status_code == 403


def test_voice_validation_summary_waits_for_human_review() -> None:
    store = MemoryVoiceValidationStore()
    from experience.voice_validation import VoiceValidationSession

    session = VoiceValidationSession(
        session_id="voice-study-1",
        participant_ref="user-1",
        case_id="case-1",
        manifest_id="manifest-1",
        manifest_hash="a" * 64,
        arm="text_and_abu_voice",
        assignment_hash="b" * 64,
        started_at=datetime.now(timezone.utc),
    )
    store.create(session)
    pending = summarize_voice_validation(store.list_sessions())
    review = VoiceComprehensionAnalystReview(
        reviewed_at=datetime.now(timezone.utc),
        reviewer_ref="admin-1",
        whole_chart_accuracy=2,
        work_path_accuracy=2,
        condition_accuracy=1,
        uncertainty_accuracy=2,
        anchor_task_passed=True,
    )
    store.save_review(session.session_id, review)
    reviewed = summarize_voice_validation(store.list_sessions())

    assert pending["human_validation_performed"] is False
    assert pending["ready_for_product_decision"] is False
    assert reviewed["human_validation_performed"] is True
    assert reviewed["ready_for_product_decision"] is False


def test_voice_study_frontend_is_internal_only_and_instruments_core_actions() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = (root / "apps/product/static/l5/app.js").read_text(encoding="utf-8")
    styles = (root / "apps/product/static/l5/styles.css").read_text(encoding="utf-8")

    assert 'get("voice_study") === "1"' in script
    assert "playback_started" in script
    assert "chapter_replayed" in script
    assert "comprehension_submitted" in script
    assert "raw_birth_data_stored" not in script
    assert '[data-voice-study-arm="text_only"]' in styles
