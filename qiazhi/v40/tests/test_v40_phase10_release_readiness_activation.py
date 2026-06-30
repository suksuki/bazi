from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary
from v40.evaluation import build_release_readiness_from_batches, evaluate_cases_against_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config
from v40.training import build_candidate_weight_version_from_batch, build_weight_activation_review

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _approved_batch(batch_id: str) -> EvaluationBatchSummary:
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    runtime = build_runtime_from_v30_export(V30ExportEnvelope.model_validate(payload))
    cases = load_evaluation_cases(SEED_PATH)
    _, summary = evaluate_cases_against_runtime(
        batch_id=batch_id,
        cases=cases,
        runtime=runtime,
        candidate_version="v40-alpha-phase10",
    )
    return summary


def test_release_readiness_and_activation_review_do_not_apply_weights() -> None:
    batch = _approved_batch("batch.phase10.unit.001")
    readiness = build_release_readiness_from_batches(
        readiness_id="readiness.phase10.unit.001",
        candidate_version="v40-alpha-phase10",
        batches=[batch],
    )
    assert readiness.recommendation == ReleaseRecommendation.APPROVE
    assert readiness.production_write_allowed is False

    weight = build_candidate_weight_version_from_batch(
        summary=batch,
        weight_version_id="weight.phase10.unit.001",
        source_training_run_id="train.phase10.unit.001",
        release_gate_id="gate.phase10.unit.001",
    )
    review = build_weight_activation_review(
        review_id="activation.phase10.unit.001",
        weight_version=weight,
        release_readiness=readiness,
    )
    assert review.decision == ReleaseRecommendation.APPROVE
    assert review.activation_applied is False
    assert review.production_write_allowed is False


def test_release_readiness_api_and_activation_review_persist() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    batch = _approved_batch("batch.phase10.api.001")
    weight = build_candidate_weight_version_from_batch(
        summary=batch,
        weight_version_id="weight.phase10.api.001",
        source_training_run_id="train.phase10.api.001",
        release_gate_id="gate.phase10.api.001",
    )

    readiness_response = client.post(
        f"{API_PREFIX}/release-readiness/from-batches",
        json={
            "readiness_id": "readiness.phase10.api.001",
            "candidate_version": "v40-alpha-phase10",
            "batches": [batch.model_dump(mode="json")],
            "persist": True,
        },
    )
    assert readiness_response.status_code == 200
    readiness_body = readiness_response.json()
    assert readiness_body["summary"]["recommendation"] == "approve"
    assert readiness_body["writes_v40_production"] is False

    review_response = client.post(
        f"{API_PREFIX}/weights/activation-reviews",
        json={
            "review_id": "activation.phase10.api.001",
            "weight_version": weight.model_dump(mode="json"),
            "release_readiness": readiness_body["summary"],
            "reviewed_by_role": "admin",
            "persist": True,
        },
    )
    assert review_response.status_code == 200
    review_body = review_response.json()
    assert review_body["activation_applied"] is False
    assert review_body["writes_v40_production"] is False

    readiness_rows = client.get(f"{API_PREFIX}/release-readiness?limit=5").json()["readiness"]
    assert any(row["readiness_id"] == "readiness.phase10.api.001" for row in readiness_rows)
    review_rows = client.get(f"{API_PREFIX}/weights/activation-reviews?limit=5").json()["reviews"]
    assert any(row["review_id"] == "activation.phase10.api.001" for row in review_rows)
