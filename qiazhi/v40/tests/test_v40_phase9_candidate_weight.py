from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.contracts.base import ReleaseRecommendation
from v40.contracts.evaluation import EvaluationBatchSummary
from v40.evaluation import evaluate_cases_against_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config
from v40.training import build_candidate_weight_version_from_batch


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _approved_batch_summary() -> EvaluationBatchSummary:
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    runtime = build_runtime_from_v30_export(V30ExportEnvelope.model_validate(payload))
    cases = load_evaluation_cases(SEED_PATH)
    _, summary = evaluate_cases_against_runtime(
        batch_id="batch.phase9.unit.001",
        cases=cases,
        runtime=runtime,
        candidate_version="v40-alpha-phase9",
    )
    return summary


def test_candidate_weight_version_requires_approved_batch() -> None:
    summary = _approved_batch_summary()
    weight = build_candidate_weight_version_from_batch(
        summary=summary,
        weight_version_id="weight.phase9.unit.001",
        source_training_run_id="train.phase9.unit.001",
        release_gate_id="gate.phase9.unit.001",
    )
    assert weight.active is False
    assert weight.release_gate_id == "gate.phase9.unit.001"

    rejected = EvaluationBatchSummary(
        batch_id="batch.phase9.rejected.001",
        candidate_version="v40-alpha-phase9",
        case_count=1,
        run_ids=["run-1"],
        blocked_count=1,
        recommendation=ReleaseRecommendation.REJECT,
    )
    with pytest.raises(ValueError, match="requires approved batch"):
        build_candidate_weight_version_from_batch(
            summary=rejected,
            weight_version_id="weight.phase9.rejected.001",
            source_training_run_id="train.phase9.rejected.001",
            release_gate_id="gate.phase9.rejected.001",
        )


def test_candidate_weight_api_persists_without_activation() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    summary = _approved_batch_summary()

    response = client.post(
        f"{API_PREFIX}/weights/candidates/from-batch",
        json={
            "weight_version_id": "weight.phase9.api.001",
            "source_training_run_id": "train.phase9.api.001",
            "release_gate_id": "gate.phase9.api.001",
            "batch_summary": summary.model_dump(mode="json"),
            "persist": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["active"] is False
    assert body["writes_v40_production"] is False
    assert body["weight_version"]["active"] is False

    weights = client.get(f"{API_PREFIX}/weights/candidates?limit=5").json()["weights"]
    assert any(weight["weight_version_id"] == "weight.phase9.api.001" for weight in weights)
