from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.test_brain_training_examples_phase2 import _decision_trace
from v30.api.app import create_app
from v30.brain import optimize_central_brain_policy
from v30.training import BrainTrainingExampleStore, build_brain_training_example
from v30.validation.central_brain_phase2_replay_gate import build_central_brain_phase2_replay_gate


def test_phase2_replay_gate_passes_eligible_candidate_and_safe_replay_examples() -> None:
    examples = [_example(f"good-{index}") for index in range(5)]
    candidate = optimize_central_brain_policy(examples, min_examples=3)
    gate = build_central_brain_phase2_replay_gate(
        candidate_policy=candidate,
        replay_examples=examples[:2],
        validation_result=_validation_result(),
        min_replay_examples=1,
    )

    assert gate["version"] == "v30.central_brain_phase2_replay_gate.v1"
    assert gate["promotion_signal"] == "eligible"
    assert gate["decision"]["phase2_replay_gate_ready"] is True
    assert gate["chart_fact_mutation_allowed"] is False


def test_phase2_replay_gate_blocks_high_risk_replay_examples() -> None:
    train_examples = [_example(f"train-{index}") for index in range(5)]
    risky_replay = [
        _example(
            f"risky-{index}",
            claim_correctness=0.25,
            template_risk=0.8,
            overclaim_risk=0.75,
        )
        for index in range(2)
    ]
    candidate = optimize_central_brain_policy(train_examples, min_examples=3)
    gate = build_central_brain_phase2_replay_gate(
        candidate_policy=candidate,
        replay_examples=risky_replay,
        validation_result=_validation_result(),
        min_replay_examples=1,
    )

    assert gate["promotion_signal"] == "blocked"
    failed = set(gate["decision"]["failed_check_ids"])
    assert "replay_template_risk" in failed
    assert "replay_overclaim_risk" in failed


def test_phase2_replay_gate_admin_api_runs_candidate_and_gate(tmp_path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    store = BrainTrainingExampleStore(runtime_dir)
    for index in range(8):
        store.append(_example(f"api-{index}"))
    store.build_splits(seed=3, train_ratio=0.6, validation_ratio=0.2)
    client = TestClient(create_app())

    response = client.post(
        "/api/v30/admin/training/brain-examples/replay-gate",
        json={"train_split": "train", "replay_split": "replay", "min_examples": 3, "min_replay_examples": 1},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["version"] == "v30.admin.brain_training_example_replay_gate.v1"
    assert payload["gate"]["promotion_signal"] == "eligible"
    assert payload["chart_fact_mutation_allowed"] is False


def _example(
    example_id: str,
    *,
    claim_correctness: float = 0.86,
    template_risk: float = 0.08,
    overclaim_risk: float = 0.1,
):
    return build_brain_training_example(
        reading_id="phase2-reading",
        source="runtime_feedback",
        decision=_decision_trace(),
        question_outcome={"confirmed": True, "selected_option": example_id, "followup_useful": True},
        labels={
            "claim_correctness": claim_correctness,
            "question_information_gain": 0.78,
            "advice_actionability": 0.82,
            "template_risk": template_risk,
            "overclaim_risk": overclaim_risk,
            "user_cost": 0.18,
        },
        example_id=example_id,
    )


def _validation_result() -> dict[str, object]:
    return {
        "version": "v30.central_reading_synthetic_validation.v1",
        "status": "completed",
        "decision": {
            "central_reading_synthetic_ready": True,
            "failed_check_ids": [],
            "chart_fact_mutation_allowed": False,
        },
    }
