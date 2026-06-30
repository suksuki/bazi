from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.training import LabelSource, LabelTargetType, LabelValue, TrainingLabelEvent
from v40.engines import build_native_bazi_runtime
from v40.evaluation import (
    build_release_readiness_from_evidence_batches,
    build_training_replay_batch_summary,
    evaluate_cases_against_runtime,
    replay_training_example,
)
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config
from v40.synthetic import load_synthetic_seeds
from v40.training import build_training_example_from_labels


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _approved_evaluation_batch(batch_id: str):
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    runtime = build_runtime_from_v30_export(V30ExportEnvelope.model_validate(payload))
    cases = load_evaluation_cases(SEED_PATH)
    _, summary = evaluate_cases_against_runtime(
        batch_id=batch_id,
        cases=cases,
        runtime=runtime,
        candidate_version="v40-phase36",
    )
    return summary


def _native_runtime():
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    return build_native_bazi_runtime(
        request_id="request.phase36.runtime.001",
        reading_id="reading.phase36.runtime.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )


def _approved_replay_batch(batch_id: str):
    runtime = _native_runtime()
    label = TrainingLabelEvent(
        event_id=f"label:{runtime.reading_id}:phase36",
        reading_id=runtime.reading_id,
        source=LabelSource.PRACTITIONER_SELECTION,
        target_type=LabelTargetType.BRANCH,
        target_ids=[runtime.branches[0].branch_id],
        label=LabelValue.SUPPORTS,
        strength=0.84,
        confidence=0.78,
        reason="Phase36 mixed readiness label。",
        created_by_role="practitioner",
        local_only=True,
    )
    example = build_training_example_from_labels(
        example_id="example.phase36.pass.001",
        reading_id=runtime.reading_id,
        label_events=[label],
        topic=Topic.CAREER,
        local_overlay_refs=["overlay.phase36.pass.001"],
    )
    replay = replay_training_example(
        replay_id="replay.phase36.pass.001",
        training_example=example,
        runtime=runtime,
        candidate_version="v40-phase36",
    )
    return build_training_replay_batch_summary(
        batch_id=batch_id,
        candidate_version="v40-phase36",
        replays=[replay],
    )


def test_release_readiness_approves_only_with_evaluation_and_replay_evidence() -> None:
    evaluation_batch = _approved_evaluation_batch("batch.phase36.eval.001")
    replay_batch = _approved_replay_batch("batch.phase36.replay.001")

    readiness = build_release_readiness_from_evidence_batches(
        readiness_id="readiness.phase36.unit.001",
        candidate_version="v40-phase36",
        evaluation_batches=[evaluation_batch],
        replay_batches=[replay_batch],
    )

    assert readiness.recommendation == ReleaseRecommendation.APPROVE
    assert readiness.batch_count == 2
    assert readiness.approved_batch_count == 2
    assert readiness.production_write_allowed is False
    assert "evaluation:batch.phase36.eval.001" in readiness.batch_ids
    assert "replay:batch.phase36.replay.001" in readiness.batch_ids


def test_release_readiness_needs_review_when_replay_evidence_is_missing() -> None:
    evaluation_batch = _approved_evaluation_batch("batch.phase36.eval.only.001")

    readiness = build_release_readiness_from_evidence_batches(
        readiness_id="readiness.phase36.missing-replay.001",
        candidate_version="v40-phase36",
        evaluation_batches=[evaluation_batch],
        replay_batches=[],
    )

    assert readiness.recommendation == ReleaseRecommendation.NEEDS_REVIEW
    assert readiness.failed_reason_counts["missing_replay_batch"] == 1
    assert readiness.batch_count == 1


def test_release_readiness_evidence_batches_api_persists_summary() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    evaluation_batch = _approved_evaluation_batch("batch.phase36.api.eval.001")
    replay_batch = _approved_replay_batch("batch.phase36.api.replay.001")

    response = client.post(
        f"{API_PREFIX}/release-readiness/from-evidence-batches",
        json={
            "readiness_id": "readiness.phase36.api.001",
            "candidate_version": "v40-phase36",
            "evaluation_batches": [evaluation_batch.model_dump(mode="json")],
            "replay_batches": [replay_batch.model_dump(mode="json")],
            "persist": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["recommendation"] == "approve"
    assert body["writes_v40_production"] is False

    rows = client.get(f"{API_PREFIX}/release-readiness?limit=10").json()["readiness"]
    assert any(row["readiness_id"] == "readiness.phase36.api.001" for row in rows)


def test_phase36_release_readiness_evidence_batches_are_v40_only() -> None:
    readiness_source = Path("qiazhi/v40/v40/evaluation/readiness.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    models = Path("qiazhi/v40/v40/api/models.py").read_text(encoding="utf-8")

    assert "build_release_readiness_from_evidence_batches" in readiness_source
    assert "/release-readiness/from-evidence-batches" in app_source
    assert "ReleaseReadinessFromEvidenceBatchesRequest" in models
    assert "missing_replay_batch" in readiness_source
    assert "writes_v40_production" in app_source
    assert "v30_" not in readiness_source
