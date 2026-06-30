from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import TrainingReplayBatchSummary
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent
from v40.engines import build_native_bazi_runtime
from v40.evaluation import build_training_replay_batch_summary, replay_training_example
from v40.storage import resolve_v40_database_config
from v40.synthetic import load_synthetic_seeds
from v40.training import build_candidate_weight_version_from_replay_batch, build_training_example_from_labels


def _runtime():
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    return build_native_bazi_runtime(
        request_id="request.phase35.runtime.001",
        reading_id="reading.phase35.runtime.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )


def _label(reading_id: str, target_id: str) -> TrainingLabelEvent:
    return TrainingLabelEvent(
        event_id=f"label:{reading_id}:phase35:{target_id}",
        reading_id=reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=[target_id],
        label=LabelValue.SUPPORTS,
        strength=0.82,
        confidence=0.76,
        reason="Phase35 replay batch candidate weight label。",
        created_by_role="practitioner",
        local_only=True,
    )


def _approved_replay_batch() -> TrainingReplayBatchSummary:
    runtime = _runtime()
    example = build_training_example_from_labels(
        example_id="example.phase35.pass.001",
        reading_id=runtime.reading_id,
        label_events=[_label(runtime.reading_id, runtime.branches[0].branch_id)],
        topic=Topic.CAREER,
        local_overlay_refs=["overlay.phase35.pass.001"],
    )
    replay = replay_training_example(
        replay_id="replay.phase35.pass.001",
        training_example=example,
        runtime=runtime,
        candidate_version="v40-phase35",
    )
    return build_training_replay_batch_summary(
        batch_id="batch.phase35.pass.001",
        candidate_version="v40-phase35",
        replays=[replay],
    )


def test_replay_batch_candidate_weight_requires_approved_replay_batch() -> None:
    summary = _approved_replay_batch()

    weight = build_candidate_weight_version_from_replay_batch(
        summary=summary,
        weight_version_id="weight.phase35.unit.001",
        source_training_run_id="train.phase35.unit.001",
        release_gate_id="gate.phase35.unit.001",
    )

    assert weight.active is False
    assert weight.source_training_run_id == "train.phase35.unit.001"
    assert weight.release_gate_id == "gate.phase35.unit.001"

    needs_review = TrainingReplayBatchSummary(
        batch_id="batch.phase35.review.001",
        candidate_version="v40-phase35",
        replay_count=1,
        replay_ids=["replay.phase35.review.001"],
        review_count=1,
        recommendation=ReleaseRecommendation.NEEDS_REVIEW,
    )

    with pytest.raises(ValueError, match="requires approved replay batch"):
        build_candidate_weight_version_from_replay_batch(
            summary=needs_review,
            weight_version_id="weight.phase35.review.001",
            source_training_run_id="train.phase35.review.001",
            release_gate_id="gate.phase35.review.001",
        )


def test_replay_batch_candidate_weight_api_persists_without_activation() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    summary = _approved_replay_batch()

    response = client.post(
        f"{API_PREFIX}/weights/candidates/from-replay-batch",
        json={
            "weight_version_id": "weight.phase35.api.001",
            "source_training_run_id": "train.phase35.api.001",
            "release_gate_id": "gate.phase35.api.001",
            "replay_batch_summary": summary.model_dump(mode="json"),
            "persist": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["active"] is False
    assert body["writes_v40_production"] is False
    assert body["weight_version"]["active"] is False

    weights = client.get(f"{API_PREFIX}/weights/candidates?limit=10").json()["weights"]
    assert any(weight["weight_version_id"] == "weight.phase35.api.001" for weight in weights)


def test_phase35_replay_batch_candidate_weight_boundary_is_v40_only() -> None:
    candidate = Path("qiazhi/v40/v40/training/candidate.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    models = Path("qiazhi/v40/v40/api/models.py").read_text(encoding="utf-8")
    project_status = Path("qiazhi/v40/v40/project/status.py").read_text(encoding="utf-8")

    assert "build_candidate_weight_version_from_replay_batch" in candidate
    assert "/weights/candidates/from-replay-batch" in app_source
    assert "CandidateWeightFromReplayBatchRequest" in models
    assert "CURRENT_PHASE = 35" in project_status
    assert "writes_v40_production" in app_source
    assert "v30_" not in candidate
