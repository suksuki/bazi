from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION, run_dialogue_heavy_validation_execution_plan
from v30.validation.dialogue_heavy_validation_execution_plan import (
    DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VALIDATION_VERSION,
    run_dialogue_heavy_validation_execution_plan_validation,
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


def test_dialogue_heavy_validation_execution_plan_lists_commands_without_running(tmp_path: Path) -> None:
    plan = run_dialogue_heavy_validation_execution_plan(
        run_id="dtc8-unit",
        sample_limit=8,
        persist_review=True,
        authorization_decision="authorize_recommended",
        settings=_settings(tmp_path),
    )

    assert plan["version"] == DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VERSION
    assert plan["status"] == "completed"
    assert plan["decision"]["decision_status"] == "dtc8_dialogue_heavy_validation_execution_plan_ready"
    assert plan["decision"]["planned_step_count"] == 2
    assert plan["decision"]["ready_to_execute"] is False
    assert plan["decision"]["runs_triggered"] is False
    assert plan["decision"]["promotion_allowed"] is False
    assert {row["gate_id"] for row in plan["execution_steps"]} == {"dialogue_synthetic_all", "dialogue_518k_sample"}
    assert all(row["command"] for row in plan["execution_steps"])
    assert all(row["run_triggered"] is False for row in plan["execution_steps"])


def test_dialogue_heavy_validation_execution_plan_validation_is_read_only(tmp_path: Path) -> None:
    validation = run_dialogue_heavy_validation_execution_plan_validation(
        run_id="dtc8-validation",
        sample_limit=8,
        persist_review=True,
        authorization_decision="authorize_recommended",
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_HEAVY_VALIDATION_EXECUTION_PLAN_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["planned_step_count"] == 2
    assert validation["decision"]["runs_triggered"] is False
    assert validation["decision"]["execution_started"] is False
    assert validation["decision"]["promotion_allowed"] is False
    assert validation["policy_boundary"]["manual_execution_required"] is True
