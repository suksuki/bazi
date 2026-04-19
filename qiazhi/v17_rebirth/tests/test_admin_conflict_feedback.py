from __future__ import annotations

from v17_rebirth.backend.api.admin_v17 import (
    _llm_conflict_feedback_quality,
    _manual_conflict_feedback_quality,
)
from v17_rebirth.backend.services.knowledge_store import build_knowledge_snapshot


def test_manual_quality_bounds_and_preference_order() -> None:
    low = _manual_conflict_feedback_quality(resolved_by="system", conflict_score=0.1)
    mid = _manual_conflict_feedback_quality(resolved_by="user", conflict_score=0.6)
    high = _manual_conflict_feedback_quality(resolved_by="llm", conflict_score=1.0)

    assert -1.0 <= low <= 1.0
    assert -1.0 <= mid <= 1.0
    assert -1.0 <= high <= 1.0
    assert mid > low


def test_manual_quality_reflects_arbiter_preference() -> None:
    base = _manual_conflict_feedback_quality(resolved_by="llm", conflict_score=0.5)
    assert _manual_conflict_feedback_quality(resolved_by="system", conflict_score=0.5) > base
    assert base == _manual_conflict_feedback_quality(resolved_by="unknown", conflict_score=0.5)


def test_build_knowledge_snapshot_counts_resolved_user_feedback() -> None:
    snapshot = build_knowledge_snapshot(
        claims=[],
        conflicts=[],
        conflict_resolutions=[],
        feedback_rows=[
            {"status": "resolved_user", "residual_correction": 0.6},
            {"status": "queued_user", "residual_correction": 0.1},
        ],
    )
    assert snapshot["conflict_history"]["feedback_arbiters"]["user"] == 2
    assert snapshot["conflict_history"]["feedback_arbiter_scores"]["user"] > 0.0


def test_llm_feedback_quality_monotonic_with_conflict_score() -> None:
    low = _llm_conflict_feedback_quality(
        resolved_by="llm",
        resolution_type="context_only",
        confidence=0.3,
        conflict_score=0.2,
    )
    high = _llm_conflict_feedback_quality(
        resolved_by="llm",
        resolution_type="context_only",
        confidence=0.3,
        conflict_score=0.8,
    )
    assert high > low
