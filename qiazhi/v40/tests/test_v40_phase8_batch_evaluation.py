from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.evaluation import evaluate_cases_against_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _runtime_from_fixture():
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    return build_runtime_from_v30_export(V30ExportEnvelope.model_validate(payload))


def test_batch_evaluation_aggregates_many_case_results() -> None:
    cases = load_evaluation_cases(SEED_PATH)
    runtime = _runtime_from_fixture()

    runs, summary = evaluate_cases_against_runtime(
        batch_id="batch.phase8.unit.001",
        cases=cases,
        runtime=runtime,
        candidate_version="v40-alpha-phase8",
    )

    assert len(runs) == 1
    assert summary.case_count == 1
    assert summary.passed_count == 1
    assert summary.blocked_count == 0
    assert summary.average_overall_score >= 0.82
    assert summary.production_write_allowed is False


def test_batch_evaluation_api_and_cli_persist_summary() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    cases = load_evaluation_cases(SEED_PATH)
    runtime = _runtime_from_fixture()
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/evaluation/batches/from-runtime",
        json={
            "batch_id": "batch.phase8.api.001",
            "cases": [case.model_dump(mode="json") for case in cases],
            "runtime": runtime.model_dump(mode="json"),
            "candidate_version": "v40-alpha-phase8",
            "persist": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is True
    assert body["summary"]["case_count"] == 1
    assert body["summary"]["production_write_allowed"] is False

    batches = client.get(f"{API_PREFIX}/evaluation/batches?limit=5").json()["batches"]
    assert any(batch["batch_id"] == "batch.phase8.api.001" for batch in batches)

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/v40_artifact_cli.py",
            "run-batch",
            "--cases",
            str(SEED_PATH),
            "--v30-export",
            str(EXPORT_PATH),
            "--batch-id",
            "batch.phase8.cli.001",
            "--candidate-version",
            "v40-alpha-phase8",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_body = json.loads(cli.stdout)
    assert cli_body["batch_id"] == "batch.phase8.cli.001"
    assert cli_body["case_count"] == 1
