from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.engines import build_native_bazi_runtime
from v40.storage import resolve_v40_database_config
from v40.synthetic import build_evaluation_cases_from_seeds, load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_native_bazi_engine_builds_runtime_without_v30_dependency() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    runtime = build_native_bazi_runtime(
        request_id="request.phase12.native.001",
        reading_id="reading.phase12.native.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
    )

    assert runtime.v30_runtime_imported is False
    assert runtime.engine_result is not None
    assert runtime.engine_result.results[0].engine_version.startswith("v40.bazi_native.")
    assert runtime.signal_registry is not None
    assert len(runtime.signal_registry.signals) >= 3
    assert runtime.verdicts
    assert runtime.advice_plans
    assert runtime.product_projection and runtime.product_projection.leakage_scan_passed is True


def test_synthetic_seeds_generate_evaluation_cases() -> None:
    seeds = load_synthetic_seeds(SEED_PATH)
    cases = build_evaluation_cases_from_seeds(seeds)

    assert len(cases) == 2
    assert all(case.case_type.value == "synthetic" for case in cases)
    assert all(case.expected_verdicts for case in cases)
    assert all(case.forbidden_assertions for case in cases)
    assert cases[0].known_reality["synthetic"] is True


def test_native_bazi_and_synthetic_api_endpoints() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    client = TestClient(create_app())

    native_response = client.post(
        f"{API_PREFIX}/runtime/native-bazi",
        json={
            "request_id": "request.phase12.api.001",
            "reading_id": "reading.phase12.api.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": "career",
            "role_key": "user",
            "persist": False,
        },
    )
    assert native_response.status_code == 200
    native_body = native_response.json()
    assert native_body["runtime"]["v30_runtime_imported"] is False
    assert native_body["runtime"]["engine_result"]["results"][0]["engine"] == "bazi"

    synthetic_response = client.post(
        f"{API_PREFIX}/synthetic/cases/from-seeds",
        json={
            "seeds": [seed.model_dump(mode="json")],
            "persist": False,
        },
    )
    assert synthetic_response.status_code == 200
    synthetic_body = synthetic_response.json()
    assert synthetic_body["cases"][0]["case_type"] == "synthetic"
    assert synthetic_body["writes_v30_state"] is False


def test_phase12_cli_runs_native_seed() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/v40_artifact_cli.py",
            "run-native-seed",
            "--path",
            str(SEED_PATH),
            "--seed-id",
            "native.career.bingchen.001",
            "--reading-id",
            "reading.phase12.cli.001",
            "--no-persist",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    body = json.loads(result.stdout)
    assert body["reading_id"] == "reading.phase12.cli.001"
    assert body["signal_count"] >= 3
    assert body["persisted"] is False
