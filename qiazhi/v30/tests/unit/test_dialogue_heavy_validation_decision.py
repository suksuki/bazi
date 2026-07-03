from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION, run_dialogue_heavy_validation_decision
from v30.validation.dialogue_heavy_validation_decision import (
    DIALOGUE_HEAVY_VALIDATION_DECISION_VALIDATION_VERSION,
    run_dialogue_heavy_validation_decision_validation,
)


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_dialogue_heavy_validation_decision_recommends_gates_without_execution(tmp_path: Path) -> None:
    result = run_dialogue_heavy_validation_decision(
        run_id="dtc6-unit",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert result["version"] == DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "dtc6_dialogue_heavy_validation_decision_ready"
    assert result["decision"]["heavy_validation_recommended"] is True
    assert set(result["decision"]["recommended_gate_ids"]) == {"dialogue_synthetic_all", "dialogue_518k_sample"}
    assert result["decision"]["runs_triggered"] is False
    assert result["decision"]["promotion_allowed"] is False
    assert result["decision"]["policy_pointer_write_allowed"] is False
    assert all(row["run_triggered"] is False for row in result["gate_matrix"])


def test_dialogue_heavy_validation_decision_validation_keeps_release_blocked(tmp_path: Path) -> None:
    validation = run_dialogue_heavy_validation_decision_validation(
        run_id="dtc6-validation",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_HEAVY_VALIDATION_DECISION_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["heavy_validation_recommended"] is True
    assert validation["decision"]["runs_triggered"] is False
    assert validation["decision"]["promotion_allowed"] is False
    assert validation["decision"]["policy_pointer_write_allowed"] is False
    assert validation["policy_boundary"]["heavy_validation_execution_allowed"] is False
