from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent
from v40.engines import build_native_bazi_runtime
from v40.evaluation import replay_training_example
from v40.storage import resolve_v40_database_config
from v40.synthetic import load_synthetic_seeds
from v40.training import build_training_example_from_labels


def _runtime():
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    return build_native_bazi_runtime(
        request_id="request.phase32.runtime.001",
        reading_id="reading.phase32.runtime.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )


def _label(reading_id: str, target_id: str) -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id=f"label:{reading_id}:phase32:{target_id}",
        reading_id=reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=[target_id],
        label=LabelValue.SUPPORTS,
        strength=0.78,
        confidence=0.72,
        reason="命理师确认该目标可进入 replay。",
        created_by_role="practitioner",
        local_only=True,
    )


def test_training_example_replay_passes_when_feedback_target_is_runtime_bound() -> None:
    runtime = _runtime()
    target_id = runtime.branches[0].branch_id
    example = build_training_example_from_labels(
        example_id="example.phase32.pass.001",
        reading_id=runtime.reading_id,
        label_events=[_label(runtime.reading_id, target_id)],
        topic=Topic.CAREER,
        local_overlay_refs=["overlay.phase32.pass.001"],
    )

    replay = replay_training_example(
        replay_id="replay.phase32.pass.001",
        training_example=example,
        runtime=runtime,
        candidate_version="v40-phase32",
    )

    assert replay.status.value == "passed"
    assert replay.recommendation.value == "approve"
    assert replay.target_coverage_rate == 1.0
    assert replay.feedback_alignment_score >= 0.9
    assert replay.matched_target_ids == [target_id]
    assert replay.production_write_allowed is False
    assert replay.chart_fact_mutation_allowed is False


def test_training_example_replay_reviews_missing_feedback_target() -> None:
    runtime = _runtime()
    example = build_training_example_from_labels(
        example_id="example.phase32.review.001",
        reading_id=runtime.reading_id,
        label_events=[_label(runtime.reading_id, "branch:missing:phase32")],
        topic=Topic.CAREER,
    )

    replay = replay_training_example(
        replay_id="replay.phase32.review.001",
        training_example=example,
        runtime=runtime,
    )

    assert replay.status.value == "review"
    assert replay.recommendation.value == "needs_review"
    assert replay.target_coverage_rate == 0.0
    assert replay.missing_target_ids == ["branch:missing:phase32"]
    assert "training_target_coverage_low" in replay.failed_reasons


def test_training_example_replay_api_persists_and_lists_result() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    runtime = _runtime()
    target_id = runtime.branches[0].branch_id
    example = build_training_example_from_labels(
        example_id="example.phase32.api.001",
        reading_id=runtime.reading_id,
        label_events=[_label(runtime.reading_id, target_id)],
        topic=Topic.CAREER,
    )
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/training/replay-example",
        json={
            "replay_id": "replay.phase32.api.001",
            "training_example": example.model_dump(mode="json"),
            "runtime": runtime.model_dump(mode="json"),
            "candidate_version": "v40-phase32",
            "persist": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["replay"]["status"] == "passed"
    assert body["persisted"] is True
    assert body["writes_v40_production"] is False
    listed = client.get(f"{API_PREFIX}/training/example-replays?reading_id={runtime.reading_id}&limit=5").json()["replays"]
    assert any(row["replay_id"] == "replay.phase32.api.001" for row in listed)


def test_phase32_replay_schema_repository_and_manifest_are_v40_only() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    manifest = Path("qiazhi/v40/v40/contracts/manifest.py").read_text(encoding="utf-8")

    assert "v40_training_example_replays" in schema
    assert "idx_v40_training_example_replays_reading" in schema
    assert "save_training_example_replay" in repository
    assert "list_training_example_replays" in repository
    assert "/training/replay-example" in app_source
    assert "/training/example-replays" in app_source
    assert "TrainingExampleReplayResult" in manifest
    assert "v30_training_example_replays" not in schema
    assert "v30_training_example_replays" not in repository
