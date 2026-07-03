from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION, run_dialogue_strategy_validation_gate
from v30.validation.dialogue_strategy_validation_gate import (
    DIALOGUE_STRATEGY_VALIDATION_GATE_VALIDATION_VERSION,
    run_dialogue_strategy_validation_gate_validation,
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


def test_dialogue_strategy_validation_gate_routes_candidate_to_synthetic_replay(tmp_path: Path) -> None:
    gate = run_dialogue_strategy_validation_gate(
        run_id="dtc3-unit",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert gate["version"] == DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION
    assert gate["status"] == "completed"
    assert gate["decision"]["decision_status"] == "dtc3_dialogue_strategy_validation_gate_ready"
    assert gate["decision"]["candidate_deserves_synthetic_replay"] is True
    assert gate["decision"]["policy_pointer_write_allowed"] is False
    assert gate["decision"]["chart_fact_mutation_allowed"] is False
    assert gate["replay_evaluation"]["meaningful_policy_delta"] is True
    assert gate["replay_evaluation"]["synthetic_replay_recommended"] is True
    assert gate["artifact_search"]["count"] >= 1


def test_dialogue_strategy_validation_gate_validation_blocks_promotion(tmp_path: Path) -> None:
    validation = run_dialogue_strategy_validation_gate_validation(
        run_id="dtc3-validation",
        sample_limit=8,
        persist_review=True,
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_STRATEGY_VALIDATION_GATE_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["candidate_deserves_synthetic_replay"] is True
    assert validation["decision"]["promotion_allowed"] is False
    assert validation["decision"]["policy_pointer_write_allowed"] is False
    assert validation["policy_boundary"]["policy_pointer_promotion_allowed"] is False
