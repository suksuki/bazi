from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.test_central_brain_phase2_replay_gate import _example
from v30.api.app import create_app
from v30.training import BrainTrainingExampleStore
from v30.validation.central_brain_phase2_distribution_gate import build_central_brain_phase2_distribution_gate


def test_phase2_distribution_gate_passes_eligible_sample() -> None:
    gate = build_central_brain_phase2_distribution_gate(
        replay_gate=_replay_gate("eligible"),
        sample_result=_result("sample", "eligible", 8),
        min_sample_cases=8,
    )

    assert gate["version"] == "v30.central_brain_phase2_distribution_gate.v1"
    assert gate["promotion_signal"] == "eligible"
    assert gate["decision"]["full_518k_required"] is False
    assert gate["chart_fact_mutation_allowed"] is False


def test_phase2_distribution_gate_blocks_failed_sample_or_missing_shard() -> None:
    failed = build_central_brain_phase2_distribution_gate(
        replay_gate=_replay_gate("eligible"),
        sample_result=_result("sample", "blocked", 8, failures=[{"reason": "distribution_drift"}]),
        min_sample_cases=8,
    )
    missing_shard = build_central_brain_phase2_distribution_gate(
        replay_gate=_replay_gate("eligible"),
        sample_result=_result("sample", "eligible", 8),
        require_shard=True,
    )

    assert failed["promotion_signal"] == "blocked"
    assert "sample_518k_eligible" in failed["decision"]["failed_check_ids"]
    assert "sample_518k_failure_free" in failed["decision"]["failed_check_ids"]
    assert missing_shard["promotion_signal"] == "blocked"
    assert "shard_518k_required" in missing_shard["decision"]["failed_check_ids"]


def test_phase2_distribution_gate_admin_api_runs_518k_sample(tmp_path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    store = BrainTrainingExampleStore(runtime_dir)
    for index in range(8):
        store.append(_example(f"distribution-api-{index}"))
    store.build_splits(seed=5, train_ratio=0.6, validation_ratio=0.2)
    client = TestClient(create_app())

    response = client.post(
        "/api/v30/admin/training/brain-examples/distribution-gate",
        json={
            "train_split": "train",
            "replay_split": "replay",
            "min_examples": 3,
            "min_replay_examples": 1,
            "sample_limit": 1,
            "include_shard": False,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["version"] == "v30.admin.brain_training_example_distribution_gate.v1"
    assert payload["gate"]["promotion_signal"] == "eligible"
    assert payload["gate"]["distribution_518k"]["sample"]["case_count"] == 1
    assert payload["chart_fact_mutation_allowed"] is False


def _replay_gate(signal: str) -> dict[str, object]:
    return {
        "version": "v30.central_brain_phase2_replay_gate.v1",
        "status": "passed" if signal == "eligible" else "blocked",
        "promotion_signal": signal,
        "chart_fact_mutation_allowed": False,
    }


def _result(mode: str, signal: str, case_count: int, failures=None) -> dict[str, object]:
    return {
        "run_id": f"v30.518k.{mode}.unit",
        "mode": mode,
        "case_count": case_count,
        "promotion_signal": signal,
        "failure_clusters": failures or [],
        "chart_fact_mutation_allowed": False,
    }
