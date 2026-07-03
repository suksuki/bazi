from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION, run_dialogue_heavy_validation_authorization
from v30.validation.dialogue_heavy_validation_authorization import (
    DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VALIDATION_VERSION,
    run_dialogue_heavy_validation_authorization_validation,
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


def test_dialogue_heavy_validation_authorization_records_intent_without_execution(tmp_path: Path) -> None:
    result = run_dialogue_heavy_validation_authorization(
        run_id="dtc7-unit",
        sample_limit=8,
        persist_review=True,
        authorization_decision="authorize_recommended",
        settings=_settings(tmp_path),
    )

    assert result["version"] == DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "dtc7_dialogue_heavy_validation_authorization_ready"
    assert set(result["decision"]["authorized_gate_ids"]) == {"dialogue_synthetic_all", "dialogue_518k_sample"}
    assert result["decision"]["runs_triggered"] is False
    assert result["decision"]["execution_allowed_in_this_step"] is False
    assert result["decision"]["promotion_allowed"] is False
    assert result["policy_boundary"]["execution_requires_dtc8"] is True


def test_dialogue_heavy_validation_authorization_can_defer_all(tmp_path: Path) -> None:
    result = run_dialogue_heavy_validation_authorization(
        run_id="dtc7-defer",
        sample_limit=8,
        persist_review=True,
        authorization_decision="defer_all",
        settings=_settings(tmp_path),
    )

    assert result["status"] == "completed"
    assert result["decision"]["authorized_gate_ids"] == []
    assert result["decision"]["runs_triggered"] is False
    assert result["next_mainline_selection"]["task_id"] == "DTC-7-WAIT"


def test_dialogue_heavy_validation_authorization_validation_blocks_execution(tmp_path: Path) -> None:
    validation = run_dialogue_heavy_validation_authorization_validation(
        run_id="dtc7-validation",
        sample_limit=8,
        persist_review=True,
        authorization_decision="authorize_recommended",
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_HEAVY_VALIDATION_AUTHORIZATION_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert set(validation["decision"]["authorized_gate_ids"]) == {"dialogue_synthetic_all", "dialogue_518k_sample"}
    assert validation["decision"]["runs_triggered"] is False
    assert validation["decision"]["execution_allowed_in_this_step"] is False
    assert validation["decision"]["promotion_allowed"] is False
