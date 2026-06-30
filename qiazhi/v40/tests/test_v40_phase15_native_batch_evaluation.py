from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.evaluation import evaluate_native_seeds
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_native_seed_batch_builds_one_runtime_per_case() -> None:
    seeds = load_synthetic_seeds(SEED_PATH)

    runtimes, cases, runs, summary = evaluate_native_seeds(
        batch_id="batch.phase15.native.001",
        seeds=seeds,
        candidate_version="v40-native-phase15",
    )

    assert len(runtimes) == len(seeds) == len(cases) == len(runs)
    assert summary.case_count == len(seeds)
    assert len({runtime.reading_id for runtime in runtimes}) == len(seeds)
    assert all(runtime.engine_result for runtime in runtimes)
    assert all(run.release_gate for run in runs)
    assert summary.run_ids == [run.run_id for run in runs]


def test_native_batch_from_seeds_api_does_not_touch_v30_or_production() -> None:
    seeds = load_synthetic_seeds(SEED_PATH)
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/evaluation/native-batch/from-seeds",
        json={
            "batch_id": "batch.phase15.api.001",
            "candidate_version": "v40-native-phase15",
            "seeds": [seed.model_dump(mode="json") for seed in seeds],
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["case_count"] == len(seeds)
    assert len(body["runs"]) == len(seeds)
    assert len(body["runtime_refs"]) == len(seeds)
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
