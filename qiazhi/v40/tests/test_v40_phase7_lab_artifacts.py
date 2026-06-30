from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.artifacts import load_evaluation_cases
from v40.storage import resolve_v40_database_config


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "golden_cases" / "seed_career.json"


def test_golden_case_seed_artifact_loads_contracts() -> None:
    cases = load_evaluation_cases(SEED_PATH)

    assert len(cases) == 1
    assert cases[0].case_id == "golden.career.stable_then_breakthrough.001"
    assert cases[0].expected_verdicts
    assert cases[0].forbidden_assertions


def test_artifact_cli_imports_cases_and_lab_summary_reads_counts() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    result = subprocess.run(
        [sys.executable, "scripts/v40_artifact_cli.py", "import-cases", "--path", str(SEED_PATH)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    body = json.loads(result.stdout)
    assert body["imported"] == 1

    client = TestClient(create_app())
    response = client.get(f"{API_PREFIX}/lab/summary")
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["counts"]["evaluation_cases"] >= 1
    assert "latest_evaluation_runs" in summary
    assert "latest_training_impacts" in summary
    assert "latest_release_gates" in summary
