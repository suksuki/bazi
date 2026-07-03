from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION, run_dialogue_synthetic_replay_queue
from v30.validation.dialogue_synthetic_replay_queue import (
    DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VALIDATION_VERSION,
    run_dialogue_synthetic_replay_queue_validation,
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


def test_dialogue_synthetic_replay_queue_batches_candidate_across_cases(tmp_path: Path) -> None:
    queue = run_dialogue_synthetic_replay_queue(
        run_id="dtc4-unit",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert queue["version"] == DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION
    assert queue["status"] == "completed"
    assert queue["decision"]["decision_status"] == "dtc4_dialogue_synthetic_replay_queue_ready"
    assert queue["decision"]["candidate_ready_for_operator_review"] is True
    assert queue["decision"]["promotion_allowed"] is False
    assert queue["decision"]["policy_pointer_write_allowed"] is False
    assert queue["aggregate"]["case_count"] >= 4
    assert queue["aggregate"]["pass_ratio"] == 1.0
    assert queue["aggregate"]["average_weighted_delta_count"] > 0
    assert all(row["passed"] is True for row in queue["replay_cases"])


def test_dialogue_synthetic_replay_queue_validation_remains_read_only(tmp_path: Path) -> None:
    validation = run_dialogue_synthetic_replay_queue_validation(
        run_id="dtc4-validation",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["candidate_ready_for_operator_review"] is True
    assert validation["decision"]["promotion_allowed"] is False
    assert validation["decision"]["policy_pointer_write_allowed"] is False
    assert validation["policy_boundary"]["policy_pointer_promotion_allowed"] is False
