from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent
from v40.engines import build_native_bazi_runtime
from v40.evaluation import build_training_replay_batch_summary, replay_training_example
from v40.storage import resolve_v40_database_config
from v40.synthetic import load_synthetic_seeds
from v40.training import build_training_example_from_labels


def _runtime():
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    return build_native_bazi_runtime(
        request_id="request.phase33.runtime.001",
        reading_id="reading.phase33.runtime.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )


def _label(reading_id: str, target_id: str) -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id=f"label:{reading_id}:phase33:{target_id}",
        reading_id=reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=[target_id],
        label=LabelValue.SUPPORTS,
        strength=0.78,
        confidence=0.72,
        reason="Phase33 replay batch label。",
        created_by_role="practitioner",
        local_only=True,
    )


def _replay(replay_id: str, target_id: str):
    runtime = _runtime()
    example = build_training_example_from_labels(
        example_id=f"example.{replay_id}",
        reading_id=runtime.reading_id,
        label_events=[_label(runtime.reading_id, target_id)],
        topic=Topic.CAREER,
        local_overlay_refs=[f"overlay.{replay_id}"],
    )
    return replay_training_example(
        replay_id=replay_id,
        training_example=example,
        runtime=runtime,
        candidate_version="v40-phase33",
    )


def test_training_replay_batch_approves_only_when_all_replays_pass() -> None:
    runtime = _runtime()
    passed = _replay("replay.phase33.pass.001", runtime.branches[0].branch_id)

    summary = build_training_replay_batch_summary(
        batch_id="batch.phase33.pass.001",
        candidate_version="v40-phase33",
        replays=[passed],
    )

    assert summary.replay_count == 1
    assert summary.passed_count == 1
    assert summary.review_count == 0
    assert summary.blocked_count == 0
    assert summary.average_feedback_alignment_score >= 0.9
    assert summary.average_target_coverage_rate == 1.0
    assert summary.recommendation.value == "approve"
    assert summary.production_write_allowed is False


def test_training_replay_batch_needs_review_when_any_replay_needs_review() -> None:
    runtime = _runtime()
    passed = _replay("replay.phase33.pass.002", runtime.branches[0].branch_id)
    review = _replay("replay.phase33.review.001", "branch:missing:phase33")

    summary = build_training_replay_batch_summary(
        batch_id="batch.phase33.review.001",
        candidate_version="v40-phase33",
        replays=[passed, review],
    )

    assert summary.replay_count == 2
    assert summary.passed_count == 1
    assert summary.review_count == 1
    assert summary.recommendation.value == "needs_review"
    assert summary.failed_reason_counts["training_target_coverage_low"] == 1


def test_training_replay_batch_api_persists_and_lists_summary() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    runtime = _runtime()
    replay = _replay("replay.phase33.api.001", runtime.branches[0].branch_id)
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/training/replay-batches",
        json={
            "batch_id": "batch.phase33.api.001",
            "candidate_version": "v40-phase33",
            "replays": [replay.model_dump(mode="json")],
            "persist": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["recommendation"] == "approve"
    assert body["persisted"] is True
    assert body["writes_v40_production"] is False
    batches = client.get(f"{API_PREFIX}/training/replay-batches?limit=5").json()["batches"]
    assert any(row["batch_id"] == "batch.phase33.api.001" for row in batches)


def test_phase33_replay_batch_schema_repository_admin_and_manifest_are_v40_only() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    admin_source = Path("qiazhi/v40/v40/admin/app.py").read_text(encoding="utf-8")
    manifest = Path("qiazhi/v40/v40/contracts/manifest.py").read_text(encoding="utf-8")

    assert "v40_training_replay_batches" in schema
    assert "save_training_replay_batch_summary" in repository
    assert "list_training_replay_batches" in repository
    assert "/training/replay-batches" in app_source
    assert "training_replay_batches" in admin_source
    assert "latest_training_replay_batches" in admin_source
    assert "TrainingReplayBatchSummary" in manifest
    assert "v30_training_replay_batches" not in schema
    assert "v30_training_replay_batches" not in repository
