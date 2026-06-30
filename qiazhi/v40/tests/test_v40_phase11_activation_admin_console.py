from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.contracts.base import ReleaseRecommendation
from v40.contracts.training import WeightActivationExecution
from v40.evaluation import build_release_readiness_from_batches, evaluate_cases_against_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config
from v40.training import build_candidate_weight_version_from_batch, build_weight_activation_execution, build_weight_activation_review


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _approved_batch():
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    runtime = build_runtime_from_v30_export(V30ExportEnvelope.model_validate(payload))
    cases = load_evaluation_cases(SEED_PATH)
    _, summary = evaluate_cases_against_runtime(
        batch_id="batch.phase11.unit.001",
        cases=cases,
        runtime=runtime,
        candidate_version="v40-alpha-phase11",
    )
    return summary


def test_weight_activation_execution_requires_review_and_rollback() -> None:
    batch = _approved_batch()
    weight = build_candidate_weight_version_from_batch(
        summary=batch,
        weight_version_id="weight.phase11.unit.001",
        source_training_run_id="train.phase11.unit.001",
        release_gate_id="gate.phase11.unit.001",
    )
    readiness = build_release_readiness_from_batches(
        readiness_id="readiness.phase11.unit.001",
        candidate_version="v40-alpha-phase11",
        batches=[batch],
    )
    review = build_weight_activation_review(
        review_id="review.phase11.unit.001",
        weight_version=weight,
        release_readiness=readiness,
    )
    execution = build_weight_activation_execution(
        execution_id="execution.phase11.unit.001",
        review=review,
        weight_version=weight,
        rollback_version_id="weight.rollback.phase10",
    )
    assert isinstance(execution, WeightActivationExecution)
    assert execution.review_decision == ReleaseRecommendation.APPROVE
    assert execution.activation_applied is True
    assert execution.v30_state_mutated is False

    with pytest.raises(ValueError, match="rollback_version_id"):
        build_weight_activation_execution(
            execution_id="execution.phase11.bad.001",
            review=review,
            weight_version=weight,
            rollback_version_id="",
        )


def test_weight_activation_api_requires_confirmation_and_sets_active() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    batch = _approved_batch()
    candidate = client.post(
        f"{API_PREFIX}/weights/candidates/from-batch",
        json={
            "weight_version_id": "weight.phase11.api.001",
            "source_training_run_id": "train.phase11.api.001",
            "release_gate_id": "gate.phase11.api.001",
            "batch_summary": batch.model_dump(mode="json"),
            "persist": True,
        },
    ).json()["weight_version"]
    readiness = client.post(
        f"{API_PREFIX}/release-readiness/from-batches",
        json={
            "readiness_id": "readiness.phase11.api.001",
            "candidate_version": "v40-alpha-phase11",
            "batches": [batch.model_dump(mode="json")],
            "persist": True,
        },
    ).json()["summary"]
    review = client.post(
        f"{API_PREFIX}/weights/activation-reviews",
        json={
            "review_id": "review.phase11.api.001",
            "weight_version": candidate,
            "release_readiness": readiness,
            "reviewed_by_role": "admin",
            "persist": True,
        },
    ).json()["review"]

    rejected = client.post(
        f"{API_PREFIX}/weights/activate",
        json={
            "execution_id": "execution.phase11.bad-confirm.001",
            "review": review,
            "weight_version": candidate,
            "rollback_version_id": "weight.rollback.phase10",
            "confirm_phrase": "YES",
        },
    )
    assert rejected.status_code == 422

    response = client.post(
        f"{API_PREFIX}/weights/activate",
        json={
            "execution_id": "execution.phase11.api.001",
            "review": review,
            "weight_version": candidate,
            "rollback_version_id": "weight.rollback.phase10",
            "confirm_phrase": "ACTIVATE_V40_WEIGHT",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["activation_applied"] is True
    assert body["writes_v30_state"] is False
    assert body["writes_v40_weight"] is True

    weights = client.get(f"{API_PREFIX}/weights/candidates?limit=10").json()["weights"]
    active = [row for row in weights if row["weight_version_id"] == "weight.phase11.api.001"]
    assert active and active[0]["active"] is True
    assert active[0]["rollback_version_id"] == "weight.rollback.phase10"


def test_v40_admin_console_serves_independent_read_model_surface() -> None:
    client = TestClient(create_admin_app())

    health = client.get(f"{ADMIN_PREFIX}/health").json()
    assert health["ok"] is True
    assert health["package"] == "v40-admin"

    page = client.get(ADMIN_PREFIX)
    assert page.status_code == 200
    assert "掐指一算 V40 Control Plane" in page.text
    assert "/admin/v40/api/summary" in page.text
